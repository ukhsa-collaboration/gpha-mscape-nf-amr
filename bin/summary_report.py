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
import plotly.express as px
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
    taxid_to_domain = {}

    # 3️⃣ Query NCBI only once per unique taxid
    for taxid in unique_taxids:
        try:
            handle = Entrez.efetch(db="taxonomy", id=taxid)
            record = ET.fromstring(handle.read())

            # Extract lineage
            lineage_info = record.find(".//LineageEx")
            species_name = None
            domain_name = None

            if lineage_info is not None:
                for taxon in lineage_info:
                    rank = taxon.find("Rank").text
                    name = taxon.find("ScientificName").text

                    # Capture domain (superkingdom)
                    if rank == "domain":
                        domain_name = name

                    # Capture species
                    if rank == "species":
                        species_name = name

            # If species not found, use main ScientificName
            if not species_name:
                species_name = record.find(".//ScientificName").text

            # If domain not found, fallback to Unknown
            if not domain_name:
                domain_name = "Unknown"

            taxid_to_species[taxid] = species_name
            taxid_to_domain[taxid] = domain_name

            time.sleep(0.4)  # Respect NCBI’s rate limit
        except Exception:
            taxid_to_species[taxid] = "Unknown"
            taxid_to_domain[taxid] = "Unknown"

    # 4️⃣ Map results back into dataframe
    df["species_name"] = df["taxid"].astype(str).map(taxid_to_species)
    df["domain"] = df["taxid"].astype(str).map(taxid_to_domain)

    return df


def format_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Format date columns in the dataframe."""
    # Format publish date
    df["published_date"] = pd.to_datetime(df["published_date"]).dt.strftime("%Y-%m-%d")

    # Convert to datetime
    df["published_date"] = pd.to_datetime(df["published_date"])

    # Extract ISO year and week
    df["epi_year"] = df["published_date"].dt.isocalendar().year
    df["epi_week"] = df["published_date"].dt.isocalendar().week

    # Combine into epi week-year format (e.g., 2025-W01)
    df["epi_week_year"] = df["epi_year"].astype(str) + "-W" + df["epi_week"].astype(str).str.zfill(2)

    return df


def summary_stats(df: pd.DataFrame, output_dir: str) -> None:
    """Generate summary statistics and save to HTML report."""
    logger.info("Generating summary statistics.")
    # Number of samples with AMR annotations
    num_samples = df["climb_id"].nunique()
    logger.info("Number of samples with AMR annotations: %d", num_samples)
    # Create a dataframe where the first column is the climb id, the second is the domain, and the third is the number of reads
    summary_df = df.groupby(["climb_id", "domain"]).size().reset_index(name="amr_hit_count")
    # From the summary_df, create a summary table that shows the min, max, median, and mean number of amr hits per domain
    summary_stats_df = (
        summary_df.groupby("domain")["amr_hit_count"]
        .agg(min_amr_hits="min", median_amr_hits="median", max_amr_hits="max")
        .reset_index()
    )

    # Figures for number of reads annotated with AMR per species per domain
    amr_annotations_per_domain_fig_list = []
    # for each domain
    for domain in df["domain"].unique():
        print(domain)
        domain_df = df[df["domain"] == domain]
        # summarise the number of unique SEQUENCE per climb_id per species
        species_sample_amr_reads = (
            domain_df.groupby(["climb_id", "species_name"])["SEQUENCE"]
            .nunique()
            .reset_index(name="unique_amr_sequence_count")
        )
        # Generate a box-whisker plot showing the distribution of unique_amr_sequence_count per species with plotly
        print(species_sample_amr_reads)

        fig = px.box(
            species_sample_amr_reads,
            x="species_name",
            y="unique_amr_sequence_count",
            title=f"Distribution of Unique AMR Sequences per Species in {domain}",
            labels={"species_name": "Taxa", "unique_amr_sequence_count": "# Reads with AMR Annotations, per sample"},
        )
        fig.write_html(Path(output_dir) / f"{domain}_amr_reads_species_distribution.html")
        amr_annotations_per_domain_fig_list.append(fig)

    amr_annotations_per_domain_html_blocks = []
    for fig in amr_annotations_per_domain_fig_list:
        amr_annotations_per_domain_html_blocks.append(fig.to_html(full_html=False, include_plotlyjs="cdn"))

    amr_annotations_per_domain_html = "\n".join(amr_annotations_per_domain_html_blocks)

    # Generate line graph with the number of AMR annotations over time, each line is a domain, grouped by week

    return amr_annotations_per_domain_html


def generate_summary_report(df: pd.DataFrame, metadata_file: str, output_dir: str) -> None:
    """Generate a summary report in HTML format."""
    # Extract CLIMB IDs from sample IDs

    # Remove ".fasta" from all items in the 'filename' column
    df["climb_id"] = df["#FILE"].str.replace(".fastq", "", regex=False)

    print(df["climb_id"])
    # Load metadata
    metadata = pd.read_csv(metadata_file, sep=",")
    print(metadata["climb_id"])
    breakpoint()

    # Merge data with metadata
    merged_df = pd.merge(df, metadata, on="climb_id", how="left")

    # format dates
    print(merged_df)
    # merged_df = format_dates(merged_df)
    # print(merged_df["published_date"])
    breakpoint()

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
