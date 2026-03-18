#!/usr/bin/env nextflow
process TAXAPLEASE_REFS{
    tag "TaxaPlease"
    label 'process_medium'
    container 'ghcr.io/ukhsa-collaboration/gpha-mscape-taxaplease:2.1.1'
    publishDir "${params.output}/", mode: 'copy'
    maxForks 4


    input:
        path(taxaplease_db)
        path(taxa_of_interest)
  
    output:
        path("taxaplease_reference_table.tsv")
        
    script:
    """
    get_taxa_of_interest.py \
        -db ${taxaplease_db} \
        --reference_taxa_list \
        ${taxa_of_interest} \
        --output_dir ./ \
        --log-level INFO
    """
}