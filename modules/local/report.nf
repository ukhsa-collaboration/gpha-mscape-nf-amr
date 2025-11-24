#!/usr/bin/env nextflow
process GENERATE_REPORT{
    tag "${climb_id}"
    publishDir "${params.output}/${climb_id}/", mode: 'copy'

    // Onyx and Onyx Helper
    container 'community.wave.seqera.io/library/pip_bio_matplotlib_numpy_pruned:489abe68b90e0d56'

    input:
    tuple  val(climb_id), path(abricate_taxa_out), val(tool), val(email)

    output:
    tuple path("res_counts_by_species_${dt}.csv"),
        path("resistance_grouped_barplot_${dt}.png"),
        path("gene_species_sequence_counts_${dt}.csv"),
        path("gene_species_sequence_heatmap_${dt}.png"),
        path("${climb_id}_sample_amr_report_${dt}.html")

    
    script:
    """
    dt=$(date +"%Y%m%d%H%M%S")

    sample_report.py \\
        -i '${abricate_taxa_out}' \\
        -e '${email}' \\
        -o ./
    
    mv res_counts_by_species.csv res_counts_by_species_\${dt}.csv
    mv resistance_grouped_barplot.png resistance_grouped_barplot_\${dt}.png
    mv gene_species_sequence_counts.csv gene_species_sequence_counts_\${dt}.csv
    mv gene_species_sequence_heatmap.png gene_species_sequence_heatmap_\${dt}.png
    mv ${climb_id}_sample_amr_report.html ${climb_id}_sample_amr_report_\${dt}.html

    """
}