#!/usr/bin/env nextflow

nextflow.enable.dsl=2

// Step 1: Fetch FASTQ files from S3
process FETCH_FASTQ {
    label "process_low"

    container 'biocontainers/python:3.10.4'

    output:
    path "${params.output}/fastq_files/*"

    script:
    """
    mkdir -p ${params.output}/fastq_files
    s3cmd get s3://mscape-published-read-fractions/${params.climb_id}/${params.climb_id}.human_filtered.fastq.gz ${params.output}/fastq_files/
    """
}

// // Step 2: Run Abricate on each FASTQ file
// process RUN_ABRICATE {
//     input:
//     path fastq_file from FETCH_FASTQ.out

//     output:
//     path "${params.output}/abricate_results.txt"

//     script:
//     """
//     abricate --db resfinder --mincov 50 --threads 4 ${fastq_file} > ${params.output}/abricate_results.txt
//     """
// }

workflow run_abricate {
    take:
        climb_id
        output
    main:
        log.info "Running Abricate subworkflow"
        log.info "CLIMB ID file: ${params.climb_id}"
        log.info "Output directory: ${params.output}"
        FETCH_FASTQ()
    //     RUN_ABRICATE(FETCH_FASTQ.out)
    
    // emit:
        
}