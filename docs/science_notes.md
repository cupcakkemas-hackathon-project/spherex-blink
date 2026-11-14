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

## Sources

- [IRSA tutorial: Introduction to SPHEREx Spectral Images](https://caltech-ipac.github.io/irsa-tutorials/spherex-intro)
- [SPHEREx Explanatory Supplement, v2.1 (2026-11-10)](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp.pdf)
- [SPHEREx Archive at IRSA: Data Products](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products)
