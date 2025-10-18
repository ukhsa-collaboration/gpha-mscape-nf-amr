#!/usr/bin/env nextflow
nextflow.enable.dsl=2

// TODO: add include to read in subworkflows
// include { AMR_ANALYSIS } from './subworkflows/amr_analysis'
// include { GENERATE_SAMPLESHEET } from './modules/local/samplesheet'


workflow {
    // TODO: Take either a sample sheet or a climb-id
    if (params.samplesheet != 'null'){
        log.info "Samplesheet input"
        // samplesheet_ch = file(params.samplesheet, type:"file", checkIfExists: true)
    } else if (params.unique_id != 'null') {
        log.info "Unique ID input"

    }
}
    // else if (params.unique_id) {
    //     sample_ch = Channel.of(tuple (${params.unique_id}, "${params.samplesheet_columns}"))
    //     samplesheet_channel = GENERATE_SAMPLESHEET(sample_ch)
    // }
    // else{
    //     exit(1, "Please specify either --unique_id or --samplesheet")
    // }
    // if (unique_id != "null"){
    //     log.info "Sample ID: ${unique_id}"
    //     log.info "Onyx Fields: ${params.samplesheet_columns}"
    //     sample_ch = Channel.of( 
    //         tuple (unique_id, "${params.samplesheet_columns}" )
    //     )
    //     GENERATE_SAMPLESHEET(sample_ch)
    //     GENERATE_SAMPLESHEET.out.view()
    //     // samplesheet = file("${params.output}/${unique_id}_samplesheet.tsv", type:"file", checkIfExists: true)
    // }
    // else if (params.samplesheet) {
    //     samplesheet = file(params.samplesheet, type:"file", checkIfExists: true)
    //     log.info "Samplesheet: ${samplesheet}"
    //         // Parse samplesheet
    //     samples = Channel
    //             .fromPath(samplesheet)
    //             .splitCsv(header: true)
    //             .splitCsv(header: true) 
                
    // }
    // else{
    //     exit(1, "Please specify either --unique_id or --samplesheet")
    // }



    // samples.out.view()
    // // // handle input parameters
    // log.info "Output directory: ${params.output}"
    // log.info "Number of CPUs (Max): ${params.max_cpus}"
    
    // // Run subworkflows
    // AMR_ANALYSIS(ch_fastqs.single_end)

// }