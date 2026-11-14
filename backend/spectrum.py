"""Aperture photometry helpers for on-the-fly SPHEREx spectra."""
import math

import numpy as np


def extract_spectrum(
    frames: list[dict], x: float, y: float, radius_px: float = 1.5
) -> list[dict]:
    """Measure background-subtracted aperture brightness at one array position.

    ``x`` and ``y`` are column and row indices in the 64x64 array (row 0 is
    south). The browser displays the array vertically flipped, so convert a
    clicked canvas row ``r`` to array row ``63 - r`` before calling this.
    Flux and error are mean surface brightness in MJy/sr.
    """
    try:
        x, y, radius_px = float(x), float(y), float(radius_px)
    except (TypeError, ValueError) as exc:
        raise ValueError("x, y, and radius_px must be finite numbers") from exc
    if not all(math.isfinite(value) for value in (x, y, radius_px)):
        raise ValueError("x, y, and radius_px must be finite numbers")
    if radius_px <= 0:
        raise ValueError("radius_px must be positive")

    points = []
    for frame in frames:
        try:
            wavelength = float(frame.get("wavelength", np.nan))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(wavelength):
            continue

        data = np.asarray(frame["data"], dtype=float)
        if data.ndim != 2:
            raise ValueError("each frame's data must be a 2D array")
        height, width = data.shape
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError("x and y must lie inside each frame")

        rows, columns = np.ogrid[:height, :width]
        distance_squared = (columns - x) ** 2 + (rows - y) ** 2
        aperture_mask = distance_squared <= radius_px**2
        outer_radius = radius_px + max(radius_px, 1.0)
        annulus_mask = (
            (distance_squared > radius_px**2)
            & (distance_squared <= outer_radius**2)
        )

        aperture_values = data[aperture_mask]
        if aperture_values.size == 0 or not np.isfinite(aperture_values).all():
            continue
        annulus_mask &= np.isfinite(data)
        annulus_values = data[annulus_mask]
        if annulus_values.size == 0:
            continue

        background = float(np.median(annulus_values))
        flux = float(np.mean(aperture_values) - background)

        variance_data = frame.get("variance")
        use_variance = variance_data is not None
        if use_variance:
            variance_data = np.asarray(variance_data, dtype=float)
            if variance_data.shape != data.shape:
                raise ValueError("variance shape must match frame data")
            aperture_variance = variance_data[aperture_mask]
            annulus_variance = variance_data[annulus_mask]
            use_variance = (
                np.isfinite(aperture_variance).all()
                and np.all(aperture_variance >= 0)
                and np.isfinite(annulus_variance).all()
                and np.all(annulus_variance >= 0)
            )

        aperture_count = aperture_values.size
        annulus_count = annulus_values.size
        if use_variance:
            # Approximate the variance of the annulus median for Gaussian noise.
            error_squared = (
                np.sum(aperture_variance) / aperture_count**2
                + (np.pi / 2)
                * np.sum(annulus_variance)
                / annulus_count**2
            )
            error = float(np.sqrt(error_squared))
        else:
            noise = 1.4826 * float(
                np.median(np.abs(annulus_values - background))
            )
            error = float(
                noise * np.sqrt(1 / aperture_count + (np.pi / 2) / annulus_count)
            )

        mjd = float(frame["mjd"])
        if not math.isfinite(mjd):
            continue
        points.append({
            "wavelength": wavelength,
            "flux": flux,
            "err": error,
            "mjd": mjd,
            "detector": int(frame["detector"]),
        })

    return sorted(points, key=lambda point: point["wavelength"])
