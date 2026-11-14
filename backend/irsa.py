"""Live pipeline: IRSA SIA2 query -> cutouts -> common-grid reprojection.

STATUS: verified against the live IRSA SIA2 service on 2026-11-14.
See docs/irsa_notes.md for the observed columns and FITS structure.
"""
import concurrent.futures as cf
import hashlib
import io
import logging
import os
import threading
import time
import warnings

import numpy as np
from astropy import log as astropy_log
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
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
_RAW_CACHE: dict[tuple[float, float, float], tuple[float, list[dict]]] = {}
_RAW_CACHE_LOCK = threading.Lock()
_WCS_WARNING_COUNTS = {"reproject": 0, "wavelength": 0}
_WCS_WARNING_LOCK = threading.Lock()


def _cache_path(url: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, hashlib.sha1(url.encode()).hexdigest() + ".fits")


def _fetch(url: str) -> bytes:
    import requests  # installed with astroquery

    p = _cache_path(url)
    if os.path.exists(p):
        with open(p, "rb") as cached:
            return cached.read()
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    open(p, "wb").write(r.content)
    return r.content


def query_images(ra: float, dec: float, fov_arcmin: float):
    """Return an astropy Table of SPHEREx spectral images covering the position."""
    from astroquery.ipac.irsa import Irsa

    coord = SkyCoord(ra * u.deg, dec * u.deg)
    collections = [name.strip() for name in COLLECTION.split(",") if name.strip()]
    tbl = Irsa.query_sia(pos=(coord, 30 * u.arcsec), collection=collections)
    return tbl


def _row_url(row, ra, dec, size_deg) -> str:
    base = str(row["access_url"])
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}center={ra},{dec}d&size={size_deg}"


def _row_mjd(row) -> float:
    return float(row["t_min"])


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


def _target_wavelength(hdul, ra: float, dec: float, image_hdu) -> float:
    """Return the WCS-WAVE wavelength at the target position, in microns."""
    spatial_wcs = WCS(image_hdu.header)
    target = SkyCoord(ra * u.deg, dec * u.deg)
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


def load_frame(row, ra, dec, size_deg, target_wcs):
    url = _row_url(row, ra, dec, size_deg)
    with fits.open(io.BytesIO(_fetch(url))) as hdul:
        img_hdu = hdul["IMAGE"]
        flags_hdu = hdul["FLAGS"] if "FLAGS" in hdul else None
        variance_hdu = hdul["VARIANCE"]
        image_wcs = WCS(img_hdu.header)

        def reproject():
            return (
                reproject_interp(
                    (img_hdu.data, image_wcs),
                    target_wcs,
                    shape_out=(OUT_PIX, OUT_PIX),
                )[0],
                reproject_interp(
                    (variance_hdu.data, image_wcs),
                    target_wcs,
                    shape_out=(OUT_PIX, OUT_PIX),
                )[0],
            )

        data, variance = _count_wcs_warnings("reproject", reproject)
        hdr = img_hdu.header
        flagged = int(np.count_nonzero(flags_hdu.data)) if flags_hdu is not None else 0
        return {
            "data": data,
            "variance": variance,
            "mjd": float(hdr.get("MJD-AVG", _row_mjd(row))),
            "detector": int(hdr.get("DETECTOR", 0)),
            "wavelength": _target_wavelength(hdul, ra, dec, img_hdu),
            "flags": f"{flagged} flagged px in cutout",
        }


def _build_frames(ra: float, dec: float, fov_arcmin: float) -> list[dict]:
    size_deg = fov_arcmin / 60.0
    # Common output grid: north-up TAN centred on the target, same for every frame.
    target_wcs = WCS(naxis=2)
    target_wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    target_wcs.wcs.crval = [ra, dec]
    target_wcs.wcs.crpix = [OUT_PIX / 2 + 0.5, OUT_PIX / 2 + 0.5]
    scale = size_deg / OUT_PIX
    target_wcs.wcs.cdelt = [-scale, scale]

    tbl = query_images(ra, dec, fov_arcmin)
    rows = sorted(tbl, key=_row_mjd)[:MAX_FRAMES]
    frames = []
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(load_frame, r, ra, dec, size_deg, target_wcs) for r in rows]
        for f in futs:
            try:
                frames.append(f.result())
            except Exception as e:  # skip frames that fail instead of failing the request
                print("frame failed:", e)
    return sorted(frames, key=lambda f: f["mjd"])


def get_raw_frames(ra: float, dec: float, fov_arcmin: float) -> list[dict]:
    """Return reprojected live frames, using a short-lived in-memory cache."""
    key = (round(ra, 6), round(dec, 6), round(fov_arcmin, 3))
    now = time.monotonic()
    with _RAW_CACHE_LOCK:
        cached = _RAW_CACHE.get(key)
        if cached is not None and now - cached[0] < RAW_CACHE_TTL_SECONDS:
            return cached[1]

    frames = _build_frames(ra, dec, fov_arcmin)
    with _RAW_CACHE_LOCK:
        _RAW_CACHE[key] = (time.monotonic(), frames)
    return frames


def make_frames(ra: float, dec: float, fov_arcmin: float) -> list[dict]:
    """Backward-compatible alias for callers using the pre-A5 name."""
    return get_raw_frames(ra, dec, fov_arcmin)
