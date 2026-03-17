#!/usr/bin/env python3

import argparse
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from taxaplease import TaxaPlease


def existing_file(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_file():
        raise FileNotFoundError(f"File does not exist: {path}")
    return path


def existing_dir(path):
    p = Path(path)
    if not p.is_dir():
        raise argparse.ArgumentTypeError(f"{p} is not an existing directory")
    return p


def setup_logging(logdir: Path, tag: str, level: str) -> Path:
    """Configure logging with console + file handlers and runtime-selected log level."""

    logdir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    logfile = logdir / f"{tag}_{timestamp}.log"

    # Clear existing handlers (avoids double logging if called twice)
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(logfile, mode="w", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    logging.info("Logging initialised.")
    logging.info("Logfile: %s", logfile)
    logging.info("Log level: %s", level.upper())

    return logfile


def read_commandline() -> argparse:
    """
        Command line arguments

        :return: argparse argument object

    # Read in taxa reference file

    # Read in database file

    """

    parser = argparse.ArgumentParser(description="AI UK Genotyping command line tool")
    parser.add_argument(
        "--output_dir",
        "-o",
        required=True,
        default=str(Path.cwd()),
        help="Output folder. Default: CWD.",
    )

    parser.add_argument(
        "--reference_taxa_list",
        "-r",
        required=True,
        type=existing_file,
        help="Text file containing full species names per line i.e. Klebsiella pneumoniae",
    )

    parser.add_argument(
        "--taxaplease_db",
        "-db",
        required=True,
        type=existing_file,
        help="Database file genenerated by taxaplease",
    )

    parser.add_argument(
        "--log-level",
        "-l",
        required=False,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level. Options: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)",
    )  # Change this to a list of options

    args = parser.parse_args()

    # Need to handle output dir before setting up logging files.
    if not Path(args.output_dir).is_dir():  # Set up output folder
        Path(args.output_dir).mkdir()

    return args


# Use taxaplease


# Extract the taxa id for taxa of interest
def get_species_names(reference_taxa_fp: str) -> list:
    """
    Read in file path for textfile of species names, split into list
    :args: filepath, str
    :return: list[species name, ... ]
    """
    logging.info("Parsing reference taxa from file %s", reference_taxa_fp)
    reference_taxa_fp = Path(reference_taxa_fp)
    with reference_taxa_fp.open("r") as f:
        species = [line.strip() for line in f if line.strip()]
    logging.info("Identified the following species %s", ", ".join(species))
    return species


# Get taxid for species
def get_taxa_id(species: list, taxaplease_db: str) -> pd.DataFrame:
    """
    Read in list of species names (strings), query database, extract taxaid, map taxid to species name as dictionary
    :args: species list, database fp (str)
    :return: dictionar {species_name: taxid, ... }
    """
    logging.info("Querying database for reference species...")
    conn = sqlite3.connect(taxaplease_db)

    out_rows = []

    for sp in species:
        query = """
            SELECT taxid, name
            FROM taxa
            WHERE name = ?
        """
        # Use parameterised query to avoid SQL injection
        df = pd.read_sql(query, conn, params=[sp])

        if df.empty:
            out_rows.append({"input_name": sp, "matched_name": None, "taxid": None})
        else:
            # Return all matches; could refine logic to take first match if preferred
            for _, row in df.iterrows():
                out_rows.append({"input_name": sp, "matched_name": row["name"], "taxid": row["taxid"]})

    conn.close()
    logging.info("Found %s matches to query species", len(out_rows))

    if len(out_rows) == 0:
        sys.exit(logging.error("No database matches to the following species:\n%s", ", ".join(species)))
    else:
        return pd.DataFrame(out_rows)


# provide all parent taxa ids for taxa of interest
def get_parent_taxid(species_match_df: pd.DataFrame, taxaplease_db: str) -> pd.DataFrame:
    """
    Get TaxaIDs from pandas dataframe column and identify all parent taxaids, extract  into a list and add as a new column to the dataframe
    :args: species_match_df dataframe, database fp (str)
    :return: dataframe with parent_taxid column
    """
    tp = TaxaPlease(database=taxaplease_db)

    parent_records = []

    for taxid in species_match_df["taxid"]:
        if pd.isna(taxid):
            parent_records.append(None)
            continue

        parent_taxids = tp.get_all_parent_taxids(int(taxid), includeSelf=False)
        records = [tp.get_record(t) for t in parent_taxids]
        parent_records.append(records)

    species_match_df["parent_records"] = parent_records
    logging.debug(species_match_df)
    return species_match_df


# write to output tsv


def main(args) -> None:
    """
    Main running of the script to run the BLAST query and wrangle the results to provide a per segment and sample summary of the genotyping results.

    :return: N/A
    """
    start_time = datetime.now()  #
    setup_logging(Path(args.output_dir), "taxaplease", args.log_level)
    logging.debug(args)

    # Get species names
    species = get_species_names(args.reference_taxa_list)
    species_match_df = get_taxa_id(species, args.taxaplease_db)
    get_parent_taxid(species_match_df, args.taxaplease_db)


def cli():
    """Entry-point wrapper for console_scripts/project.scripts."""
    args = read_commandline()
    return main(args)


if __name__ == "__main__":
    # running the module directly still works
    sys.exit(cli())
