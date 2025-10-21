#!/usr/bin/env python3
"""
Generate summary tables and visualizations from a metagenomic AMR detection table
Example input: abridge-style TSV file (e.g., from Abricate or CARD)
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from textwrap import fill

# ------------------------------------------------------------
# 1. Load data
# ------------------------------------------------------------
def load_amr_table(filepath):
    """Load AMR results table."""
    df = pd.read_csv(filepath, sep='\t')
    return df


# ------------------------------------------------------------
# 2. Summarize by resistance class
# ------------------------------------------------------------
def summarize_by_class(df):
    """Summarize gene counts by resistance class."""
    exploded = df.assign(RESISTANCE=df['RESISTANCE'].str.split(';')).explode('RESISTANCE')
    summary = (
        exploded.groupby('RESISTANCE')
        .agg(
            Gene_Count=('GENE', 'nunique'),
            Example_Genes=('GENE', lambda x: ', '.join(x.unique()[:3])),
        )
        .reset_index()
    )
    return summary.sort_values('Gene_Count', ascending=False)


# ------------------------------------------------------------
# 3. Top genes by abundance
# ------------------------------------------------------------
def summarize_top_genes(df, top_n=10):
    """List top genes by %identity * %coverage."""
    df['Score'] = df['%IDENTITY'] * df['%COVERAGE']
    top_genes = (
        df.sort_values('Score', ascending=False)
        [['GENE', '%COVERAGE', '%IDENTITY', 'PRODUCT', 'RESISTANCE', 'name']]
        .head(top_n)
    )
    return top_genes


# ------------------------------------------------------------
# 4. Visualizations
# ------------------------------------------------------------
def plot_resistance_classes(summary, outfile='amr_class_distribution.png'):
    """Pie chart of resistance classes."""
    plt.figure(figsize=(6, 6))
    plt.pie(
        summary['Gene_Count'],
        labels=summary['RESISTANCE'],
        autopct='%1.1f%%',
        startangle=140,
    )
    plt.title('AMR Genes by Resistance Class')
    plt.tight_layout()
    plt.savefig(outfile, dpi=300)
    plt.close()


def plot_identity_coverage(df, outfile='identity_vs_coverage.png'):
    """Scatter plot of %identity vs %coverage."""
    plt.figure(figsize=(7, 5))
    sns.scatterplot(
        data=df,
        x='%COVERAGE',
        y='%IDENTITY',
        hue='RESISTANCE',
        alpha=0.7,
        s=100
    )
    plt.title('Identity vs Coverage of AMR Genes')
    plt.xlabel('% Coverage')
    plt.ylabel('% Identity')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(outfile, dpi=300)
    plt.close()


# ------------------------------------------------------------
# 5. Generate Report
# ------------------------------------------------------------
def generate_report(filepath):
    df = load_amr_table(filepath)

    print("\n📊 SUMMARY: AMR Genes by Resistance Class")
    summary = summarize_by_class(df)
    print(summary.to_string(index=False))

    print("\n🔥 TOP 5 AMR Genes by Abundance (Identity × Coverage)")
    top_genes = summarize_top_genes(df, top_n=5)
    print(top_genes.to_string(index=False))

    # Visualizations
    plot_resistance_classes(summary)
    plot_identity_coverage(df)

    print("\n✅ Plots saved: 'amr_class_distribution.png' and 'identity_vs_coverage.png'")
    print("✅ Report generation complete.")


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate AMR summary report from TSV file")
    parser.add_argument("--input", help="Path to AMR result table (TSV)")
    args = parser.parse_args()

    generate_report(args.input)