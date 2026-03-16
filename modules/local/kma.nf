#!/usr/bin/env nextflow
process RUN_KMA{
    tag "${climb_id}"
    label 'process_medium'
    container 'community.wave.seqera.io/library/kma:1.6.8--8337f908ec0ef88a'
    publishDir "${params.output}/${climb_id}/kma", mode: 'copy'
    // maxForks 4

    
    errorStrategy { task.exitStatus = 95 ? "ignore" : "retry" }

    input:
        tuple val(climb_id),  path(kraken_assignments), path(kraken_report), path(fastq1)
        path(card_kma_db)

    output:
    tuple val(climb_id), path("*.res"), path("*.fsa"), path("*.frag.gz"), path("*.aln"), emit: kma_out
        
    script:
    """
    kma \\
         -i ${fastq1} \\
         -o kma_results \\
         -t_db ${card_kma_db}/nucleotide_fasta_protein_homolog_model_kma_db \\
         -ont \\
         -reassign
    
    """
}