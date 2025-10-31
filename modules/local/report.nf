#!/usr/bin/env nextflow

process SAMPLE_REPORT{
    tag "${climb_id}"
    container 'community.wave.seqera.io/library/pip_bio_matplotlib_pandas_plotly:754f7b3f0d8204e4'
    publishDir "${params.output}/${climb_id}/${amr_tool}_report/", mode: 'copy'

    // 1. Extract Read IDs from Abricate output file
    input:
    tuple  val(climb_id), path(amr_table), val(amr_tool), val(email)

    output:
    tuple file("${climb_id}_sample_amr_report.html"),
        file("resistance_grouped_barplot.png"),
        file("gene_species_sequence_heatmap.png"),
        file("res_counts_by_species.csv"),
        file("gene_species_sequence_counts.csv"), emit: report_ch
    
    script:
    """
    sample_report.py \\
        -i ${amr_table} \\
        -o ./ \\
        -e ${email}
    """
}