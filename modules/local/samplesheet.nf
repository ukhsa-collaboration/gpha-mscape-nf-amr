#!/usr/bin/env nextflow
nextflow.enable.dsl=2
process GENERATE_SAMPLESHEET{
    tag "${unique_id}"
    // Onyx and Onyx Helper
    container 'ghcr.io/ukhsa-collaboration/gpha-mscape-onyx-analysis-helper@sha256:ad7e2054e3a33121c51931446b203a8542d68eba2b9079b75a4f45a65d5123f2' // TODO: needs changing!

    // 1. Extract Read IDs from Abricate output file
    input:
    tuple val(unique_id), val(id_type), val(columns)

    // output:
    // path("${unique_id}_samplesheet.tsv")
    
    script:
    """
    echo $unique_id
    generate_onyx_samplesheet.py -i ${unique_id} -t ${id_type} -c ${columns} -o ${unique_id}_samplesheet.tsv
    """
}