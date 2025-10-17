#!/usr/bin/env nextflow
nextflow.enable.dsl=2
process GENERATE_SAMPLESHEET{
    tag "${climb_id}"
    container 'community.wave.seqera.io/library/pip_pandas:40d2e76c16c136f0'
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