# Development Notes

## Creat Env
Create an environment for testing
- With micromamba
```
mm env create -n mscape-amr-nf
mm activate mscape-amr-nf
```
- With Conda
```
conda create --name mscape_amr_nf
conda activate mscape_amr_nf
```

## Running
If running on Bryn this repo needs to be cloned to `~/shared-team/` otherwise containers will not work

## Get FASTQs
To get fastqs via S3:   
`s3cmd get s3://mscape-published-read-fractions/<climbid>/<climbid>.human_filtered.fastq.gz`

## Abricate
Install Abricate:  
`mamba install -c conda-forge -c bioconda -c defaults abricate`

Create python script to run Abricate (`mscape-amr-nf/abricate.py`)

## Testing Nextflow
Running tests:   
`nextflow run main.nf -profile test,docker -process.echo`
Run test, but don't repeat steps that have not changed:
`nextflow run main.nf -profile test,docker -process.echo -resume`

## Viewing Work Directory
Can be found here:
`/home/jovyan/shared-team/nxf_work/${USERNAME}.gpha-ukhsa-mscap/work/`

## Kraken Output Files Directory
Can be found here:
`s3://mscape-published-taxon-reports/${CLIMB_ID}`
