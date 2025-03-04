#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process ABRICATE{
    tag "${climb_id}"
    container 'community.wave.seqera.io/library/abricate:1.0.1--0fd3388e9b365eeb'
    
    input:
    tuple val(climb_id), path(fastq1)

    script:
    """
    abricate --mincov 90 --db vfdb $fastq1 > out_file
    """
    // abricate --quiet --mincov 90 --db vfdb $fastq1 > out_file
}