"""Run on a machine with internet:  python -m backend.irsa_check
Confirms the live IRSA path works for WISE 0855 and prints the column names
so the VERIFY markers in irsa.py can be fixed quickly."""
from backend import irsa

RA, DEC = 133.795, -7.2452  # WISE 0855 (08h55m10.8s, -07d14m42.5s)

tbl = irsa.query_images(RA, DEC, 2.0)
print("images found:", len(tbl))
print("columns:", tbl.colnames)
print(tbl[:3])
frames = irsa.make_frames(RA, DEC, 5.0)
print("frames built:", len(frames))
if frames:
    print({k: v for k, v in frames[0].items() if k != "data"})
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
