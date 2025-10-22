#!/usr/bin/env nextflow
nextflow.enable.dsl=2

include { GZ_TO_FASTQ     } from "../modules/local/gunzip"
include { RUN_ABRICATE    } from "../modules/local/abricate"
include { READ_ANALYSIS   } from "../modules/local/taxonomy"
include { ONYX_UPLOAD     } from "../modules/local/onyx_upload"

workflow SE_AMR_ANALYSIS {
    take:
    single_end_ch

    main:
    // 1. Gunzip FASTQ
    // Abricate can use fastq.gz, so just point to files.
    GZ_TO_FASTQ(single_end_ch)
    
    // 2 - Run Abricate
    RUN_ABRICATE(GZ_TO_FASTQ.out)

    // test if any AMR annotations have been made
    RUN_ABRICATE.out.abricate_results
        .branch{
            climb_id,  kraken_assignments, kraken_report, abricate_out ->
            // Skips abricate file if it contains only header, i.e. no AMR annotations have been made
            annotated: abricate_out.readLines().size() > 1
            unannotated: abricate_out.readLines().size() <= 1
        }. set{amr_status}
    // Remap channels
    if (amr_status.unannotated){
        amr_status.unannotated
            .map{ climb_id,  kraken_assignments, kraken_report, abricate_out ->
                tuple( climb_id, abricate_out, 'None')
        }
        .set{ unannotated_ch }
        // 4. Output to Onyx
        // ONYX_UPLOAD(unannotated_ch)
    }

    if (amr_status.annotated){
        amr_status.annotated
            .map{ climb_id,  kraken_assignments, kraken_report, abricate_out ->
                tuple( climb_id, kraken_assignments, kraken_report, abricate_out, 'Annotated')
        }
        .set{ annotated_ch }
        // 3. Extract species IDs for each READ assigned AMR  
        READ_ANALYSIS( annotated_ch )
        // 4. Output to Onyx
        // ONYX_UPLOAD(READ_ANALYSIS.out)
    }

}