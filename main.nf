#!/usr/bin/env nextflow
// nextflow.enable.dsl=2

// TODO: add include to read in subworkflows


process checkPath {    
    script:
    """
    echo "Current PATH: \$PATH" >temp.txt
    """
}

// // Print parameters
// log.info "CLIMB ID file: ${params.climb_id}"
// log.info "Output directory: ${params.output}"
// log.info "Number of threads: ${params.threads}"


// workflow {
//     // handle input parameters

//     // Run subworkflows

// }