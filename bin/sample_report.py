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
import os
import textwrap
import time
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Union

import matplotlib.pyplot as plt  # type: ignore
import numpy as np  # type: ignore
import pandas as pd  # type: ignore
import plotly.graph_objects as go  # type: ignore
from Bio import Entrez  # type: ignore
from matplotlib.axes import Axes  # type: ignore
from matplotlib.figure import Figure  # type: ignore


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
    args = parser.parse_args()
    return args


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


def explode_resistance(df: pd.DataFrame) -> pd.DataFrame:
    # One-hot encode the semicolon-separated list in RESISTANCE
    res_dummies = df["RESISTANCE"].str.get_dummies(sep=";").astype(bool)
    # Join back and (optionally) keep or drop the original RESISTANCE column
    out = pd.concat([df, res_dummies], axis=1)  # .drop(columns=['RESISTANCE'])
    return out


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
    fp = os.path.join(output_path, str("gene_species_sequence_counts.csv"))
    pivot.to_csv("gene_species_sequence_counts.csv")
    fp = os.path.join(output_path, str("gene_species_sequence_heatmap.png"))
    fig.savefig(fp, dpi=300)

    return fig


def most_common(
    data: Union[pd.Series, Iterable], dropna: bool = True, top_n: int = 1, as_percent: bool = True, round_dp: int = 2
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
    coocc: str = "class_pair_cooccurrence_counts.csv", include_plotlyjs="cdn", full_html: bool = False
) -> str:
    labels = coocc.index.tolist()
    fig = go.Figure(
        go.Heatmap(
            z=coocc.values,
            x=labels,
            y=labels,
            colorscale="Viridis",
            colorbar=dict(title="Co-occurrence<br>(count of sequences)"),
            hovertemplate="Row %{y} × Col %{x}<br>Count: %{z}<extra></extra>",
        )
    )
    fig.update_layout(
        title=None,
        xaxis_title="Class",
        yaxis_title="Class",
        xaxis=dict(tickangle=45),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=60, r=20, t=20, b=80),
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
<h1>AMR Report: {title}</h1>
<p class="small">Generated: {timestamp}</p>

<div class="card">
<h2>AMR Summary</h2>
<ul>
    <li>Total AMR annotations: <b>{total_amr_count}</b>.</li>
    <li>Total unique AMR elements: <b>{total_unique_genes}</b></li>
        <ul>
            <li>Top 5: <b>{gene_string}</b></li>
            <li>Classes of resistance observed: {resistance_string}.</li>
        </ul>
</ul>
{genes_sankey_html}
<h3>Number of Reads with Annotated Genes, per Species</h3>
<img class="img" src="{heatmap_img}" alt="Identity vs Coverage"/>
</div>

<div class="card">
<h2>Read Summary</h2>
<ul>
    <li> The median number of AMR annotations per read was {median_read_amr_count}.</li>
    <li> The maximum number of AMR annotations per read was {max_read_amr_count}. {reads_w_max_amr_count} reads had this many AMR hits.<li>
    <li> The median number of AMR classes per read was {median_read_class_count}.</li>
    <li> The maximum number of AMR classes for a read was {max_read_class_count}. {reads_w_max_class_count} reads had this many AMR hits.<li>
</ul>
<h3>Plot of AMR Class Co-Occurance on Reads</h3>
{coocc_fig}
</div>
<div class="card">
<h2>Taxa Summary</h2>
<p> 
<ul>
    <li>Total unique taxa associated with AMR annotations: <b>{no_of_taxa}</b>:</li>
        <ul><li>Top 5: <b>{taxa_string}</b>.</li></ul>
</ul>
{species_sankey_html}

</div>

<div class="card">
<h2>Plots</h2>
<h3>AMR Genes by Resistance Class</h3>
<p>The number of unique reads annotated with a gene confering resistance to a given class of antimicrobial.</p>
<img class="img" src="{bar_class_img}" alt="Class distribution"/>



<div class="footer">
<p>Source file: {source_file}</p>
<p>Notes: Tables derived from input. 'RESISTANCE' column is split on ';' to produce class-level counts.</p>
</div>
</body>
</html>
"""


# -------------------------
# Main
# -------------------------
def generate_html_report(df: pd.DataFrame, output_path: str, sample_id: str, amr_tsv: str):
    # Create boolean columns for each resistance class
    res_expanded_df = explode_resistance(df)
    fp = os.path.join(output_path, str("output_with_booleans.csv"))

    unique_resistance_classes = (
        df["RESISTANCE"]
        .dropna()
        .str.split(";")
        .explode()
        .str.strip()
        .str.lower()  # or .str.capitalize() if you prefer
        .dropna()
        .unique()
    )

    res_counts_by_species = summarize_by_class(res_expanded_df, unique_resistance_classes)
    fp = os.path.join(output_path, str("res_counts_by_species.csv"))
    res_counts_by_species.to_csv(fp, index=True)

    # Summary information for paragraphs:
    def most_common_string(top5):
        most_common_list = []
        most_common_list.append(str(f"{top5[0][0]} (AMR Reads: {top5[0][1]}, {top5[0][2]}%)"))
        for item in top5[1:]:
            most_common_list.append(str(f"{item[0]} ({item[1]}, {item[2]}%)"))
        return str(", ".join(most_common_list))

    top5_spp = most_common(df["species_name"], top_n=5)
    most_common_taxa_str = most_common_string(top5_spp)

    top5_genes = most_common(df["GENE"], top_n=5)
    most_common_genes_str = most_common_string(top5_genes)

    # create figures
    fig1 = plot_class_bar(res_counts_by_species, output_path)
    fig2 = heatplot(df, output_path)

    species_sankey_html = sankey_html_from_counts(
        df, "Total reads", "species_name", include_plotlyjs="cdn", full_html=False
    )

    genes_sankey_html = sankey_html_from_counts(df, "Total reads", "GENE", include_plotlyjs="cdn", full_html=False)

    bar_class_b64 = fig_to_base64(fig1)
    heatplot_b64 = fig_to_base64(fig2)

    # tables to HTML
    summary_html = df_to_html_table(res_counts_by_species)

    read_amr_summary_dict, coocc_fig = read_amr_summary(res_expanded_df, unique_resistance_classes, output_path)

    html = HTML_TEMPLATE.format(
        title=sample_id,
        timestamp=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        summary_table=summary_html,
        total_amr_count=len(df["SEQUENCE"]),
        no_of_taxa=len(df["species_name"].unique()),
        taxa_string=most_common_taxa_str,
        total_unique_genes=len(df["GENE"].unique()),
        gene_string=most_common_genes_str,
        resistance_string=", ".join(unique_resistance_classes),
        bar_class_img=bar_class_b64,
        heatmap_img=heatplot_b64,
        species_sankey_html=species_sankey_html,
        genes_sankey_html=genes_sankey_html,
        median_read_amr_count=read_amr_summary_dict["median_read_amr_count"],
        max_read_amr_count=read_amr_summary_dict["max_read_amr_count"],
        reads_w_max_amr_count=read_amr_summary_dict["reads_w_max_amr_count"],
        median_read_class_count=read_amr_summary_dict["median_read_class_count"],
        max_read_class_count=read_amr_summary_dict["max_read_class_count"],
        reads_w_max_class_count=read_amr_summary_dict["reads_w_max_class_count"],
        coocc_fig=coocc_fig,
        source_file=amr_tsv,
    )

    fp = os.path.join(output_path, str(f"{sample_id}_sample_amr_report.html"))
    with open(fp, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"Saved HTML report to: {output_path}")


def main():
    args = get_args()
    amr_tsv = args.input_tsv
    output_path = args.output
    email = args.email
    sample_id = os.path.basename(amr_tsv).split("_")[0]

    df = load_table(amr_tsv)
    df = simplify_taxa(email, df)

    generate_html_report(df, output_path, sample_id, amr_tsv)


if __name__ == "__main__":
    main()
