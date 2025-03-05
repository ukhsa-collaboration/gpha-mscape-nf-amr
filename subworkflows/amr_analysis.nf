#!/usr/bin/env nextflow
nextflow.enable.dsl=2

include {ABRICATE} from "../modules/abricate"


workflow AMR_ANALYSIS {
    take:
    ch_fastqs

    main:
    // 1 - Run Abricate
    // Abricate can use fastq.gz, so just point to files.
    ch_fastqs.single_end.view()
    ABRICATE(ch_fastqs.single_end)
    SCAGAIRE(ABRICATE.out.abricate_out)
}