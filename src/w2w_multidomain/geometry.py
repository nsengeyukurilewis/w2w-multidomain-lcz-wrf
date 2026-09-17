from pathlib import Path

from netCDF4 import Dataset


class GeoEmValidationError(RuntimeError):
    """Raised when a WRF geo_em file is structurally invalid."""


def validate_geo_em(path):
    """
    Validate the structural requirements needed by the multi-domain W2W workflow.

    Returns
    -------
    dict
        Basic domain metadata.
    """
    path = Path(path)

    if not path.exists():
        raise GeoEmValidationError(f"geo_em file does not exist: {path}")

    with Dataset(path, "r") as ds:
        required = ("XLAT_M", "XLONG_M")

        for name in required:
            if name not in ds.variables:
                raise GeoEmValidationError(
                    f"{path.name}: missing required variable {name}"
                )

        xlat = ds.variables["XLAT_M"]
        xlong = ds.variables["XLONG_M"]

        if xlat.ndim != 3:
            raise GeoEmValidationError(
                f"{path.name}: XLAT_M must be 3-D; "
                f"got ndim={xlat.ndim}, dimensions={xlat.dimensions}"
            )

        if xlong.ndim != 3:
            raise GeoEmValidationError(
                f"{path.name}: XLONG_M must be 3-D; "
                f"got ndim={xlong.ndim}, dimensions={xlong.dimensions}"
            )

        if xlat.dimensions != ("Time", "south_north", "west_east"):
            raise GeoEmValidationError(
                f"{path.name}: unexpected XLAT_M dimensions: "
                f"{xlat.dimensions}"
            )

        if xlong.dimensions != ("Time", "south_north", "west_east"):
            raise GeoEmValidationError(
                f"{path.name}: unexpected XLONG_M dimensions: "
                f"{xlong.dimensions}"
            )

        time_size = len(ds.dimensions["Time"])

        if time_size < 1:
            raise GeoEmValidationError(
                f"{path.name}: Time dimension is empty (size={time_size}); "
                "cannot read XLAT_M[0,:,:] or XLONG_M[0,:,:]. "
                "Regenerate or repair the geo_em file before W2W processing."
            )

        xlat_2d = xlat[0, :, :]
        xlong_2d = xlong[0, :, :]

        if xlat_2d.size == 0 or xlong_2d.size == 0:
            raise GeoEmValidationError(
                f"{path.name}: latitude/longitude arrays are empty"
            )

        return {
            "path": str(path),
            "time": time_size,
            "south_north": xlat.shape[1],
            "west_east": xlat.shape[2],
            "lat_min": float(xlat_2d.min()),
            "lat_max": float(xlat_2d.max()),
            "lon_min": float(xlong_2d.min()),
            "lon_max": float(xlong_2d.max()),
        }


def read_latlon(path):
    """
    Read the first valid latitude/longitude record from a WRF geo_em file.

    The production workflow intentionally requires Time >= 1.
    """
    validate_geo_em(path)

    with Dataset(path, "r") as ds:
        xlat = ds.variables["XLAT_M"][0, :, :]
        xlong = ds.variables["XLONG_M"][0, :, :]

        return xlat[:], xlong[:]
