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

## Abricate
Install Abricate:  
`mamba install -c conda-forge -c bioconda -c defaults abricate`

Create python script to run Abricate (`src/mscape-amr-nf/abricate.py`)

## Get FASTQs

