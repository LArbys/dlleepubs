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

#SUPERADIR=/cluster/kappa/wongjiradlab/lyates01/dl_production/detsys/noiseAmpUp/larcv
#LARLITEDIR=/cluster/kappa/wongjiradlab/lyates01/dl_production/detsys/noiseAmpUp/larlite
#SUPERATRUTH=/cluster/kappa/wongjiradlab/lyates01/dl_production/detsys/noiseAmpUp/larcv_mctruth

SUPERADIR=/cluster/kappa/wongjiradlab/lyates01/dl_production/run1ext/larcv
LARLITEDIR=/cluster/kappa/wongjiradlab/lyates01/dl_production/run1ext/larlite
SUPERATRUTH=

#SUPERADIR=/cluster/kappa/wongjiradlab/larbys/data/db/numi_kdar_only_sample/LArCV
#LARLITEDIR=/cluster/kappa/wongjiradlab/larbys/data/db/numi_kdar_only_sample/LArLITE
#SUPERATRUTH=/cluster/kappa/wongjiradlab/larbys/data/db/numi_kdar_only_sample/LArCV


srun ./run_singularity_extract_runlist.sh $SUPERADIR $LARLITEDIR $SUPERATRUTH
