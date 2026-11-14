# Role A: Data lead

**Why this role matters most:** if real SPHEREx images do not come out of the backend, there is no real demo. Everyone else is blocked until task A3 works. If you are stuck for more than 2 hours, say so and the team helps.

Read `AGENTS.md` first (rules, data facts, known traps).

## You own
`backend/irsa.py`, `backend/irsa_check.py`, `backend/app.py`, `scripts/` (create it), `docs/irsa_notes.md` (create it).
Do not edit `backend/imaging.py` (role B), `frontend/` (role C), README/tests/deploy files (role D).

## What the code does today
`app.py` exposes `/api/frames`. For `source=live` it calls `irsa.make_frames(ra, dec, fov_arcmin)`:
1. `query_images` asks IRSA SIA2 for SPHEREx images covering the position.
2. Rows are sorted by time and cut to `MAX_FRAMES`.
3. For each row, `load_frame` downloads a **cutout** (`?center=ra,decd&size=deg`), caches it on disk in `.cache/`, reads the `IMAGE` extension, and reprojects it onto a common 64x64 north-up grid with `reproject_interp`.
4. Returns dicts: `data` (2D float array), `mjd`, `detector`, `wavelength`, `flags`.
`imaging.apply_mode` then does stack/diff, and `app.py` encodes PNGs.

All of this is **untested against real IRSA**. Items marked `# VERIFY` are guesses.

---

## A1. Run the first check (do this first, tonight)
1. `pip install -r requirements.txt`, then `python -m backend.irsa_check` on a machine with normal internet.
2. Save the full output into `docs/irsa_notes.md`: number of images found, `tbl.colnames`, the first 3 rows, any error text.
3. If the query fails, check which of these is the problem: network access, wrong collection name, wrong function arguments. Try the examples in the IRSA tutorials above and compare.

**Done when:** `docs/irsa_notes.md` contains real column names and a real row, and `irsa_check` prints "images found: N" with N > 0.

## A2. Fix everything marked `# VERIFY` in `irsa.py`
- Which column holds the image URL (`access_url`? `uri`? something else)? Is it a direct file URL or a datalink URL? If it already has a `?` query string, the cutout string must be appended with `&`.
- Which column holds the observation time, and is it MJD? Which holds the wavelength range (ObsCore has `em_min`/`em_max` in metres) and detector?
- Open one cutout in Python (`astropy.io.fits`) and print `hdul.info()` plus the `IMAGE` header. Record the real extension names and header keys for observation time and detector in `docs/irsa_notes.md`. Fix `load_frame` to use them.
- Check the cutout size unit and the smallest size IRSA allows. Note it in `irsa_notes.md`.

**Done when:** no `# VERIFY` comments remain (or each remaining one says why), and `irsa_notes.md` lists the verified facts.

## A3. Real frames for WISE 0855, end to end
1. Start the server and request `http://127.0.0.1:8000/api/frames?ra=133.7951&dec=-7.2452&fov=3&source=live`.
2. Check: at least 10 frames; `mjd` increasing; frames returned within about 60 seconds (more is OK for now, we fix speed in A6).
3. Visual check: save a few PNGs (decode the base64) or view in the UI. Stars should stay in the **same place** from frame to frame (no jumping by more than about 1 pixel). If they jump, the common-grid reprojection is wrong.
4. Tell role C and D immediately when this works; they are waiting on it.

**Done when:** the UI with "Live SPHEREx (IRSA)" shows an animation of real WISE 0855 data with stable background stars.

## A4. Wavelength for every frame
Each image has a `WCS-WAVE` extension describing wavelength per pixel. Use the IRSA intro tutorial (`spherex-intro`) to learn how to read it. The wavelength at the **target pixel** (centre of the cutout) is what goes in `frame["wavelength"]`, in micron.

**Done when:** every frame has a finite wavelength between 0.75 and 5.1 micron, values differ across frames, and detector number and wavelength are consistent (D1 around 0.75-1.09 micron). Update the table in `AGENTS.md` section 4 with the verified ranges for D1-D6.

## A5. Keep raw frames available, add a cache
- Create `get_raw_frames(ra, dec, fov)` in `irsa.py` returning the list of dicts **before** PNG encoding, with an in-memory cache keyed by rounded `(ra, dec, fov)` and a time-to-live of a few hours (so new weekly data eventually appears).
- `app.py` should call it for `/api/frames`, and role B's spectrum route must reuse it so the images are not downloaded twice.

**Done when:** a second request for the same position returns in under 1 second, and `get_raw_frames` is importable by `backend/spectrum.py`.

## A6. Smarter frame selection, speed and robustness
- Replace "first 60 by time" with an **even subsample across the whole time range**, up to `MAX_FRAMES`. Make `MAX_FRAMES` configurable by env var (already is).
- Keep the parallel download (8 workers). Add a timeout and one retry per cutout. A failed cutout is skipped, not fatal (already so).
- Be polite to IRSA: do not hammer it; check its usage policy for rate limits and note it in `irsa_notes.md`.
- Clear errors: no images found should return 404 with a friendly message; IRSA down returns 502.
- Create `scripts/warm_cache.py` that requests all five test targets at fov 3 arcmin so the first demo request is instant.

**Done when:** WISE 0855 at 3 arcmin loads in under 20 seconds cold and under 1 second warm; the warm script runs without errors for all five targets.

## A7. Updates and collections
- Confirm which collections exist right now (is there a `spherex_qr3`?). Make the collection configurable (env var `SPHEREX_COLLECTION` exists). Consider querying wide and deep collections and merging.
- Document in `irsa_notes.md` how new weekly data shows up (it should be automatic because we query live; the in-memory cache TTL controls how fast).

**Done when:** `irsa_notes.md` has a short "how updating works" paragraph that role D can paste into the README.

## A8. Flags
The `FLAGS` extension marks bad pixels. Ask role B which bits to mask (they should read the SPHEREx Explanatory Supplement). Set flagged pixels to NaN in `data` before reprojection, and put a readable summary in `frame["flags"]` (for example "3 of 361 pixels flagged").

**Done when:** `frame["flags"]` is meaningful on real data, and flagged pixels no longer produce bright speckles.

## A9. Small API additions
- Add `size_px` (64) and `pixel_scale_arcsec` (`fov_arcmin*60/64`) to the `/api/frames` response.
- Add `GET /healthz` returning `{"ok": true}`.
- Wire role B's `/api/spectrum` route once `backend/spectrum.py` exists (B may add a clearly marked block at the end of `app.py`).
- Update `TARGETS` in `app.py` with the verified coordinates that role D provides in `docs/targets.md`.
- Update section 6 of `AGENTS.md`.

**Done when:** `curl` shows the new fields and `/healthz` works.

## Hand-offs
- To B: `get_raw_frames` (A5), flag bits question (A8).
- To C: new response fields (A9).
- To D: working live demo (A3), updating notes (A7), health endpoint (A9).
- From D: verified target coordinates.
