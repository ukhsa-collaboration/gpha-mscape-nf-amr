#!/usr/bin/env nextflow

include { RUN_ABRICATE          } from "../modules/local/abricate"
include { RUN_METAPOINTFINDER   } from "../modules/local/metapointfinder"
include { RUN_KMA               } from "../modules/local/kma"
include { TAXAPLEASE_REFS       } from "../modules/local/taxaplease"
include { KMA_TAXA_LINKAGE      } from "../modules/local/taxonomy"

include { GZ_TO_FASTQ           } from "../modules/local/gunzip"
include { ABRICATE_TAXA_LINKAGE } from "../modules/local/taxonomy"
include { GENERATE_REPORT       } from "../modules/local/report"
include { ONYX_UPLOAD           } from "../modules/local/onyx_upload"


workflow SE_AMR_ANALYSIS {
    take:
    single_end_ch

    main:

    card_kma_db = file(params.card_kma_db, checkIfExists: true)
    taxaplease_db = file(params.taxaplease_db, checkIfExists: true)

    // Get Reference TaxIDs
    def ch_taxa_of_interest = Channel.of(
        file("${projectDir}/references/taxa_of_interest.txt", checkIfExists: true)
    )
    TAXAPLEASE_REFS(taxaplease_db, ch_taxa_of_interest)

    // KMA Mapping
    RUN_KMA(single_end_ch, card_kma_db)

    RUN_KMA.out.kma_out.view()
    RUN_KMA.out.kma_mapping_tsv.view()

    // Get TaxIDs for Reads from Kraken data
    KMA_TAXA_LINKAGE(single_end_ch, RUN_KMA.out.kma_mapping_tsv)


    // // 1. Gunzip FASTQ
    // // Abricate can use fastq.gz, so just point to files.
    // GZ_TO_FASTQ(single_end_ch)
    
   

    // // 2 - Run Abricate
    // RUN_ABRICATE(GZ_TO_FASTQ.out)



    // // test if any AMR annotations have been made
    // RUN_ABRICATE.out.abricate_results
    //     .branch{
    //         climb_id,  kraken_assignments, kraken_report, abricate_out ->
    //         // Skips abricate file if it contains only header, i.e. no AMR annotations have been made
    //         annotated: abricate_out.readLines().size() > 1
    //         unannotated: abricate_out.readLines().size() <= 1
    //     }. set{amr_status}
    // // Remap channels
    // if (amr_status.unannotated){
    //     amr_status.unannotated
    //         .map{ climb_id,  kraken_assignments, kraken_report, abricate_out ->
    //             tuple( climb_id, abricate_out, 'None', 'abricate')
    //     }
    //     .set{ abricate_ch }
 
    // }

    // if (amr_status.annotated){
    //     amr_status.annotated
    //         .map{ climb_id,  kraken_assignments, kraken_report, abricate_out ->
    //             tuple( climb_id, kraken_assignments, kraken_report, abricate_out, 'Annotated', 'abricate')
    //     }
    //     .set{ annotated_ch }
    //     // 3.0 Extract species IDs for each READ assigned AMR  
    //     READ_ANALYSIS( annotated_ch )
    //     // Rename for input to onyx
    //     READ_ANALYSIS.out.set{abricate_ch}
    //     // 3.1 Produce HTML report
    //     abricate_ch
    //         .map{ climb_id,  abricate_taxa_out, piepline_Status, tool ->
    //             tuple( climb_id, abricate_taxa_out, tool, params.email )
    //         }
    //         .set{ report_ch }
    //     GENERATE_REPORT( report_ch )
    // }
    // // 4. Output to Onyx
    // ONYX_UPLOAD(abricate_ch)

}