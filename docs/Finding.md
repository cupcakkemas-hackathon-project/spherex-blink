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

All current checks passed:

- `/healthz` returned HTTP 200.
- Single/live view returned 58 frames in 16.9 seconds.
- Stack/live view returned 30 frames from all six detectors.
- Difference/live view returned 58 frames.
- Timestamps increased correctly in all three views.
- Single detector counts: `{1: 8, 2: 10, 3: 10, 4: 10, 5: 10, 6: 10}`.
- Stack detector counts: `{1: 3, 2: 5, 3: 7, 4: 3, 5: 5, 6: 7}`.
- Difference detector counts: `{1: 8, 2: 10, 3: 10, 4: 10, 5: 10, 6: 10}`.
- Wavelengths were present in single, stack, and difference responses.
- Spectrum returned HTTP 200 with 57 points.
- Spectrum was confirmed as non-synthetic.
- Spectrum flux and error values were present.
- Spectrum wavelengths were valid and sorted.
- Spectrum coverage by detector was:
  - D1: 0.816870-1.039132 micron
  - D2: 1.152649-1.591008 micron
  - D3: 1.640745-2.382276 micron
  - D4: 2.428191-3.535491 micron
  - D5: 3.886603-4.370041 micron
  - D6: 4.425614-4.968323 micron

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

- The current cold single/live request took 16.9 seconds; this is within the 20-second target but still depends on IRSA response time.
- Some IRSA cutouts may be skipped because of intermittent HTTP 503 responses.
- A later live search showed: `Error: IRSA is temporarily unavailable: IRSA did not return any requested cutouts`.
- This means IRSA returned no usable cutouts for that request after the backend's retry attempts; retrying later may succeed.
- Frame counts can vary between runs.
- New searches can take more than 30 seconds for some targets.
- The no-data query needs a timely, clear user-facing message.
- While a new search is loading, old frame metadata may remain visible.
- Mobile and deployed-site testing were not performed in this local run.

## Latest observed failure

The browser displayed:

```text
Error: IRSA is temporarily unavailable: IRSA did not return any requested cutouts
```

This is a live IRSA/data availability failure, not a frontend rendering error. The backend retries cutout downloads and skips individual failures, but reports an error when all requested cutouts fail.

## Overall result

The `main` branch passed all current automated API verification checks. Core live-data loading in all three views, detector coverage, wavelength handling, and non-synthetic spectrum generation are working locally.