#!/bin/bash
#
#SBATCH --job-name=prepflist
#SBATCH --output=log_prepflist.txt
#SBATCH --ntasks=1
#SBATCH --time=480:00
#SBATCH --mem-per-cpu=2000

#SUPERADIR=/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/mcc8v5/bnb_5e19/larcv
#LARLITEDIR=/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/mcc8v5/bnb_5e19/larlite
#SUPERADIR=/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/mcc8v5/bnbrun1open/larcv
#LARLITEDIR=/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/mcc8v5/bnbrun1open/larlite
#SUPERATRUTH=

#SUPERADIR=/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/comparison_samples/ncpizero/supera_links
#LARLITEDIR=/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/comparison_samples/ncpizero/larlite_links
#SUPERATRUTH=

#SUPERADIR=/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/mcc8.4/extunb/p00/larcv
#LARLITEDIR=/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/mcc8.4/extunb/p00/larlite
#SUPERATRUTH=

#SUPERADIR=/cluster/kappa/90-days-archive/wongjiradlab/vgenty/michel_data/larcv
#LARLITEDIR=/cluster/kappa/90-days-archive/wongjiradlab/vgenty/michel_data/larlite
#SUPERATRUTH=

SUPERADIR=/cluster/kappa/wongjiradlab/lyates01/dl_production/overlay_full/larcv_p01
LARLITEDIR=/cluster/kappa/wongjiradlab/lyates01/dl_production/overlay_full/larlite_p01
SUPERATRUTH=

srun ./run_singularity_extract_runlist.sh $SUPERADIR $LARLITEDIR $SUPERATRUTH
