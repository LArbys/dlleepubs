#!/bin/bash
#
#SBATCH --job-name=prepflist
#SBATCH --output=log_prepflist.txt
#SBATCH --ntasks=1
#SBATCH --time=960:00
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

#SUPERADIR=/cluster/tufts/wongjiradlab/lyates01/sharing/daviosthings/mcc9_v13_bnboverlay/larcv
#LARLITEDIR=/cluster/tufts/wongjiradlab/lyates01/sharing/daviosthings/mcc9_v13_bnboverlay/larlite
#SUPERATRUTH=/cluster/tufts/wongjiradlab/lyates01/sharing/daviosthings/mcc9_v13_bnboverlay/larcv_mctruth

SUPERADIR=/cluster/tufts/wongjiradlab/lyates01/dl_production/mcc9_genie3_thresholds/0MeV_to_200MeV/larcv
LARLITEDIR=/cluster/tufts/wongjiradlab/lyates01/dl_production/mcc9_genie3_thresholds/0MeV_to_200MeV/larlite
SUPERATRUTH=/cluster/tufts/wongjiradlab/lyates01/dl_production/mcc9_genie3_thresholds/0MeV_to_200MeV/larcv_mctruth

#SUPERADIR=/cluster/kappa/wongjiradlab/larbys/data/db/numi_kdar_only_sample_input_files/LArCV/
#LARLITEDIR=/cluster/kappa/wongjiradlab/larbys/data/db/numi_kdar_only_sample_input_files/LArLITE/
#SUPERATRUTH=/cluster/kappa/wongjiradlab/larbys/data/db/numi_kdar_only_sample_input_files/LArCV_Truth/

#SUPERADIR=/cluster/kappa/wongjiradlab/larbys/data/mcc9/beta1_extbnb/larcv
#LARLITEDIR=/cluster/kappa/wongjiradlab/larbys/data/mcc9/beta1_extbnb/larlite
#SUPERATRUTH=


srun ./run_singularity_extract_runlist.sh $SUPERADIR $LARLITEDIR $SUPERATRUTH
