#!/bin/bash


CONTAINER=/cluster/kappa/90-days-archive/wongjiradlab/larbys/images/dllee_unified/singularity-dllee-unified-taggerv2alpha-20171121.img
SCRIPT_IC=/cluster/kappa/wongjiradlab/larbys/pubs/dlleepubs/dlcosmictag/check_pubs_job.py
WORKDIR_IC=/cluster/kappa/wongjiradlab/larbys/pubs/dlleepubs/dlcosmictag/

module load singularity

singularity exec ${CONTAINER} bash -c "source /usr/local/bin/thisroot.sh && cd ${WORKDIR} && python ${SCRIPT_IC} $1 $2 $3"

