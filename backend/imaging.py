"""Shared image helpers: stacking, differencing, stretching, PNG encoding."""
import base64
import io

import numpy as np
from PIL import Image


def stretch(img: np.ndarray) -> np.ndarray:
    """asinh stretch to 0-255 uint8, robust to outliers."""
    a = np.nan_to_num(img.astype(float), nan=0.0)
    lo, hi = np.percentile(a, [5, 99.7])
    if hi <= lo:
        hi = lo + 1e-9
    a = np.clip((a - lo) / (hi - lo), 0, 1)
    a = np.arcsinh(a * 10) / np.arcsinh(10)
    return (a * 255).astype(np.uint8)


def to_png_b64(img: np.ndarray) -> str:
    buf = io.BytesIO()
    # FITS/reprojected arrays have row 0 = south edge; PNG row 0 = top of picture.
    # Flip so the picture is north-up (east is left, because the grid has RA increasing leftwards).
    Image.fromarray(np.flipud(stretch(img))).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def apply_mode(frames: list[dict], mode: str) -> list[dict]:
    """frames: dicts with 'data' (2D array) and metadata, sorted by time.

    single -> unchanged
    stack  -> mean of all frames from the same detector, placed at the mean time
              (improves signal-to-noise; the six detector arrays are separate bands)
    diff   -> each frame minus the median of all frames (static sky cancels,
              moving objects leave a +/- pair)
    """
    if mode == "diff" and frames:
        med = np.nanmedian(np.stack([f["data"] for f in frames]), axis=0)
        return [{**f, "data": f["data"] - med} for f in frames]
    if mode == "stack":
        groups: dict[int, list[dict]] = {}
        for f in frames:
            groups.setdefault(f["detector"], []).append(f)
        out = []
        for det, fs in sorted(groups.items()):
            out.append({
                "detector": det,
                "mjd": float(np.mean([f["mjd"] for f in fs])),
                "wavelength": float(np.mean([f["wavelength"] for f in fs])),
                "flags": f"{len(fs)} frames stacked",
                "data": np.nanmean(np.stack([f["data"] for f in fs]), axis=0),
            })
        return sorted(out, key=lambda f: f["mjd"])
    return frames
