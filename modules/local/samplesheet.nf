#!/usr/bin/env nextflow
nextflow.enable.dsl=2
process GENERATE_SAMPLESHEET{
    tag "${climb_id}"
    // Onyx and Onyx Helper
    container 'ghcr.io/ukhsa-collaboration/gpha-mscape-sample-qc:latest' // TODO: needs changing!

    // 1. Extract Read IDs from Abricate output file
    input:
    tuple val(unique_id), val(id_type), val(columns)

    output:
    path("${samplesheet}.tsv")
    
    script:
    """
    echo $climb_id
    generate_onyx_samplesheet.py -i ${unique_id} -t ${id_type} -c ${columns} -o ${samplesheet}.tsv
    """
}