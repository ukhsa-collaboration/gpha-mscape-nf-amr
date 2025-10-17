#!/usr/bin/env nextflow
nextflow.enable.dsl=2
process GENERATE_SAMPLESHEET{
    tag "${climb_id}"
    // Onyx and Onyx Helper
    container 'ghcr.io/ukhsa-collaboration/gpha-mscape-sample-qc:latest' // TODO: needs changing!
    // publishDir "${params.output}/abricate", mode: 'copy'

    // 1. Extract Read IDs from Abricate output file
    input:
    tuple val("${id}_samplesheet.tsv"), val("${id_type}"), val("${columns}"),

    output:
    path("${sample_sheet}.tsv")
    
    script:
    """
    echo $climb_id
    generate_onyx_samplesheet.py -i ${id} -t ${id_type} -c ${columns} -o ${sample_sheet}.tsv
    """
}