# mscape-amr-nf
Nextflow process for running AMR detection using Abricate on ONT metagenomic samples

## Usage
- Provide nextflow with a sample spreadsheet that contains either climb-id and S3 fastq locations, example can be found in `test/test-sample-sheet.csv`.

### Creating Sample Sheet
- Install dependencies:
```
pip install -r requirements.txt
```

- To create sample-sheet with a list of CLIMB-IDs (exmaple `test/climb_ids.txt`) simply run:   
```
python bin/generate-sample-sheet.py 
    --input climb_ids.txt 
    --output sample-sheet.csv
```

## To Do
- [x] Create environment
- [X] Create repo structure
- [ ] Set up formatting and linting (Ruff)
- [X] set up Nextflow config files
- [X] Install depedencies (Abricate, scagaire)
- [X] Develop script to create sample-sheet
- [X] NextFlow: Take CLIMB-ID list, pull FASTQ URIs from database (stored as text strings)
- [X] Nextflow: Run Abricate 
- [ ] Nextflow: Run Scagaire 
- [ ] Nextflow: Set up for multiple input samples
- [ ] Nextflow: Set up for multiple species (Scagaire)


## Dependencies
- [Abricate](https://github.com/tseemann/abricate):  
Mass screening of contigs for antimicrobial resistance or virulence genes.
- [Scagaire](https://github.com/quadram-institute-bioscience/scagaire):  
Scagaire allows you to take in gene predictions from a metagenomic sample and filter them by bacterial/pathogenic species. 

## Create Initial Scripts 
- [ ] Create Abricate module
- [ ] Create Abricate test module
- [ ] Create Scagaire module
- [ ] Create Scagaire test module