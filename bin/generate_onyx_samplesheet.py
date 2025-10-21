#!/usr/bin/env python

import os
from onyx import OnyxConfig, OnyxEnv, OnyxClient
from onyx_analysis_helper import onyx_analysis_helper_functions as oa
import argparse
from pathlib import Path
import pandas as pd

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
    parser.add_argument("-i", "--id",
                help="Sample ID.",
                required=True, type=str)
    # parser.add_argument("-t", "--id_column",
    #             help="Column ID can be found in.",
    #             required=True, type=str)
    parser.add_argument("-c", "--columns",
                help="Columns from Onyx, should be column seperated string.",
                required=True, type=str)
    parser.add_argument("-o", "--output",
                help="Output directory for downloaded data",
                required=True, type=Path)
    args = parser.parse_args()
    return args


@oa.call_to_onyx
def get_record(sample_id: str, columns: list) -> tuple[dict, int]:
    """
    Using unique sample ID, query Onyx database to get appropriate columns
    """
    with OnyxClient(config) as client:
            df = pd.DataFrame(client.filter(
            project = "mscape",
            climb_id = sample_id,
            include = columns
        ))
    exit_code = 0

    return df, exit_code


def main():
    args = get_args()
    col_names = args.columns.split(',')
    df, exit_code = get_record(args.id, col_names)
    df.to_csv(args.output, index=False)


if __name__ == "__main__":
    main() 