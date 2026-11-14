"""Run on a machine with internet:  python -m backend.irsa_check
Confirms the live IRSA path works for WISE 0855 and prints the column names
so the VERIFY markers in irsa.py can be fixed quickly."""
from backend import irsa

RA, DEC = 133.795, -7.2452  # WISE 0855 (08h55m10.8s, -07d14m42.5s)

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
    print({k: v for k, v in frames[0].items() if k != "data"})
    if not all(
        frame["data"].shape == frame["variance"].shape
        and frame["data"].shape == (irsa.OUT_PIX, irsa.OUT_PIX)
        and isinstance(frame["detector"], int)
        for frame in frames
    ):
        raise RuntimeError("a frame is missing a valid data/variance shape or detector")
    print("raw frame fields: data, variance, wavelength, detector, flags")
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
