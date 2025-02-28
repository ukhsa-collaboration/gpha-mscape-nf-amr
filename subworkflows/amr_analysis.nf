#!/usr/bin/env nextflow
nextflow.enable.dsl=2

include {ABRICATE} from "../modules/abricate"

workflow AMR_ANALYSIS {
    take:
    single_end_samples

    main:
    // 1 - Run Abricate
    // Abricate can use fastq.gz, so just point to files.
    ABRICATE(single_end_samples)
}