#!/bin/bash

infillout=$1
supera=$2
WORKDIR=$3

CONTAINER=/cluster/tufts/wongjiradlab/larbys/larbys-containers/singularity_ubdl_032919.img
SCRIPT=$WORKDIR/check_infill_pubs_job.py

module load singularity

singularity exec ${CONTAINER} bash -c "cd /cluster/tufts/wongjiradlab/kmason03/uboonecode/ubdl && source setenv.sh && source configure.sh && cd ublarcvserver && source configure.sh && source /usr/local/root/build/bin/thisroot.sh && cd ${WORKDIR} && python ${SCRIPT} $infillout $supera"

