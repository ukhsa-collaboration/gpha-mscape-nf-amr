#!/usr/bin/env nextflow
nextflow.enable.dsl=2

include { GZ_TO_FASTQ   } from "../modules/local/gunzip"
include { RUN_ABRICATE  } from "../modules/local/abricate"
include { READ_ANALYSIS } from "../modules/local/taxonomy"
include { ABRICATE_RUN  } from '../modules/nf-core/abricate/run/main'
//                                 ../modules/nf-core/abricate/run/main.nf

// include {SCAGAIRE} from "../modules/scagaire"


workflow AMR_ANALYSIS {
    take:
    single_end_ch

    main:
    // 1. Gunzip FASTQ
    // Abricate can use fastq.gz, so just point to files.
    GZ_TO_FASTQ(single_end_ch)
    
    // 2 - Run Abricate
    RUN_ABRICATE(GZ_TO_FASTQ.out)


    // 3 - Run Abricate as per nf-core, requires val(meta), path(contigs)
    single_end_ch
        .map{ climb_id, kraken_assignments, kraken_report, fastq1 ->
        tuple(climb_id , fastq1 ) 
    }.set { id_fastq_ch }

    id_fastq_ch.view()

    // test if any AMR annotations have been made
    RUN_ABRICATE.out.abricate_results
        .branch{
            climb_id, kraken_assignments, kraken_report, abricate_out ->
            // The abricate file will cotnain only headers if no AMR annotations have been made
            annotated: abricate_out.readLines().size() > 1
            unannotated: abricate_out.readLines().size() <= 1
        }. set{amr_status}
    // amr_status.unannotated.view()
    // // if not AMR annotations then skip
    amr_status.unannotated
        .map{ climb_id, kraken_assignments, kraken_report, abricate_out ->
            log.info "The AMR annotation pipeline was not ran on ${climb_id}."
            return null
        }

    // 3. Extract species IDs for each READ assigned AMR
    READ_ANALYSIS(amr_status.annotated)
    READ_ANALYSIS.out.view()

}