#!/usr/bin/env nextflow
nextflow.enable.dsl=2

include {GZ_TO_FASTQ} from "../modules/gunzip"
include {ABRICATE} from "../modules/abricate"
include {READ_EXTRACT} from "../modules/taxonomy"
include {SCAGAIRE} from "../modules/scagaire"

workflow AMR_ANALYSIS {
    take:
    single_end_ch

    main:
    // 1. Gunzip FASTQ
    // Abricate can use fastq.gz, so just point to files.
    GZ_TO_FASTQ(single_end_ch)
    
    // 2 - Run Abricate
    ABRICATE(GZ_TO_FASTQ.out)

    // test if any AMR annotations have been made
    ABRICATE.out
        .branch{
            climb_id, kraken_assignments, kraken_report, abricate_out ->
            // The abricate file will cotnain only headers if no AMR annotations have been made
            annotated: abricate_out.readLines().size() > 1
            unannotated: abricate_out.readLines().size() <= 1
        }. set{amr_status}
    // if not AMR annotations then skip
    amr_status.unannotated
        .map{
            log.info "No AMR annotations where made for ${climb_id}."
            return null
        }

    // 3. Extract species IDs for each READ assigned AMR
    // READ_EXTRACT(amr_status.annotated)

    // 4. Run Scagaire
    // SCAGAIRE(ABRICATE.out.abricate)
}