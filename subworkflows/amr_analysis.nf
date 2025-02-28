#!/usr/bin/env nextflow
nextflow.enable.dsl=2

include {ABRICATE} from "../modules/abricate"



workflow AMR_ANALYSIS {
    take:
    single_end

    main:
    // 1 - Run Abricate
    // Abricate can use fastq.gz, so just point to files.
    ABRICATE(ch_fastqs.single_end)
}