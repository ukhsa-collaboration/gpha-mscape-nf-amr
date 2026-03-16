#!/usr/bin/env nextflow
process RUN_KMA{
    tag "${climb_id}"
    label 'process_medium'
    container 'community.wave.seqera.io/library/kma:1.6.8--8337f908ec0ef88a'
    publishDir "${params.output}/${climb_id}/kma", mode: 'copy'
    maxForks 4

    input:
        tuple val(climb_id),  path(kraken_assignments), path(kraken_report), path(fastq1)
        path(card_kma_db)

    output:
        tuple path("*tsv"), path("*.res"), path("*.fsa"), path("*.frag.gz"), path("*.aln"), emit: kma_out 
    // Other minisnpfinder output files: path(class), path(accession), path(dna_class), path(dna_accession), path(*.prot.hits.txt), path(*.prot.input.tsv), path(*.res), path(*.frag.gz), path((*.dna.input.tsv),

            
            

    script:
    """
    kma \\
         -i ${fastq1} \\
         -o kma_card_out/nucleotide_fasta_protein_homolog_model_kma_db \\
         -t_db ${kma_card_db} \\
         -ont \\
         -reassign;
    
    cp kma_card_out.res kma_card_out.res.tsv
    """
}