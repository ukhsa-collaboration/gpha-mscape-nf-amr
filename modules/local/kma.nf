#!/usr/bin/env nextflow
process RUN_KMA_SR{
    tag "${climb_id}"
    label 'process_medium'
    container 'community.wave.seqera.io/library/kma:1.6.8--8337f908ec0ef88a'
    publishDir "${params.output}/${climb_id}/kma", mode: 'copy'
    maxForks 4

    
    errorStrategy { task.exitStatus = 95 ? "ignore" : "retry" }

    input:
        tuple val(climb_id),  path(kraken_assignments), path(kraken_report), path(fastq1)
        path(card_kma_db)

    output:
    tuple val(climb_id), path("kma_results.res"), path("kma_results.fsa"), path("kma_results.frag.gz"), path("kma_results.aln"), emit: kma_out
    tuple val(climb_id), path(kraken_assignments), path(kraken_report), path("mapping_info.tsv"), emit: kma_mapping
        
    script:
    """
    kma \\
         -i ${fastq1} \\
         -o kma_results \\
         -t_db ${card_kma_db}/nucleotide_fasta_protein_homolog_model_kma_db \\
         -ont \\
         -reassign

    gunzip kma_results.frag.gz
    echo "read\t#_equally_well_mapping_templates\tmapping_score\ttemplate_start_position\ttemplate_end_position\tchoosen_template\tread_id" >mapping_info.tsv
    cat kma_results.frag >>mapping_info.tsv
    gzip kma_results.frag
    """
}

process RUN_KMA_PR{
    tag "${climb_id}"
    label 'process_medium'
    container 'community.wave.seqera.io/library/kma:1.6.8--8337f908ec0ef88a'
    publishDir "${params.output}/${climb_id}/kma", mode: 'copy'
    maxForks 4

    
    errorStrategy { task.exitStatus = 95 ? "ignore" : "retry" }

    input:
        tuple val(climb_id),  path(kraken_assignments), path(kraken_report), path(fastq1)
        path(card_kma_db)

    output:
    tuple val(climb_id), path("kma_results.res"), path("kma_results.fsa"), path("kma_results.frag.gz"), path("kma_results.aln"), emit: kma_out
    tuple val(climb_id), path(kraken_assignments), path(kraken_report), path("mapping_info.tsv"), emit: kma_mapping
        
    script:
    """
    kma \\
         -i ${fastq1} \\
         -o kma_results \\
         -t_db ${card_kma_db}/nucleotide_fasta_protein_homolog_model_kma_db \\
         -ont \\
         -reassign

    gunzip kma_results.frag.gz
    echo "read\t#_equally_well_mapping_templates\tmapping_score\ttemplate_start_position\ttemplate_end_position\tchoosen_template\tread_id" >mapping_info.tsv
    cat kma_results.frag >>mapping_info.tsv
    gzip kma_results.frag
    """
}