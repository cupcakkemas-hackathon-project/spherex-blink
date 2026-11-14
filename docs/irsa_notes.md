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
will be handled by the wavelength task.

The cutout `size` parameter is in degrees. The tested `0.05` degree request
returned a 29 by 29 pixel cutout. The IRSA cutout service is not assumed to
have a fixed minimum here; callers should use a positive degree value suited
to the requested field of view.

## Updating

The app queries IRSA live, so newly searchable DR1 and QR3 images are picked up
automatically. IRSA documents that ingestion is weekly and SIA2 availability
can lag ingestion by about a day. The app's in-memory cache should therefore
have a finite TTL when it is added; a process restart also clears it.

## AI disclosure record

This verification note and the related code changes were prepared with
AI-assisted coding. The team should include that assistance in the submission
disclosure, alongside the human verification commands and IRSA documentation.
