"""Live pipeline: IRSA SIA2 query -> cutouts -> common-grid reprojection.

STATUS: written from IRSA's public tutorials but NOT yet run against the live
archive (the build environment could not reach irsa.ipac.caltech.edu). Run
`python -m backend.irsa_check` on your own machine first and fix any column
names that differ. Places that need verification are marked  # VERIFY.
"""
import concurrent.futures as cf
import hashlib
import io
import os

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
from reproject import reproject_interp

COLLECTION = os.environ.get("SPHEREX_COLLECTION", "spherex_qr2")  # wide survey
CACHE_DIR = os.environ.get("CACHE_DIR", ".cache")
MAX_FRAMES = int(os.environ.get("MAX_FRAMES", "60"))
OUT_PIX = 64
PIX_SCALE_ARCSEC = 6.2  # SPHEREx native pixel size


def _cache_path(url: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, hashlib.sha1(url.encode()).hexdigest() + ".fits")


def _fetch(url: str) -> bytes:
    import requests  # installed with astroquery

    p = _cache_path(url)
    if os.path.exists(p):
        return open(p, "rb").read()
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    open(p, "wb").write(r.content)
    return r.content


def query_images(ra: float, dec: float, fov_arcmin: float):
    """Return an astropy Table of SPHEREx spectral images covering the position."""
    from astroquery.ipac.irsa import Irsa

    coord = SkyCoord(ra * u.deg, dec * u.deg)
    tbl = Irsa.query_sia(pos=(coord, 30 * u.arcsec), collection=COLLECTION)
    return tbl


def _row_url(row, ra, dec, size_deg) -> str:
    base = str(row["access_url"])  # VERIFY column name (tutorial TAP path uses 'uri')
    return f"{base}?center={ra},{dec}d&size={size_deg}"


def _row_mjd(row) -> float:
    return float(row["t_min"])  # VERIFY: SIA2 ObsCore t_min is MJD


def load_frame(row, ra, dec, size_deg, target_wcs):
    url = _row_url(row, ra, dec, size_deg)
    with fits.open(io.BytesIO(_fetch(url))) as hdul:
        img_hdu = hdul["IMAGE"]
        flags_hdu = hdul["FLAGS"] if "FLAGS" in hdul else None
        data, _ = reproject_interp(
            (img_hdu.data, WCS(img_hdu.header)), target_wcs, shape_out=(OUT_PIX, OUT_PIX)
        )
        hdr = img_hdu.header
        flagged = int(np.count_nonzero(flags_hdu.data)) if flags_hdu is not None else 0
        return {
            "data": data,
            "mjd": float(hdr.get("MJD-AVG", _row_mjd(row))),  # VERIFY header key
            "detector": int(hdr.get("DETECTOR", 0)),           # VERIFY header key
            "wavelength": float("nan"),                          # TODO: from WCS-WAVE extension
            "flags": f"{flagged} flagged px in cutout",
        }


def make_frames(ra: float, dec: float, fov_arcmin: float) -> list[dict]:
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
