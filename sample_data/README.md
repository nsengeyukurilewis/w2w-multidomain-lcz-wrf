# Sample and Production Data

Large production datasets are not stored in this repository.

## Production data

The development/validation case uses:

- WRF `geo_em.dXX.nc` files
- LCZ Version 3 GeoTIFF
- Copernicus GLO-30 DSM-derived WRF topography

Production files should be obtained from their original sources and checked
against the provenance information recorded in the project configuration.

## Domain count

The software does not assume four domains.

All files matching:

    geo_em.dXX.nc

are discovered automatically.

Each discovered domain is independently checked for:

- valid WRF dimensions
- non-empty Time dimension
- valid XLAT_M/XLONG_M
- complete LCZ coverage

## Data licensing

Users are responsible for complying with the licenses and attribution
requirements of all external datasets.

Do not add large external datasets to this repository unless redistribution
is explicitly permitted.

## Recommended provenance record

For every production dataset record:

    Dataset:
    Provider:
    Version:
    URL:
    Acquisition date:
    Processing date:
    CRS:
    Resolution:
    License:
    SHA256:
