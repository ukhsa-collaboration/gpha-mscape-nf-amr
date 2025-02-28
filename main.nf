#!/usr/bin/env nextflow
// nextflow.enable.dsl=2

// TODO: add include to read in subworkflows
include { AMR_ANALYSIS } from './subworkflows/amr_analysis'

if (!params.samplesheet) {
    error "Please provide a samplesheet with --samplesheet"
}

Channel
    .fromPath(params.samplesheet)
    .splitCsv(header: true)
    .map { row ->
        def climb_id = row.climb_id
        def fastq1 = row.human_filtered_reads_1
        def fastq2 = row.containsKey('human_filtered_reads_2') ? row.human_filtered_reads_2 : null // set to null if empty
        println "DEBUG: sample_id=${climb_id}, fastq1=${fastq1}, fastq2=${fastq2}"
        return fastq2 ? [climb_id, fastq1, fastq2] : [climb_id, fastq1]
    }
    .branch(
        paired_end: { it && it.size() == 3 },  
        single_end: { it && it.size() == 2 }
    )
    .set { paired_end, single_end }

// // View the separated channels
// paired_end_samples.view { it -> "Paired-end: ${it}" }
// single_end_samples.view { it -> "Single-end: ${it}" }

// workflow {
//     // handle input parameters
//     log.info "Samplesheet: ${params.samplesheet}"
//     log.info "Output directory: ${params.output}"
//     log.info "Number of CPUs (Max): ${params.max_cpus}"
//     // Run subworkflows
//     AMR_ANALYSIS(single_end_samples)
//     // run_abricate(params.climb_id, params.output)

// }