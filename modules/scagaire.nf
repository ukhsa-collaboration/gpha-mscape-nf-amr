#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process SCAGAIRE{
    // tag "${climb_id}"
    // container 'community.wave.seqera.io/library/scagaire:0.0.4--d340715dde589279'

    // input:
    // tuple val(climb_id), path(abricate)

    // Read in Abricate results
    // What taxa was assigned to a given read?

    script:
    """
    echo test
    """
    // t=$(cat {input.top_hit} | paste -sd "," -)
    // scagaire "$t" {input.amr_res} -n card -s {output.summary} -o {output.report}
    // if [ ! -f "{output.summary}" ]; then
    //     echo "No species in database" > {output.summary}
    //     echo "No Report" > {output.report}
    // fi
    // """
}