#!/usr/bin/env nextflow
// nextflow.enable.dsl=2

// TODO: add include to read in subworkflows
include { AMR_ANALYSIS } from './subworkflows/amr_analysis'
include {ABRICATE} from "./modules/abricate"

if (!params.samplesheet) {
    error "Please provide a samplesheet with --samplesheet"
}

// Define a channel from the sample sheet
samples = Channel
    .fromPath(params.samplesheet)
    .splitCsv(header: true)
    .map { row ->
        def climb_id = row.climb_id
        def fastq1 = row.human_filtered_reads_1
        def fastq2 = row.containsKey('human_filtered_reads_2') ? row.human_filtered_reads_2 : null
        return fastq2 ? tuple(climb_id, fastq1, fastq2) : tuple(climb_id, fastq1)
    }
    .branch{ v ->
        paired_end: v.size() == 3 
        single_end: v.size() == 2 
    }
    // Assign the separated channels
    .set { ch_fastqs }  // Define separate channels

workflow {
    // handle input parameters
    log.info "Samplesheet: ${params.samplesheet}"
    log.info "Output directory: ${params.output}"
    log.info "Number of CPUs (Max): ${params.max_cpus}"
    
    // Run subworkflows
    ABRICATE(ch_fastqs.single_end)
    // run_abricate(params.climb_id, params.output)

}