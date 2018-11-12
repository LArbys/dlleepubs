#!/bin/sh

# REMEMBER, WE ARE IN THE CONTAINER RIGHT NOW
# This means we access the network wongjiradlab folder through
#  /cluster/kappa/wongjiradlab
# which is different from the path as seen from the worker nodes
#  /cluster/kappa/90-days-archive/wongjiradlab

export DLLEE_UNIFIED_BASEDIR=/usr/local/share/dllee_unified

source /usr/local/bin/thisroot.sh
source /usr/local/share/dllee_unified/configure.sh
export PATH=${DLLEE_UNIFIED_BASEDIR}/larlitecv/app/AnalyzeTagger:${PATH}
export LD_LIBRARY_PATH=${DLLEE_UNIFIED_BASEDIR}/larlitecv/app/AnalyzeTagger:${LD_LIBRARY_PATH}

input_larcv=$1
input_larlite=$2
ana_output=$3
mccversion=$4

echo "CURRENT DIR: "$PWD
echo "SLURM PROCID: "${SLURM_PROCID}
echo "ANAOUT: "${ana_output}

# run analysis program
run_pixelscale_analysis $input_larcv $input_larlite out_pixelscaleana.root $mccversion || exit

# copy output to db location
cp out_pixelscaleana.root $ana_output || exit

# clean up
rm *

