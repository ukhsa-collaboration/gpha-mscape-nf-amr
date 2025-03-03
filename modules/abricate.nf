#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process ABRICATE{
    tag "${climb_id}"
    container 'community.wave.seqera.io/library/abricate:1.0.1--0fd3388e9b365eeb'
    
    input:
    tuple val(climb_id), path(fastq1), ${params.output}

    script:
    """
    echo "CLIMB-ID: $climb_id"
    echo "FASTQ 1: $fastq1"
    """

}