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
    // 1 - Run Abricate
    // Abricate can use fastq.gz, so just point to files.
    single_end_ch.view()
    GZ_TO_FASTQ(single_end_ch)
    ABRICATE(GZ_TO_FASTQ.out)
    TAXONOMY(ABRICATE.out)
    // 2. Extract species IDs for each READ assigned AMR

    // 3. Run Scagaire
    // SCAGAIRE(ABRICATE.out.abricate)
}