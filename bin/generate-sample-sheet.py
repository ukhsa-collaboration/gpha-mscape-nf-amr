import os
from onyx import OnyxConfig, OnyxEnv, OnyxClient
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
    parser.add_argument("-i", "--input",
                help="input file containing CLIMB-IDs",
                required=True, type=Path)
    parser.add_argument("-o", "--output",
                help="Output directory for downloaded data",
                required=True, type=Path)
    args = parser.parse_args()
    return args

def parse_file(fp: Path):
    """
    Read in text file, seperate climb ids into lis
    :args: filepath str()
    """
    with open(fp, "r", encoding="utf-8-sig") as file:
        data = file.readlines()  # Reads lines into a list
        data = [line.strip() for line in data]  # Remove newline characters
        return data

def get_record_by_climb_id(climb_id_list: list):
    # for climb_id in climb_id_list:
    #     print(f'Processing: {climb_id}')
    # climb_id_list = ["C-514753DBDA"]
    dict_list = []
    for id in climb_id_list:
        with OnyxClient(config) as client:
                data = pd.DataFrame(client.filter(
                project = "mscape",
                climb_id = id
            ))
        read_1_link = data["human_filtered_reads_1"][0]
        read_2_link = data["human_filtered_reads_2"][0]
        taxon_reports_dir = data["taxon_reports"][0]
        dict_list.append({'climb_id': id, 
             'human_filtered_reads_1': read_1_link, 
             'human_filtered_reads_2': read_2_link,
             'taxon_reports_dir': taxon_reports_dir,
             'kraken_assignments': os.path.join(
                 taxon_reports_dir,
                 str(id)+str('_PlusPF.kraken_assignments.tsv')),
             'kraken_report': os.path.join(
                 taxon_reports_dir, 
                 str(id)+str('_PlusPF.kraken_report.json'))
        })
    return dict_list

def write_to_csv(dict_list: list, output: Path):
     """
     Write list of dictionaries to csv
     :args: [{CLIMB-ID, READ1, READ2}], Path(output)
     :return: save as csv
     """
     with open(output, mode="w", newline="") as file:
        # Define the column names (fieldnames)
        fieldnames = dict_list[0].keys()  # Extract keys from the first dictionary
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dict_list)

def main():
    args = get_args()
    climb_id_list = parse_file(args.input)
    dict_list = get_record_by_climb_id(climb_id_list)
    write_to_csv(dict_list, args.output)

if __name__ == "__main__":
    main()