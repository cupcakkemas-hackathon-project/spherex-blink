import collections
import math
import os
import time

import requests

B = os.environ.get("SPHEREX_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
FAILED = False


def get(path, **kw):
    t = time.time()
    response = requests.get(B + path, params=kw, timeout=300)
    return response, time.time() - t


def ok(condition, message):
    global FAILED
    if not condition:
        FAILED = True
    print(("PASS  " if condition else "FAIL  ") + message)


def verify_frames(mode):
    query = dict(ra=133.7951, dec=-7.2452, fov=3, mode=mode, source="live")
    response, elapsed = get("/api/frames", **query)
    ok(response.status_code == 200, f"{mode} frames returns 200")
    if response.status_code != 200:
        return []
    payload = response.json()
    frames = payload.get("frames", [])
    ok(payload.get("source") == "live", f"{mode} response is live")
    ok(bool(frames), f"{mode} has frames ({len(frames)})")
    mjds = [frame["mjd"] for frame in frames]
    ok(mjds == sorted(mjds), f"{mode} times increasing")
    counts = collections.Counter(frame["detector"] for frame in frames)
    print(f"      {mode} elapsed: {elapsed:.1f}s; detector counts: {dict(sorted(counts.items()))}")
    return frames


try:
    response, _ = get("/healthz")
    ok(response.status_code == 200 and response.json() == {"ok": True}, "healthz")

    single = verify_frames("single")
    stack = verify_frames("stack")
    diff = verify_frames("diff")
    for mode, frames in (("single", single), ("stack", stack), ("diff", diff)):
        ok(all(frame.get("wavelength") is not None for frame in frames),
           f"{mode} wavelengths present")

    response, elapsed = get(
        "/api/spectrum", ra=133.7951, dec=-7.2452, fov=3, x=32, y=32,
        source="live",
    )
    ok(response.status_code == 200, f"/api/spectrum selected pixel returns 200 (got {response.status_code})")
    if response.status_code == 200:
        payload = response.json()
        ok(payload.get("source") != "synthetic", "spectrum is not synthetic")
        points = payload.get("points", [])
        ok(bool(points), f"spectrum has points ({len(points)})")
        ok(all(0.75 <= point["wavelength"] <= 5.1 for point in points),
           "spectrum wavelengths valid")
        ok(all(point["flux"] is not None and point["err"] is not None for point in points),
           "spectrum flux/error values present")
        by_detector = collections.defaultdict(list)
        for point in points:
            by_detector[point["detector"]].append(point["wavelength"])
        ordered = sorted(points, key=lambda point: point["wavelength"])
        gaps = [
            (left["wavelength"], right["wavelength"])
            for left, right in zip(ordered, ordered[1:])
            if right["wavelength"] - left["wavelength"] > 0.1
        ]
        for detector in sorted(by_detector):
            values = by_detector[detector]
            print(f"      D{detector} coverage: {min(values):.6f}-{max(values):.6f} micron ({len(values)} points)")
        print(f"      spectrum elapsed: {elapsed:.1f}s; gaps > 0.1 micron: {gaps or 'none'}")
        ok([point["wavelength"] for point in points] == sorted(point["wavelength"] for point in points),
           "spectrum sorted by wavelength")
except (requests.RequestException, ValueError, KeyError) as error:
    FAILED = True
    print(f"FAIL  validation request failed: {error}")

raise SystemExit(1 if FAILED else 0)