#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process ABRICATE{
    tag "${climb_id}"
    container 'community.wave.seqera.io/library/abricate:1.0.1--0fd3388e9b365eeb'
    
    publishDir 'abricate'

    input:
    tuple val(climb_id), path(fastq1)

    output:
    val(climb_id) into abricate_ch
    //, path '${climb_id}.abricate.txt'

    script:
    """
    echo $climb_id
    """

 
    // script:
    // """
    // abricate --quiet --mincov 90 --db vfdb '${fastq1}' > '${climb_id}.abricate.txt'
    // """
}