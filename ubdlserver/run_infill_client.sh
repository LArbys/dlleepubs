#!/bin/bash

inputfile=$1
outputfile=$2
job_workdir=$3
logfile=infill_client.log
script=/cluster/tufts/wongjiradlab/kmason03/uboonecode/ubdl/ublarcvserver/app/UBInfill/clustertest/start_ublarcvserver_infill_client.py

cd /cluster/tufts/wongjiradlab/kmason03/uboonecode/ubdl
source setenv.sh
source configure.sh

cd ublarcvserver
source configure.sh
cd app/UBInfill/clustertest
ls

export PYTHONPATH=$PWD:$PYTHONPATH
cp $script $job_workdir/
cd $job_workdir

echo "ARG: $3"
echo "WORKDIR: $job_workdir"
echo "PWD: $PWD"
echo "PYTHONPATH: ${PYTHONPATH}"

cmd="python ${script} -l ${logfile} -d tcp://10.246.81.72:6000 -i ${inputfile} -o ${outputfile} -t True"

echo $cmd
$cmd
