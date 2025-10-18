#!/usr/bin/env nextflow
nextflow.enable.dsl=2

include { GENERATE_SAMPLESHEET } from './modules/local/samplesheet'
// include { AMR_ANALYSIS } from './subworkflows/amr_analysis'


workflow {
    // TODO: Take either a sample sheet or a climb-id
    if (params.samplesheet){
        log.info "Samplesheet input: ${params.samplesheet}"
        samplesheet_ch = channel.fromPath(params.samplesheet)
    } else if (params.unique_id) {
        log.info "Unique ID input: ${params.unique_id}"
        sample_ch = Channel.of(tuple (params.unique_id, params.samplesheet_columns))
        samplesheet_ch = GENERATE_SAMPLESHEET(sample_ch).samplesheet
    }
    else{
        exit(1, "Please specify either --unique_id or --samplesheet")
    }
    samples = samplesheet_ch.splitCsv(header: true, quote: '\"')
        .map { row ->
            def climb_id = row.climb_id
            def taxon_report_dir = row.taxon_reports
            def fastq1 = row.human_filtered_reads_1
            def fastq2 = row.containsKey('human_filtered_reads_2') ? row.human_filtered_reads_2 : null
            return fastq2 ? tuple(climb_id, taxon_report_dir, fastq1, fastq2) : tuple(climb_id, taxon_report_dir, fastq1)
        }
        .branch{ v ->
            paired_end: v.size() == 4
            single_end: v.size() == 3
        // Assign the separated channels
        }
        .set { ch_fastqs }  // Define separate channels
    ch_fastqs.single_end.view()
    // ch_fastqs.view()
}   

    // // // handle input parameters
    // log.info "Output directory: ${params.output}"
    // log.info "Number of CPUs (Max): ${params.max_cpus}"
    
    // // Run subworkflows
    // AMR_ANALYSIS(ch_fastqs.single_end)

// }