#!/bin/sh

# REMEMBER, WE ARE IN THE CONTAINER RIGHT NOW
# This means we access the next work drives through some mounted folders

export DLLEE_UNIFIED_BASEDIR=/usr/local/share/dllee_unified

source /usr/local/bin/thisroot.sh
source /usr/local/share/dllee_unified/configure.sh

tagger_cfg_path=$1
inputlist_dir=$2
larcv_output=$3
larlite_output=$4
jobid_list=$5

cd ${inputlist_dir}/../

echo "CURRENT DIR: "$PWD
echo "SLURM PROCID: "${SLURM_PROCID}
echo "INPUTLIST_DIR: "${inputlist_dir}
echo "LARCVOUT: "${larcv_output}
echo "LARLITEOUT: "${larlite_output}
echo "JOBIDLIST="$jobid_list

let NUM_PROCS=`cat ${jobid_list} | wc -l`
echo "number of processes: $NUM_PROCS"
if [ "$NUM_PROCS" -lt "${SLURM_PROCID}" ]; then
    echo "No Procces ID to run."
    return
fi

let "proc_line=${SLURM_PROCID}+1"
echo "sed -n ${proc_line}p ${jobid_list}"
let jobid=`sed -n ${proc_line}p ${jobid_list}`
echo "JOBID ${jobid}"

slurm_folder=`printf slurm_tagger_job%09d ${jobid}`
mkdir -p ${slurm_folder}
cd ${slurm_folder}/

# copy over input list
inputlist_larcv=`printf ${inputlist_dir}/input_larcv_%09d.txt ${jobid}`
inputlist_larlite=`printf ${inputlist_dir}/input_larlite_%09d.txt ${jobid}`

cp $inputlist_larcv input_larcv.txt
cp $inputlist_larlite input_larlite.txt
cp $tagger_cfg_path tagger_wire.cfg

ls -lh

# ./run_tagger [cfg]
logfile=`printf log_%04d.txt ${jobid}`
run_tagger tagger_wire.cfg >& logfile || exit

cp tagger_anaout_larcv.root $larcv_output
cp tagger_anaout_larlite.root $larlite_output

# clean up
cd ../
rm -r $slurm_folder
