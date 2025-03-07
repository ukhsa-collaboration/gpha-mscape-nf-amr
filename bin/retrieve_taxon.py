#!/usr/bin/env

import pandas as pd
import json
import argparse
from pathlib import Path

def commandline():
    '''
    Input arguments for script
    :return: argparse object containing file paths to tsv and json
    '''
    parser = argparse.ArgumentParser(
        description="Left join a TSV file with a JSON file based on taxid.")
    parser.add_argument(
        "-t",
        "--tsv",
        required=True,
        help="Input TSV file (with read_id and taxid).")
    parser.add_argument(
        "-j",
        "--json",
        required=True,
        help="Input JSON file (with taxid and name).")
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output TSV file after join.")
    args = parser.parse_args()
    return args

def load_files(tsv_fp: Path, json_fp: Path):
    '''
    Load in tsv file as 
    '''
    # Load TSV file into a DataFrame
    df_tsv = pd.read_csv(tsv_fp,
                         sep="\t",
                         header=None,
                         names=["read_id", "taxid"])

    # Load JSON file
    with open(json_fp, "r") as f:
        taxid_dict = json.load(f)

    return df_tsv, taxid_dict

def add_species(df_tsv: pd.DataFrame, taxid_dict: dict):
    '''
    Match taxid to species and left join to df_tsv
    :params:    pd.Dataframe with read ID and tax id
                dictionary with taxid information
    :return: df_tsv with left joined 'name'
    '''
    # Convert dictionary into pandas dataframe
    taxid_df = pd.DataFrame.from_dict(taxid_dict, orient='index')
    taxid_df.reset_index(inplace=True)
    taxid_df.rename(columns={'index': 'taxid_key'}, inplace=True)
    for df in [df_tsv, taxid_df]:
        df['taxid'] = df['taxid'].astype(str)
    df_merged  = df_tsv.merge(taxid_df[['taxid','name','raw_rank','rank']],
                              on='taxid', how='left')
    return df_merged

def write_tsv(df_merged: pd.DataFrame, output_fn: Path):
    '''
    Write pandas dataframe to tsv
    :params: pandas dataframe, output file path   
    '''
    df_merged.to_csv(output_fn, sep='\t', index=False)

def main():
    args = commandline()
    df_tsv, taxid_dict = load_files(args.tsv, args.json)
    df_merged = add_species(df_tsv, taxid_dict)
    write_tsv(df_merged, args.output)

if __name__ == "__main__":
    main()