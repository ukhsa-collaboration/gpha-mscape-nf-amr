#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process GZ_TO_FASTQ{
    tag "${climb_id}"
    container 'community.wave.seqera.io/library/pip_gunzip:1ea8ddc0b75355cd'

    input:
    tuple val(climb_id), path(kraken_assignments), path(kraken_report), path(fastq1)

    output:
    tuple val(climb_id), path(kraken_assignments), path(kraken_report), path("${climb_id}.fastq")

    script:
    """
    gunzip -c "${fastq1}" > "${climb_id}.fastq"
    """


}
