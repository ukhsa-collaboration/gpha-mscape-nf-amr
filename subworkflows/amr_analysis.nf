#!/usr/bin/env nextflow
nextflow.enable.dsl=2

include { GZ_TO_FASTQ     } from "../modules/local/gunzip"
include { RUN_ABRICATE_DB } from "../modules/local/abricate"
include { READ_ANALYSIS   } from "../modules/local/taxonomy"

workflow AMR_ANALYSIS {
    take:
    single_end_ch

    main:
    // 0. Simplify Channel, to just fastq for the first processes
    single_end_ch.map{
        climb_id, kraken_assignments, kraken_report, fastq1 ->
        tuple( climb_id, fastq1 )
    }.set{ fastq_ch }

    // 1. Gunzip FASTQ
    GZ_TO_FASTQ(fastq_ch)
    
    // 2 - Run Abricate with specified databases
    abricate_db_list = params.abricate_databases?.split(',') as List
    db_ch = channel.fromList(abricate_db_list)
    RUN_ABRICATE_DB(GZ_TO_FASTQ.out.combine(db_ch))

    // 3. Check if AMR annotations have been made
    RUN_ABRICATE_DB.out.abricate_results.branch{
        climb_id, db, abricate_out ->
        // Skips if only header (no annotations) 
        annotated: abricate_out.readLines().size() > 1
        unannotated: abricate_out.readLines().size() <= 1
    }. set{amr_status}
    
    // // if no AMR annotations then skip
    amr_status.unannotated.map{ 
            climb_id, db, abricate_out ->
            log.info "No ${db} database annotations found for ${climb_id}."
            return null
    }

    // // 3. Extract species IDs for each READ assigned AMR
    // READ_ANALYSIS(amr_status.annotated)
    // READ_ANALYSIS.out.view()

}