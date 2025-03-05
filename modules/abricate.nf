#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process GZ_TO_FASTQ{
    input:
    tuple val(climb_id), path(fastq1)

    output:
   tuple val(climb_id), path(fastq)

    script:
    """
    gunzip -c "${fastq_gz}" > "${fastq}"
    """


}

process ABRICATE{
    // tag "${climb_id}"
    container 'community.wave.seqera.io/library/abricate:1.0.1--0fd3388e9b365eeb'
    
    // publishDir 'abricate'

    input:
    tuple val(climb_id), path(fastq1)

    output:
    tuple  val(climb_id), path('abricate_out.txt'), emit: abricate

    script:
    """
    tar -xf '${fastq1}' 
    abricate --quiet --db ncbi '${fastq1}' > 'abricate_out.txt'
    """
}