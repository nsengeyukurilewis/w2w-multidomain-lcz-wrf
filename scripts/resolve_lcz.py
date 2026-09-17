#!/usr/bin/env python3

import argparse
from pathlib import Path

from w2w_multidomain.domains import validate_all_domains
from w2w_multidomain.lcz import resolve_lcz


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Resolve an LCZ raster that completely covers every "
            "discovered WRF geo_em.dXX.nc domain."
        )
    )

    parser.add_argument(
        "--geo-em-dir",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--lcz",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--fallback-path",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--fallback-url",
        default=None,
    )

    args = parser.parse_args()

    domains = validate_all_domains(args.geo_em_dir)

    kwargs = {}

    if args.fallback_url:
        kwargs["fallback_url"] = args.fallback_url

    result = resolve_lcz(
        supplied_lcz=args.lcz,
        domains=domains,
        fallback_enabled=True,
        fallback_path=args.fallback_path,
        **kwargs,
    )

    print("=== LCZ RESOLUTION ===")
    print("discovered domains:", ", ".join(
        item["name"] for item in domains
    ))
    print("selected LCZ:", result["selected_path"])
    print("source:", result["source"])
    print("downloaded:", result["downloaded"])

    print()
    print("=== SUPPLIED LCZ COVERAGE ===")

    for item in result["supplied_report"]["domains"]:
        print(
            f'{item["domain"]}: '
            f'{"PASS" if item["covered"] else "FAIL"}'
        )

    if result["fallback_report"] is not None:
        print()
        print("=== FALLBACK LCZ V3 COVERAGE ===")

        for item in result["fallback_report"]["domains"]:
            print(
                f'{item["domain"]}: '
                f'{"PASS" if item["covered"] else "FAIL"}'
            )


if __name__ == "__main__":
    main()
