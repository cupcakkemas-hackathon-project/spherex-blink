# IRSA verification notes

## A1 check

Command:

```text
python -m backend.irsa_check
```

The first attempt failed before contacting IRSA because the local environment
did not have Astropy installed:

```text
ModuleNotFoundError: No module named 'astropy'
```

After installing the existing `requirements.txt`, the check reached IRSA but
the configured `spherex_qr2` collection returned no rows:

```text
images found: 0
columns: ['s_ra', 's_dec', 'facility_name', 'instrument_name', 'dataproduct_subtype', 'calib_level', 'dataproduct_type', 'energy_bandpassname', 'energy_emband', 'obs_id', 's_resolution', 'em_min', 'em_max', 'em_res_power', 'proposal_title', 'access_url', 'access_format', 'access_estsize', 't_exptime', 's_region', 'obs_collection', 'obs_intent', 'algorithm_name', 'facility_keywords', 'instrument_keywords', 'environment_photometric', 'proposal_id', 'proposal_pi', 'proposal_project', 'target_name', 'target_type', 'target_standard', 'target_moving', 'target_keywords', 'obs_release_date', 's_xel1', 's_xel2', 's_pixel_scale', 'position_timedependent', 't_min', 't_max', 't_resolution', 't_xel', 'obs_publisher_did', 's_fov', 'em_xel', 'pol_states', 'pol_xel', 'cloud_access', 'o_ucd', 'upload_row_id']
frames built: 0
```

IRSA's current SPHEREx data-access documentation (12 November 2026) says
QR2 data are no longer searchable through SIA2. The searchable spectral-image
collections are DR1, DR1 deep, QR3, and QR3 deep. A query for WISE 0855 using
`['spherex_dr1', 'spherex_qr3']` returned 258 rows. The A1 check used the
challenge position `RA=133.795`, `Dec=-7.2452`.

## Verified SIA2 metadata

The successful SIA2 table contains these relevant columns:

- `access_url`: direct on-premises FITS data URL.
- `t_min` and `t_max`: observation time bounds in MJD.
- `em_min` and `em_max`: wavelength bounds in metres.
- `s_pixel_scale`, `s_fov`, and `s_region`: image geometry metadata.
- `cloud_access`: cloud-hosted access information.

The first three rows of the successful query were printed by the probe. Their
table columns matched the complete column list above. The earliest row had:

```text
access_url =
https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/2025W19_1B/l2b-v27-2026-197/3/level2_2025W19_1B_0116_1D3_spx_l2b-v27-2026-197.fits
t_min = 60800.700028
t_max = 60800.701361
```

The first three rows, with the fields needed by the pipeline, were:

```text
1 {'s_ra': '134.41457781198824', 's_dec': '-9.004141208277177', 'obs_id': '2025W19_1B_0116_1', 'access_url': 'https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/2025W19_1B/l2b-v27-2026-197/3/level2_2025W19_1B_0116_1D3_spx_l2b-v27-2026-197.fits', 't_min': '60800.700028', 't_max': '60800.701361', 'em_min': '1.6301e-06', 'em_max': '2.4346e-06', 'obs_collection': 'spherex_dr1'}
2 {'s_ra': '134.40997823066974', 's_dec': '-9.023376583067057', 'obs_id': '2025W19_1B_0116_1', 'access_url': 'https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/2025W19_1B/l2b-v27-2026-197/6/level2_2025W19_1B_0116_1D6_spx_l2b-v27-2026-197.fits', 't_min': '60800.700028', 't_max': '60800.701361', 'em_min': '4.4115e-06', 'em_max': '5.0096e-06', 'obs_collection': 'spherex_dr1'}
3 {'s_ra': '134.35703397184722', 's_dec': '-9.19228782270585', 'obs_id': '2025W19_1B_0116_2', 'access_url': 'https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/2025W19_1B/l2b-v27-2026-197/3/level2_2025W19_1B_0116_2D3_spx_l2b-v27-2026-197.fits', 't_min': '60800.701521', 't_max': '60800.702853', 'em_min': '1.6301e-06', 'em_max': '2.4346e-06', 'obs_collection': 'spherex_dr1'}
```

The successful rerun of `python -m backend.irsa_check` printed:

```text
images found: 258
frames built: 42
```

During frame construction, 503 Service Unavailable responses occurred for
some cutout URLs; those frames were skipped by the existing error handling.
This is an IRSA service response, not evidence that every cutout is currently
available.

## Verified cutout FITS structure

Using the first real row and:

```text
?center=133.7951,-7.2452d&size=0.05
```

the cutout returned:

```text
0 PRIMARY   PrimaryHDU
1 IMAGE     ImageHDU       (29, 29) float32
2 FLAGS     ImageHDU       (29, 29) int32
3 VARIANCE  ImageHDU       (29, 29) float32
4 ZODI      ImageHDU       (29, 29) float32
5 EPSF      BinTableHDU
6 WCS-WAVE  BinTableHDU
```

The `IMAGE` extension header contained:

```text
EXTNAME = IMAGE
BUNIT = MJy / sr
DETECTOR = 3
OBSID = 2025W19_1B_0116_1
DATE = 2026-07-17T10:16:06.188
MJD-AVG = 60800.70069465
```

Therefore `MJD-AVG` and `DETECTOR` are verified header keys for a cutout.
`WCS-WAVE` is a binary-table spectral WCS extension; its wavelength lookup
has one row and three columns:

```text
columns: X (9J), Y (14J), VALUES (252E)
```

`X` and `Y` are the lookup-grid pixel coordinates. `VALUES` contains a
two-element wavelength/bandwidth pair at each lookup-grid point, in microns.
The `IMAGE` header contains the alternate spectral WCS keys
`CTYPE1W= WAVE-TAB`, `CTYPE2W= WAVE-TAB`, `CUNIT1W= um`, and
`CUNIT2W= um`. Following the IRSA tutorial, the code constructs
`WCS(header=image_header, fobj=hdul, key="W")`, disables SIP distortion for
that spectral WCS, converts the target pixel with `pixel_to_world`, and uses
the wavelength component.

The probe used a real WISE 0855 cutout at `RA=133.7951`, `Dec=-7.2452`,
`size=0.08333333333333333` degrees. It returned a 49 by 49 `IMAGE` and
resolved the target pixel to approximately `(24.2154, 23.7705)` with a
wavelength of `2.3649379` micron and bandwidth `0.0586735` micron.

The updated `python -m backend.irsa_check` run on 2026-11-14 built 58 frames
from 258 SIA rows. The checker validated that all 58 wavelengths were finite
and within 0.75-5.1 micron; all 58 values were distinct. Some cutouts
returned HTTP 503 and were skipped, as documented above.

Measured target-position wavelength ranges from that run:

| Detector | Minimum (micron) | Maximum (micron) | Frames |
|---|---:|---:|---:|
| D1 | 0.783449 | 1.114556 | 18 |
| D2 | 1.280405 | 1.629437 | 8 |
| D3 | 2.209355 | 2.413861 | 3 |
| D4 | 2.436878 | 3.830132 | 19 |
| D5 | 4.039577 | 4.407620 | 7 |
| D6 | 4.860919 | 5.004498 | 3 |

The detector ordering is consistent across the sampled frames and follows the
six SPHEREx bands from short to long wavelength. The observed edges can extend
slightly beyond the rounded tutorial labels (for example D1 reaches 1.114556
and D4 reaches 3.830132 micron), so these measured ranges should be used for
the current dataset rather than treating the rounded labels as hard limits.

The cutout `size` parameter is in degrees. The tested `0.05` degree request
returned a 29 by 29 pixel cutout. The IRSA cutout service is not assumed to
have a fixed minimum here; callers should use a positive degree value suited
to the requested field of view.

## Updating

The app queries IRSA live, so newly searchable DR1 and QR3 images are picked up
automatically. IRSA documents that ingestion is weekly and SIA2 availability
can lag ingestion by about a day. The app's in-memory cache should therefore
have a finite TTL when it is added; a process restart also clears it.

## A5 raw-frame cache and variance verification

`backend.irsa.get_raw_frames(ra, dec, fov)` now returns the reprojected raw
frame dictionaries before PNG encoding. Each live frame includes `data`,
`variance`, `mjd`, `wavelength`, `detector`, and `flags`. The `VARIANCE`
extension is reprojected onto the same 64 by 64 output grid as `IMAGE`.
Results are cached in memory by rounded `(ra, dec, fov)` for four hours by
default; `RAW_CACHE_TTL_SECONDS` can override that value.

On 2026-11-14, `python -m backend.irsa_check` built 59 live frames. It
validated matching 64 by 64 `data` and `variance` shapes, 59 finite
wavelengths, and 59 distinct wavelength values. The same-process cache timing
for WISE 0855 at five arcminutes was:

```text
first request: 7.959s (59 frames)
second request: 0.000012s (59 frames)
```

`from backend.irsa import get_raw_frames` imported successfully.

Using a clean Uvicorn process on port 8765, two identical live
`/api/frames?ra=133.7951&dec=-7.2452&fov=5&source=live` requests took 9.415
seconds and 0.029 seconds respectively, with 59 frames returned both times.

## WCS warning check

The repeated SIP/`CTYPE` text came from Astropy's WCS logger at INFO level;
the pipeline now sets that logger to WARNING, leaving higher-severity messages
visible. The checker counts `WCS.all_world2pix` convergence warnings separately
for the image/variance reprojection and target wavelength lookup. The verified
2026-11-14 run reported:

```text
WCS convergence warnings: reproject=0, wavelength=0, total=0
```

Thus no affected frames required an alignment comparison in that run. A real
cutout neighbor check at the target pixel `(24.2154, 23.7705)` returned
center/neighbor wavelengths of `2.364938`, `2.364908`, `2.364483`, `2.364968`,
and `2.365393` micron, confirming a smooth local wavelength field rather than
a lookup failure.

## AI disclosure record

This verification note and the related code changes were prepared with
AI-assisted coding. The team should include that assistance in the submission
disclosure, alongside the human verification commands and IRSA documentation.
