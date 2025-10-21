#!/usr/bin/env nextflow
nextflow.enable.dsl=2
process ONYX_UPLOAD{
    tag "${unique_id}"
    publishDir "${params.output}/", mode: 'copy', pattern: "*.csv"

    // Onyx and Onyx Helper
    container 'ghcr.io/ukhsa-collaboration/gpha-mscape-onyx-analysis-helper:pr-2'

    input:
    tuple val(unique_id), path(abricate_taxa_out)

    output:
    path("${unique_id}_amr_analysis_fields.json"), emit: onyx_json
    
    script:
    """
    onyx_upload.py \\
        -i C-${unique_id} \\
        -t ${abricate_taxa_out} \\
        -o ./ \\
        --pipeline_status Annotated \\
        --amr_params \"{'db': '${params.arg_abricate_db}', 'minid': '${params.arg_abricate_minid}', 'mincov': '${params.arg_abricate_mincov}'}\" \\
        -s mscape \\
        --store-onyx
 
    """
}