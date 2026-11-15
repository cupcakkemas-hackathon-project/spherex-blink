# SPHEREx Blink

SPHEREx Blink is a web tool for the NASA Space Apps Challenge **Planet X and
SPHEREx**. A user enters a sky position using Right Ascension (RA) and
Declination (Dec), and the tool displays real SPHEREx observations of that
patch as a time-ordered animation.

The goal is to make it easier for students, volunteers, and citizen
scientists to notice moving or changing sources such as nearby stars, brown
dwarfs, comets, asteroids, and variable objects.

## How it works

1. The user enters decimal or sexagesimal sky coordinates.
2. The backend queries the NASA/IPAC Infrared Science Archive (IRSA).
3. IRSA returns small image cutouts instead of full-size FITS files.
4. The backend aligns the images to a common north-up, east-left grid.
5. The browser displays the images as an animation with date, detector,
   wavelength, and flag metadata.

The viewer provides:

- **All frames:** observations in time order.
- **Stack by detector:** combines frames from each detector.
- **Difference:** subtracts a reference image to highlight changes.
- **Spectrum API:** returns wavelength, flux, error, date, and detector values
  for a selected image position.
- **URL parameters:** coordinates, field of view, view mode, and data source
  can be included in a URL.

The five verified target coordinates are listed in
[`docs/targets.md`](docs/targets.md).

## Benefits, impact, and creativity

SPHEREx data is normally accessed through specialist archives and large
astronomical files. SPHEREx Blink provides a simpler visual workflow: enter a
position, compare observations, and inspect changes without learning an
archive query language.

The project is creative because it combines a public-friendly blink animation
with detector stacking, difference images, wavelength metadata, and spectrum
extraction. The team considered scientific validity, image alignment,
proper motion, changing wavelengths between observations, response time,
intermittent archive failures, and usability for people without astronomy or
programming experience.

Synthetic data is clearly labelled as fake and is used only for interface
testing. Scientific results shown by the live mode come from real SPHEREx
data accessed through IRSA.

## Tools and technologies

- Python 3.10+
- FastAPI and Uvicorn for the API and web server
- HTML, CSS, and vanilla JavaScript for the frontend
- Astropy for coordinates, FITS files, and WCS
- `reproject` for image alignment
- NumPy and Pillow for image processing and PNG output
- NASA/IPAC IRSA for SPHEREx data and cutouts
- SIMBAD for verifying the five target identities and coordinates

## Run locally

Python 3.10 or newer and an internet connection are required for live
SPHEREx data. Synthetic demo mode can be used without IRSA access, but it is
not real scientific data.

From the repository root:

```powershell
pip install -r requirements.txt
python -m uvicorn backend.app:app --port 8000
```

Open the website:

```text
http://127.0.0.1:8000/
```

Useful local endpoints:

```text
http://127.0.0.1:8000/healthz
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/?ra=133.7951&dec=-7.2452&fov=3&mode=single&source=live
```

The live example may take time on its first request because the application
must query IRSA, download cutouts, reproject images, and create PNG frames.

## Verification

Run the IRSA connectivity check:

```powershell
python -m backend.irsa_check
```

Run the API verification:

```powershell
python scripts/verify_api.py
```

The verification checks health, live frames, all three view modes, detector
coverage, timestamps, wavelengths, spectrum output, caching, and invalid
input handling.

Latest local verification on `main`:

- Single/live view: 58 frames in 16.9 seconds.
- Stack/live view: 30 frames.
- Difference/live view: 58 frames.
- Spectrum: 57 valid non-synthetic points.
- All automated API checks passed.
- Full findings are recorded in [`docs/Finding.md`](docs/Finding.md).

## Honest limitations

- The first live request is slower because data must be fetched and
  processed; cached repeats are much faster.
- IRSA can temporarily return HTTP 503 or no usable cutouts. The application
  retries downloads and reports an IRSA-unavailable error if all requested
  cutouts fail.
- Frame counts and load times can vary between requests.
- SPHEREx pixels are about 6.2 arcseconds wide.
- Brightness can change because the observed wavelength changes between
  frames, not necessarily because the object itself varies.
- Public deployment and mobile-network testing have not been completed.
- The project does not claim that a moving object is visible unless it was
  actually observed during testing.

## Project files

| File or folder | Purpose |
|---|---|
| `backend/app.py` | FastAPI routes, request validation, response formatting, and page hosting |
| `backend/irsa.py` | IRSA queries, FITS cutouts, caching, reprojection, wavelength and flag data |
| `backend/imaging.py` | Stacking, difference images, contrast stretching, and PNG encoding |
| `backend/spectrum.py` | Spectrum extraction from cached raw frames |
| `backend/demo.py` | Synthetic demo data for UI testing only |
| `frontend/index.html` | Browser interface and animation controls |
| `scripts/verify_api.py` | Automated API verification |
| `scripts/warm_cache.py` | Prefetches real target data for a faster demo |
| `docs/targets.md` | SIMBAD-based coordinates for the five targets |
| `docs/Finding.md` | Test results, observed errors, and limitations |
| `docs/irsa_notes.md` | Verified IRSA data-access notes |
| `requirements.txt` | Python dependencies |
| `AGENTS.md` | Shared project context and contributor rules |

## Data and credits

SPHEREx data is accessed through the NASA/IPAC Infrared Science Archive
(IRSA). The project uses Astropy, reproject, NumPy, Pillow, FastAPI, and
Uvicorn. Any public submission should include the acknowledgement requested
by IRSA for SPHEREx data products.
