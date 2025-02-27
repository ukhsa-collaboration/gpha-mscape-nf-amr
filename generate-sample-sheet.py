import os
from onyx import OnyxConfig, OnyxEnv, OnyxClient
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
    parser.add_argument("-i", "--input",
                help="input file containing CLIMB-IDs",
                required=True, type=Path)
    parser.add_argument("-o", "--output",
                help="Output directory for downloaded data",
                required=True, type=Path)
    args = parser.parse_args()
    return args

def get_record_by_climb_id(climb_id_list: list):
    # for climb_id in climb_id_list:
    #     print(f'Processing: {climb_id}')
    # climb_id_list = ["C-514753DBDA"]
    input_list = climb_id_list
    print(climb_id_list)
    with OnyxClient(config) as client:
            data = pd.DataFrame(client.filter(
            project = "mscape",
            climb_id = input_list[0]
        ))
    # read_1_link = data["human_filtered_reads_1"][0]
    # read_2_link = data["human_filtered_reads_2"][0]
    print(data)

    # with OnyxClient(config) as client:
    #     lookups = client.lookups()
    #     print(lookups)

def parse_file(fp: Path):
    """
    Read in text file, seperate climb ids into lis
    :args: filepath str()
    """
    with open(fp, "r") as file:
        data = file.readlines()  # Reads lines into a list
        data = [line.strip() for line in data]  # Remove newline characters
        return data

def main():
    args = get_args()
    climb_id_list = parse_file(args.input)
    get_record_by_climb_id(climb_id_list)

if __name__ == "__main__":
    main()