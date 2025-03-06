import pandas as pd
import json
import argparse

# Argument parser
parser = argparse.ArgumentParser(description="Left join a TSV file with a JSON file based on taxid.")
parser.add_argument("-t", "--tsv", required=True, help="Input TSV file (with read_id and taxid).")
parser.add_argument("-j", "--json", required=True, help="Input JSON file (with taxid and name).")
parser.add_argument("-o", "--output", required=True, help="Output TSV file after join.")
args = parser.parse_args()

# Load TSV file into a DataFrame
df_tsv = pd.read_csv(args.tsv, sep="\t", header=None, names=["read_id", "taxid"])

# Load JSON file
with open(args.json, "r") as f:
    taxid_dict = json.load(f)

# Convert JSON to DataFrame
df_json = pd.DataFrame.from_dict(taxid_dict, orient="index")
df_json = df_json[["taxid", "name"]]
df_json["taxid"] = df_json["taxid"].astype(str)  # Ensure taxid is string

# Merge (left join) TSV with JSON
df_merged = df_tsv.merge(df_json, on="taxid", how="left")

# Save the output
df_merged.to_csv(args.output, sep="\t", index=False)

print(f"Left join completed! Output saved to {args.output}")