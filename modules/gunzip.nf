#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process GZ_TO_FASTQ{
    container 'community.wave.seqera.io/library/abricate:1.0.1--0fd3388e9b365eeb'

    input:
    tuple val(climb_id), path(fastq1)

    output:
    tuple val(climb_id), path(fastq)

    script:
    """
    gunzip -c "${fastq1}" > "${fastq}"
    """


}
