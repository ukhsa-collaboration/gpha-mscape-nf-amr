# mscape-amr-nf
Nextflow process for running AMR detection using Abricate on ONT metagenomic samples

## Usage
- Provide nextflow with a sample spreadsheet that contains either climb-id and S3 fastq locations.

### Creating Sample Sheet
- Install dependencies:
```
pip install -r requirements.txt
```

- To create sample-sheet with a list of CLIMB-IDs simply run:   
```
python bin/generate-sample-sheet.py 
    --input climb_ids.txt 
    --output sample-sheet.csv
```

### Running on Bryn
```
nextflow run -latest ukhsa-collaboration/gpha-mscape-nf-amr -profile docker --samplesheet test-sample-sheet.csv --output test-amr-out -resume
```


## Dependencies
- [Abricate](https://github.com/tseemann/abricate):  
Mass screening of contigs for antimicrobial resistance or virulence genes.

