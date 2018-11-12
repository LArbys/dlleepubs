#!/bin/bash

# we are not in the container

CONVERT_CONTAINER=$1
LARBYS_PYTORCH_CONTAINER=$2
larcv1_supera_path=$3
OUTPUT_DIRECTORY=$4
WEIGHTS_DIR=$5
WORKDIR=$6

jobid=${SLURM_ARRAY_JOB_ID}
ROOTSCRIPT=/usr/local/root/release/bin/thisroot.sh

# Step Zero: setup
# ----------------
# setup singularity
module load singularity
# job directory
jobdir=`printf /tmp/jobdir_dlcosmictag_%d_%03d ${SLURM_JOB_ID} ${SLURM_ARRAY_JOB_ID}` 
mkdir -p $jobdir
cd $jobdir

# Step One: conversion from larcv1 to larcv2
# ------------------------------------------
# copy to jobdir
PRODUCTLIST="image2d:wire image2d:segment chstatus:wire chstatus:wiremc"
larcv1_supera=$(basename ${larcv1_supera_path})
scp ${larcv1_supera_path} .
singularity exec bash -c "source ${ROOTSCRIPT} && cd /usr/local/convertlarcv/ && python convert_larcv1_to_larcv2.py /tmp/${larcv1_supera} ${PRODUCTLIST}" 

# Step Two: produce different neural network output
# -------------------------------------------------

# LArFlow wholeview to cropped images
# Y2U
# Y2V
deploy_y2u="./run_larflow_wholeview.py -i ${converted_larcv1} -o ${outfile_larflowy2u} -c ${checkpoint_larflow_y2u} -f Y2U -g ${gpuid} -b 1 --ismc --saveadc"
deploy_y2v="./run_larflow_wholeview.py -i ${converted_larcv1} -o ${outfile_larflowy2v} -c ${checkpoint_larflow_y2v} -f Y2V -g ${gpuid} -b 1"
singularity exec bash -c "source ${ROOTSCRIPT} cd /usr/local/larflow && source configure.sh && cd deploy && ${deploy_y2u}"

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
