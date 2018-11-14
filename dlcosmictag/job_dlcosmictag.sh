#!/bin/bash

# we are not in the container

CONVERT_CONTAINER=$1
LARBYS_PYTORCH_CONTAINER=$2
larcv1_supera_path=$3
OUTPUT_DIRECTORY=$4
WEIGHTS_DIR=$5
WORKDIR=$6

jobid=${SLURM_ARRAY_TASK_ID}
let gpuid=${jobid}%6
ROOTSCRIPT=/usr/local/root/release/bin/thisroot.sh
echo "SLURM JOBID: ${SLURM_JOB_ID}"
echo "SLURM ARRAYID: ${SLURM_ARRAY_TASK_ID}"
echo "GPUID: ${gpuid}"


# Step Zero: setup
# ----------------
# setup singularity
module load singularity
# job directory
jobdir=`printf /tmp/jobdir_dlcosmictag_%d_%03d ${SLURM_JOB_ID} ${SLURM_ARRAY_TASK_ID}` 
mkdir -p $jobdir
cd $jobdir
ls -lh

# Step One: conversion from larcv1 to larcv2
# ------------------------------------------
# copy to jobdir
PRODUCTLIST="image2d:wire image2d:ancestor chstatus:wire chstatus:wiremc"
larcv1_supera=$(basename ${larcv1_supera_path})
convertoutput=${jobdir}/convertout.root
#scp ${larcv1_supera_path} ${jobdir}/
#singularity exec ${CONVERT_CONTAINER} /bin/bash -c "source ${ROOTSCRIPT} && cd /usr/local/convertlarcv/ && python convert_larcv1_to_larcv2.py ${jobdir}/${larcv1_supera} ${convertoutput} jobid${SLURM_JOBID}p${SLURM_ARRAY_TASK_ID} ${PRODUCTLIST}"
# for debug, copy the output to workdir
#cp *.root ${WORKDIR}

# Step Two: produce different neural network output
# -------------------------------------------------

# LArFlow wholeview to cropped images
# Y2U
# Y2V
# debug copy larcv2 conversion file to job
scp ${WORKDIR}/convertout.root ${convertoutput}
# debug copy of larflow
larflow_repodir_ic=/cluster/kappa/wongjiradlab/twongj01/larflow
# container copy of larflow
#larflow_repodir_ic=/usr/local/larflow

outfile_larflowy2u=`printf %s/larflowout_y2u.root ${jobdir}`
outfile_larflowy2v=`printf %s/larflowout_y2v.root ${jobdir}`
checkpoint_larflow_y2u="/tmp/larflow_weights/devfiltered_larflow_y2u_832x512_32inplanes.tar"
checkpoint_larflow_y2v="/tmp/larflow_weights/devfiltered_larflow_y2v_832x512_32inplanes.tar"
cd ${larflow_repodir_ic}/deploy/
deploy_y2u="python run_larflow_wholeview.py -i ${convertoutput} -o ${outfile_larflowy2u} -c ${checkpoint_larflow_y2u} -f Y2U -g ${gpuid} -b 2 --saveadc --workdir=${jobdir}/"
deploy_y2v="python run_larflow_wholeview.py -i ${convertoutput} -o ${outfile_larflowy2v} -c ${checkpoint_larflow_y2v} -f Y2V -g ${gpuid} -b 2 --workdir=${jobdir}/"
echo "Y2U command: ${deploy_y2u}"
echo "Y2V command: ${deploy_y2v}"

singularity exec --nv ${LARBYS_PYTORCH_CONTAINER} bash -c "source ${ROOTSCRIPT} && cd ${larflow_repodir_ic} && source configure.sh && cd deploy && ${deploy_y2u}"
singularity exec --nv ${LARBYS_PYTORCH_CONTAINER} bash -c "source ${ROOTSCRIPT} && cd ${larflow_repodir_ic} && source configure.sh && cd deploy && ${deploy_y2v}"

# Infill crops to crops
# Y
# U
# V

# Extended SSNet
# Y
# U
# V

# Step 3: Hadd
# -------------

# Step 4: LArFlow Post-processor
# ------------------------------
# Produces larlite hits and output larcv with whole-view labels

# Step 5: Truth cluster
# ---------------------

# Step 6: Flash-Match
# --------------------


# Transfer to output
# ------------------
