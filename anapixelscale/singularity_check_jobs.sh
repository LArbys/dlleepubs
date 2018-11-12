#!/bin/bash

WORKDIR=/cluster/kappa/wongjiradlab/larbys/pubs/dlleepubs/anatagger/
CONTAINER=/cluster/kappa/90-days-archive/wongjiradlab/larbys/images/singularity-dllee-ubuntu/singularity-dllee-unified-ubuntu16.04-20180816.img
SCRIPT=/cluster/kappa/wongjiradlab/larbys/pubs/dlleepubs/anatagger/check_pubs_job.py

module load singularity

singularity exec ${CONTAINER} bash -c "source /usr/local/bin/thisroot.sh && cd ${WORKDIR} && python ${SCRIPT} $1 $2"

