#!/usr/bin/env nextflow
nextflow.enable.dsl=2
process GENERATE_SAMPLESHEET{
    tag "${unique_id}"
    // Onyx and Onyx Helper
    container 'http://ghcr.io/ukhsa-collaboration/gpha-mscape-onyx-analysis-helperhttp://ghcr.io/ukhsa-collaboration/gpha-mscape-onyx-analysis-helper'

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