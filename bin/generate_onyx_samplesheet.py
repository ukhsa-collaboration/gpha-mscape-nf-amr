#!/usr/bin/env python

import os
from onyx import OnyxConfig, OnyxEnv, OnyxClient
from onyx_analysis_helper import onyx_analysis_helper_functions as oa
import argparse
from pathlib import Path
import pandas as pd
import csv

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

# def parse_file(fp: Path):
#     """
#     Read in text file, seperate climb ids into lis
#     :args: filepath str()
#     """
#     with open(fp, "r", encoding="utf-8-sig") as file:
#         data = file.readlines()  # Reads lines into a list
#         data = [line.strip() for line in data]  # Remove newline characters
#         data = [s.replace('"', '') for s in data] # remove " from strings
#         return data
# @oa.call_to_onyx
# def get_record_by_climb_id(sample_id: str, id_column: str, columns: list):
#     dict_list = []
#     try:
#         with OnyxClient(config) as client:
#                 data = pd.DataFrame(client.filter(
#                 project = "mscape",
#                 id_column = sample_id
#                 include = columns,
#             ))
#     except KeyError:
#         print(f"Sample {id} not found in database. Skipping.")
#         pass
#     return dict_list

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
    # climb_id_list = parse_file(args.input)
    # dict_list = get_record_by_climb_id(climb_id_list)
    # write_to_csv(dict_list, args.output)

if __name__ == "__main__":
    main()