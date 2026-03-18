#!/usr/bin/env python3
"""
amr_html_report.py

Create a single-file HTML AMR report from an Abricate/CARD-style TSV/CSV.

Produces:
 - summary tables (resistance class summary, top genes)
 - plots (pie of classes, scatter identity vs coverage, bar top genes)
 - single HTML file with embedded images (base64) and tables
"""

import argparse
import base64
import io
import logging
import sys
import textwrap
import time
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from Bio import Entrez
from matplotlib.axes import Axes
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)


# -------------------------
# Utilities
# -------------------------
def get_args() -> argparse.Namespace:
    """
    Command Line
    :return: argParse variable
    """
    parser = argparse.ArgumentParser(description="Generate a sample HTML report for Abricate and Kraken annotations.")
    parser.add_argument(
        "-i",
        "--input_tsv",
        help="AMR table with read taxonomic information included.",
        required=True,
        type=Path,
    )
    parser.add_argument("-o", "--output", help="Output folder.", required=True, type=Path)
    parser.add_argument("-e", "--email", help="Email address to query Enterez.", required=True, type=str)
    parser.add_argument("-t", "--taxon_id", help="Taxon ID to filter reads on.", required=False, type=int)
    args = parser.parse_args()
    return args


# Logger set up
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


def df_to_html_table(df: pd.DataFrame) -> pd.DataFrame:
    """Return pretty HTML table string for a DataFrame."""
    return df.to_html(classes="table", index=False, justify="left", border=0, escape=False)


def fig_to_base64(fig: Figure) -> str:
    """Convert a Matplotlib figure to a base64 PNG."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    plt.close(fig)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("ascii")
    return f"data:image/png;base64,{b64}"


# -------------------------
# Data loading and processing
# -------------------------
def load_table(path: str | Path) -> pd.DataFrame:
    # Try TSV first, then auto-detect
    try:
        df = pd.read_csv(path, sep="\t")
    except Exception:
        df = pd.read_csv(path, sep=None)
    # normalize column names (strip whitespace)
    df.columns = [c.strip() for c in df.columns]
    return df


def main() -> None:
    args = get_args()
    amr_tsv = args.input_tsv
    output_path = args.output
    email = args.email
    sample_id = Path(amr_tsv).name.split("_")[0]

    log_file = Path(output_path, "amr_html_report_log.txt")
    set_up_logger(log_file)

    # Add in rest of code including logging messages:
    logger.info("AMR report generation started.")  # Example only - add more informative logging messages

    df = load_table(amr_tsv)

    if args.taxon_id:
        df = df[df["taxid"] == args.taxon_id]
        if df.empty:
            logger.info("Dataframe is empty. No results match Taxon ID %s", args.taxon_id)
            sys.exit()

    df = simplify_taxa(email, df)

    # Write to logs if component finished successfully (or not):
    logger.info("AMR report generation successfully completed")


if __name__ == "__main__":
    main()
