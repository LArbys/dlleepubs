#!/bin/bash


CONTAINER=/cluster/kappa/90-days-archive/wongjiradlab/larbys/images/dllee_unified/singularity-dllee-unified-taggerv2alpha-20171121.img
SCRIPT=$3/check_pubs_job.py

module load singularity

singularity exec ${CONTAINER} bash -c "source /usr/local/bin/thisroot.sh && cd ${WORKDIR} && python ${SCRIPT} $1 $2"

