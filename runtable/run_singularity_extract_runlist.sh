#!/bin/bash

supera_folder=$1
larlite_folder=$2

container=/cluster/kappa/90-days-archive/wongjiradlab/larbys/images/dllee_unified/singularity-dllee-unified-taggerv2alpha-20171121.img

module load singularity
workdir=$PUB_TOP_DIR/dlleepubs/runtable
singularity exec ${container} \
    bash -c "source /usr/local/bin/thisroot.sh && cd /usr/local/share/dllee_unified && source configure.sh && cd ${workdir} && python extract_runlist.py ${supera_folder} ${larlite_folder}"
