#!/usr/bin/env nextflow

include { GZ_TO_FASTQ     } from "../modules/local/gunzip"
include { RUN_ABRICATE    } from "../modules/local/abricate"
include { READ_ANALYSIS   } from "../modules/local/taxonomy"
include { ONYX_UPLOAD     } from "../modules/local/onyx_upload"
include { SAMPLE_REPORT   } form "../modules/local/report"

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
                tuple( climb_id, abricate_out, 'None', 'abricate')
        }
        .set{ abricate_ch }
 
    }

    if (amr_status.annotated){
        amr_status.annotated
            .map{ climb_id,  kraken_assignments, kraken_report, abricate_out ->
                tuple( climb_id, kraken_assignments, kraken_report, abricate_out, 'Annotated', 'abricate')
        }
        .set{ annotated_ch }
        // 3. Extract species IDs for each READ assigned AMR  
        READ_ANALYSIS( annotated_ch )
        // Rename for input to onyx
        READ_ANALYSIS.out.set{abricate_ch}

        // 4. Generate Sample Report output
        // sample report requires climb_id, READ_ANALYSIS.out, params.email
        abricate_ch
            .map{climb_id, amr_table, pipeline_status, amr_tool ->
                tuple ( climb_id, amr_table, amr_too, ${params.email} )
        }
        .set(read_analysis_ch)
        SAMPLE_REPORT(read_analysis_ch)


    }


    // 4. Output to Onyx
    ONYX_UPLOAD(abricate_ch)

}