"""Shared image helpers: stacking, differencing, stretching, PNG encoding."""
import base64
import io

import numpy as np
from PIL import Image

STACK_WINDOW_DAYS = 7.0


def stretch(img: np.ndarray) -> np.ndarray:
    """asinh stretch to 0-255 uint8, robust to outliers."""
    a = img.astype(float, copy=False)
    valid = np.isfinite(a)
    out = np.zeros(a.shape, dtype=np.uint8)
    if not valid.any():
        return out

    lo, hi = np.percentile(a[valid], [5, 99.7])
    if hi <= lo:
        hi = lo + 1e-9
    scaled = np.clip((a[valid] - lo) / (hi - lo), 0, 1)
    scaled = np.arcsinh(scaled * 10) / np.arcsinh(10)
    out[valid] = (scaled * 255).astype(np.uint8)
    return out


def to_png_b64(img: np.ndarray) -> str:
    buf = io.BytesIO()
    # FITS/reprojected arrays have row 0 = south edge; PNG row 0 = top of picture.
    # Flip so the picture is north-up (east is left, because the grid has RA increasing leftwards).
    Image.fromarray(np.flipud(stretch(img))).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def apply_mode(frames: list[dict], mode: str) -> list[dict]:
    """frames: dicts with 'data' (2D array) and metadata, sorted by time.

    single -> unchanged
    stack  -> mean within fixed 7-day windows per detector
    diff   -> each frame minus the median of all frames (static sky cancels,
              moving objects leave a +/- pair)
    """
    if mode == "diff" and frames:
        med = np.nanmedian(np.stack([f["data"] for f in frames]), axis=0)
        return [{**f, "data": f["data"] - med} for f in frames]
    if mode == "stack":
        groups: dict[tuple[int, int], list[dict]] = {}
        for f in frames:
            week = int(np.floor(float(f["mjd"]) / STACK_WINDOW_DAYS))
            groups.setdefault((f["detector"], week), []).append(f)
        out = []
        for (det, _week), fs in sorted(groups.items()):
            data = np.stack([np.asarray(f["data"], dtype=float) for f in fs])
            valid = np.isfinite(data)
            stacked_data = np.full(data.shape[1:], np.nan)
            stacked_frame = {
                "detector": det,
                "mjd": float(np.mean([f["mjd"] for f in fs])),
                "wavelength": float(np.mean([f["wavelength"] for f in fs])),
                "flags": f"{len(fs)} frames stacked",
            }

            if all(f.get("variance") is not None for f in fs):
                variance = np.stack([
                    np.asarray(f["variance"], dtype=float) for f in fs
                ])
                valid &= np.isfinite(variance) & (variance > 0)
                weights = np.zeros_like(data)
                np.divide(1.0, variance, out=weights, where=valid)
                weight_sum = np.sum(weights, axis=0)
                weighted_sum = np.sum(np.where(valid, data, 0) * weights, axis=0)
                np.divide(weighted_sum, weight_sum, out=stacked_data, where=weight_sum > 0)

                stacked_variance = np.full(data.shape[1:], np.nan)
                np.divide(1.0, weight_sum, out=stacked_variance, where=weight_sum > 0)
                stacked_frame["variance"] = stacked_variance
            else:
                count = np.sum(valid, axis=0)
                total = np.sum(np.where(valid, data, 0), axis=0)
                np.divide(total, count, out=stacked_data, where=count > 0)

            stacked_frame["data"] = stacked_data
            out.append(stacked_frame)
        return sorted(out, key=lambda f: f["mjd"])
    return frames
