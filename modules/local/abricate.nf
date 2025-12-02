#!/usr/bin/env nextflow
process RUN_ABRICATE{
    tag "${climb_id}"
    label 'process_medium'
    container 'community.wave.seqera.io/library/abricate:1.0.1--0fd3388e9b365eeb'
    maxForks 4

    input:
    tuple val(climb_id),  path(kraken_assignments), path(kraken_report), path(fastq1)

    output:
    tuple  val(climb_id),  path(kraken_assignments), path(kraken_report), path("abricate_out.tsv"), emit: abricate_results

    script:
    """
    abricate \\
        --db ${params.arg_abricate_db} \\
        --minid ${params.arg_abricate_minid} \\
        --mincov ${params.arg_abricate_mincov} \\
        --threads $task.cpus \\
        ${fastq1} > abricate_out.tsv
    """
}