# mscape-amr-nf
Nextflow process for running AMR detection using Abricate on ONT metagenomic samples

## Usage
- Provide nextflow with a sample spreadsheet that contains either climb-id and S3 fastq locations.

### Running on Bryn
Note that the full filepath for output directory is required.

- Running with a samplesheet:
```
nextflow run \
    -latest \
    -r main \
    ukhsa-collaboration/gpha-mscape-nf-amr \
    -profile docker \
    --samplesheet <SAMPLESHEET.csv> \
    --output <OUTDIR> \
    -e.ONYX_DOMAIN=$ONYX_DOMAIN \
    -e.ONYX_TOKEN=$ONYX_TOKEN \
```
- Running with unique id:
```
nextflow run \
    -latest \
    -r main \
    ukhsa-collaboration/gpha-mscape-nf-amr \
    -profile docker \
    --unique_id <UNIQUE_ID> \
    --output <OUTDIR> \
    -e.ONYX_DOMAIN=$ONYX_DOMAIN \
    -e.ONYX_TOKEN=$ONYX_TOKEN \
```
