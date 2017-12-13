#!/bin/bash

GPUID=$1
WORKDIR=$2
OUTFILE=$3
INPUTLISTS=${WORKDIR}/inputlists
JOBIDLIST=${WORKDIR}/rerunlist.txt

echo "launching job=$i" && cd ${WORKDIR} && ./run_gpu_job.sh ${WORKDIR} ${INPUTLISTS} ${OUTFILE} ${JOBIDLIST} ${GPUID} >> log_ssnettufts_job.txt 2>&1 &
