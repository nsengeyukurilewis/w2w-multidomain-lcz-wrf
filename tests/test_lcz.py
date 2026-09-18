from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_bounds

from w2w_multidomain.lcz import (
    check_lcz_coverage,
    resolve_lcz,
)


def make_lcz(path, left, bottom, right, top):
    transform = from_bounds(
        left,
        bottom,
        right,
        top,
        20,
        20,
    )

    data = np.ones((20, 20), dtype=np.uint8)

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=20,
        width=20,
        count=1,
        dtype="uint8",
        crs="EPSG:4326",
        transform=transform,
    ) as ds:
        ds.write(data, 1)


def domains():
    return [
        {
            "name": "d01",
            "lat_min": 37.0,
            "lat_max": 38.0,
            "lon_min": 126.0,
            "lon_max": 127.0,
        },
        {
            "name": "d02",
            "lat_min": 37.2,
            "lat_max": 37.8,
            "lon_min": 126.2,
            "lon_max": 126.8,
        },
    ]


def test_all_domains_covered(tmp_path):
    path = tmp_path / "lcz.tif"

    make_lcz(
        path,
        125.0,
        36.0,
        128.0,
        39.0,
    )

    report = check_lcz_coverage(path, domains())

    assert report["all_domains_covered"] is True
    assert report["missing_domains"] == []


def test_larger_lcz_extent_is_valid(tmp_path):
    """An LCZ raster may extend beyond the WRF domain boundaries."""
    path = tmp_path / "lcz.tif"

    # Deliberately much larger than both required WRF domains.
    make_lcz(
        path,
        120.0,
        32.0,
        135.0,
        43.0,
    )

    report = check_lcz_coverage(path, domains())

    assert report["all_domains_covered"] is True
    assert report["missing_domains"] == []
    assert all(item["covered"] for item in report["domains"])


def test_partial_coverage_is_detected(tmp_path):
    path = tmp_path / "lcz.tif"

    make_lcz(
        path,
        126.1,
        37.1,
        126.9,
        37.9,
    )

    report = check_lcz_coverage(path, domains())

    assert report["all_domains_covered"] is False
    assert report["missing_domains"] == ["d01"]


def test_fallback_is_selected_when_supplied_lcz_is_incomplete(tmp_path):
    supplied = tmp_path / "supplied.tif"
    fallback = tmp_path / "fallback.tif"

    make_lcz(
        supplied,
        125.0,
        36.0,
        126.5,
        38.5,
    )

    make_lcz(
        fallback,
        125.0,
        36.0,
        128.0,
        39.0,
    )

    result = resolve_lcz(
        supplied_lcz=supplied,
        domains=domains(),
        fallback_enabled=True,
        fallback_path=fallback,
    )

    assert result["source"] == "official_rub_lcz_v3"
    assert result["selected_path"] == fallback
    assert result["fallback_report"]["all_domains_covered"] is True


def test_supplied_lcz_is_retained_when_complete(tmp_path):
    supplied = tmp_path / "supplied.tif"
    fallback = tmp_path / "fallback.tif"

    make_lcz(
        supplied,
        125.0,
        36.0,
        128.0,
        39.0,
    )

    result = resolve_lcz(
        supplied_lcz=supplied,
        domains=domains(),
        fallback_enabled=True,
        fallback_path=fallback,
    )

    assert result["source"] == "supplied"
    assert result["selected_path"] == supplied
    assert result["downloaded"] is False
    assert not fallback.exists()
