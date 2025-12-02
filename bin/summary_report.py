"""
Docstring for bin.summary_report
Generate a summary report from given data inputs.
Data Inputs:
- CSV file containng all *_abricate_taxa_out.csv files
- Metadata file containng sample information
Outputs:
- Summary report in HTML format
"""

import argparse
import logging
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
from Bio import Entrez

logger = logging.getLogger(__name__)


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a summary report from given data inputs.")
    parser.add_argument(
        "-i", "--input_tsv", required=True, help="Path to the input TSV file containing abricate taxa data."
    )
    parser.add_argument(
        "-m", "--metadata", required=True, help="Path to the metadata file containing sample information."
    )
    parser.add_argument("-e", "--email", required=True, help="Email address for NCBI Entrez.")

    parser.add_argument("-o", "--output_dir", required=True, help="Directory to save the output summary report.")
    return parser.parse_args()


def set_up_logger(log_file: str) -> None:
    """Example logger set up which can be amended as required. In this example,
    all logging messages go a log file. The logger is
    set to append mode so logs from older runs are not overwritten.
    """

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")

    out_handler = logging.FileHandler(log_file, mode="a")
    out_handler.setFormatter(formatter)
    out_handler.setLevel(logging.INFO)
    logger.addHandler(out_handler)


def simplify_taxa(email: str, df: pd.DataFrame) -> pd.DataFrame:
    """Take table in that contains taxid column, simplify the species using
    Entrez. Return table containing simplified name column
    """
    Entrez.email = email  # required by NCBI

    # 1️⃣ Get unique taxids
    unique_taxids = df["taxid"].dropna().unique().astype(str)

    # 2️⃣ Create a lookup dict to store results
    taxid_to_species = {}

    # 3️⃣ Query NCBI only once per unique taxid
    for taxid in unique_taxids:
        try:
            handle = Entrez.efetch(db="taxonomy", id=taxid)
            record = ET.fromstring(handle.read())

            # Extract lineage
            lineage_info = record.find(".//LineageEx")
            species_name = None
            if lineage_info is not None:
                for taxon in lineage_info:
                    rank = taxon.find("Rank").text
                    name = taxon.find("ScientificName").text
                    if rank == "species":
                        species_name = name
                        break

            # If the taxid itself is already at species level
            if not species_name:
                species_name = record.find(".//ScientificName").text

            taxid_to_species[taxid] = species_name
            time.sleep(0.4)  # Respect NCBI’s rate limit (max 3/sec)
        except Exception:
            taxid_to_species[taxid] = "Unknown"

    # 4️⃣ Map the results back into your dataframe
    df["species_name"] = df["taxid"].astype(str).map(taxid_to_species)

    return df


def summary_stats(df: pd.DataFrame, output_dir: str) -> None:
    """Generate summary statistics and save to HTML report."""
    summary = df.groupby("species_name").size().reset_index(name="count")
    print(summary)


def generate_summary_report(df: pd.DataFrame, metadata_file: str, output_dir: str) -> None:
    """Generate a summary report in HTML format."""
    # Extract CLIMB IDs from sample IDs

    # Remove ".fasta" from all items in the 'filename' column
    df["climb_id"] = df["#FILE"].str.replace(".fasta", "", regex=False)

    # Load metadata
    metadata = pd.read_csv(metadata_file, sep=",")

    # Merge data with metadata
    merged_df = pd.merge(df, metadata, on="climb_id", how="left")

    # Format publish date
    merged_df["published_date"] = pd.to_datetime(merged_df["published_date"]).dt.strftime("%Y-%m-%d")

    # Generate Summary Statement for report
    summary_stats(merged_df, output_dir)

    logger.info("Summary report generated at %s", output_dir)


def main() -> None:
    args = get_args()
    if args.output_dir:
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(args.output_dir, "amr_html_summary_report_log.txt")
    set_up_logger(log_file)
    logger.info("Starting summary report generation.")
    df = pd.read_csv(args.input_tsv, sep="\t")
    logger.info("Simplifying taxa using Enterez.")
    df = simplify_taxa(args.email, df)
    generate_summary_report(df, args.metadata, args.output_dir)


if __name__ == "__main__":
    main()
