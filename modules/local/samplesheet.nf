#!/usr/bin/env nextflow
nextflow.enable.dsl=2
process GENERATE_SAMPLESHEET{
    tag "${unique_id}"
    // Onyx and Onyx Helper
    container 'ghcr.io/ukhsa-collaboration/gpha-mscape-sample-qc@sha256:d53d97b3903c953794a1ba18b293abad972d10146603c01b0aa21e1a5c047ece' // TODO: needs changing!

    // 1. Extract Read IDs from Abricate output file
    input:
    tuple val(unique_id), val(id_type), val(columns)

    output:
    path("${samplesheet}.tsv")
    
    script:
    """
    echo $unique_id
    generate_onyx_samplesheet.py -i ${unique_id} -t ${id_type} -c ${columns} -o ${unique_id}_samplesheet.tsv
    """
}