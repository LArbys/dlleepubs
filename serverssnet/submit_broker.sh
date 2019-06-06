#!/bin/bash
#
#SBATCH --job-name=ssn_server
#SBATCH --output=ssn_server.log
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=8000
#SBATCH --time=3-0:00:00
#SBATCH --cpus-per-task=3
#SBATCH --partition gpu
#SBATCH --nodelist=pgpu03

CONTAINER=/cluster/tufts/wongjiradlab/larbys/images/singularity-ssnetserver/singularity-ssnetserver-caffelarbys-cuda8.0.img
#SSS_BASEDIR=/usr/local/ssnetserver
SSS_BASEDIR=/cluster/tufts/wongjiradlab/larbys/ssnetserver
WORKDIR=/cluster/tufts/wongjiradlab/larbys/pubs/dlleepubs/serverssnet/
TIMESTAMP_FILE=/cluster/tufts/wongjiradlab/larbys/pubs/dlleepubs/serverssnet/ssnetserver_broker_start.txt

module load singularity
singularity exec ${CONTAINER} bash -c "cd ${SSS_BASEDIR}/grid && ./run_broker_w_timestamp_file.sh ${SSS_BASEDIR} ${WORKDIR} ${TIMESTAMP_FILE}"
