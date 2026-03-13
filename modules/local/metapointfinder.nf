#!/usr/bin/env nextflow
process RUN_METAPOINTFINDER{
    tag "${climb_id}"
    label 'process_medium'
    container 'community.wave.seqera.io/library/metapointfinder:1.01--5d58f0a02b5fc1c8'
    maxForks 4

    input:
        tuple val(climb_id),  path(kraken_assignments), path(kraken_report), path(fastq1)
        path(amrfinder_db)

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