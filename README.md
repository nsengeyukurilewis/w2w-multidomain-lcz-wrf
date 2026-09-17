# Domain-Native Multi-Domain LCZ-to-WRF Preprocessing

A reproducible workflow for integrating Local Climate Zone (LCZ) data into
multiple WRF `geo_em.dXX.nc` domains using W2W.

The workflow is designed to support an arbitrary number of WRF domains.
Domains are discovered automatically from `geo_em.dXX.nc` files rather than
being hard-coded as D01-D04.

## Method

The workflow performs the following steps:

1. Discover all `geo_em.dXX.nc` files.
2. Validate each WRF geogrid file.
3. Read the geographic extent of each domain.
4. Verify that the supplied LCZ GeoTIFF provides complete spatial coverage.
5. Clip the LCZ raster to each WRF domain.
6. Run W2W independently for every covered domain.
7. Validate the resulting LCZ and urban-parameter fields.
8. Produce machine-readable quality-control results.

Conceptually:

    LCZ GeoTIFF
         |
         +-----------------------------+
         |             |               |
       D01           D02             D03 ... DNN
         |             |               |
       W2W           W2W             W2W
         |             |               |
         +-------------+---------------+
                       |
                    QA/QC
                       |
                WRF geo_em products

Each domain is processed independently at its native WRF resolution.

## Domain discovery

The workflow does not assume a fixed number of domains.

For example, the same code can process:

    geo_em.d01.nc
    geo_em.d02.nc
    geo_em.d03.nc
    geo_em.d04.nc

or:

    geo_em.d01.nc
    geo_em.d02.nc
    geo_em.d03.nc
    geo_em.d04.nc
    geo_em.d05.nc
    geo_em.d06.nc

or any other valid set of `geo_em.dXX.nc` files.

## Spatial coverage and automatic LCZ fallback

The supplied LCZ raster must completely cover every discovered WRF domain.

A domain is considered covered only when:

    LCZ extent >= WRF domain extent

Partial LCZ coverage is not silently accepted.

If the supplied LCZ raster does not cover all discovered domains, the
workflow can automatically obtain the official RUB Global LCZ Version 3
Cloud-Optimized GeoTIFF and repeat the coverage check.

The fallback source is:

    https://lcz-generator.rub.de/cogs/lcz_filter_v3_cog.tif

The supplied LCZ is always preferred when it already covers every domain.
The fallback is used only when coverage is incomplete.

If neither source covers every discovered domain, processing stops with an
explicit error. The workflow never silently processes only a subset of
domains.

The number of domains is not hard-coded.

## W2W

The reference implementation uses:

    W2W 0.6.0

W2W is used independently for each WRF domain.

The workflow does not derive finer-domain LCZ fields by simply interpolating
or copying a parent-domain LCZ classification. Each domain is processed
against the common LCZ source at its own native grid.

## Input data

The production workflow can use:

- WRF `geo_em.dXX.nc` files
- LCZ GeoTIFF
- W2W 0.6.0
- WRF/WPS-compatible spatial metadata

The repository does not redistribute large production datasets.

Users should obtain source datasets from their original providers and follow
their respective licenses and attribution requirements.

## Our production case

The development and validation case uses:

- Seoul metropolitan region
- WRF nested domains
- COP30-based topographic preprocessing
- LCZ Version 3
- W2W 0.6.0

The current production geometry is:

    D01: 9 km
    D02: 3 km
    D03: 1 km
    D04: 100 m

with the corresponding WRF domain definitions supplied by the production
`namelist.wps`.

The production LCZ source is a pinned LCZ Version 3 GeoTIFF.

The production topography uses Copernicus GLO-30 DSM data.

Large production files remain outside this Git repository.

## Data provenance

Production data should be recorded using:

- source name
- version
- acquisition date
- spatial reference
- spatial resolution
- checksum
- license
- original provider
- processing date

The repository should contain metadata and checksums rather than large
non-redistributable source files.

## Validation

The workflow validates, where applicable:

- WRF NetCDF dimensions
- `XLAT_M`
- `XLONG_M`
- non-empty `Time` dimension
- LCZ geographic coverage
- LCZ class integrity
- urban LCZ extent
- `FRC_URB2D`
- `URB_PARAMS`
- `HI_URB2D`
- consistency between LCZ and urban fraction

A malformed input is rejected before W2W processing.

## Important input validation rule

A WRF `geo_em.dXX.nc` file must contain a valid latitude/longitude record:

    XLAT_M(Time, south_north, west_east)
    XLONG_M(Time, south_north, west_east)

and:

    Time >= 1

For example, a file with:

    XLAT_M shape = (0, 99, 99)

is invalid for this workflow and must be repaired or regenerated before
W2W processing.

The workflow deliberately does not hide such errors.

## Reproducibility

The software environment pins W2W:

    w2w==0.6.0

Python tests are executed through GitHub Actions.

The production data are intentionally separated from the software repository
so that the workflow can be reproduced with either:

1. the original production datasets obtained from their providers, or
2. the small redistributable sample data supplied with this repository.

## Repository structure

    .
    ├── README.md
    ├── CITATION.cff
    ├── LICENSE
    ├── pyproject.toml
    ├── requirements.txt
    ├── environment.yml
    ├── src/
    │   └── w2w_multidomain/
    ├── scripts/
    ├── config/
    ├── tests/
    ├── sample_data/
    ├── examples/
    └── .github/
        └── workflows/

## Status

This repository is under active development.

The method is being validated first against the production Seoul/COP30/LCZ
workflow before the public sample-data pipeline is finalized.
