#!/usr/bin/env nextflow
process GENERATE_REPORT{
    tag "${unique_id}"
    // publishDir "${params.output}/${unique_id}/", mode: 'copy', pattern: "*.csv"

    // Onyx and Onyx Helper
    container 'community.wave.seqera.io/library/pip_bio_matplotlib_numpy_pruned:489abe68b90e0d56'

    input:
    tuple  val(climb_id), path(abricate_taxa_out), val(tool), val(email)

    // output:
    // path("${unique_id}_samplesheet.csv"), emit: samplesheet
    
    script:
    """
    sample_report.py \\
        -i '${abricate_taxa_out}' \\
        -e '${email}' \\
        -o ./
    """
}