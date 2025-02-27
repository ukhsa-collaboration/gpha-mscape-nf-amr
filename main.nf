#!/usr/bin/env nextflow
// nextflow.enable.dsl=2

// TODO: add include to read in subworkflows
include { get_sampledata } from './subworkflows/get_sampledata'

if (!params.samplesheet) {
    error "Please provide a samplesheet with --samplesheet"
}

Channel
    .fromPath(params.samplesheet)
    .splitCsv(header: true)
    .map { row =>
        def climb_id = row.CLIMB-ID
        return value(climb_id)
    }
    .set { ch_samplesheet }

workflow {
    // handle input parameters
    log.info "Samplesheet: ${params.samplesheet}"
    log.info "Output directory: ${params.output}"
    log.info "Number of CPUs (Max): ${params.max_cpus}"
    // Run subworkflows
    get_sampledata(ch_samplesheet)
    // run_abricate(params.climb_id, params.output)

}