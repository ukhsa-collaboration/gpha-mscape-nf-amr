#!/usr/bin/env nextflow

include { GENERATE_SAMPLESHEET } from './modules/local/samplesheet'
include { SE_AMR_ANALYSIS      } from './subworkflows/se_amr_analysis'
include { ONYX_UPLOAD          } from "../modules/local/onyx_upload"


workflow {
    // Handle either samplesheet or climb id
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
    // Split csv into channgels
    samples = samplesheet_ch.splitCsv(header: true, quote: '\"')
        .map { row ->
            def climb_id = row.climb_id
            // def taxon_report_dir = row.taxon_reports
            def kraken_assignments = file("${row.taxon_reports}/*_PlusPF.kraken_assignments.tsv")
            def kraken_report = file("${row.taxon_reports}/*_PlusPF.kraken_report.json")
            def fastq1 = row.human_filtered_reads_1
            def fastq2 = row.containsKey('human_filtered_reads_2') ? row.human_filtered_reads_2 : null
            return fastq2 ? tuple(climb_id, kraken_assignments, kraken_report, fastq1, fastq2) : tuple(climb_id, kraken_assignments, kraken_report, fastq1)
        }
        // Split channel by the number of reads
        .branch{ v -> 
            paired_end: v.size() == 5
            single_end: v.size() == 4
        }
        .set { ch_fastqs } 
    if (ch_fastqs.paired_end){
        ch_fastqs.paired_end
            .map{ val(climb_id), path(kraken_assignments), path(kraken_report), path(fastq1) ->
                    tuple( val(climb_id), '', 'failed', 'None')
             }
             .set{ failed_ch }
             log.info  "${climb_id} is paired-end, analysis not ran."
             ONYX_UPLOAD( failed_ch )
            }
    }
        
    SE_AMR_ANALYSIS(ch_fastqs.single_end)
}