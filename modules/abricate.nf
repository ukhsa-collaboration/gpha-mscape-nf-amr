#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process ABRICATE{
    tag "${climb_id}"
    container 'community.wave.seqera.io/library/abricate:1.0.1--0fd3388e9b365eeb'
    
    input:
    tuple val(climb_id), path(taxon_report_dir), path(fastq1)

    output:
    tuple  val(climb_id), path(taxon_report_dir), path('abricate_out.txt')

    script:
    """
    abricate --quiet --mincov 90 --db card '${fastq1}' > 'abricate_out.txt'
    """
}