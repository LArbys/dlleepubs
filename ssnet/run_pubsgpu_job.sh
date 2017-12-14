#!/bin/bash

# REMEMBER, WE ARE IN THE CONTAINER RIGHT NOW
# This means we access the next work drives through some mounted folders
# The submit command also moved us to right local folder

# Get arguments
jobdir=$1
inputlist_dir=$2
outputfile=$3
jobid_list=$4
gpuid=$5
PROCID=0

# setup the container software
# ----------------------------

export PATH=/usr/local/nvidia:${PATH}
export LD_LIBRARY_PATH=/usr/local/nvidia:${LD_LIBRARY_PATH}
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1

# ROOT6
source /usr/local/bin/thisroot.sh

# larbys stack
source /etc/larbys.sh
cd /usr/local/larbys/ssnet_example/sw
source setup.sh

# go to job dir
# -------------
cd $jobdir

echo "WORKDIR/CURRENTDIR: "${PWD}
echo "INPUTLIST DIR: "${inputlist_dir}
echo "OUTPUT FILE: "${outputfile}
echo "JOBID_LIST:"${jobid_list}
echo "GPU ID: "${gpuid}
echo "MKL_NUM_THREADS=${MKL_NUM_THREADS}"
echo "OMP_NUM_THREADS=${OMP_NUM_THREADS}"

# check that the process number is greater than the number of job ids
let NUM_PROCS=`cat ${jobid_list} | wc -l`
echo "number of processes: $NUM_PROCS"
if [ "$NUM_PROCS" -lt "${SLURM_PROCID}" ]; then
    echo "No Procces ID to run."
    return
fi

# Get job id
let "proc_line=${PROCID}+1"
let jobid=`sed -n ${proc_line}p ${jobid_list}`
echo "JOBID ${jobid}"

# make path to input list
inputlist=`printf ${inputlist_dir}/inputlist_%09d.txt ${jobid}`

# get input files
larcv_file=`sed -n 1p ${inputlist}`
tagger_file=`sed -n 2p ${inputlist}`

slurm_folder=`printf slurm_ssnet_job%09d ${jobid}`
mkdir -p ${slurm_folder}

# Make log file
logfile=`printf ${slurm_folder}/log_%09d.txt ${jobid}`

# echo into it
echo "RUNNING SSNET JOB ${jobid}" > $logfile
echo "larcv file: ${larcv_file}" >> $logfile
echo "tagger file: ${tagger_file}" >> $logfile

# temp output file
outfile_temp=`printf ${slurm_folder}/ssnet_out_%09d.root ${jobid}`

echo "temporary output file: ${outfile_temp}" >> $logfile

# define output
outfile_ssnet=$outputfile
echo "final output location: ${outfile_ssnet}" >> $logfile

# command
echo "RUNNING: python run_ssnet_mcc8.py ${jobid} ${gpuid} ${outfile_temp} ${larcv_file} ${tagger_file}" >> $logfile

# RUN
python run_ssnet_mcc8.py ${jobid} ${gpuid} ${outfile_temp} ${larcv_file} ${tagger_file} >> $logfile 2>&1 || exit

# ONE DAY TELL THE PUBSDB WE'RE DONE

# COPY DATA
cp $outfile_temp $outfile_ssnet

# clean up
rm -r $slurm_folder
