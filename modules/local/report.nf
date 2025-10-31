#!/usr/bin/env nextflow

process SAMPLE_REPORT{
    tag "${climb_id}"
    container ''
    // publishDir "${params.output}/${climb_id}/${tool}_report/", mode: 'copy'

    // 1. Extract Read IDs from Abricate output file
    input:
    tuple  val(climb_id), path(amr_table), val(amr_tool), val(email)

    // output:
    // tuple  val(climb_id), path("${climb_id}_abricate_taxa_out.tsv"), val(pipeline_status), val(tool)
    
    script:
    """
    sample_report.py \\
        -i ${amr_table} \\
        -o ./ \\
        -e ${email}
    """
}