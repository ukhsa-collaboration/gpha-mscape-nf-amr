#!/usr/bin/env nextflow
nextflow.enable.dsl=2
process ONYX_UPLOAD{
    tag "${unique_id}"
    publishDir "${params.output}/", mode: 'copy', pattern: "*.csv"

    // Onyx and Onyx Helper
    container 'ghcr.io/ukhsa-collaboration/gpha-mscape-onyx-analysis-helper:@sha256:80429e36f92be75033432d601739c554f6011a4b9dde9c28ad6e562e629b2400'

    input:
    tuple val(unique_id), path(abricate_taxa_out)

    // output:
    // path("${unique_id}_amr_analysis_fields.json"), emit: onyx_json
    
    script:
    """
    printf "{'db': '${params.arg_abricate_db}', 'minid': '${params.arg_abricate_minid}', 'mincov': '${params.arg_abricate_mincov}'}"

    // onyx_upload.py \
    //     -i C-${unique_id} \
    //     -t ${abricate_taxa_out} \
    //     -o ./ \
    //     -p Annotated \
    //     -s mscape \
    //     --store-onyx
 
    """
}