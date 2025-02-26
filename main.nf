#!/usr/bin/env nextflow
// nextflow.enable.dsl=2

// TODO: add include to read in subworkflows
include { run_abricate } from './subworkflows/run_abricate'

process checkPath {    
    script:
    """
    echo "Current PATH: \$PATH" >temp.txt
    """
}

workflow {
    // handle input parameters
    log.info "CLIMB ID file: ${params.climb_id}"
    log.info "Output directory: ${params.output}"
    log.info "Number of CPUs (Max): ${params.max_cpus}"
    // Run subworkflows
    run_abricate(params.climb_id, params.output)

}