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
        def climb_id = row.CLIMB-ID
        def fastq1 = row.human_filtered_reads_1
        def fastq2 = row.human_filtered_reads_2
        return tuple(climb_id, fastq1, fastq2)
    }
    .set { ch_samplesheet }

workflow {
    // handle input parameters
    log.info "Samplesheet: ${params.samplesheet}"
    log.info "Output directory: ${params.output}"
    log.info "Number of CPUs (Max): ${params.max_cpus}"
    // Run subworkflows
    AMR_ANALYSIS(ch_samplesheet)
    // run_abricate(params.climb_id, params.output)

}