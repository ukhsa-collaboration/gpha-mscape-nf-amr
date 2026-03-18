#!/usr/bin/env nextflow
process KMA_TAXA_LINKAGE{
    tag "${climb_id}"
    label 'process_low'
    container 'community.wave.seqera.io/library/pip_pandas:40d2e76c16c136f0'
    publishDir "${params.output}/${climb_id}/kma", mode: 'copy'

    // 1. Extract Read IDs from Abricate output file
    input:
    tuple val(climb_id), path(kraken_assignments), path(kraken_report)
    kma_mapping_tsv

    script:
    """
    tail -n +2 ${kma_mapping_tsv} | cut -f7 | sort | uniq > unique_amr_reads.txt
    
    grep -Ff unique_amr_reads.txt "${kraken_assignments}" | \\
        cut -f2-3 > read_taxid_assignment.tsv

    retrieve_taxon.py \\
        -t read_taxid_assignment.tsv \\
        -j ${kraken_report} \\
        -a ${kma_mapping_tsv} \\
        -r "read_id" \\
        -o ${climb_id}_kma_taxa_out.tsv
    """



}

process READ_ANALYSIS{
    tag "${climb_id}"
    label 'process_low'
    container 'community.wave.seqera.io/library/pip_pandas:40d2e76c16c136f0'
    publishDir "${params.output}/${climb_id}/", mode: 'copy'

    // 1. Extract Read IDs from Abricate output file
    input:
    tuple val(climb_id), path(kraken_assignments), path(kraken_report), path(abricate_out), val(pipeline_status), val(tool)

    output:
    tuple  val(climb_id), path("${climb_id}_abricate_taxa_out.tsv"), val(pipeline_status), val(tool)
    
    script:
    """
    tail -n +2 ${abricate_out} | cut -f2 | sort | uniq > unique_amr_reads.txt
    
    grep -Ff unique_amr_reads.txt "${kraken_assignments}" | \\
        cut -f2-3 > read_taxid_assignment.tsv

    retrieve_taxon.py \\
        -t read_taxid_assignment.tsv \\
        -j ${kraken_report} \\
        -a ${abricate_out} \\
        -r "SEQUENCE" \\
        -o ${climb_id}_abricate_taxa_out.tsv
    """
}