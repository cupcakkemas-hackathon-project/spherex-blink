"""Run on a machine with internet:  python -m backend.irsa_check
Confirms the live IRSA path works for WISE 0855 and prints the column names
so the VERIFY markers in irsa.py can be fixed quickly."""
import base64
import io

import numpy as np
from PIL import Image
from astropy.io import fits

from backend import irsa
from backend.imaging import to_png_b64

RA, DEC = 133.795, -7.2452  # WISE 0855 (08h55m10.8s, -07d14m42.5s)


def _decode_png(encoded: str) -> np.ndarray:
    return np.asarray(Image.open(io.BytesIO(base64.b64decode(encoded))))


def check_encoder_modes() -> None:
    values = np.array([[-1.0, 0.0, 1.0]])
    default = to_png_b64(values)
    explicit_default = to_png_b64(values, symmetric=False)
    if default != explicit_default:
        raise RuntimeError("single/stack encoder behavior changed")

    rendered = _decode_png(to_png_b64(values, symmetric=True))
    if not (rendered[0, 0] < 128 < rendered[0, 2]):
        raise RuntimeError("symmetric encoder does not separate negative/positive values")
    print("encoder mode check: PASS (diff symmetric; single/stack unchanged)")


check_encoder_modes()

tbl = irsa.query_images(RA, DEC, 2.0)
print("images found:", len(tbl))
print("columns:", tbl.colnames)
print(tbl[:3])
irsa.reset_wcs_warning_counts()
frames = irsa.get_raw_frames(RA, DEC, 5.0)
print("frames built:", len(frames))
warning_counts = irsa.get_wcs_warning_counts()
print(
    "WCS convergence warnings:",
    f"reproject={warning_counts['reproject']}, "
    f"wavelength={warning_counts['wavelength']}, "
    f"total={sum(warning_counts.values())}",
)
if frames:
    print({
        k: v for k, v in frames[0].items()
        if k not in ("data", "variance", "flag_mask")
    })
    if not all(
        frame["data"].shape == (irsa.OUT_PIX, irsa.OUT_PIX)
        and frame["flag_mask"].shape == frame["data"].shape
        and np.issubdtype(frame["flag_mask"].dtype, np.integer)
        and isinstance(frame["detector"], int)
        for frame in frames
    ):
        raise RuntimeError("a frame is missing a valid data/flag_mask shape or detector")
    flagged_counts = [int(np.count_nonzero(frame["flag_mask"])) for frame in frames]
    print("flagged pixels per frame:", flagged_counts)
    if not all(frame["variance_approx"] is True for frame in frames):
        raise RuntimeError("variance_approx is not set on every frame")
    missing_variance = sum(frame["variance"] is None for frame in frames)
    print("frames with missing variance:", missing_variance)
    print("raw frame fields: data, variance, variance_approx, flag_mask, wavelength, detector, flags")
    wavelengths = [frame["wavelength"] for frame in frames]
    if not all(
        isinstance(value, float) and 0.75 <= value <= 5.1
        for value in wavelengths
    ):
        raise RuntimeError("a frame has an invalid SPHEREx wavelength")
    print("finite wavelengths:", len(wavelengths))
    print("distinct wavelengths:", len(set(wavelengths)))
    by_detector = {}
    for frame in frames:
        by_detector.setdefault(frame["detector"], []).append(frame["wavelength"])
    print("detector wavelength ranges (micron):")
    for detector in sorted(by_detector):
        values = by_detector[detector]
        print(
            f"  D{detector}: {min(values):.6f} - {max(values):.6f} "
            f"({len(values)} frames)"
        )

    first_row = tbl[0]
    size_deg = 5.0 / 60.0
    target_wcs = irsa.WCS(naxis=2)
    target_wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    target_wcs.wcs.crval = [RA, DEC]
    target_wcs.wcs.crpix = [irsa.OUT_PIX / 2 + 0.5, irsa.OUT_PIX / 2 + 0.5]
    target_wcs.wcs.cdelt = [-size_deg / irsa.OUT_PIX, size_deg / irsa.OUT_PIX]
    cutout_url = irsa._row_url(first_row, RA, DEC, size_deg)
    cutout_bytes = irsa._fetch(cutout_url)
    with fits.open(io.BytesIO(cutout_bytes)) as source_hdul:
        original_flags = np.asarray(source_hdul["FLAGS"].data)
        original_values = np.unique(original_flags)
        image_wcs = irsa.WCS(source_hdul["IMAGE"].header)
        projected_flags = irsa._reproject_flag_mask(
            source_hdul["FLAGS"], image_wcs, target_wcs
        )
    if not np.all(np.isin(projected_flags, original_values)):
        raise RuntimeError("reprojected flag_mask contains values absent from source FLAGS")
    print("flag_mask values: PASS (all values present in original FLAGS)")

    with fits.open(io.BytesIO(cutout_bytes)) as source_hdul:
        without_variance = fits.HDUList([
            hdu.copy() for hdu in source_hdul if hdu.name != "VARIANCE"
        ])
        missing_variance_bytes = io.BytesIO()
        without_variance.writeto(missing_variance_bytes)
    original_fetch = irsa._fetch
    irsa._fetch = lambda _url: missing_variance_bytes.getvalue()
    try:
        frame_without_variance = irsa.load_frame(
            first_row, RA, DEC, size_deg, target_wcs
        )
    finally:
        irsa._fetch = original_fetch
    if frame_without_variance["variance"] is not None:
        raise RuntimeError("missing VARIANCE extension did not produce None")
    print("missing VARIANCE regression: PASS (frame retained with variance=None)")
