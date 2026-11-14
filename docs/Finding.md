# Testing Findings

**Date:** 14 November 2026  
**Branch:** `main`

## Setup

- Pulled `main`: already up to date with `origin/main`
- Started the server with:
  `python -m uvicorn backend.app:app --port 8000`
- Ran:
  `python scripts/verify_api.py`

## Automated API test results

All checks passed:

- `/healthz` returned HTTP 200.
- The live frames endpoint returned HTTP 200.
- 57 live frames were returned.
- First request completed in 21.5 seconds.
- Cached repeat request completed in 0.07 seconds.
- The second request was under one second.
- Frame timestamps increased correctly.
- All six detectors were represented: `{1: 8, 2: 10, 3: 9, 4: 10, 5: 10, 6: 10}`.
- Every detector had at least three frames.
- Wavelengths were valid.
- `/api/spectrum` returned HTTP 200.
- The spectrum returned 57 valid points.
- Spectrum wavelengths were sorted.
- Spectrum contained no NaN flux or error values.
- Different image pixels produced different wavelength values.
- Centre wavelength coverage was 0.82-4.97 microns.
- Invalid coordinate inputs were rejected correctly.

## Manual browser observations

- WISE 0855:
  - All frames loaded: 28 frames.
  - Stack by detector loaded: 6 frames.
  - Difference view loaded: 28 frames.
  - Date, detector, wavelength, and flags were displayed.
- Barnard's Star loaded 19 frames.
- Epsilon Indi B loaded 8 frames.
- RW Aurigae remained on "Fetching images..." after 30 seconds.
- R Draconis remained on "Fetching images..." after 30 seconds.
- Sexagesimal coordinates were accepted:
  `08h55m10.8s / -7d14m42.5s`.
- Changing the field of view updated the URL.
- A no-data position (`RA 10, Dec -85`) did not return a clear message within 60 seconds.

## Issues and limitations

- The first live request took 21.5 seconds, slightly above the target of 20 seconds.
- Some IRSA cutouts may be skipped because of intermittent HTTP 503 responses.
- Frame counts can vary between runs.
- New searches can take more than 30 seconds for some targets.
- The no-data query needs a timely, clear user-facing message.
- While a new search is loading, old frame metadata may remain visible.
- Mobile and deployed-site testing were not performed in this local run.

## Overall result

The `main` branch passed all automated API verification checks. Core live-data loading, caching, detector coverage, wavelength handling, and spectrum generation are working locally.