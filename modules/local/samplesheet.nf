#!/usr/bin/env nextflow
nextflow.enable.dsl=2
process GENERATE_SAMPLESHEET{
    tag "${unique_id}"
    publishDir "${params.output}/", mode: 'copy'

    // Onyx and Onyx Helper
    container 'ghcr.io/ukhsa-collaboration/gpha-mscape-onyx-analysis-helper:pr-2'

    input:
    tuple val(unique_id), val(columns)

    output:
    path("${unique_id}_samplesheet.tsv")
    
    script:
    """
    echo $unique_id
    generate_onyx_samplesheet.py -i '${unique_id}' -c '${columns}' -o ${unique_id}_samplesheet.tsv
    """
}