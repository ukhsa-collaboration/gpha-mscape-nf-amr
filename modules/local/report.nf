#!/usr/bin/env nextflow

process SAMPLE_REPORT{
    tag "${climb_id}"
    container 'community.wave.seqera.io/library/pip_bio_matplotlib_pandas_plotly:754f7b3f0d8204e4'
    publishDir "${params.output}/${climb_id}/${tool}_report/", mode: 'copy'

    // 1. Extract Read IDs from Abricate output file
    input:
    tuple  val(climb_id), path(amr_table), val(amr_tool), val(email)

    output:
    tuple  val(climb_id), path(amr_table), val(amr_tool), val(email)
    
    script:
    """
    sample_report.py \\
        -i ${amr_table} \\
        -o ./ \\
        -e ${email}
    """
}