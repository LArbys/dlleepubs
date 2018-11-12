#!/bin/bash

#SBATCH --job-name=prep_larflow_pgpu03
#SBATCH --output=prep_larflow_pgpu03.log
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=2000
#SBATCH --time=10:00
#SBATCH --cpus-per-task=1
#SBATCH --partition gpu
#SBATCH --nodelist=pgpu03

# This script copies
# 1) network weights for DL Cosmic Networks


mkdir -p /tmp/larflow_weights/
rsync -av --progress /cluster/kappa/90-days-archive/wongjiradlab/twongj01/larflow/weights/dev_filtered/* /tmp/larflow_weights/
