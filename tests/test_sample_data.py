from pathlib import Path

from netCDF4 import Dataset
import rasterio


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "sample_data"


def test_sample_domains_exist():
    domains = sorted(SAMPLE.glob("geo_em.d*.nc"))

    assert len(domains) >= 2
    assert [p.name for p in domains] == [
        "geo_em.d01.nc",
        "geo_em.d02.nc",
    ]


def test_sample_domains_have_valid_time_and_coordinates():
    for path in sorted(SAMPLE.glob("geo_em.d*.nc")):
        with Dataset(path) as ds:
            assert "Time" in ds.dimensions
            assert len(ds.dimensions["Time"]) >= 1

            assert "XLAT_M" in ds.variables
            assert "XLONG_M" in ds.variables

            xlat = ds.variables["XLAT_M"]
            xlong = ds.variables["XLONG_M"]

            assert xlat.ndim == 3
            assert xlong.ndim == 3

            assert xlat.dimensions == (
                "Time",
                "south_north",
                "west_east",
            )

            assert xlong.dimensions == (
                "Time",
                "south_north",
                "west_east",
            )

            assert xlat.shape[1] > 0
            assert xlat.shape[2] > 0


def test_sample_lcz_exists_and_is_georeferenced():
    path = SAMPLE / "lcz_filter_v3_sample.tif"

    assert path.exists()

    with rasterio.open(path) as ds:
        assert ds.count == 1
        assert ds.width > 0
        assert ds.height > 0
        assert ds.crs is not None
        assert ds.crs.to_string() == "EPSG:4326"


def test_sample_lcz_fully_covers_all_domains():
    lcz_path = SAMPLE / "lcz_filter_v3_sample.tif"

    with rasterio.open(lcz_path) as lcz:
        west, south, east, north = lcz.bounds

        for path in sorted(SAMPLE.glob("geo_em.d*.nc")):
            with Dataset(path) as ds:
                lat = ds.variables["XLAT_M"][0, :, :]
                lon = ds.variables["XLONG_M"][0, :, :]

                domain_south = float(lat.min())
                domain_north = float(lat.max())
                domain_west = float(lon.min())
                domain_east = float(lon.max())

            assert domain_west >= west
            assert domain_east <= east
            assert domain_south >= south
            assert domain_north <= north
