#!/usr/bin/env nextflow
process GENERATE_REPORT{
    tag "${climb_id}"
    publishDir "${params.output}/${climb_id}/", mode: 'copy'

    // Onyx and Onyx Helper
    container 'community.wave.seqera.io/library/pip_bio_matplotlib_numpy_pruned:489abe68b90e0d56'

    input:
    tuple  val(climb_id), path(abricate_taxa_out), val(tool), val(email)

    // output:
    path("res_counts_by_species.csv"),
    path("resistance_grouped_barplot.png"),
    path("gene_species_sequence_counts.csv"),
    path("gene_species_sequence_heatmap.png"),
    path("${unique_id}_sample_amr_report.html"), emit: html_report

    
    script:
    """
    sample_report.py \\
        -i '${abricate_taxa_out}' \\
        -e '${email}' \\
        -o ./
    """
}