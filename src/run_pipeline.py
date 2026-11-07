"""
Run the full ETL pipeline: extract -> transform -> (optional) load into MySQL.

Examples
    python src/run_pipeline.py                 # download 365 days, clean, save CSVs
    python src/run_pipeline.py --days 90       # shorter history
    python src/run_pipeline.py --mysql         # also load into MySQL
    python src/run_pipeline.py --skip-extract  # re-clean already downloaded JSON
"""

import argparse

from extract import extract_all
from transform import transform_all


def main():
    parser = argparse.ArgumentParser(description="Weather ETL pipeline")
    parser.add_argument("--days", type=int, default=365, help="days of history to download")
    parser.add_argument("--mysql", action="store_true", help="load the results into MySQL")
    parser.add_argument("--skip-extract", action="store_true", help="use existing raw JSON files")
    args = parser.parse_args()

    if not args.skip_extract:
        print("1/3 Extract")
        extract_all(history_days=args.days)
    print("2/3 Transform")
    outputs = transform_all()
    if args.mysql:
        print("3/3 Load into MySQL")
        from load import load_all
        load_all(outputs)
    else:
        print("3/3 Load skipped (use --mysql to load into MySQL). CSVs are in data/processed/")


if __name__ == "__main__":
    main()
