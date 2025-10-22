#!/usr/bin/env nextflow
nextflow.enable.dsl=2
process ONYX_UPLOAD{
    tag "${unique_id}"
    publishDir "${params.output}/${unique_id}", mode: 'copy', pattern: "*.json"

    // Onyx and Onyx Helper
    container 'ghcr.io/ukhsa-collaboration/gpha-mscape-onyx-analysis-helper:pr-2'

    input:
    tuple val(unique_id), path(abricate_taxa_out), val(pipeline_status), val(tool)

    output:
    path("${unique_id}_amr_analysis_fields.json"), emit: onyx_json
    
    script:
    """
    //  For samples failed samples, need to create an empty directory
    mkdir -p "${params.output}/${unique_id}"
    
    onyx_upload.py \\
        -i ${unique_id} \\
        -f ${params.output}/${unique_id} \\
        -o ./ \\
        --pipeline_status ${pipeline_status} \\
        --amr_params \"tool:${tool},db:${params.arg_abricate_db},minid:${params.arg_abricate_minid},mincov:${params.arg_abricate_mincov}\" \\
        --pipeline_info \"name:${workflow.manifest.name},version:${workflow.manifest.version},homePage:${workflow.manifest.homePage}\" \\
        -s mscape \\
        --store-onyx
 
    """
}