#!/bin/bash
#
#SBATCH --job-name=prepflist
#SBATCH --output=log_prepflist.txt
#SBATCH --ntasks=1
#SBATCH --time=480:00
#SBATCH --mem-per-cpu=4000

SUPERADIR=/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/mcc8.3/corsika_mcc8.3_p02
LARLITEDIR=

srun ./run_singularity_extract_runlist.sh $SUPERADIR $LARLITEDIR