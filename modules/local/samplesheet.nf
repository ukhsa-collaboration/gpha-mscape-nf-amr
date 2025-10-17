#!/usr/bin/env nextflow
nextflow.enable.dsl=2
process GENERATE_SAMPLESHEET{
    tag "${unique_id}"
    // Onyx and Onyx Helper
    container 'ghcr.io/ukhsa-collaboration/gpha-mscape-onyx-analysis-helper:pr-2' // TODO: needs changing!

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