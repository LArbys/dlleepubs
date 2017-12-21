#!/bin/bash
#
#SBATCH --job-name=prepflist
#SBATCH --output=log_prepflist.txt
#SBATCH --ntasks=1
#SBATCH --time=480:00
#SBATCH --mem-per-cpu=4000

SUPERADIR=/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/mcc8.4/cocktail_p04/supera
LARLITEDIR=/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/mcc8.4/cocktail_p04/larlite

srun ./run_singularity_extract_runlist.sh $SUPERADIR $LARLITEDIR