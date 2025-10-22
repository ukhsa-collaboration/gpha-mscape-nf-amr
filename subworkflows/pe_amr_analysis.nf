#!/usr/bin/env nextflow

include { ONYX_UPLOAD     } from "../modules/local/onyx_upload"

workflow PE_AMR_ANALYSIS {
    take:
    paired_end_ch

    main:
    paired_end_ch
        .map{ climb_id, kraken_assignments, kraken_report, fastq1, fastq2  ->
                tuple( climb_id, "${params.output}/${climb_id}", 'Failed', 'None')
        }
        .set{ failed_ch }
        ONYX_UPLOAD( failed_ch )
        }

}