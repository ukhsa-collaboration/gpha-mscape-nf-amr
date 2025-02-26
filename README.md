# mscape-amr-nf
Nextflow process for running AMR detection using Abricate on ONT metagenomic samples

## To Do
- [x] Create environment
- [X] Create repo structure
- [ ] Set up formatting and linting (Ruff)
- [X] Install depedencies (Abricate, scagaire)
- [ ] Run AMR analysis with local scripts
- [ ] Run Scagaire analysis with local scripts
- [ ] Create NexFlow workflow 
- [ ] Run NextFlow workflow

## Created Env
```
mm env create -n amr-workflow
mm activate amr-workflow
```

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