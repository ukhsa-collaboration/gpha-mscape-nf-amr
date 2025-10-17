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
    parser.add_argument("-t", "--id_column",
                help="Column ID can be found in.",
                required=True, type=str)
    parser.add_argument("-c", "--columns",
                help="Columns from Onyx, should be column seperated string.",
                required=True, type=str)
    parser.add_argument("-o", "--output",
                help="Output directory for downloaded data",
                required=True, type=Path)
    args = parser.parse_args()
    return args


@oa.call_to_onyx
def get_record(sample_id: str, id_column: str, columns: list):
    """
    Using unique sample ID, query Onyx database to get appropriate columns
    """
    try:
        with OnyxClient(config) as client:
                data = pd.DataFrame(client.filter(
                project = "mscape",
                id_column = sample_id,
                include = columns
            ))
    except KeyError:
        print(f"Sample {id} not found in database. Skipping.")
        pass
    return data

# def write_to_csv(dict_list: list, output: Path):
#      """
#      Write list of dictionaries to csv
#      :args: [{CLIMB-ID, READ1, READ2}], Path(output)
#      :return: save as csv
#      """
#      with open(output, mode="w", newline="") as file:
#         # Define the column names (fieldnames)
#         fieldnames = dict_list[0].keys()  # Extract keys from the first dictionary
#         writer = csv.DictWriter(file, fieldnames=fieldnames)
#         writer.writeheader()
#         writer.writerows(dict_list)

def main():
    args = get_args()
    print(args)
    data = get_record(args.id, args.id_column, args.columns)
    print(data)
    # dict_list = get_record_by_climb_id(climb_id_list)
    # write_to_csv(dict_list, args.output)

if __name__ == "__main__":
    main()