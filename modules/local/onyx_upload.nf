#!/usr/bin/env nextflow
nextflow.enable.dsl=2
process ONYX_UPLOAD{
    tag "${unique_id}"
    publishDir "${params.output}/", mode: 'copy', pattern: "*.json"

    // Onyx and Onyx Helper
    container 'ghcr.io/ukhsa-collaboration/gpha-mscape-onyx-analysis-helper:pr-2'

    input:
    tuple val(unique_id), path(abricate_taxa_out)

    output:
    path("${unique_id}_amr_analysis_fields.json"), emit: onyx_json
    
    script:
    """
    onyx_upload.py \\
        -i ${unique_id} \\
        -t ${abricate_taxa_out} \\
        -o ./ \\
        --pipeline_status Annotated \\
        --amr_params \"${params.arg_abricate_db},${params.arg_abricate_minid},${params.arg_abricate_mincov}\" \\
        --pipeline_info \"${workflow.manifest.name},${workflow.manifest.version},${workflow.manifest.homePage}\"
        -s mscape \\
        --store-onyx
 
    """
}