#!/bin/bash

cd /usr/local/ubdl
source setenv.sh
source configure.sh
cd scripts
source setenv_ublarcvserver.sh

weightdir=/cluster/kappa/wongjiradlab/larbys/ssnet_models/v1_pytorch_extracted/
let line=${SLURM_ARRAY_TASK_ID}+1
devnum=`sed -n ${line}p /cluster/kappa/wongjiradlab/larbys/pubs/dlleepubs/ubdlserver/tufts_pgpu03_assignments.txt`
device=`printf cuda:%d ${devnum}`
logfile=`printf /tmp/worker_id%d.log ${SLURM_ARRAY_TASK_ID}`
script=/cluster/kappa/wongjiradlab/larbys/pubs/dlleepubs/ubdlserver/start_ublarcvserver_worker.py
#scrpit=start_ublarcvserver_worker.py
cmd="python ${script} -l ${logfile} -d tcp://localhost:6000 -m ${device} -w ${weightdir}"

echo $cmd
$cmd

