#!/bin/sh
#
#SBATCH --job-name=ubpostclient_49550109
#SBATCH --output=/cluster/tufts/wongjiradlab/larbys/grid_work_dir/post_mcc9v12_intrinsicoverlay/post_mcc9v12_intrinsicoverlay_4955_109/log_ubpostclient_4955_109.txt
#SBATCH --ntasks=1
#SBATCH --time=8:00:00
#SBATCH --mem-per-cpu=3000

# CONTAINER
CONTAINER=/cluster/tufts/wongjiradlab/larbys/larbys-containers/singularity_ubdl_041519.img

# UBDL LOCATION
UBDL_DIR=/cluster/tufts/wongjiradlab/twongj01/ubdl

# LOCATION OF POSTSERVER CODE (IN CONTAINER)
UBPOST_BASEDIR=/cluster/tufts/wongjiradlab/twongj01/ubdl

# WORKING DIRECTORY
WORKDIR=/cluster/tufts/wongjiradlab/larbys/grid_work_dir/post_mcc9v12_intrinsicoverlay/post_mcc9v12_intrinsicoverlay_4955_109

# PATHS (IN CONTAINER)
SUPERA_INPUTPATH=/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/db/mcc9v12_intrinsicoverlay/stage1/049/55/001/09//supera-Run004955-SubRun000109.root
LARFLOW_INPUTPATH=/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/db/mcc9v12_intrinsicoverlay/ubdlserver/049/55/001/09//larflow-noinfill-larcv-mcc9v12_intrinsicoverlay-Run004955-SubRun000109.root
OPRECO_INPUTPATH=/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/db/mcc9v12_intrinsicoverlay/stage1/049/55/001/09//opreco-Run004955-SubRun000109.root
RECO2D_INPUTPATH=/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/db/mcc9v12_intrinsicoverlay/stage1/049/55/001/09//reco2d-Run004955-SubRun000109.root
SSNET_INPUTPATH=/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/db/mcc9v12_intrinsicoverlay/stage1/049/55/001/09//ssnetserveroutv2-larcv-Run004955-SubRun000109.root

UBPOST_OUTDIR=/cluster/tufts/wongjiradlab/larbys/data/db/mcc9v12_intrinsicoverlay/ubdlserver/049/55/001/09
UBPOST_LARLITE_OUTFILE=ubpost-noinfill-larlite-mcc9v12_intrinsicoverlay-Run004955-SubRun000109.root
UBPOST_LARCV_OUTFILE=ubpost-noinfill-larcv-mcc9v12_intrinsicoverlay-Run004955-SubRun000109.root

ENVSETUP="cd $UBDL_DIR && source setenv.sh && source configure.sh && cd larflow && source configure.sh"
COPY_UBSPLIT_CFG="cp $UBDL_DIR/larflow/postprocessor/ubsplit.cfg ."
COMMAND="dev -c $LARFLOW_INPUTPATH -su $SUPERA_INPUTPATH -re $RECO2D_INPUTPATH -op $OPRECO_INPUTPATH -wss $SSNET_INPUTPATH -oll $UBPOST_LARLITE_OUTFILE -olc $UBPOST_LARCV_OUTFILE"
COPY_POST_OUT="cp $UBPOST_LARLITE_OUTFILE $UBPOST_OUTPATH_DIR && cp $UBPOST_LARCV_OUTFILE $UBPOST_OUTDIR"
echo "$COMMAND"

mkdir -p $WORKDIR
mkdir -p $UBPOST_OUTPATH_DIR
module load singularity
srun singularity exec $CONTAINER bash -c "$ENVSETUP && cd $WORKDIR && $COPY_UBSPLIT_CFG && $COMMAND && $COPY_POST_OUT"

