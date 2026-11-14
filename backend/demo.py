"""SYNTHETIC demo frames. NOT real SPHEREx data.

Used only so the UI can be shown when IRSA is unreachable. Every response built
from this module is flagged source='synthetic' and the UI shows a banner.
"""
import numpy as np

SIZE = 64


def make_frames(ra: float, dec: float, n: int = 36) -> list[dict]:
    # Seed from position so the same target always gives the same fake field.
    rng = np.random.default_rng(int(abs(ra * 1000) + abs(dec * 1000)))
    n_stars = 25
    sx = rng.uniform(4, SIZE - 4, n_stars)
    sy = rng.uniform(4, SIZE - 4, n_stars)
    sf = rng.uniform(40, 300, n_stars)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]

    def blob(x, y, f, s=1.4):
        return f * np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * s * s))

    mover_start = np.array([8.0, 40.0])
    mover_vel = rng.uniform([0.9, -0.8], [1.3, -0.3])  # pixels per frame
    frames = []
    for i in range(n):
        det = 1 + (i % 6)
        img = rng.normal(10, 4, (SIZE, SIZE))
        for x, y, f in zip(sx, sy, sf):
            img += blob(x, y, f * (0.8 + 0.1 * det / 6))
        mx, my = mover_start + mover_vel * i
        if 0 <= mx < SIZE and 0 <= my < SIZE:
            img += blob(mx, my, 150)
        frames.append({
            "data": img,
            "mjd": 61000.0 + i * 0.5,
            "wavelength": 0.75 + 0.8 * det,
            "detector": det,
            "flags": "synthetic",
        })
    return frames
