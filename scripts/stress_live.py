"""Hit the LIVE API repeatedly and report crashes. Start the server first.

Usage:  python scripts/stress_live.py [N]        (default N=5)
Optional: SPHEREX_BASE_URL (default http://127.0.0.1:8000)

Each request uses a different field of view, so the in-memory cache cannot answer it and
the real download + reprojection path runs every time.
Cost warning: each NEW fov downloads about 60 cutouts from IRSA. Be polite, keep N small.
Tip: run it twice, restarting the server in between. The second run reuses the cutouts saved
in .cache (fast, no downloads) and mainly tests reprojection under concurrency.
"""
import os
import sys
import time

import requests

BASE = os.environ.get("SPHEREX_BASE_URL", "http://127.0.0.1:8000")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 5
problems = 0
for i in range(N):
    fov = round(2.0 + 0.1 * i, 1)
    t0 = time.time()
    try:
        r = requests.get(BASE + "/api/frames",
                         params=dict(ra=133.7951, dec=-7.2452, fov=fov, source="live"),
                         timeout=300)
        n = len(r.json().get("frames", [])) if r.status_code == 200 else 0
        print(f"{i + 1}/{N} fov={fov}: HTTP {r.status_code}, {n} frames, {time.time() - t0:.1f}s")
        if r.status_code != 200 or n == 0:
            problems += 1
    except Exception as e:
        problems += 1
        print(f"{i + 1}/{N} fov={fov}: FAILED ({type(e).__name__}: {e})")
        try:
            requests.get(BASE + "/healthz", timeout=5)
        except Exception:
            print("   -> the server is DOWN (it probably crashed). Check its terminal for the error.")
            break
print("problems:", problems)
sys.exit(1 if problems else 0)