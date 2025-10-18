#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process RUN_ABRICATE_DB{
    tag "${climb_id}"
    container 'community.wave.seqera.io/library/abricate:1.0.1--0fd3388e9b365eeb'
    
    input:
    tuple val(climb_id), path(kraken_assignments), path(kraken_report), path(fastq1), val(db)

    output:
    tuple  val(climb_id), path(kraken_assignments), path(kraken_report),  path("abricate_${db}_out.tsv"), emit: abricate_results

    script:
    """
    abricate --quiet --mincov 90 --db ${db} ${fastq1} > abricate_${db}_out.tsv
    """
}