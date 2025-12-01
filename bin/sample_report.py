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
import re
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
        help="Abricate AMR table with read taxonomic information included.",
        required=True,
        type=Path,
    )
    parser.add_argument("-o", "--output", help="Output folder.", required=True, type=Path)
    parser.add_argument("-e", "--email", help="Email address to query Enterez.", required=True, type=str)
    parser.add_argument("-t", "--taxon_id", help="Taxon ID to filter reads on.", required=False, type=int)
    args = parser.parse_args()
    return args


# Logger set up
def set_up_logger(stdout_file: str) -> logging.Logger:
    """Example logger set up which can be amended as required. In this example,
    all logging messages go to a stdout log file, and error messages also go to
    stderr log. If the component runs correctly, stderr is empty. The logger is
    set to append mode so logs from older runs are not overwritten.
    """

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")

    out_handler = logging.FileHandler(stdout_file, mode="a")
    out_handler.setFormatter(formatter)
    out_handler.setLevel(logging.INFO)
    logger.addHandler(out_handler)

    stderr_file = str(stdout_file).replace(".txt", "_stderr.txt")
    err_handler = logging.FileHandler(stderr_file, mode="a")
    err_handler.setFormatter(formatter)
    err_handler.setLevel(logging.ERROR)
    logger.addHandler(err_handler)

    return logger


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


# -------------------------
# Summaries & plots
# -------------------------x
def summarize_by_class(df: pd.DataFrame, unique_resistance_classes: list) -> pd.DataFrame:
    # Ensure TRUE/FALSE (strings) are booleans; if they’re already booleans, this is harmless
    for c in unique_resistance_classes:
        if df[c].dtype != bool:
            df[c] = df[c].astype(str).str.strip().str.upper().map({"TRUE": True, "FALSE": False})

    # Group by species and count TRUEs per column
    res_counts_by_species = df.groupby("species_name")[unique_resistance_classes].sum().astype(int)

    # Add number of rows and total TRUEs across all resistance classes
    res_counts_by_species["n_reads"] = df.groupby("species_name").size()
    res_counts_by_species["total_TRUE"] = res_counts_by_species[unique_resistance_classes].sum(axis=1)

    res_counts_by_species = res_counts_by_species.reset_index()  # moves index to a column named 'index' by default
    # If you want to rename it and ensure it's the first column:
    res_counts_by_species = res_counts_by_species.rename(columns={"index": "species_name"})

    return res_counts_by_species


def plot_class_bar(df: pd.DataFrame, output_path: str) -> Figure:
    # ---- Choose which columns to plot (exclude metadata columns) ----
    meta_cols = ["species_name", "n_reads", "total_TRUE"]
    value_cols = [c for c in df.columns if c not in meta_cols]

    # Optional: set a specific plotting order for categories (else uses CSV order)
    # value_cols = ['aminoglycoside','carbapenem','cephalosporin','fluoroquinolone',
    #               'macrolide','penam','penem','peptide','fosfomycin','monobactam',
    #               'glycylcycline','phenicol','rifamycin','tetracycline','triclosan']

    # ---- Build grouped (side-by-side) bars ----
    species = df["species_name"].tolist()
    n_groups = len(species)
    n_series = len(value_cols)

    x = np.arange(n_groups, dtype=float)  # group centers
    group_width = 0.84  # total width occupied by all bars in a group
    bar_width = group_width / n_series
    offsets = (np.arange(n_series) - (n_series - 1) / 2.0) * bar_width

    # A nice categorical colour palette (larger than needed to avoid repeats)
    # You can replace with plt.cm.get_cmap('tab20') for more categories.
    palette = plt.cm.tab20.colors if n_series > 10 else plt.cm.Set3.colors
    colors = [palette[i % len(palette)] for i in range(n_series)]

    fig, ax = plt.subplots(figsize=(14, 6), constrained_layout=True)

    for i, col in enumerate(value_cols):
        y = df[col].values
        ax.bar(x + offsets[i], y, width=bar_width, label=col, color=colors[i], edgecolor="white", linewidth=0.7)

    # ---- Cosmetics ----
    ax.set_xlabel(None)
    ax.set_ylabel("# of Reads", fontsize=11)
    ax.set_title("Reads Counts Grouped by Species and Class of Resistance", fontsize=13, pad=10)

    # Wrap long species labels to keep them readable
    wrapped_labels = [textwrap.fill(s, width=18) for s in species]
    ax.set_xticks(x)
    ax.set_xticklabels(wrapped_labels, rotation=0, ha="center")

    # Light grid and clean spines
    ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.6)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    # Legend outside the plot to the right
    leg = ax.legend(title="Class", bbox_to_anchor=(1.02, 1), loc="upper left", borderaxespad=0.0)
    plt.setp(leg.get_title(), fontsize=10)

    # Optional: add value labels for small numbers
    def autolabel(ax: Axes | np.ndarray) -> None:
        for container in ax.containers:
            ax.bar_label(container, fmt="%.0f", padding=2, fontsize=8)

    # Uncomment to show labels:
    # autolabel(ax)

    # Save and/or show
    fp = Path(output_path, "resistance_grouped_barplot.png")
    plt.savefig(fp, dpi=300)

    return fig


# TODO: Replace with plotly
def heatplot(df: pd.DataFrame, output_path: str) -> Figure:
    # Sanity check: make sure required columns exist
    required = {"GENE", "species_name", "SEQUENCE"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Count unique SEQUENCE per (GENE, species_name)
    pivot = df.groupby(["GENE", "species_name"])["SEQUENCE"].nunique().unstack(fill_value=0)

    # (Optional) Order: genes by total descending, species by total descending
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
    pivot = pivot[pivot.sum(axis=0).sort_values(ascending=False).index]

    # Mask zeros -> show as white
    z = pivot.values.astype(float)
    z_masked = np.ma.masked_where(z == 0, z)

    # Colormap: any Matplotlib cmap works; set masked (zeros) to white
    cmap = plt.cm.magma_r.copy()  # try 'viridis', 'Blues', etc., if you prefer
    cmap.set_bad(color="white")

    # Figure size scales with data dimensions
    fig_h = max(3, 0.4 * z.shape[0])
    fig_w = max(14, 0.4 * z.shape[1])

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), constrained_layout=True)
    im = ax.imshow(z_masked, aspect="auto", interpolation="nearest", cmap=cmap)

    # Axis labels/ticks
    ax.set_xticks(range(z.shape[1]))
    ax.set_xticklabels(pivot.columns, rotation=60, ha="right")
    ax.set_yticks(range(z.shape[0]))
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel(None)
    ax.set_ylabel("AMR Genes")
    ax.set_title("Unique read counts for AMR genes, per species")

    # Colorbar
    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label("Unique SEQUENCE count")

    # Light grid to aid reading
    ax.set_xticks(np.arange(-0.5, z.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, z.shape[0], 1), minor=True)
    ax.grid(which="minor", color="lightgrey", linestyle="-", linewidth=0.5)
    ax.tick_params(which="minor", bottom=False, left=False)

    # Save (optional)
    fp = Path(output_path, "gene_species_sequence_counts.csv")
    pivot.to_csv(fp)
    fp = Path(output_path, "gene_species_sequence_heatmap.png")
    fig.savefig(fp, dpi=300)

    return fig


def most_common(
    data: pd.Series | Iterable,
    top_n: int = 1,
    *,
    dropna: bool = True,
    as_percent: bool = True,
    round_dp: int = 2,
) -> tuple[object, int, float] | list[tuple[object, int, float]]:
    """
    Return the most common item(s) in a pandas Series (or any iterable),
    along with their counts and percentages of the total.

    Parameters
    ----------
    data : pd.Series or Iterable
        The column/sequence to analyze.
    dropna : bool, default True
        Whether to ignore NA/None/NaN values when counting.
    top_n : int, default 1
        How many of the most frequent values to return.
        If multiple values tie at a boundary, all tied values are included
        (so you may get more than `top_n` rows).
    as_percent : bool, default True
        If True, returns percentage (0–100). If False, returns proportion (0–1).
    round_dp : int, default 2
        Decimal places to round the percentage/proportion.

    Returns
    -------
    - If `top_n == 1`: (value, count, pct_or_prop)
    - If `top_n > 1`:  [(value, count, pct_or_prop), ...]
      Ordered from most to least frequent.

    Notes
    -----
    - Percent/prop denominator is the number of rows considered (after dropna).
    - Ties are handled by selecting all values that share the `top_n`-th rank.
    """
    # Convert to Series if needed
    s = pd.Series(data)

    # Optionally drop missing
    s = s.dropna() if dropna else s

    total = len(s)
    if total == 0:
        # No data case
        result = [] if top_n > 1 else (None, 0, 0.0)
        return result

    counts = s.value_counts(dropna=False)  # already dropped if dropna=True

    # Identify the cutoff for top_n with ties
    if top_n >= len(counts):
        top_counts = counts
    else:
        cutoff = counts.iloc[top_n - 1]
        top_counts = counts[counts >= cutoff]

    # Build result list
    factor = 100.0 if as_percent else 1.0
    vals = [(idx, int(cnt), round((cnt / total) * factor, round_dp)) for idx, cnt in top_counts.items()]

    # Return single tuple if top_n == 1 and exactly one mode
    if top_n == 1 and len(vals) == 1:
        return vals[0]
    return vals


def sankey_html_from_counts(
    df: pd.DataFrame,
    source_label: str,
    column: str,
    top_n: int | None = None,
    other_label: str = "Other",
    title: str | None = None,
    include_plotlyjs: str = "cdn",  # 'cdn' | 'directory' | 'inline' | False
    *,
    full_html: bool = False,  # return a <div> snippet if False
) -> str:
    """
    Build a single-source Sankey: source_label -> categories in `column`.
    Returns an HTML string (either a <div> snippet or full HTML).
    """
    s = df[column].astype(str)
    counts = s.value_counts()
    if top_n is not None and top_n < len(counts):
        head = counts.iloc[:top_n]
        tail_sum = counts.iloc[top_n:].sum()
        if tail_sum > 0:
            counts = pd.concat([head, pd.Series({other_label: tail_sum})])

    labels = [source_label] + counts.index.tolist()
    values = counts.values.tolist()

    # Nodes: index 0 is the source; 1..n are categories
    node = {"label": labels, "pad": 12, "thickness": 18}
    link = {
        "source": [0] * len(values),  # all from source node 0
        "target": list(range(1, len(values) + 1)),
        "value": values,
        "label": counts.index.tolist(),
    }

    fig = go.Figure(go.Sankey(node=node, link=link))
    fig.update_layout(title=None, margin={"l": 10, "r": 10, "t": 10, "b": 10})

    # Return a minimal HTML string for embedding
    return fig.to_html(include_plotlyjs=include_plotlyjs, full_html=full_html)


def coocc_heatmap_div(
    coocc: str = "class_pair_cooccurrence_counts.csv", include_plotlyjs: str = "cdn", *, full_html: bool = False
) -> str:
    labels = coocc.index.tolist()
    fig = go.Figure(
        go.Heatmap(
            z=coocc.values,
            x=labels,
            y=labels,
            colorscale="Viridis",
            colorbar={"title": "Co-occurrence<br>(count of sequences)"},
            hovertemplate="Row %{y} × Col %{x}<br>Count: %{z}<extra></extra>",
        )
    )
    fig.update_layout(
        title=None,
        xaxis_title="Class",
        yaxis_title="Class",
        xaxis={"tickangle": 45},
        yaxis={"autorange": "reversed"},
        margin={"l": 60, "r": 20, "t": 20, "b": 80},
    )
    # Return a DIV snippet you can paste into any HTML document
    return fig.to_html(include_plotlyjs=include_plotlyjs, full_html=full_html)


def read_amr_summary(df: pd.DataFrame, unique_resistance_classes: list, output_path: str) -> dict:
    """Generate summary information about AMR annotations per read."""
    class_cols = unique_resistance_classes

    # Coerce TRUE/FALSE → booleans (safe if already bool)
    for c in class_cols:
        df[c] = df[c].astype(str).str.strip().str.upper().map({"TRUE": True, "FALSE": False})

    # 2) Core per-SEQUENCE metrics
    per_seq_hits = df.groupby("SEQUENCE").size().rename("n_hits")
    per_seq_genes = df.groupby("SEQUENCE")["GENE"].nunique().rename("n_genes")
    per_seq_class_presence = df.groupby("SEQUENCE")[class_cols].any().astype(int)
    per_seq_classes = per_seq_class_presence.sum(axis=1).rename("n_classes")

    per_seq = pd.concat([per_seq_hits, per_seq_genes, per_seq_classes, per_seq_class_presence], axis=1).reset_index()

    # 3) Distributions for reporting
    hist_hits = per_seq["n_hits"].value_counts().sort_index().rename_axis("n_hits").reset_index(name="n_sequences")
    hist_classes = (
        per_seq["n_classes"].value_counts().sort_index().rename_axis("n_classes").reset_index(name="n_sequences")
    )

    # 4) Optional: class co-occurrence (sequence-level)
    presence = per_seq_class_presence
    coocc = pd.DataFrame(index=class_cols, columns=class_cols, dtype=int)
    for i in class_cols:
        for j in class_cols:
            coocc.loc[i, j] = int(((presence[i] == 1) & (presence[j] == 1)).sum())

    # Find the row where n_hits is maximum
    max_hits_row = hist_hits.loc[hist_hits["n_hits"].idxmax()]
    # Extract the corresponding n_sequences value
    n_sequences_for_max_hits = max_hits_row["n_sequences"]

    # Find the row where n_hits is maximum
    max_class_row = hist_classes.loc[hist_classes["n_classes"].idxmax()]
    # Extract the corresponding n_sequences value
    n_sequences_for_max_classes = max_class_row["n_sequences"]

    read_amr_dict = {
        "median_read_amr_count": per_seq["n_hits"].median(),
        "reads_w_max_amr_count": n_sequences_for_max_hits,
        "max_read_amr_count": hist_hits["n_hits"].max(),
        "median_read_class_count": per_seq["n_classes"].median(),
        "max_read_class_count": hist_classes["n_classes"].max(),
        "reads_w_max_class_count": n_sequences_for_max_classes,
    }

    fig = coocc_heatmap_div(coocc)
    return read_amr_dict, fig


# -------------------------
# HTML assembly
# -------------------------
HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>AMR Report - {title}</title>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>
body {{ font-family: Arial, Helvetica, sans-serif; margin: 20px; color: #222; }}
h1, h2, h3 {{ color: #0b4d6b; }}
.table {{ border-collapse: collapse; width: 100%; margin-bottom: 1rem; }}
.table th, .table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; }}
.table th {{ background: #f2f2f2; }}
.card {{ border: 1px solid #e1e1e1; padding: 12px; border-radius: 6px; margin-bottom: 16px; background: #fff; }}
.img {{ max-width: 100%; height: auto; border: 1px solid #ddd; padding: 6px; background: #fafafa; }}
.small {{ font-size: 0.9rem; color: #666; }}
.footer {{ margin-top: 40px; font-size: 0.9rem; color: #666; }}
</style>
</head>
<body>
<div class="card">
<h1>AMR Report: {title}</h1>
<p class="small">Generated: {timestamp}</p>
</div>

<div class="card">
<h2>Summary</h2>
<ul>
    <li>Number of reads with AMR annotations: <b>{total_reads_w_amr}</b> 
        {domain_counts_html}
    </li>
    <li> Classes of resistance observed are summarized below:
        {domain_profiles_html}
    </li>
    <li> AMR genes observed are summarized below (# reads):
        {domain_genes_html}
    </li>
</ul>
</div>
{gene_coverage_table_html}
{gene_figure_html}

</body>
</html>
"""  # noqa: E501


# {genes_sankey_html}
# <h3>Number of Reads with Annotated Genes, per Species</h3>
# <img class="img" src="{heatmap_img}" alt="Identity vs Coverage"/>
# </div>

# <div class="card">
# <h2>Read Summary</h2>
# <ul>
#     <li> The median number of AMR annotations per read was {median_read_amr_count}.</li>
#     <li> The maximum number of AMR annotations per read was {max_read_amr_count}. {reads_w_max_amr_count} reads had this many AMR hits.<li>
#     <li> The median number of AMR classes per read was {median_read_class_count}.</li>
#     <li> The maximum number of AMR classes for a read was {max_read_class_count}. {reads_w_max_class_count} reads had this many AMR hits.<li>
# </ul>
# <h3>Plot of AMR Class Co-Occurance on Reads</h3>
# {coocc_fig}
# </div>
# <div class="card">
# <h2>Taxa Summary</h2>
# <p>
# <ul>
#     <li>Total unique taxa associated with AMR annotations: <b>{no_of_taxa}</b>:</li>
#         <ul><li>Top 5: <b>{taxa_string}</b>.</li></ul>
# </ul>
# {species_sankey_html}

# </div>

# <div class="card">
# <h2>Plots</h2>
# <h3>AMR Genes by Resistance Class</h3>
# <p>The number of unique reads annotated with a gene confering resistance to a given class of antimicrobial.</p>
# <img class="img" src="{bar_class_img}" alt="Class distribution"/>


# <div class="footer">
# <p>Source file: {source_file}</p>
# <p>Notes: Tables derived from input. 'RESISTANCE' column is split on ';' to produce class-level counts.</p>
# </div>


def coverage_stats_from_tables(coverage_tables: dict) -> pd.DataFrame:
    """
    coverage_tables: dict with keys (gene, species_name) and values DataFrame
                     with columns ['Position', 'Coverage'].
    Returns a DataFrame of summary statistics for each (gene, species).
    """
    rows = []
    for (gene, species), df in coverage_tables.items():
        # Ensure expected columns exist
        if not {"Position", "Coverage"}.issubset(df.columns):
            raise ValueError(f"Table for ({gene}, {species}) must have 'Position' and 'Coverage' columns.")

        # Basic stats
        ref_len = int(df["Position"].max())  # number of positions
        covered_mask = df["Coverage"] > 0
        covered_len = int(covered_mask.sum())  # positions with coverage > 0
        pct_covered = 100.0 * covered_len / ref_len if ref_len > 0 else 0.0
        mean_cov = float(df["Coverage"].mean())
        median_cov = float(df["Coverage"].median())
        min_cov = int(df["Coverage"].min())
        max_cov = int(df["Coverage"].max())

        # Coverage start/end (None if no coverage)
        if covered_len > 0:
            start_pos = int(df.loc[covered_mask, "Position"].min())
            end_pos = int(df.loc[covered_mask, "Position"].max())
        else:
            start_pos = None
            end_pos = None

        rows.append(
            {
                "Gene": gene,
                "Species": species,
                "Reference length (bp)": ref_len,
                "Covered length (bp)": covered_len,
                "% Covered": round(pct_covered, 2),
                "Mean coverage": round(mean_cov, 2),
                "Median coverage": round(median_cov, 2),
                "Min coverage": min_cov,
                "Max coverage": max_cov,
                "Start of coverage": start_pos if start_pos is not None else "-",
                "End of coverage": end_pos if end_pos is not None else "-",
            }
        )

    return pd.DataFrame(rows)


def make_html_table(df_stats: pd.DataFrame, title: str = "Coverage Statistics") -> str:
    """
    Create a styled HTML table string from the stats DataFrame.
    """
    # Basic CSS for readability
    css = """
    <style>
    .table { border-collapse: collapse; width: 100%; margin: 1rem 0; font-family: Arial, Helvetica, sans-serif; }
    .table th, .table td { border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; }
    .table th { background: #f2f2f2; }
    .card { border: 1px solid #e1e1e1; padding: 12px; border-radius: 6px; margin: 16px 0; background: #fff; }
    h2 { color: #0b4d6b; margin: 0 0 8px 0; }
    </style>
    """

    # Convert DataFrame to HTML
    table_html = df_stats.to_html(index=False, classes=["table"], escape=False)

    # Wrap in a card
    html = f"""
    {css}
    <div class="card">
      <h2>{(title)}</h2>
      {table_html}
    </div>
    """
    return html


def gene_figures(df: pd.DataFrame) -> dict[str, go.Figure]:
    """
    Generate coverage plots per gene using Plotly.
    Returns a dictionary mapping gene names to Plotly Figure objects.
    """
    gene_figs = {}

    for gene in df["GENE"].unique():
        fig = go.Figure()

        # Add a line for each species for this gene
        for (g, species), group in df.groupby(["GENE", "species_name"]):
            if g == gene:
                # Create coverage array
                gene_length = int(group["COVERAGE"].iloc[0].split("/")[-1])
                coverage_array = np.zeros(gene_length, dtype=int)

                for cov in group["COVERAGE"]:
                    start = int(cov.split("-")[0])
                    end = int(cov.split("-")[1].split("/")[0])
                    coverage_array[start - 1 : end] += 1  # Increment coverage for positions

                coverage_df = pd.DataFrame({"Position": range(1, gene_length + 1), "Coverage": coverage_array})

                fig.add_trace(
                    go.Scatter(x=coverage_df["Position"], y=coverage_df["Coverage"], mode="lines", name=species)
                )

        # Customize layout
        fig.update_layout(
            title=f"Coverage Plot for Gene: {gene}",
            xaxis_title="Position",
            yaxis_title="Coverage",
            template="plotly_white",
        )

        gene_figs[gene] = fig

    return gene_figs


def make_gene_figure_html_block(gene: str, fig: go.Figure) -> str:
    """
    Create an HTML block for a gene coverage figure.
    """
    # Save plot as HTML div
    cov_gene_figures = fig.to_html(full_html=False, include_plotlyjs="cdn")

    gene_figure_html_block = f"""
    <div class="card">
        <h2>Gene {gene} Coverage Plot</h2>
        {cov_gene_figures}
    </div>
    """
    return gene_figure_html_block


# Function to build coverage table per gene
def generate_gene_summary_html(df: pd.DataFrame) -> str:
    """Generate gene coverage summary HTML blocks."""

    # Generate tables for each gene-species combination
    coverage_tables = {}

    for gene_species, group in df.groupby(["GENE", "species_name"]):
        # Get gene length from value after '/'
        gene_length = int(group["COVERAGE"].iloc[0].split("/")[-1])

        # Initialize coverage array
        coverage_array = np.zeros(gene_length, dtype=int)

        # Process each read
        for cov in group["COVERAGE"]:
            start = int(cov.split("-")[0])
            end = int(cov.split("-")[1].split("/")[0])
            coverage_array[start - 1 : end] += 1  # Increment coverage for positions

        # Create DataFrame for this gene
        coverage_df = pd.DataFrame({"Position": range(1, gene_length + 1), "Coverage": coverage_array})

        coverage_tables[gene_species] = coverage_df

    #  Generate stats
    df_stats = coverage_stats_from_tables(coverage_tables)
    # Create HTML table
    cov_table_html = make_html_table(df_stats, title="AMR Gene Coverage Summary")

    gene_fig_list = []
    # Generate coverage plots per gene
    for gene in df["GENE"].unique():
        # Generate Figure
        gene_figs = gene_figures(df[df["GENE"] == gene])
        fig = gene_figs[gene]
        gene_fig_list.append(fig)

    # Create HTML block for all gene figures
    gene_figure_html_blocks = []
    for gene, fig in zip(df["GENE"].unique(), gene_fig_list):
        block = make_gene_figure_html_block(gene, fig)
        gene_figure_html_blocks.append(block)
    gene_figure_html = "\n".join(gene_figure_html_blocks)

    return cov_table_html, gene_figure_html


# -------------------------
# Main
# -------------------------
def generate_html_report(df: pd.DataFrame, output_path: str, sample_id: str, amr_tsv: str) -> None:
    # Create boolean columns for each resistance class
    fp = Path(output_path, "output_with_booleans.csv")

    # Get number of reads with AMR annotations
    total_reads_w_amr = df["SEQUENCE"].nunique()
    # Get number of reads with AMR annotations by domain
    domain_read_count_dict = {}
    domain_species_list_dict = {}

    for domain in df["domain"].unique():
        domain_df = df[df["domain"] == domain]

        # Count unique reads
        domain_read_count = domain_df["SEQUENCE"].nunique()
        domain_read_count_dict[domain] = domain_read_count

        # Count unique species
        species_list = domain_df["species_name"].unique()
        if len(species_list) > 1:
            domain_species_list_dict[domain] = species_list.join(", ")
        elif len(species_list) == 1:
            domain_species_list_dict[domain] = species_list[0]
        else:
            domain_species_list_dict[domain] = "No species level annotations."

    # Build HTML dynamically
    domain_counts_html = ""
    for domain in df["domain"].unique():
        reads = domain_read_count_dict.get(domain, 0)
        species = domain_species_list_dict.get(domain, 0)
        domain_counts_html += f"<ul><b>{domain}</b>:<ul>Read Counts: {reads}</ul><ul>Species: {species}</ul></ul>\n"

    # Get resistance profiles by domain
    def get_resistance_profile(domain: str) -> str:
        domain_df = df[df["domain"] == domain]
        if domain_df.empty:
            return "None"
        unique_resistance_classes = (
            domain_df["RESISTANCE"].dropna().str.split(";").explode().str.strip().str.lower().dropna().unique()
        )
        return ", ".join(unique_resistance_classes)

    domain_profiles_dict = {}
    for domain in df["domain"].unique():
        profile = get_resistance_profile(domain)
        domain_profiles_dict[domain] = profile

    domain_profiles_html = ""
    for domain, profile in domain_profiles_dict.items():
        domain_profiles_html += f"<ul><b>{domain}</b>: {profile}</ul>\n"

    # AMR Genes by domain
    def get_gene_profile(domain: str) -> str:
        domain_df = df[df["domain"] == domain]
        if domain_df.empty:
            return "None"

        # Count occurrences of each gene
        gene_counts = domain_df["GENE"].dropna().str.strip().str.upper().value_counts()

        # Format as "GENE (count)"
        formatted_genes = [f"{gene} ({count})" for gene, count in gene_counts.items()]

        return ", ".join(formatted_genes)

    domain_gene_profiles_dict = {}
    for domain in df["domain"].unique():
        gene_profile = get_gene_profile(domain)
        domain_gene_profiles_dict[domain] = gene_profile

    domain_genes_html = ""
    for domain, genes in domain_gene_profiles_dict.items():
        domain_genes_html += f"<ul><b>{domain}</b>: {genes}</ul>\n"

    # Summarise Gene Content

    gene_figure_html_block, cov_table_html = generate_gene_summary_html(df)

    # Summarise reads
    # Get unique resistance classes
    unique_genes = df["GENE"].dropna().str.strip().str.upper().unique().tolist()
    # Create a dataframe with SEQUENCE, each GENE associated with SEQUENCE

    # read_amr_summary_dict, coocc_fig = read_amr_summary(df, unique_resistance_classes, output_path)
    # Generate a summary HTML table for reads with AMR annotations

    # min, max, median number of AMR annotations per read
    # min, max, median number of AMR classes per read

    html = HTML_TEMPLATE.format(
        title=sample_id,
        timestamp=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        # Read counts
        total_reads_w_amr=total_reads_w_amr,
        domain_counts_html=domain_counts_html,
        domain_profiles_html=domain_profiles_html,
        domain_genes_html=domain_genes_html,
        # Gene summaries
        gene_figure_html=gene_figure_html_block,
        gene_coverage_table_html=cov_table_html,
        # AMR Profiles
        # median_read_amr_count=read_amr_summary_dict["median_read_amr_count"],
        # max_read_amr_count=read_amr_summary_dict["max_read_amr_count"],
        # reads_w_max_amr_count=read_amr_summary_dict["reads_w_max_amr_count"],
        # median_read_class_count=read_amr_summary_dict["median_read_class_count"],
        # max_read_class_count=read_amr_summary_dict["max_read_class_count"],
        # reads_w_max_class_count=read_amr_summary_dict["reads_w_max_class_count"],
        # coocc_fig=coocc_fig,
        # source_file=amr_tsv,
    )

    fp = Path(output_path, str(f"{sample_id}_sample_amr_report.html"))
    with Path.open(fp, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"Saved HTML report to: {output_path}")  # noqa: T201


def main() -> None:
    args = get_args()
    amr_tsv = args.input_tsv
    output_path = args.output
    email = args.email
    sample_id = Path(amr_tsv).name.split("_")[0]

    log_file = Path(output_path, "amr_html_report_log.txt")
    set_up_logger(log_file)
    logger = logging.getLogger(__name__)

    # Add in rest of code including logging messages:
    logger.info("AMR report generation started.")  # Example only - add more informative logging messages

    df = load_table(amr_tsv)
    if args.taxon_id:
        df = df[df["taxid"] == args.taxon_id]
        if df.empty:
            logger.info("Dataframe is empty. No results match Taxon ID %s", args.taxon_id)
            sys.exit()

    df = simplify_taxa(email, df)

    generate_html_report(df, output_path, sample_id, amr_tsv)

    # Write to logs if component finished successfully (or not):
    logger.info("AMR report generation successfully completed")


if __name__ == "__main__":
    main()
