# Development Notes

## To Do
- [x] Create environment
- [X] Create repo structure
- [X] Set up formatting and linting (Ruff)
- [X] set up Nextflow config files
- [X] Install depedencies (Abricate, scagaire)
- [X] Develop script to create sample-sheet
- [X] NextFlow: Take CLIMB-ID list, pull FASTQ URIs from database (stored as text strings)
- [X] Nextflow: Run Abricate 
- [ ] Nextflow: Run Scagaire 
- [X] Nextflow: Set up for multiple input samples
- [ ] Nextflow: Set up for multiple species (Scagaire)


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
`s3cmd get s3://mscape-published-read-fractions/<CLIMB_ID>/<CLIMB_ID>.human_filtered.fastq.gz`

## Abricate
Install Abricate:  
`mamba install -c conda-forge -c bioconda -c defaults abricate`

Create python script to run Abricate (`mscape-amr-nf/abricate.py`)

## Testing Nextflow
Running tests:   
`nextflow run main.nf -profile docker --samplesheet /shared/team/amr/nextflow/test_data/test-sample-sheet.csv -process.echo`
Run test, but don't repeat steps that have not changed:
`nextflow run main.nf -profile docker -resume --samplesheet /shared/team/amr/nextflow/test_data/test-sample-sheet.csv -process.echo`

Running from GitHub directly (requires permissions)
`nextflow run nfellaby/amr-nf -r dev -profile test,docker -resume --samplesheet /shared/team/amr/nextflow/test_data/test-sample-sheet.csv`

Note: You will want to pull the latest version of the repo
`nextflow pull nfellaby/amr-nf`

## Viewing Work Directory
Can be found here:
`/home/jovyan/shared-team/nxf_work/${USERNAME}.gpha-ukhsa-mscap/work/`

## Kraken Output Files Directory
Can be found here:
`s3://mscape-published-taxon-reports/${CLIMB_ID}`
