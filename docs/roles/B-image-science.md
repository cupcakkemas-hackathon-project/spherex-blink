# Role B: Image and science

**Your job:** make the pictures actually reveal moving things, make the science honest, and build the standout feature (spectrum on the fly).

Read `AGENTS.md` first (rules, data facts, known traps).

## You own
`backend/imaging.py`, `backend/spectrum.py` (create it), `docs/science_notes.md` (create it).
Do not edit `irsa.py`/`app.py` (role A), `frontend/` (role C). If you need a new field or route, ask A or add the clearly marked block that task B6 describes.

## What the code does today
`imaging.stretch` turns one 2D array into 0-255 with a percentile clip and an asinh curve. `to_png_b64` encodes PNGs (north up, east left). `apply_mode(frames, mode)` implements:
- `single`: unchanged
- `stack`: for each detector, average all its frames into one (so you get at most 6 frames)
- `diff`: each frame minus the median of **all** frames

Frames are dicts: `data` (2D array, MJy/sr), `mjd`, `wavelength` (micron or NaN), `detector` (1-6), `flags` (text).

Until role A has real data, test with `source=synthetic` (fake: 25 static stars plus one moving blob).

---

## B1. Understand the data and the problem (30-60 min, no code)
- Read the "SPHEREx Spectral Image" section of https://caltech-ipac.github.io/irsa-tutorials/spherex-intro and the SPHEREx Explanatory Supplement (linked from the IRSA SPHEREx page).
- Write `docs/science_notes.md` with short plain-language answers to: What is in each extension (`IMAGE`, `FLAGS`, `VARIANCE`, `ZODI`, `PSF`)? What do the flag bits mean (tell role A which to mask)? Why does a star's brightness change between frames? What is zodiacal light and should we subtract it (`ZODI` extension)?

**Done when:** `science_notes.md` exists with those answers and a list of caveats the team should mention in the demo.

## B2. Check and tune the picture on real data (needs role A, task A3)
- Is the 5-99.7 percentile asinh stretch good for faint objects? Try alternatives (sigma-clipped limits, a single shared stretch for all frames vs. per-frame). A per-frame stretch hides real brightness changes; a shared one shows them but may flicker. Pick one and explain why in `science_notes.md`.
- Bad pixels and cosmic rays make bright speckles that look like movers. Handle NaNs and outliers (for example clip single-pixel spikes with a small median filter, **only if it does not erase real point sources**).
- Remember frames are 64x64 upsampled from about 19 native pixels for a 2 arcmin field. Do not over-sharpen.

**Done when:** on WISE 0855 real data, background stars look like clean dots and the blink looks smooth rather than flickering.

## B3. Improve `stack`
Averaging all frames of a detector into one image destroys the time dimension, which defeats the purpose. Change `stack` to average **within time windows**: for each detector, group frames into windows (for example one per week or per survey pass, make it a constant), and return one stacked frame per (detector, window), still sorted by time.
- Weight by inverse variance if the `VARIANCE` extension is available (ask role A to carry it through in the frame dict, as `frame["variance"]`).
- Put the number of frames combined in `frame["flags"]` (already done: "N frames stacked").

**Done when:** stacking visibly lowers noise on real data and a moving object still shows motion between stacked frames.

## B4. Improve `diff`
Subtracting the median of **all** frames across **different detectors** leaves residuals, because star brightness depends on wavelength. Do the subtraction **per detector** (median of that detector's frames), keeping the output in time order. Show positive and negative residuals sensibly (symmetric stretch around 0 is better than the percentile stretch for diff images). Add a `diff` flag text such as "difference vs. detector median".

**Done when:** in diff mode, static stars mostly vanish, and a moving object leaves a visible bright/dark pair.

## B5. Optional: smoother blinking across wavelengths
Frames from different detectors differ in brightness. Consider an optional normalisation so a blink through time does not flash. Only do this if it helps; document it.

## B6. Spectrum on the fly (the standout feature)
Create `backend/spectrum.py` with:

```python
def extract_spectrum(frames, x, y, radius_px=1.5):
    """frames: raw frames from irsa.get_raw_frames (2D 'data' in MJy/sr).
    x, y: pixel position on the 64x64 grid (array indices, row 0 = south).
    Returns list of {"wavelength", "flux", "err", "mjd", "detector"} sorted by wavelength."""
```
- Aperture photometry: sum (or mean) within `radius_px`, subtract the median of a surrounding ring as local background. Use `variance` for the error if available.
- Skip frames where the wavelength is NaN or the aperture touches NaNs.
- Note for the grid: the canvas shows the array **flipped vertically** (north up), so a click at canvas row `r` is array row `63 - r`. Document this in the function.
- Add the route at the end of `app.py` in a block marked `# --- spectrum (B) ---` (tell role A): `GET /api/spectrum?ra=&dec=&fov=&x=&y=` using `irsa.get_raw_frames` (do not download again). Add a synthetic fallback only for `source=synthetic`, labelled fake.
- Caveat to write down: each image samples one wavelength at that sky position, so the spectrum is built from many separate observations at different dates. A moving object changes position between them.

**Done when:** for a bright star (use a field around Barnard's Star or R Dra) the spectrum is a smooth curve across about 0.75-5 micron, and the response matches the contract in `AGENTS.md` section 6.

## B7. Science check for the write-up
Run a short test and write results into `science_notes.md`: does WISE 0855 visibly move in `single` and `diff` modes? Over how many days? Roughly how many arcseconds (use about 8 arcsec/year as a rough check, verify the real value)? Does Barnard's Star (about 10 arcsec/year) need a larger field? These numbers become talking points in the demo.

## B8. Stretch only
Help role C with a Gaia or WISE overlay (Aladin Lite). Only after everything above works.

## Hand-offs
- From A: `get_raw_frames`, wavelengths, variance and flags in frames.
- To A: which flag bits to mask (B1).
- To C: spectrum route is ready (B6).
- To D: caveats and talking points (B1, B7).
