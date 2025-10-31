#!/usr/bin/env python3

import argparse
import os
from pathlib import Path

import pandas as pd
from onyx import OnyxClient, OnyxConfig, OnyxEnv
from onyx_analysis_helper import onyx_analysis_helper_functions as oa

config = OnyxConfig(
    domain=os.environ[OnyxEnv.DOMAIN],
    token=os.environ[OnyxEnv.TOKEN],
)


def get_args() -> argparse.Namespace:
    """
    Command Line
    :return: argParse variable
    """
    parser = argparse.ArgumentParser(description="generate-sample-sheet")
    parser.add_argument("-i", "--id", help="Sample ID.", required=True, type=str)
    parser.add_argument(
        "-c", "--columns", help="Columns from Onyx, should be comma seperated string.", required=True, type=str
    )
    parser.add_argument("-o", "--output", help="Output filepath.", required=True, type=Path)
    args = parser.parse_args()
    return args


@oa.call_to_onyx
def get_record(sample_id: str, columns: list) -> tuple[dict, int]:
    """
    Using unique sample ID, query Onyx database to get appropriate columns
    """
    # Ensure climb_id is included in columns list
    if "climb_id" not in columns:
        columns.append("climb_id")

    with OnyxClient(config) as client:
        df = pd.DataFrame(client.filter(project="mscape", climb_id=sample_id, include=columns))
    exit_code = 0

    # TODO: handle no records returned
    return df, exit_code


def main() -> None:
    args = get_args()
    col_names = args.columns.split(",")
    df, exit_code = get_record(args.id, col_names)
    df.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
