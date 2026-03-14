#!/usr/bin/env nextflow
process RUN_METAPOINTFINDER{
    tag "${climb_id}"
    label 'process_medium'
    container 'community.wave.seqera.io/library/metapointfinder:1.01--5d58f0a02b5fc1c8'
    publishDir "${params.output}/${climb_id}/metasnpfinder", mode: 'copy'
    maxForks 4

    input:
        tuple val(climb_id),  path(kraken_assignments), path(kraken_report), path(fastq1)
        path(amrfinder_db)

    output:
        tuple path(*.prot.updated_table_with_scores_and_mutations.tsv), path(*.dna.updated_table_with_scores_and_mutations.tsv), path(*.class.prot.summary.txt), path(*gene.prot.summary.txt), path(*.class.dna.summary.txt), path(*gene.dna.summary.txt), emit: metasnpfinder_out
        tuple path(*.error), path(*.log), emit: metasnpfinder_logs 
        // Other minisnpfinder output files: path(class), path(accession), path(dna_class), path(dna_accession), path(*.prot.hits.txt), path(*.prot.input.tsv), path(*.res), path(*.frag.gz), path((*.dna.input.tsv),

            
            

    script:
    """
    metapointfinder.py \\
        --input ${fastq1} \\
        --db ${amrfinder_db} \\
        --output ./ \\
        --identity ${params.arg_abricate_minid} \\
        --threads ${task.cpus} \\
        --force
    """
}