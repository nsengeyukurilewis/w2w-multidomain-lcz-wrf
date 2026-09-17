from pathlib import Path
import re

from .geometry import validate_geo_em


DOMAIN_PATTERN = re.compile(r"^geo_em\.d(\d{2})\.nc$")


def discover_domains(geo_em_directory):
    """
    Discover all WRF geo_em.dXX.nc files.

    Returns domains sorted numerically by domain number.
    """
    directory = Path(geo_em_directory)

    if not directory.is_dir():
        raise FileNotFoundError(
            f"WRF geo_em directory does not exist: {directory}"
        )

    discovered = []

    for path in directory.iterdir():
        if not path.is_file():
            continue

        match = DOMAIN_PATTERN.match(path.name)

        if match is None:
            continue

        number = int(match.group(1))

        discovered.append(
            {
                "number": number,
                "name": f"d{number:02d}",
                "path": path,
            }
        )

    discovered.sort(key=lambda item: item["number"])

    if not discovered:
        raise RuntimeError(
            f"No files matching geo_em.dXX.nc found in {directory}"
        )

    return discovered


def validate_all_domains(geo_em_directory):
    """
    Discover and structurally validate every WRF domain.
    """
    domains = discover_domains(geo_em_directory)

    results = []

    for domain in domains:
        metadata = validate_geo_em(domain["path"])

        results.append(
            {
                **domain,
                **metadata,
            }
        )

    return results
