# AGENTS.md: read this first

This file is for AI coding agents (Copilot, Claude Code, etc.) helping a human teammate on this repo.
Humans: you can read it too. It is the shared context for the whole project.

## 0. How to start a session

1. Ask the person which role they are: **A (Data)**, **B (Image & science)**, **C (Frontend)** or **D (Product, deploy & presentation)**.
2. Read the official brief in `docs/CHALLENGE.md` and what judges look for in `docs/JUDGING.md`, then the matching file in `docs/roles/` (`A-data.md`, `B-image-science.md`, `C-frontend.md`, `D-product-deploy.md`).
   Judging criteria in `docs/JUDGING.md` are not yet verified against the 2026 guide; do not state them as fact until role D has confirmed them.
3. Work through that person's tasks **in order**. Each task has "Done when" checks. Do not skip them.
4. Assume the person may be new to astronomy and possibly to this kind of code. Explain in plain words, define terms, keep answers short.

## 1. What this project is

Hackathon project for the **2026 NASA Space Apps Challenge, "Planet X and SPHEREx"** (event: 14-15 Nov 2026, 48 hours, team of 4).

**Goal:** a public web tool. The user enters a sky position (RA/Dec). The tool shows an aligned, time-ordered animation ("blink") of SPHEREx telescope images of that patch, so moving objects (comets, asteroids, brown dwarfs, nearby stars) are easy to spot. It must work with **real SPHEREx data** from NASA's IRSA archive.

Test targets named by the challenge: Barnard's Star, Epsilon Indi B, WISE 0855 (RA 08h55m10.831s, Dec -7d14m42.53s), RW Aurigae, R Draconis.

Optional extras the challenge mentions (these earn bonus credit only after the core works): stack images per detector, add/subtract images in time, choose field of view, spectra on the fly ("extra kudos"), Gaia/WISE overlay, coordinates in the URL for embedding, metadata such as contamination flags, easy updating as new data arrives.

Judging is by the Space Apps criteria (impact, creativity, validity, relevance, presentation). **Validity** means real data, honestly shown. **Presentation** means a clear demo video and README. A small tool that works beats a big tool that is half-working.

## 2. Non-negotiable rules

1. **Never present synthetic data as real.** `source=synthetic` is fake data for UI testing only and must always show the red banner. Never remove the banner. Never use synthetic results in the demo video or submission.
2. **Never claim something works unless you ran it.** If you did not run it, say "not tested". The live IRSA pipeline was written without ever being run (see section 5).
3. **Do not invent** IRSA column names, FITS header keys, URLs or numbers. Look them up in the IRSA docs (section 4) or by running a real query and printing the result.
4. **One owner per file** (section 3). If you need a change in someone else's file, tell the person to ask the owner. Do not edit it yourself.
5. **API changes are additive only** (add fields, never rename or remove). After any change, update section 6 of this file and tell role D.
6. Keep code simple, commented, Python 3.10+. Do not add a dependency without telling the person and adding it to `requirements.txt`.
7. Small commits, `git pull` before starting, never force-push. Never commit `.cache/`, `__pycache__/`, `.venv/` or downloaded FITS files.
8. Time is short. Prefer working over perfect. **Feature freeze at hour 40 of 48**: after that only bug fixes, testing, video and submission.

## 3. Who owns what

| Role | Owns | Role file |
|---|---|---|
| A, Data | `backend/irsa.py`, `backend/irsa_check.py`, `backend/app.py`, `scripts/`, `docs/irsa_notes.md` | `docs/roles/A-data.md` |
| B, Image & science | `backend/imaging.py`, `backend/spectrum.py` (new), `docs/science_notes.md` | `docs/roles/B-image-science.md` |
| C, Frontend | `frontend/` | `docs/roles/C-frontend.md` |
| D, Product & deploy | `README.md`, `docs/` (except notes owned above), `tests/`, deployment files, `.gitignore`, video & submission | `docs/roles/D-product-deploy.md` |

`backend/demo.py` (synthetic data) is shared; change it only to keep it matching the real response shape.

## 4. Facts about the data (from IRSA documentation; verify when you can)

- SPHEREx data lives at **IRSA** (NASA/IPAC Infrared Science Archive). Main product: **Level 2 Spectral Image multi-extension FITS files (MEF)**, about 72 MB each. **Never download a full file.** Use cutouts.
- Find images covering a position: SIA2 service `https://irsa.ipac.caltech.edu/SIA` with a `COLLECTION` parameter (documented: `spherex_qr2` wide survey, `spherex_qr2_deep`, `spherex_qr2_cal`; a third-party page also mentions `spherex_qr3`, unconfirmed). Or TAP at `https://irsa.ipac.caltech.edu/TAP`. In Python: `astroquery.ipac.irsa.Irsa.query_sia(pos=(coord, radius), collection=...)` or `pyvo`.
- Cutouts: append a query string to the image URL, e.g. `<image_url>?center=<ra>,<dec>d&size=<deg>` (size in degrees). Result keeps the same extensions: `IMAGE`, `FLAGS`, `VARIANCE`, `ZODI`, `PSF`, `WCS-WAVE`. `IMAGE` is in MJy/sr.
- Pixels are about 6.2 arcsec. Six detector arrays (D1-D6): three short-wavelength, three long-wavelength. Each has a linear variable filter, so **the wavelength changes across the detector** and the wavelength seen at a given sky position changes from image to image. Total range 0.75-5.1 micron. D1 is about 0.75-1.09 micron and D2 about 1.10-1.62 micron (from the SPXQuery package); the others are to be verified.
- New images are released **weekly**; the SIA/ObsTAP search can lag slightly behind. A live query therefore picks up new data automatically.
- Official docs and tutorials (read these before guessing):
  - https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-access
  - https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products
  - https://caltech-ipac.github.io/irsa-tutorials/spherex-intro
  - https://caltech-ipac.github.io/irsa-tutorials/spherex-cutouts
  - https://caltech-ipac.github.io/irsa-tutorials/spherex-psf/
  - https://spxquery.readthedocs.io (a community package that already queries IRSA and downloads cutouts; useful reference)
- **WISE** is an older NASA infrared telescope. **WISE 0855** is a very cold, fast-moving brown dwarf and our main test object. The Gaia/WISE overlay is optional.

## 4b. Other words

RA/Dec = sky longitude/latitude. Cutout = small square cropped from a big image. Stacking = averaging images to reduce noise. Difference image = subtract a reference so static things vanish and movers remain. Brown dwarf = object between planet and star. Proper motion = a star's own motion across the sky (arcsec/year).

## 5. Known issues and traps (do not rediscover these)

1. **The live pipeline has never been run.** It was written from tutorials in a sandbox with no access to IRSA. Lines marked `# VERIFY` in `backend/irsa.py` are guesses (column names `access_url`, `t_min`; header keys `MJD-AVG`, `DETECTOR`). Role A fixes this first.
2. `irsa.py` currently keeps only the **earliest** `MAX_FRAMES` (60) images. For a position with hundreds of images this hides most of the data. Should sample evenly across time.
3. **Proper motion vs. coordinates.** The coordinates in `TARGETS` in `app.py` are approximate J2000 values. Barnard's Star moves about 10 arcsec/year, so by 2026 it is roughly 4 arcminutes from its J2000 position, outside a 2 arcmin field. WISE 0855 moves about 8 arcsec/year. Use epoch-corrected positions or a bigger field of view. Role D must verify (SIMBAD).
4. **Epsilon Indi B** is a brown dwarf pair far from the bright star Epsilon Indi A (several arcminutes; verify). The current coordinate is probably Epsilon Indi A, not B.
5. The **R Draconis** coordinate in `app.py` (RA 245.39) looks wrong; R Dra is near RA 16h32m (about 248.2 degrees). Verify in SIMBAD.
6. A bug was fixed: PNG frames were upside down (row 0 is south). `to_png_b64` now flips so images are **north up, east left**.
7. Brightness of a star changes from frame to frame mostly because the **observed wavelength** changes, not because the star varies. Do not stack or difference across different detectors without thinking about this.
8. Output frames are 64x64 px on a common grid, but a 2 arcmin field is only about 19 native pixels wide. Frames are upsampled and smooth.
9. The API sends **PNG images**, so raw flux values are lost. Anything needing real numbers (spectra) must use the raw arrays on the server (see role A task A5, role B task B6).
10. Free hosting may sleep or block outbound connections. Test that the deployed server can reach `irsa.ipac.caltech.edu`.

## 6. API contract (current)

`GET /api/targets` returns `{ "<name>": {"ra": deg, "dec": deg}, ... }`

`GET /api/frames?ra=&dec=&fov=&mode=&source=`
- `ra`, `dec`: decimal degrees, or sexagesimal like `08h55m10.8s` / `-7d14m42.5s`
- `fov`: arcmin, clamped to 0.5-10 (default 2)
- `mode`: `single` | `stack` | `diff` (default `single`)
- `source`: `live` | `synthetic` (default `live`)

Response:
```json
{
  "source": "live",
  "ra": 133.7951, "dec": -7.2452, "fov_arcmin": 2.0, "mode": "single",
  "frames": [
    {"png": "<base64 PNG, 64x64, north up, east left>",
     "mjd": 61000.5, "wavelength": 1.23, "detector": 2, "flags": "text"}
  ]
}
```
`wavelength` is micron, or NaN when unknown. Errors: 400 bad input, 404 no images, 502 IRSA failure; body `{"detail": "..."}`.

Planned additions (additive):
- `size_px` (64) and `pixel_scale_arcsec` in the `/api/frames` response (role A, task A9)
- `GET /api/spectrum?ra=&dec=&fov=&x=&y=` returns `{"points":[{"wavelength":..,"flux":..,"err":..,"mjd":..,"detector":..}]}` (role B writes `backend/spectrum.py`, role A wires the route)
- `GET /healthz` returns `{"ok": true}` (role A, for deployment)

Pixel geometry (for click-to-coordinates): grid is 64x64, centre at canvas pixel (31.5, 31.5), scale = `fov_arcmin*60/64` arcsec per pixel, north up, east left. `ra = ra0 - (x-31.5)*scale_deg/cos(dec0)`, `dec = dec0 + (31.5-y)*scale_deg`, where `scale_deg = fov_arcmin/60/64`.

## 7. Run and test

```bash
pip install -r requirements.txt
python -m uvicorn backend.app:app --port 8000     # open http://127.0.0.1:8000
python -m backend.irsa_check                       # needs internet access to IRSA
```
Quick API check without internet: `curl "http://127.0.0.1:8000/api/frames?ra=133.7951&dec=-7.2452&source=synthetic"`.

## 8. Definition of done for the project

- Real SPHEREx frames shown for all five test targets, aligned (stars do not jump), in time order.
- Works from a public link; example buttons; URL parameters work.
- At least: stack-by-detector or difference mode that visibly helps on real data.
- Honest limitations listed in the README. No fake data in the demo.
- README, 2-minute demo video, and submission text finished before hour 46.
