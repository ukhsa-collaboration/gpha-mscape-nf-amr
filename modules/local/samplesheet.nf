#!/usr/bin/env nextflow
nextflow.enable.dsl=2
process GENERATE_SAMPLESHEET{
    tag "${unique_id}"
    publishDir "${params.output}/", mode: 'copy', pattern: "*.csv"

    // Onyx and Onyx Helper
    container 'ghcr.io/ukhsa-collaboration/onyx-analysis-helper@sha256:80429e36f92be75033432d601739c554f6011a4b9dde9c28ad6e562e629b2400'

    input:
    tuple val(unique_id), val(columns)

    output:
    path("${unique_id}_samplesheet.csv"), emit: samplesheet
    
    script:
    """
    echo $unique_id
    generate_onyx_samplesheet.py \\
        -i '${unique_id}' \\
        -c '${columns}' \\
        -o ${unique_id}_samplesheet.csv
    """
}