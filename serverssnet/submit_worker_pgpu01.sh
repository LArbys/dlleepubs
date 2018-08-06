#!/bin/bash
#
#SBATCH --job-name=ssn_workers_pgpu01
#SBATCH --output=ssn_workers_pgpu01.log
#SBATCH --mem-per-cpu=2000
#SBATCH --time=3-0:00:00
#SBATCH --cpus-per-task=1
#SBATCH --partition gpu
#SBATCH --nodelist=pgpu01
#SBATCH --array=0-5

CONTAINER=/cluster/kappa/90-days-archive/wongjiradlab/larbys/images/singularity-ssnetserver/singularity-ssnetserver-caffelarbys-cuda8.0.img
#SSS_BASEDIR=/usr/local/ssnetserver
SSS_BASEDIR=/cluster/kappa/wongjiradlab/larbys/ssnetserver
WORKDIR=/cluster/kappa/wongjiradlab/larbys/pubs/dlleepubs/serverssnet

# IP ADDRESSES OF BROKER
BROKER=10.246.81.73 # PGPU03
# BROKER=10.X.X.X # ALPHA001

PORT=5560

# GPU LIST
#GPU_ASSIGNMENTS=/cluster/kappa/wongjiradlab/twongj01/ssnetserver/grid/tufts_pgpu01_assignments.txt
GPU_ASSIGNMENTS=/cluster/kappa/wongjiradlab/larbys/pubs/dlleepubs/serverssnet/tufts_pgpu01_assignments.txt
WORKEROFFSET=100

module load singularity
singularity exec --nv ${CONTAINER} bash -c "cd ${SSS_BASEDIR}/grid && ./run_caffe1worker.sh ${SSS_BASEDIR} ${WORKDIR} ${BROKER} ${PORT} ${GPU_ASSIGNMENTS} ${WORKEROFFSET}"
