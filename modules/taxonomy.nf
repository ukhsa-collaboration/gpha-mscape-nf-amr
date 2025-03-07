#!/usr/bin/env nextflow
nextflow.enable.dsl=2

process READ_EXTRACT{
    tag "${climb_id}"
    container 'community.wave.seqera.io/library/pip_argparse_pandas_pathlib:2f69bdc5b6cf9eae' // Not sure if this works

    // 1. Extract Read IDs from Abricate output file
    input:
    tuple val(climb_id), path(kraken_assignments), path(kraken_report),  path(abricate_out)

    script:
    """
    echo $climb_id
    tail -n +2 ${abricate_out} | cut -f2 | sort | uniq > unique_amr_reads.txt
    while read i; do grep -P "\$i\t" ${kraken_assignments} | cut -f 2-3 >>read_taxid_assignment.tsv; done< unique_amr_reads.txt
    
    retrieve_taxon -t read_taxid_assignment.tsv -j ${kraken_report} -o reads_kraken_info.tsv
    """
}