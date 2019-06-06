#!/bin/bash
#
#SBATCH --job-name=ubdl_server
#SBATCH --output=ubdl_server.log
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=8000
#SBATCH --time=3-0:00:00
#SBATCH --cpus-per-task=2
#SBATCH --partition gpu
#SBATCH --nodelist=pgpu02

CONTAINER=/cluster/tufts/wongjiradlab/larbys/larbys-containers/ubdl_singularity_031219.img
SERVER_BASEDIR=/usr/local/ubdl
WORKDIR=/cluster/tufts/wongjiradlab/larbys/pubs/dlleepubs/ubdlserver

module load singularity
singularity exec ${CONTAINER} bash -c "cd ${SERVER_BASEDIR} && source setenv.sh && source configure.sh \
&& cd scripts && source setenv_ublarcvserver.sh && \
./start_ublarcvserver_broker.py -l ${WORKDIR}/ubdl_server.log 6000"
