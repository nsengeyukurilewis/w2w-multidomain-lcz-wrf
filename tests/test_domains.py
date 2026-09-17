import numpy as np
from netCDF4 import Dataset

from w2w_multidomain.domains import discover_domains


def make_geo_em(path):
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
        xlong[0, :, :] = np.arange(12).reshape(3, 4)


def test_discovers_arbitrary_number_of_domains(tmp_path):
    make_geo_em(tmp_path / "geo_em.d03.nc")
    make_geo_em(tmp_path / "geo_em.d01.nc")
    make_geo_em(tmp_path / "geo_em.d07.nc")
    make_geo_em(tmp_path / "geo_em.d02.nc")

    # This file must not be interpreted as a WRF domain.
    (tmp_path / "geo_em.bad.nc").touch()

    domains = discover_domains(tmp_path)

    assert [d["name"] for d in domains] == [
        "d01",
        "d02",
        "d03",
        "d07",
    ]
