#!/bin/bash
#
#SBATCH --job-name=prepflist_mcc8v7_fullosc_overlay
#SBATCH --output=log_prepflist_mcc8v7_fullosc_overlay.txt
#SBATCH --ntasks=1
#SBATCH --time=480:00
#SBATCH --mem-per-cpu=2000

SUPERADIR=/cluster/kappa//wongjiradlab/vgenty/fullosc/larcv
LARLITEDIR=/cluster/kappa//wongjiradlab/vgenty/fullosc/larlite
SUPERATRUTH=


srun ./run_singularity_extract_runlist.sh $SUPERADIR $LARLITEDIR $SUPERATRUTH
