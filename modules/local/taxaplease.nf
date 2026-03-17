#!/usr/bin/env nextflow
process RUN_TAXAPLEASE{
    tag "${climb_id}"
    label 'process_medium'
    container 'ghcr.io/ukhsa-collaboration/gpha-mscape-taxaplease:2.1.1'
    publishDir "${params.output}/${climb_id}/taxaplease", mode: 'copy'
    maxForks 4


    input:
        file(kma_mapping_tsv)
        val(climb_id), path(kraken_assignments), path(kraken_report), path(fastq1)
        path(taxaplease_db)
  
        
    script:
    """
    taxaplease --database ${taxaplease_db} record --record 1337

    """
}