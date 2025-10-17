#!/usr/bin/env nextflow
nextflow.enable.dsl=2

// TODO: add include to read in subworkflows
include { AMR_ANALYSIS } from './subworkflows/amr_analysis'
include { GENERATE_SAMPLESHEET } from './modules/local/samplesheet'


workflow {
    // TODO: Take either a sample sheet or a climb-id
    unique_id = "${params.unique_id}"

    if (unique_id != "null"){
        log.info "Sample ID: ${unique_id}"
        log.info "Onyx Fields: ${params.samplesheet_columns}"
        sample_ch = Channel.of( 
            tuple (unique_id, "${params.samplesheet_columns}" )
        )
        GENERATE_SAMPLESHEET(sample_ch)
        // samplesheet = file("${params.output}/${unique_id}_samplesheet.tsv", type:"file", checkIfExists: true)
    }
    else if (params.samplesheet) {
        samplesheet = file(params.samplesheet, type:"file", checkIfExists: true)
        log.info "Samplesheet: ${samplesheet}"
        samples = Channel
            
    }
    else{
        exit(1, "Please specify either --unique_id or --samplesheet")
    }

    // // Parse samplesheet
    // samples = Channel
    //         .fromPath(samplesheet)
    //         .splitCsv(header: true)
    //         .map { row ->
    //             def climb_id = row.climb_id
    //             def taxon_reports = row.taxon_reports
    //             def fastq1 = row.human_filtered_reads_1
    //             def fastq2 = row.containsKey('human_filtered_reads_2') ? row.human_filtered_reads_2 : null
    //             return fastq2 ? tuple(climb_id, taxon_reports, fastq1, fastq2) : tuple(climb_id, taxon_reports, fastq1)
    //         }
    //         .branch{ v ->
    //             paired_end: v.size() == 4
    //             single_end: v.size() == 3
    //         }
    //         .set { ch_fastqs }  

    // samples.out.view()
    // // // handle input parameters
    // log.info "Output directory: ${params.output}"
    // log.info "Number of CPUs (Max): ${params.max_cpus}"
    
    // // Run subworkflows
    // AMR_ANALYSIS(ch_fastqs.single_end)

}