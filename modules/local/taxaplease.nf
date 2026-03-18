#!/usr/bin/env nextflow
process RUN_TAXAPLEASE{
    tag "${climb_id}"
    label 'process_medium'
    container 'ghcr.io/ukhsa-collaboration/gpha-mscape-taxaplease:2.1.1'
    publishDir "${params.output}/${climb_id}/taxaplease", mode: 'copy'
    maxForks 4


    input:
        path(kma_mapping_tsv)
        tuple val(climb_id), path(kraken_assignments), path(kraken_report), path(fastq1)
        path(taxaplease_db)
        path(taxa_of_interest)
  
    output:
        path("taxa_of_interest_taxaplease.tsv")
        
    script:
    """
    get_taxa_of_interest.py \\
         -db ${taxaplease_db} \\
         --reference_taxa_list ${taxa_of_interest} \\  
         --output_dir ./ \\
         --log-level INFO
    """
}