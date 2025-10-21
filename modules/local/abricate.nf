#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process RUN_ABRICATE{
    tag "${climb_id}"
    label 'process_medium'
    container 'community.wave.seqera.io/library/abricate:1.0.1--0fd3388e9b365eeb'

    input:
    tuple val(climb_id),  path(kraken_assignments), path(kraken_report), path(fastq1)

    output:
    tuple  val(climb_id),  path(kraken_assignments), path(kraken_report), path("abricate_out.tsv"), emit: abricate_results

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''

    """
    abricate \\
        $args \\
        --threads $task.cpus \\
        ${fastq1} > abricate_out.tsv
    """
}