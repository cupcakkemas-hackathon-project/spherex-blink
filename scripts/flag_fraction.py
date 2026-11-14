"""Report how much of each frame the recommended FLAGS mask would hide (nothing is applied).

Usage (needs internet access to IRSA):  python scripts/flag_fraction.py
Bits: the recommended starting mask from docs/science_notes.md
      (0, 2, 6, 7, 9, 10, 11, 14, 15, 17, 20 and 22-29). If that doc changes, edit BITS.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.irsa import get_raw_frames  # noqa: E402

BITS = [0, 2, 6, 7, 9, 10, 11, 14, 15, 17, 20] + list(range(22, 30))
MASK = sum(1 << b for b in BITS)

frames = get_raw_frames(133.7951, -7.2452, 3.0)
rec, anyb = [], []
for f in frames:
    m = f.get("flag_mask")
    if m is None:
        continue
    m = np.asarray(m).astype(np.int64)
    rec.append(float(np.mean((m & MASK) != 0)))
    anyb.append(float(np.mean(m != 0)))
print("frames:", len(frames), "| with flag_mask:", len(rec))
if rec:
    for name, v in (("recommended mask", rec), ("any bit set", anyb)):
        print(f"{name:17s} min {min(v):.2f}  median {np.median(v):.2f}  max {max(v):.2f}")
else:
    print("no frame has a flag_mask; is this the latest code?")