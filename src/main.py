#!/usr/bin/env parser python3
import argparse
import sys

import boto3

from libs.regions_mng import RegionsMng


def get_all_regions() -> list:
    ec2 = boto3.client("account")
    return ec2.list_regions(
        RegionOptStatusContains=["ENABLED", "ENABLED_BY_DEFAULT"]
    )["Regions"]


def load() -> list:
    print("INFO: Loading (this might take a few minutes)...")
    return [RegionsMng(region["RegionName"]) for region in get_all_regions()]


def clean(regions: list, dry_run: list):
    print("\n\nINFO: Deleting ....")
    [region.clean(dry_run=dry_run) for region in regions]


def main(dry_run: bool) -> int:
    regions = load()
    clean(regions=regions, dry_run=dry_run)
    print("\nINFO: Completed Successful")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Deletes the default VPCs and all linked resources."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Simulate the run without making changes"
    )
    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run))
