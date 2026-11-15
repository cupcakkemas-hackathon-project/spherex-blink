"""Live pipeline: IRSA SIA2 query -> cutouts -> common-grid reprojection.

STATUS: verified against the live IRSA SIA2 service on 2026-11-14.
See docs/irsa_notes.md for the observed columns and FITS structure.
"""
import concurrent.futures as cf
import hashlib
import io
import logging
import os
import re
import threading
import time
import warnings

import numpy as np
from astropy import log as astropy_log
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.table import vstack
from astropy.wcs import WCS
from reproject import reproject_interp

logging.getLogger("astropy.wcs.wcs").setLevel(logging.ERROR)
astropy_log.setLevel("WARNING")

COLLECTION = os.environ.get("SPHEREX_COLLECTION", "spherex_dr1,spherex_qr3")
CACHE_DIR = os.environ.get("CACHE_DIR", ".cache")
MAX_FRAMES = int(os.environ.get("MAX_FRAMES", "60"))
RAW_CACHE_TTL_SECONDS = float(os.environ.get("RAW_CACHE_TTL_SECONDS", str(4 * 60 * 60)))
OUT_PIX = 64
PIX_SCALE_ARCSEC = 6.2  # SPHEREx native pixel size
_RAW_CACHE: dict[tuple, tuple[float, list[dict]]] = {}
_RAW_CACHE_LOCK = threading.Lock()
_FLAG_REPROJECT_LOCK = threading.Lock()
_WCS_WARNING_COUNTS = {"reproject": 0, "wavelength": 0}
_WCS_WARNING_LOCK = threading.Lock()
LOGGER = logging.getLogger(__name__)
DOWNLOAD_TIMEOUT_SECONDS = float(os.environ.get("IRSA_TIMEOUT_SECONDS", "30"))
DOWNLOAD_ATTEMPTS = 3


class IRSAUnavailableError(RuntimeError):
    """Raised when IRSA cannot provide any requested cutouts."""


def _cache_path(url: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, hashlib.sha1(url.encode()).hexdigest() + ".fits")


def _fetch(url: str) -> bytes:
    import requests  # installed with astroquery

    p = _cache_path(url)
    if os.path.exists(p):
        with open(p, "rb") as cached:
            return cached.read()
    for attempt in range(DOWNLOAD_ATTEMPTS):
        try:
            r = requests.get(url, timeout=DOWNLOAD_TIMEOUT_SECONDS)
            if r.status_code == 503 and attempt < DOWNLOAD_ATTEMPTS - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            r.raise_for_status()
            content = r.content
            with open(p, "wb") as cached:
                cached.write(content)
            return content
        except requests.Timeout:
            if attempt == DOWNLOAD_ATTEMPTS - 1:
                raise
            time.sleep(0.5 * (attempt + 1))
        except requests.HTTPError as error:
            if error.response is None or error.response.status_code != 503:
                raise
            if attempt == DOWNLOAD_ATTEMPTS - 1:
                raise
            time.sleep(0.5 * (attempt + 1))
    raise RuntimeError("cutout download failed")


def query_images(ra: float, dec: float, fov_arcmin: float):
    """Return an astropy Table of SPHEREx spectral images covering the position."""
    from astroquery.ipac.irsa import Irsa

    coord = SkyCoord(ra * u.deg, dec * u.deg)
    collections = [name.strip() for name in COLLECTION.split(",") if name.strip()]
    if not collections:
        raise IRSAUnavailableError("No SPHEREx collections are configured")

    tables = []
    failures = []
    for collection in collections:
        try:
            table = Irsa.query_sia(
                pos=(coord, 30 * u.arcsec), collection=[collection]
            )
            if len(table) == 0:
                failures.append(f"{collection}: no rows returned")
                LOGGER.warning(
                    "SPHEREx collection %s returned no rows", collection
                )
                continue
            tables.append(table)
        except Exception as error:
            failures.append(f"{collection}: {error}")
            LOGGER.warning(
                "SPHEREx collection %s failed: %s", collection, error
            )

    if not tables:
        details = "; ".join(failures) or "no rows returned"
        raise IRSAUnavailableError(
            f"All configured SPHEREx collections failed ({details})"
        )

    merged = vstack(tables, metadata_conflicts="silent")
    seen_urls = set()
    keep = []
    for index, row in enumerate(merged):
        url = str(row["access_url"])
        if url not in seen_urls:
            seen_urls.add(url)
            keep.append(index)
    return merged[keep]


def _row_url(row, ra, dec, size_deg) -> str:
    base = str(row["access_url"])
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}center={ra},{dec}d&size={size_deg}"


def _row_mjd(row) -> float:
    return float(row["t_min"])


def _row_detector(row) -> int | None:
    """Read the verified detector number from the SIA access URL."""
    match = re.search(r"_(?:\d+)D([1-6])(?:_|$)", str(row["access_url"]))
    return int(match.group(1)) if match else None


def _evenly_sample(rows: list, count: int) -> list:
    ordered = sorted(rows, key=lambda row: (_row_mjd(row), str(row["access_url"])))
    if count >= len(ordered):
        return ordered
    indices = np.linspace(0, len(ordered) - 1, count).round().astype(int)
    return [ordered[index] for index in indices]


def _select_rows(tbl) -> list:
    """Select a stable, time-spread sample with a fair detector allocation."""
    by_detector: dict[int, list] = {}
    unknown = []
    for row in tbl:
        detector = _row_detector(row)
        if detector is None:
            unknown.append(row)
        else:
            by_detector.setdefault(detector, []).append(row)

    if unknown:
        LOGGER.warning("Skipping %d SIA rows without a verified detector URL", len(unknown))
    if not by_detector:
        return []

    detectors = sorted(by_detector)
    selected_counts = {
        detector: min(len(by_detector[detector]), MAX_FRAMES // 6)
        for detector in detectors
    }
    remaining = MAX_FRAMES - sum(selected_counts.values())
    while remaining > 0:
        added = False
        for detector in detectors:
            if selected_counts[detector] < len(by_detector[detector]):
                selected_counts[detector] += 1
                remaining -= 1
                added = True
                if remaining == 0:
                    break
        if not added:
            break

    selected = []
    for detector in detectors:
        selected.extend(
            _evenly_sample(by_detector[detector], selected_counts[detector])
        )
    return sorted(selected, key=lambda row: (_row_mjd(row), str(row["access_url"])))


def reset_wcs_warning_counts() -> None:
    with _WCS_WARNING_LOCK:
        for key in _WCS_WARNING_COUNTS:
            _WCS_WARNING_COUNTS[key] = 0


def get_wcs_warning_counts() -> dict[str, int]:
    with _WCS_WARNING_LOCK:
        return dict(_WCS_WARNING_COUNTS)


def _count_wcs_warnings(label: str, operation):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = operation()
    for warning in caught:
        if "WCS.all_world2pix failed to converge" in str(warning.message):
            with _WCS_WARNING_LOCK:
                _WCS_WARNING_COUNTS[label] += 1
        else:
            warnings.showwarning(
                warning.message,
                warning.category,
                warning.filename,
                warning.lineno,
                warning.file,
                warning.line,
            )
    return result


def _wavelength_at_coord(hdul, target: SkyCoord, image_hdu) -> float:
    """Return the WCS-WAVE wavelength at a selected sky position, in microns."""
    spatial_wcs = WCS(image_hdu.header)
    spectral_wcs = WCS(header=image_hdu.header, fobj=hdul, key="W")
    spectral_wcs.sip = None

    def lookup():
        x, y = spatial_wcs.world_to_pixel(target)
        return spectral_wcs.pixel_to_world(x, y)

    wavelength, _ = _count_wcs_warnings("wavelength", lookup)
    value = float(wavelength.to_value(u.um))
    if not np.isfinite(value) or not 0.75 <= value <= 5.1:
        raise ValueError(f"target wavelength is outside SPHEREx range: {value}")
    return value


def _target_wavelength(hdul, ra: float, dec: float, image_hdu) -> float:
    """Return the WCS-WAVE wavelength at the query center, in microns."""
    return _wavelength_at_coord(hdul, SkyCoord(ra * u.deg, dec * u.deg), image_hdu)


def _reproject_flag_mask(flags_hdu, image_wcs, target_wcs) -> np.ndarray:
    """Reproject FLAGS without blending bit values."""
    source = np.asarray(flags_hdu.data)
    source_values = np.unique(source)
    fill_value = source_values[0]
    with _FLAG_REPROJECT_LOCK:
        projected = reproject_interp(
            (source.astype(float, copy=False), image_wcs),
            target_wcs,
            shape_out=(OUT_PIX, OUT_PIX),
            order="nearest-neighbor",
            return_footprint=False,
        )
    projected = np.asarray(projected)
    projected[~np.isfinite(projected)] = fill_value
    projected = np.rint(projected).astype(np.int64)
    unexpected = ~np.isin(projected, source_values)
    if np.any(unexpected):
        # Keep the mask categorical even if the reprojection backend returns
        # a rounded value not present in the source due to WCS edge effects.
        distances = np.abs(
            projected[unexpected, None] - source_values[None, :]
        )
        projected[unexpected] = source_values[np.argmin(distances, axis=1)]
    return projected


def load_frame(row, ra, dec, size_deg, target_wcs, sample_pixel=None):
    url = _row_url(row, ra, dec, size_deg)
    with fits.open(io.BytesIO(_fetch(url))) as hdul:
        img_hdu = hdul["IMAGE"]
        flags_hdu = hdul["FLAGS"] if "FLAGS" in hdul else None
        variance_hdu = hdul["VARIANCE"] if "VARIANCE" in hdul else None
        image_wcs = WCS(img_hdu.header)

        def reproject():
            data = reproject_interp(
                (img_hdu.data, image_wcs),
                target_wcs,
                shape_out=(OUT_PIX, OUT_PIX),
            )[0]
            variance = None
            if variance_hdu is not None:
                # Interpolating variance like intensity is approximate and is
                # suitable only for relative weights, not calibrated errors.
                variance = reproject_interp(
                    (variance_hdu.data, image_wcs),
                    target_wcs,
                    shape_out=(OUT_PIX, OUT_PIX),
                )[0]
            return data, variance

        data, variance = _count_wcs_warnings("reproject", reproject)
        flag_mask = (
            _reproject_flag_mask(flags_hdu, image_wcs, target_wcs)
            if flags_hdu is not None
            else np.zeros((OUT_PIX, OUT_PIX), dtype=np.int64)
        )
        hdr = img_hdu.header
        detector = int(hdr.get("DETECTOR", 0))
        expected_detector = _row_detector(row)
        if expected_detector is not None and detector != expected_detector:
            raise ValueError(
                f"detector URL/header mismatch: D{expected_detector} vs D{detector}"
            )
        flagged = int(np.count_nonzero(flags_hdu.data)) if flags_hdu is not None else 0
        if sample_pixel is None:
            sample_coord = SkyCoord(ra * u.deg, dec * u.deg)
        else:
            sample_coord = target_wcs.pixel_to_world(*sample_pixel)
        return {
            "data": data,
            "variance": variance,
            "variance_approx": True,
            "flag_mask": flag_mask,
            "mjd": float(hdr.get("MJD-AVG", _row_mjd(row))),
            "detector": detector,
            "wavelength": _wavelength_at_coord(hdul, sample_coord, img_hdu),
            "flags": f"{flagged} flagged px in cutout",
        }


def _build_frames(
    ra: float, dec: float, fov_arcmin: float, sample_pixel=None
) -> list[dict]:
    size_deg = fov_arcmin / 60.0
    # Common output grid: north-up TAN centred on the target, same for every frame.
    target_wcs = WCS(naxis=2)
    target_wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    target_wcs.wcs.crval = [ra, dec]
    target_wcs.wcs.crpix = [OUT_PIX / 2 + 0.5, OUT_PIX / 2 + 0.5]
    scale = size_deg / OUT_PIX
    target_wcs.wcs.cdelt = [-scale, scale]

    tbl = query_images(ra, dec, fov_arcmin)
    rows = _select_rows(tbl)
    frames = []
    # Astropy WCS/reproject calls can corrupt the process heap when several
    # FITS frames are processed concurrently on Windows.
    with cf.ThreadPoolExecutor(max_workers=1) as ex:
        futs = [
            ex.submit(
                load_frame,
                r,
                ra,
                dec,
                size_deg,
                target_wcs,
                sample_pixel,
            )
            for r in rows
        ]
        for f in futs:
            try:
                frames.append(f.result())
            except Exception as error:  # one unavailable cutout must not stop the rest
                LOGGER.debug("Frame skipped: %s", error)
    skipped = len(rows) - len(frames)
    if skipped:
        LOGGER.warning("Skipped %d of %d cutout frames", skipped, len(rows))
    if rows and not frames:
        raise IRSAUnavailableError("IRSA did not return any requested cutouts")
    return sorted(frames, key=lambda f: f["mjd"])


def get_raw_frames(
    ra: float, dec: float, fov_arcmin: float, sample_pixel=None
) -> list[dict]:
    """Return reprojected live frames, sampling wavelength at ``sample_pixel``.

    ``sample_pixel`` is an ``(x, y)`` pixel on the raw array grid. The normal
    frame endpoint omits it and samples the query center; spectrum requests
    pass the clicked position so each wavelength matches that sky position.
    """
    sample_key = (
        None if sample_pixel is None else tuple(round(v, 3) for v in sample_pixel)
    )
    key = (round(ra, 6), round(dec, 6), round(fov_arcmin, 3), sample_key)
    now = time.monotonic()
    with _RAW_CACHE_LOCK:
        cached = _RAW_CACHE.get(key)
        if cached is not None and now - cached[0] < RAW_CACHE_TTL_SECONDS:
            return cached[1]

    frames = _build_frames(ra, dec, fov_arcmin, sample_pixel)
    with _RAW_CACHE_LOCK:
        _RAW_CACHE[key] = (time.monotonic(), frames)
    return frames


def make_frames(ra: float, dec: float, fov_arcmin: float) -> list[dict]:
    """Backward-compatible alias for callers using the pre-A5 name."""
    return get_raw_frames(ra, dec, fov_arcmin)
