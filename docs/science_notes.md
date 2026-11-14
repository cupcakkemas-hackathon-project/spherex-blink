# SPHEREx science notes

## What is in a Level 2 Spectral Image?

Each Level 2 file is for one detector and one exposure. Its image pixels are calibrated surface brightness, not point-source brightness in a unit such as Jy.

- **IMAGE** — calibrated surface brightness in MJy/sr. Zodiacal light has **not** been subtracted. [IRSA intro, §§6, 8](https://caltech-ipac.github.io/irsa-tutorials/spherex-intro); [Explanatory Supplement, §2.2](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp.pdf)
- **FLAGS** — a per-pixel bitmask: several flags can apply to one pixel at once. The assigned bits and meanings below are from Table 16 of the [Explanatory Supplement, pp. 33–35](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp.pdf); the [IRSA intro, §9](https://caltech-ipac.github.io/irsa-tutorials/spherex-intro) also shows how to read flag names from a file's header.
- **VARIANCE** — an estimated variance for each calibrated surface-brightness pixel, in (MJy/sr)^2. [IRSA intro, §10](https://caltech-ipac.github.io/irsa-tutorials/spherex-intro)
- **ZODI** — a per-pixel model estimate of the zodiacal-light background, in MJy/sr. This background remains in IMAGE. [IRSA intro, §11](https://caltech-ipac.github.io/irsa-tutorials/spherex-intro); [Explanatory Supplement, §§2.2, 3.2.11](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp.pdf)
- **PSF** — the point-spread function, describing how a point-like source is spread over pixels. Current DR1/QR3 files use an oversampled **EPSF** model; QR2 files use a **PSF** cube. [IRSA intro, §12](https://caltech-ipac.github.io/irsa-tutorials/spherex-intro); [Data Products guide, “EPSF” and “PSF”](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products)

## FLAGS: assigned bits and a starting mask

Bit numbers are positions in the bitmap, not the numeric flag values. The supplement assigns these bits:

| Bit | Name | Meaning |
|---:|---|---|
| 0 | TRANSIENT | An onboard transient (such as a cosmic-ray hit); can also flag charge spill from a bright source. |
| 1 | OVERFLOW | The onboard overflow threshold was reached. |
| 2 | SUR_ERROR | Onboard data/checksum error; together with TRANSIENT or OVERFLOW, can identify an early event. |
| 6 | NONFUNC | Permanently unusable/dead pixel. |
| 7 | DICHROIC | Low-throughput pixel in the Band 3/4 dichroic region; not useful for photometry. |
| 9 | MISSING_DATA | Onboard data for the pixel was lost before archive ingest. |
| 10 | HOT | Noisy or spurious signal; not usable for science. |
| 11 | COLD | Abnormally low or unresponsive pixel; not usable for science. |
| 12 | FULLSAMPLE | Full sample history is available; informational only. |
| 14 | PHANMISS | Missing phantom pixels prevented a correction. |
| 15 | NONLINEAR | A reliable nonlinearity correction could not be determined; exclude from most science analyses. |
| 17 | PERSIST | Affected by persistent charge above the Level 2 threshold. |
| 19 | OUTLIER | Flagged by the outlier-pixel detection module. |
| 20 | CROSSTALK | Affected by ordinary crosstalk. |
| 21 | SOURCE | Mapped to a known source; this is not itself a bad-pixel flag. |
| 22 | GHOST | Affected by an optical ghost from a bright source in the image. |
| 23 | GHOST_FPA | Affected by a bright source on another detector; currently unused and subsumed into GHOST_EXT. |
| 24 | GHOST_EXT | Affected by an optical ghost from a source outside the field of view. |
| 25 | STREAK | Affected by a detected streak, usually consistent with an Earth-orbiting object. |
| 26 | BLOOM | Affected by charge blooming from a bright source. |
| 27 | SNOWBALL | Affected by a large snowball event. |
| 28 | HALO | Affected by the halo of a transient; use caution in science analysis. |
| 29 | SATELLITE_HALO | Affected by the halo of a satellite streak; not recommended for science analysis. |

The defined bit positions above are the ones listed in Table 16; do not infer meanings for unlisted positions.

**Recommended starting mask for derived stacks/photometry:** follow the IRSA Mosaic Tool's L2 rule and exclude pixels with bits **0, 2, 6, 7, 9, 10, 11, 14, 15, 17, 20, 22–29**. In names: TRANSIENT, SUR_ERROR, NONFUNC, DICHROIC, MISSING_DATA, HOT, COLD, PHANMISS, NONLINEAR, PERSIST, CROSSTALK, GHOST, GHOST_FPA, GHOST_EXT, STREAK, BLOOM, SNOWBALL, HALO, SATELLITE_HALO. The mosaic propagates OVERFLOW (1), SOURCE (21), and OUTLIER (19); FULLSAMPLE (12) is informational. [Explanatory Supplement, §3.4.3, p. 46](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp.pdf)

This is the archive's mosaic recipe, not a rule to silently erase pixels from every raw blink frame. For our viewer, keep the original frame available and retain/display its flags; use the mask for derived stacks or photometry. The supplement notes that TRANSIENT can include cosmic rays or charge spill, so a flag is useful context, not proof of an astronomical mover. [Explanatory Supplement, Table 16, pp. 33–35](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp.pdf)

## Why a star's brightness changes between frames

SPHEREx uses linear variable filters: wavelength changes across each detector. When the spacecraft repoints, the same star can land on pixels that measure different wavelengths. A star's spectrum is not equally bright at every wavelength, so its measured brightness can change even if the star itself did not vary. A brightness change across different wavelengths is not, by itself, evidence of variability. [IRSA intro, §§8, 8b–8c](https://caltech-ipac.github.io/irsa-tutorials/spherex-intro); [Explanatory Supplement, §2.2](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp.pdf)

## Zodiacal light: what it is and whether to subtract it

Zodiacal light is diffuse foreground light from interplanetary dust. The ZODI layer is the mission's model estimate of that background, and the Level 2 IMAGE does not have it subtracted. The model captures spatial and temporal variation but can underestimate the amplitude, so subtraction can leave residual background. [Explanatory Supplement, §§2.2, 3.2.11](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp.pdf)

For **derived stacks/mosaics**, subtract ZODI as `IMAGE - ZODI`, matching the official IRSA Mosaic Tool procedure; keep in mind the model may leave residuals. For **single-frame blinking**, do not silently replace the archived image with a zodi-subtracted one: preserve the original view, or clearly label subtraction as a processing choice. [Explanatory Supplement, §3.4.3, p. 46](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp.pdf)

## Caveats to say in the demo

- Each detector image samples a wavelength that depends on where the target falls on that detector. Frames taken at different times can therefore differ in wavelength as well as time.
- Brightness changes between frames can be caused by wavelength, image quality, or background processing; they do not prove that a star varied.
- The displayed L2 images include zodiacal background; any subtraction uses a model and may leave residuals.
- Flags describe pixel conditions and can overlap. A flagged pixel should be treated as a warning to inspect, not as evidence of a moving astronomical object.

## B2: WISE 0855 display check

On 2026-11-14, a live `/api/frames` request for WISE 0855 at 3 arcmin returned 56 real frames in 135 seconds. Their MJDs were nondecreasing across 181.808 days; repeated MJDs occur for observations sharing a timestamp. The live UI at 2 arcmin loaded and played 42 real frames. The IRSA cutout service returned some HTTP 503 errors, and one frame was rejected because its target wavelength was outside the supported range; failed frames were skipped. These counts and timing are from this run, not a guarantee of future query performance. [IRSA verification notes](./irsa_notes.md)

I compared the existing per-frame 5th–99.7th percentile asinh stretch with a pooled shared stretch, a per-detector shared stretch, and a robust median/MAD clipping trial on real cutouts. The shared stretches retained cross-frame brightness differences but changed contrast between frames; the clipping trial made background grain dominate. For the motion-finder display, keep **per-frame 5th–99.7th percentile asinh**: it kept faint point sources visible across the detector bands in the sample. This is a display stretch, not photometry; it hides real frame-to-frame brightness differences, so do not interpret rendered brightness as variability.

`stretch` now estimates its limits from finite pixels only and paints NaN/Inf pixels black. This prevents no-coverage pixels from shifting the lower percentile. I did not add a median filter: the real sources are compact, and filtering them without validating source preservation risks removing genuine point sources. Per-pixel FLAGS are not yet passed into `data` by the current loader (it only returns a count in `frame["flags"]`), so cosmic-ray/bad-pixel masking still needs Role A's A8 implementation. Until then, isolated flagged pixels may remain visible.

## B3: Time-window stacking

`stack` now groups frames by detector and fixed 7-day windows anchored to MJD 0. This preserves separate wavelength bands and returns the groups in time order rather than collapsing each detector's full history into one image. If every frame in a group has a `variance` array, the stack uses per-pixel inverse-variance weighting and returns the variance of the weighted mean. Otherwise it uses the finite-pixel arithmetic mean. In either case, `flags` records how many frames were combined.

The current Role A loader does not yet include `variance` in its frame dictionaries, so live app stacks currently take the arithmetic-mean path. Ask Dhiya to carry the FITS VARIANCE extension through as `frame["variance"]` before describing live stacks as inverse-variance weighted.

On 2026-11-14, a live 3-arcmin WISE 0855 API request returned 8 chronological stack frames spanning MJD 60800.746–60980.321 and detectors D1–D6. The corresponding 59-input run formed groups of 3–15 frames; a rough high-pass noise comparison gave a median stack/input ratio of 0.637. This is only an image-texture check, not calibrated uncertainty. I could not confidently identify WISE 0855 or verify its motion in the stacks, so the moving-source acceptance check remains open; its coordinates and epoch also need Role D's verification.

## B4: Detector-specific differences

`diff` now subtracts each frame's median reference made from frames of the same detector, then returns frames in MJD order and appends `difference vs. detector median` to the flags text. `stretch_symmetric` clips at the 99.7th percentile of absolute residuals and maps zero to mid-gray, with negative and positive residuals on opposite sides. The regular stretch remains unchanged for single and stacked images.

The current Role A route still calls `to_png_b64` without `symmetric=True`. Ask Dhiya to pass `symmetric=(mode == "diff")` so the API actually displays both residual signs. In a real 3-arcmin WISE 0855 run, 59 frames across D1–D6 produced 59 chronological differences. The inspected frames still showed source residuals, and I could not confidently identify a moving object; therefore the visual acceptance check is not yet met.

## B5: Wavelength normalization decision

I did not add another normalization. The existing per-frame stretch already maps each frame's 5th–99.7th percentile range to the display range. Applying a positive linear rescale and offset before that stretch cancels out. I checked median/MAD normalization on 59 live WISE 0855 frames: it changed **0 of 241,664** rendered 8-bit pixels. The shared stretch comparison in B2 also changed contrast between frames. Keep the existing stretch; it is for visibility, not preserving photometric brightness across wavelengths.

## B6: Spectrum extraction

`extract_spectrum` reports the mean aperture brightness minus the median of a surrounding annulus, in MJy/sr. It propagates `variance` when the aperture and annulus variances are valid; otherwise it estimates the error from the annulus's robust scatter. For a canvas click at row `r`, pass array row `y = 63 - r`.

This is not yet a complete API feature: `irsa.get_raw_frames` and `/api/spectrum` are not present, and the current loader's wavelength is evaluated at the query center rather than an arbitrary clicked pixel. Ask Dhiya to provide raw frames with wavelengths evaluated at the selected sky position, carry variance when available, and wire the route at the end of `app.py`. An initial live field probe around the approximate Barnard's Star coordinates returned 41 frames from D2, D3, D5, and D6, so it did not demonstrate a smooth 0.75–5 micron spectrum. Also, each point comes from a different observation date; a moving object may no longer be at the clicked position.

## B7: Motion and field-of-view check

The SIMBAD Harvard mirror lists WISE 0855's proper-motion components as -8123.7 and +673.2 mas/yr, a total of **8.152 arcsec/yr**. Across the 181.808-day SPHEREx span, that predicts about **4.06 arcsec** of motion: 1.44 pixels on the resampled 3-arcmin grid, but only 0.65 of a native SPHEREx pixel. I queried 30 real frames centered on the SIMBAD-propagated position for the middle of the observation span (RA 133.760695°, Dec -7.242262°) and inspected single frames plus per-detector differences directly; this was not an end-to-end UI test. I could not confidently identify WISE 0855 moving in either view. The long-baseline D1/D4 frames were faint at the predicted position; the three D5 visits spanned 7 minutes and the three D6 visits spanned about 3.2 hours. This is a non-detection in this sample, not evidence that the object did not move. [SIMBAD: WISEA J085510.74-071442.5](https://simbad.cfa.harvard.edu/simbad/sim-id?Ident=WISEA+J085510.74-071442.5); [IRSA verification notes](./irsa_notes.md)

SIMBAD lists Barnard's Star's total proper motion as **10.393 arcsec/yr**. From the approximate J2000 target position to 2026-11-14, that is about **4.65 arcmin**. The current 2-arcmin field (1-arcmin half-width) will miss it; the 10-arcmin option (5-arcmin half-width) can just contain it, so an epoch-corrected coordinate and some margin are preferable. A live 10-arcmin field returned 53 frames over 11.618 days. The brightest median pixel in D2–D6 was at (33–34, 60–61), consistent within about a pixel with the SIMBAD-propagated position (33.7, 59.8). This supports the larger-field conclusion, but the short baseline is not a proper-motion measurement. [SIMBAD: Barnard's Star](https://simbad.cfa.harvard.edu/simbad/sim-id?Ident=Barnard%27s+Star)

## Sources

- [IRSA tutorial: Introduction to SPHEREx Spectral Images](https://caltech-ipac.github.io/irsa-tutorials/spherex-intro)
- [SPHEREx Explanatory Supplement, v2.1 (2026-11-10)](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp.pdf)
- [SPHEREx Archive at IRSA: Data Products](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products)
