#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process ABRICATE{
    tag "${climb_id}"
    container 'community.wave.seqera.io/library/pip_s3cmd:04c678b1462475bc'
    
    input:
    tuple val(climb_id, fastq1, fastq2)

    script:
    """
    echo "CLIMB-ID: $climbd_id"
    echo "FASTQ 1: $fastq1"
    echo "FASTQ 2: $fastq2"
    """

}