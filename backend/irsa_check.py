"""Run on a machine with internet:  python -m backend.irsa_check
Confirms the live IRSA path works for WISE 0855 and prints the column names
so the VERIFY markers in irsa.py can be fixed quickly."""
from backend import irsa

RA, DEC = 133.795, -7.2452  # WISE 0855 (08h55m10.8s, -07d14m42.5s)

tbl = irsa.query_images(RA, DEC, 2.0)
print("images found:", len(tbl))
print("columns:", tbl.colnames)
print(tbl[:3])
frames = irsa.make_frames(RA, DEC, 2.0)
print("frames built:", len(frames))
if frames:
    print({k: v for k, v in frames[0].items() if k != "data"})
