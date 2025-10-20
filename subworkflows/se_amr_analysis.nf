#!/usr/bin/env nextflow
nextflow.enable.dsl=2

include { GZ_TO_FASTQ     } from "../modules/local/gunzip"
include { RUN_ABRICATE_DB } from "../modules/local/abricate"
include { READ_ANALYSIS   } from "../modules/local/taxonomy"

workflow SE_AMR_ANALYSIS {
    take:
    single_end_ch

    main:
    // 1. Gunzip FASTQ
    // Abricate can use fastq.gz, so just point to files.
    GZ_TO_FASTQ(single_end_ch)
    
    // 2 - Run Abricate
    // Run Abricate with multiple databases
    abricate_db_list = params.abricate_databases?.split(',') as List
    db_ch = channel.fromList(abricate_db_list)
    RUN_ABRICATE_DB(GZ_TO_FASTQ.out.combine(db_ch))

    // test if any AMR annotations have been made
    RUN_ABRICATE_DB.out.abricate_results
        .branch{
            climb_id,  kraken_assignments, kraken_report, abricate_out ->
            // Skips abricate file if it contains only header, i.e. no AMR annotations have been made
            annotated: abricate_out.readLines().size() > 1
            unannotated: abricate_out.readLines().size() <= 1
        }. set{amr_status}
    // // if not AMR annotations then skip
    amr_status.unannotated
        .map{ climb_id,  kraken_assignments, kraken_report, abricate_out ->
            log.info "The AMR annotation pipeline was not ran on ${climb_id}."
            return null
        }

    // 3. Extract species IDs for each READ assigned AMR
    // Combine Channels 
    single_end_ch.join(amr_status.annotated).map{
        climb_id, kraken_assignments, kraken_report, fastq1, db, abricate_out ->
        tuple(climb_id, kraken_assignments, kraken_report, db, abricate_out)
    }.set{ single_end_anno_ch }


    READ_ANALYSIS(single_end_anno_ch)
    log.info "Completes annotation."

}