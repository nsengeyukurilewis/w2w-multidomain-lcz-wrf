from pathlib import Path
from urllib.request import Request, urlopen

import rasterio


DEFAULT_LCZ_V3_URL = (
    "https://lcz-generator.rub.de/cogs/lcz_filter_v3_cog.tif"
)


class LCZCoverageError(RuntimeError):
    """Raised when an LCZ raster does not cover required WRF domains."""


def raster_bounds(lcz_path):
    """Return the geographic bounds of an LCZ raster."""
    lcz_path = Path(lcz_path)

    if not lcz_path.exists():
        raise FileNotFoundError(f"LCZ raster does not exist: {lcz_path}")

    with rasterio.open(lcz_path) as ds:
        if ds.crs is None:
            raise LCZCoverageError(
                f"{lcz_path.name}: LCZ raster has no CRS"
            )

        if ds.crs.to_epsg() != 4326:
            raise LCZCoverageError(
                f"{lcz_path.name}: expected EPSG:4326, got {ds.crs}"
            )

        return {
            "left": float(ds.bounds.left),
            "bottom": float(ds.bounds.bottom),
            "right": float(ds.bounds.right),
            "top": float(ds.bounds.top),
            "crs": ds.crs.to_string(),
            "width": ds.width,
            "height": ds.height,
            "resolution": tuple(float(v) for v in ds.res),
        }


def domain_is_covered(domain_metadata, lcz_bounds):
    """Return True when an LCZ raster completely covers a WRF domain."""
    return (
        lcz_bounds["left"] <= domain_metadata["lon_min"]
        and lcz_bounds["right"] >= domain_metadata["lon_max"]
        and lcz_bounds["bottom"] <= domain_metadata["lat_min"]
        and lcz_bounds["top"] >= domain_metadata["lat_max"]
    )


def check_lcz_coverage(lcz_path, domains):
    """
    Check complete LCZ coverage for every discovered WRF domain.

    Parameters
    ----------
    lcz_path : path-like
        LCZ GeoTIFF.
    domains : iterable of dict
        Results from validate_all_domains().

    Returns
    -------
    dict
        Coverage report with per-domain status.
    """
    bounds = raster_bounds(lcz_path)
    results = []

    for domain in domains:
        covered = domain_is_covered(domain, bounds)

        results.append(
            {
                "domain": domain["name"],
                "covered": bool(covered),
                "lat_min": domain["lat_min"],
                "lat_max": domain["lat_max"],
                "lon_min": domain["lon_min"],
                "lon_max": domain["lon_max"],
            }
        )

    missing = [
        item["domain"]
        for item in results
        if not item["covered"]
    ]

    return {
        "lcz_path": str(lcz_path),
        "lcz_bounds": bounds,
        "domains": results,
        "all_domains_covered": not missing,
        "missing_domains": missing,
    }


def download_lcz_v3(output_path, url=DEFAULT_LCZ_V3_URL):
    """
    Download the official RUB Global LCZ Version 3 COG.

    The destination is created atomically through a temporary file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    temporary = output_path.with_suffix(
        output_path.suffix + ".download"
    )

    request = Request(
        url,
        headers={
            "User-Agent": (
                "w2w-multidomain-lcz-wrf/"
                "0.1.0"
            )
        },
    )

    try:
        with urlopen(request, timeout=120) as response, \
                temporary.open("wb") as dst:

            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                dst.write(chunk)

        temporary.replace(output_path)

    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise

    return output_path


def resolve_lcz(
    supplied_lcz,
    domains,
    fallback_enabled=True,
    fallback_url=DEFAULT_LCZ_V3_URL,
    fallback_path=None,
):
    """
    Select an LCZ raster that covers every discovered WRF domain.

    The supplied LCZ is always tried first. The official RUB LCZ v3
    COG is downloaded only when the supplied raster fails coverage.
    """
    supplied_lcz = Path(supplied_lcz)

    supplied_report = check_lcz_coverage(
        supplied_lcz,
        domains,
    )

    if supplied_report["all_domains_covered"]:
        return {
            "selected_path": supplied_lcz,
            "source": "supplied",
            "downloaded": False,
            "supplied_report": supplied_report,
            "fallback_report": None,
        }

    if not fallback_enabled:
        missing = ", ".join(
            supplied_report["missing_domains"]
        )
        raise LCZCoverageError(
            "Supplied LCZ raster does not cover all discovered "
            f"WRF domains; missing: {missing}"
        )

    if fallback_path is None:
        raise ValueError(
            "fallback_path is required when LCZ fallback is enabled"
        )

    fallback_path = Path(fallback_path)

    if not fallback_path.exists():
        download_lcz_v3(
            output_path=fallback_path,
            url=fallback_url,
        )
        downloaded = True
    else:
        downloaded = False

    fallback_report = check_lcz_coverage(
        fallback_path,
        domains,
    )

    if not fallback_report["all_domains_covered"]:
        missing = ", ".join(
            fallback_report["missing_domains"]
        )
        raise LCZCoverageError(
            "Official LCZ v3 fallback does not cover all discovered "
            f"WRF domains; missing: {missing}"
        )

    return {
        "selected_path": fallback_path,
        "source": "official_rub_lcz_v3",
        "downloaded": downloaded,
        "supplied_report": supplied_report,
        "fallback_report": fallback_report,
    }
