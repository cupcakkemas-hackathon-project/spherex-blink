"""FastAPI app. Run from the project root:  uvicorn backend.app:app --reload"""
import os
import re
import math

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend import demo
from backend.imaging import apply_mode, to_png_b64

app = FastAPI(title="SPHEREx Blink")
FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend")
SIZE_PX = 64

# Built-in example targets (J2000 degrees). Barnard's Star etc. are approximate;
# the user can always type exact coordinates.
TARGETS = {
    "WISE 0855": (133.7951, -7.2452),
    "Barnard's Star": (269.452, 4.693),
    "Epsilon Indi B": (330.872, -56.786),
    "RW Aurigae": (76.9565, 30.4005),
    "R Draconis": (245.3908, 66.7603),
}


def parse_angle(s: str, is_ra: bool) -> float:
    """Accepts decimal degrees, or sexagesimal like 08h55m10.8s / -7d14m42.5s."""
    s = s.strip()
    try:
        return float(s)
    except ValueError:
        pass
    nums = [float(x) for x in re.findall(r"[\d.]+", s)]
    if not nums:
        raise ValueError(f"cannot parse '{s}'")
    sign = -1 if s.startswith("-") else 1
    val = sum(n / 60 ** i for i, n in enumerate(nums[:3]))
    return sign * val * (15 if is_ra else 1)


@app.get("/api/targets")
def targets():
    return {k: {"ra": v[0], "dec": v[1]} for k, v in TARGETS.items()}


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/api/frames")
def frames(ra: str, dec: str, fov: float = 2.0, mode: str = "single", source: str = "live"):
    try:
        ra_d, dec_d = parse_angle(ra, True), parse_angle(dec, False)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not (0 <= ra_d < 360 and -90 <= dec_d <= 90):
        raise HTTPException(400, "RA must be 0-360 deg and Dec -90 to 90 deg")
    fov = max(0.5, min(fov, 10.0))
    if mode not in ("single", "stack", "diff"):
        raise HTTPException(400, "mode must be single, stack or diff")

    if source == "synthetic":
        raw = demo.make_frames(ra_d, dec_d)
    else:
        try:
            from backend import irsa
            raw = irsa.get_raw_frames(ra_d, dec_d, fov)
        except irsa.IRSAUnavailableError as e:
            raise HTTPException(502, f"IRSA is temporarily unavailable: {e}")
        except Exception as e:
            raise HTTPException(502, f"Live SPHEREx query failed: {e}")
        if not raw:
            raise HTTPException(404, "No SPHEREx images cover that position yet.")

    out = apply_mode(raw, mode)
    pixel_scale_arcsec = fov * 60 / SIZE_PX

    def json_wavelength(value):
        return value if isinstance(value, (int, float)) and math.isfinite(value) else None

    return {
        "source": source,
        "ra": ra_d, "dec": dec_d, "fov_arcmin": fov, "mode": mode,
        "size_px": SIZE_PX, "pixel_scale_arcsec": pixel_scale_arcsec,
        "frames": [
            {"png": to_png_b64(f["data"]), "mjd": f["mjd"],
             "wavelength": json_wavelength(f.get("wavelength")),
             "detector": f["detector"], "flags": f["flags"]}
            for f in out
        ],
    }


@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND, "index.html"))


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


# --- spectrum (B) ---
@app.get("/api/spectrum")
def spectrum(
    ra: str,
    dec: str,
    fov: float = 2.0,
    x: float = 31.5,
    y: float = 31.5,
    source: str = "live",
):
    try:
        ra_d, dec_d = parse_angle(ra, True), parse_angle(dec, False)
    except ValueError as error:
        raise HTTPException(400, str(error))
    if not (0 <= ra_d < 360 and -90 <= dec_d <= 90):
        raise HTTPException(400, "RA must be 0-360 deg and Dec -90 to 90 deg")
    if not all(math.isfinite(value) for value in (fov, x, y)):
        raise HTTPException(400, "fov, x and y must be finite numbers")
    if not 0.5 <= fov <= 10:
        raise HTTPException(400, "fov must be between 0.5 and 10 arcmin")
    if not 0 <= x <= SIZE_PX - 1 or not 0 <= y <= SIZE_PX - 1:
        raise HTTPException(400, "x and y must be between 0 and 63")
    if source not in ("live", "synthetic"):
        raise HTTPException(400, "source must be live or synthetic")

    # The PNG is vertically flipped for display; the extractor uses array rows.
    array_y = SIZE_PX - 1 - y
    if source == "synthetic":
        raw = demo.make_frames(ra_d, dec_d)
    else:
        try:
            from backend import irsa
            raw = irsa.get_raw_frames(
                ra_d, dec_d, fov, sample_pixel=(x, array_y)
            )
        except irsa.IRSAUnavailableError as error:
            raise HTTPException(502, f"IRSA is temporarily unavailable: {error}")
        except Exception as error:
            raise HTTPException(502, f"Live SPHEREx query failed: {error}")
        if not raw:
            raise HTTPException(404, "No SPHEREx images cover that position yet.")

    try:
        from backend.spectrum import extract_spectrum
        points = extract_spectrum(raw, x, array_y)
    except ImportError as error:
        raise HTTPException(502, f"Spectrum extractor is unavailable: {error}")
    except Exception as error:
        raise HTTPException(502, f"Spectrum extraction failed: {error}")
    response = {"points": points}
    if source == "synthetic":
        response["source"] = "synthetic (fake demo data)"
    return response
