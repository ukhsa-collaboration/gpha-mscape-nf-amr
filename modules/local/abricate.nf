#!/usr/bin/env nextflow
<<<<<<< HEAD
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
=======

nextflow.enable.dsl=2

process RUN_ABRICATE_DB{
    tag "${climb_id}"
    container 'community.wave.seqera.io/library/abricate:1.0.1--0fd3388e9b365eeb'
    
    input:
    tuple val(climb_id), path(fastq1), val(db)

    output:
    tuple  val(climb_id), val(db), path("abricate_${db}_out.tsv"), emit: abricate_results

    script:
    """
    abricate --quiet --mincov 90 --db ${db} ${fastq1} > abricate_${db}_out.tsv
>>>>>>> 711fab109ee3db4cdeed55f12207a26c9e0eb819
    """
}