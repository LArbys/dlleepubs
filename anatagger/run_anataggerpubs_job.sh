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

anatagger_cfg_path=$1
inputlist_dir=$2
ana_output=$3
jobid=$4

cd ${inputlist_dir}/../

echo "CURRENT DIR: "$PWD
echo "SLURM PROCID: "${SLURM_PROCID}
echo "INPUTLIST_DIR: "${inputlist_dir}
echo "ANAOUT: "${ana_output}

# define input list into job dir
#inputlist_tagger_larcv=${inputlist_dir}/input_tagger_larcv.txt
#inputlist_tagger_larlite=${inputlist_dir}/input_tagger_larlite.txt
#inputlist_source_larcv=${inputlist_dir}/input_source_larcv.txt
#inputlist_source_larlite=${inputlist_dir}/input_source_larlite.txt

# copy config
cp $anatagger_cfg_path anatagger.cfg

ls -lh

# run analysis program
run_v2_analysis anatagger.cfg || exit

# copy output to db location
cp output_taggerana.root $ana_output || exit

# clean up
cd ../
rm -r $slurm_folder
