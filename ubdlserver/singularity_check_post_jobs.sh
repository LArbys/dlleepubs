#!/bin/bash

postout=$1
supera=$2
WORKDIR=$3

CONTAINER=/cluster/tufts/wongjiradlab/larbys/larbys-containers/singularity_ubdl_041519.img
SCRIPT=$WORKDIR/check_post_pubs_job.py

module load singularity

singularity exec ${CONTAINER} bash -c "source /usr/local/root/build/bin/thisroot.sh && cd ${WORKDIR} && python ${SCRIPT} $postout $supera"

