"""Warm the live frame cache for all built-in targets.

Run with the API server already started:
    python scripts/warm_cache.py
"""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from backend.app import TARGETS


BASE_URL = os.environ.get("SPHEREX_BASE_URL", "http://127.0.0.1:8000")
TIMEOUT_SECONDS = float(os.environ.get("SPHEREX_WARM_TIMEOUT_SECONDS", "120"))


def main() -> None:
    for name, (ra, dec) in TARGETS.items():
        response = requests.get(
            f"{BASE_URL.rstrip('/')}/api/frames",
            params={"ra": ra, "dec": dec, "fov": 3, "source": "live"},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        frame_count = len(payload.get("frames", []))
        if not frame_count:
            raise RuntimeError(f"{name}: response contained no frames")
        print(f"{name}: warmed {frame_count} frames")


if __name__ == "__main__":
    main()
