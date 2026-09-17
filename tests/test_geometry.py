from pathlib import Path

import pytest

from w2w_multidomain.geometry import (
    GeoEmValidationError,
    validate_geo_em,
)


def test_missing_geo_em(tmp_path):
    with pytest.raises(GeoEmValidationError, match="does not exist"):
        validate_geo_em(tmp_path / "geo_em.d01.nc")


def test_empty_time_dimension(tmp_path):
    from netCDF4 import Dataset

    path = tmp_path / "geo_em.d02.nc"

    with Dataset(path, "w") as ds:
        ds.createDimension("Time", 0)
        ds.createDimension("south_north", 99)
        ds.createDimension("west_east", 99)

        ds.createVariable(
            "XLAT_M",
            "f4",
            ("Time", "south_north", "west_east"),
        )
        ds.createVariable(
            "XLONG_M",
            "f4",
            ("Time", "south_north", "west_east"),
        )

    with pytest.raises(
        GeoEmValidationError,
        match="Time dimension is empty",
    ):
        validate_geo_em(path)


def test_valid_geo_em(tmp_path):
    import numpy as np
    from netCDF4 import Dataset

    path = tmp_path / "geo_em.d01.nc"

    with Dataset(path, "w") as ds:
        ds.createDimension("Time", 1)
        ds.createDimension("south_north", 3)
        ds.createDimension("west_east", 4)

        xlat = ds.createVariable(
            "XLAT_M",
            "f4",
            ("Time", "south_north", "west_east"),
        )
        xlong = ds.createVariable(
            "XLONG_M",
            "f4",
            ("Time", "south_north", "west_east"),
        )

        xlat[0, :, :] = np.arange(12).reshape(3, 4)
        xlong[0, :, :] = np.arange(12).reshape(3, 4) + 120

    result = validate_geo_em(path)

    assert result["time"] == 1
    assert result["south_north"] == 3
    assert result["west_east"] == 4
    assert result["lat_min"] == 0.0
    assert result["lat_max"] == 11.0
    assert result["lon_min"] == 120.0
    assert result["lon_max"] == 131.0
