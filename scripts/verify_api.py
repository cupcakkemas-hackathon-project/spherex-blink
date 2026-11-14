import time, math, collections, requests
B = "http://127.0.0.1:8000"
def get(path, **kw):
    t = time.time(); r = requests.get(B + path, params=kw, timeout=300); return r, time.time() - t
def ok(c, m): print(("PASS  " if c else "FAIL  ") + m)

r, _ = get("/healthz"); ok(r.json() == {"ok": True}, "healthz")

q = dict(ra=133.7951, dec=-7.2452, fov=3, source="live")
r1, t1 = get("/api/frames", **q); r2, t2 = get("/api/frames", **q)
j1, j2 = r1.json(), r2.json(); f = j1["frames"]
ok(r1.status_code == 200, "frames returns 200")
ok(len(f) == len(j2["frames"]) and [x["mjd"] for x in f] == [x["mjd"] for x in j2["frames"]],
   f"same frames both times ({len(f)} frames)")
print(f"      time first / second request: {t1:.1f}s / {t2:.2f}s")
ok(t2 < 1.0, "second request under 1 s")
ok(j1.get("size_px") == 64 and abs(j1.get("pixel_scale_arcsec", 0) - 3*60/64) < 1e-6, "size_px and pixel_scale_arcsec")
ok([x["mjd"] for x in f] == sorted(x["mjd"] for x in f), "times increasing")
cnt = collections.Counter(x["detector"] for x in f)
print("      detector counts:", dict(sorted(cnt.items())))
ok(all(cnt.get(d, 0) >= 3 for d in range(1, 7)), "every detector has at least 3 frames")
ok(all(x["wavelength"] is not None and 0.75 <= x["wavelength"] <= 5.1 for x in f), "wavelengths valid")

# spectrum route
def spec(x, y):
    r, _ = get("/api/spectrum", ra=133.7951, dec=-7.2452, fov=3, x=x, y=y)
    return r
r = spec(32, 32)
ok(r.status_code == 200, f"/api/spectrum centre returns 200 (got {r.status_code})")
if r.status_code == 200:
    p = r.json()["points"]
    wl = [a["wavelength"] for a in p]
    ok(len(p) > 0, f"spectrum has points ({len(p)})")
    ok(all(isinstance(v, (int, float)) and not math.isnan(v) and 0.75 <= v <= 5.1 for v in wl), "spectrum wavelengths valid")
    ok(wl == sorted(wl), "sorted by wavelength")
    ok(all(not (isinstance(a[k], float) and math.isnan(a[k])) for a in p for k in ("flux", "err") if a.get(k) is not None), "no NaN flux/err")
    pe = spec(5, 5)
    if pe.status_code == 200:
        we = [a["wavelength"] for a in pe.json()["points"]]
        ok(set(round(v, 4) for v in wl) != set(round(v, 4) for v in we), "different pixel gives different wavelengths (per-pixel map in use)")
    print("      coverage at centre (micron):", round(min(wl), 2), "-", round(max(wl), 2))
for bad in [(99, 5), (-1, 5), ("abc", 5)]:
    ok(spec(*bad).status_code in (400, 422), f"bad input {bad} rejected")