#!/bin/bash

# we are not in the container

CONVERT_CONTAINER=$1
LARBYS_PYTORCH_CONTAINER=$2
larcv1_supera_path=$3
OUTPUT_DIRECTORY=$4
WEIGHTS_DIR=$5
WORKDIR=$6

jobid=${SLURM_ARRAY_TASK_ID}
#let gpuid=${jobid}%6
gpuid=0
ROOTSCRIPT=/usr/local/root/release/bin/thisroot.sh
WORKDIR_IC=`echo ${WORKDIR} | sed 's/90-days-archive//g'`

echo "SLURM JOBID: ${SLURM_JOB_ID}"
echo "SLURM ARRAYID: ${SLURM_ARRAY_TASK_ID}"
echo "GPUID: ${gpuid}"
echo "WORKDIR: ${WORKDIR}"
echo "WORKDIR IN CONTAINER: ${WORKDIR_IC}"


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
larlite_mcinfo_ic=`echo ${larcv1_supera_path} | sed 's/supera/mcinfo/g' | sed 's/90-days-archive//'`
larlite_opreco_ic=`echo ${larcv1_supera_path} | sed 's/supera/opreco/g' | sed 's/90-days-archive//'`
larlite_reco2d_ic=`echo ${larcv1_supera_path} | sed 's/supera/reco2d/g' | sed 's/90-days-archive//'`
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
larflow_repodir=/cluster/kappa/90-days-archive/wongjiradlab/twongj01/larflow
larflow_repodir_ic=/cluster/kappa/wongjiradlab/twongj01/larflow
# container copy of larflow
#larflow_repodir_ic=/usr/local/larflow

outfile_larflowy2u=`printf %s/larflowout_y2u.root ${jobdir}`
outfile_larflowy2v=`printf %s/larflowout_y2v.root ${jobdir}`
checkpoint_larflow_y2u="/tmp/larflow_weights/devfiltered_larflow_y2u_832x512_32inplanes.tar"
checkpoint_larflow_y2v="/tmp/larflow_weights/devfiltered_larflow_y2v_832x512_32inplanes.tar"
deploy_y2u="python run_larflow_wholeview.py -i ${convertoutput} -o ${outfile_larflowy2u} -c ${checkpoint_larflow_y2u} -f Y2U -g ${gpuid} -b 2 --saveadc --workdir=${jobdir}/"
deploy_y2v="python run_larflow_wholeview.py -i ${convertoutput} -o ${outfile_larflowy2v} -c ${checkpoint_larflow_y2v} -f Y2V -g ${gpuid} -b 2 --workdir=${jobdir}/"
echo "Y2U command: ${deploy_y2u}"
echo "Y2V command: ${deploy_y2v}"
#singularity exec --nv ${LARBYS_PYTORCH_CONTAINER} bash -c "source ${ROOTSCRIPT} && cd ${larflow_repodir_ic} && source configure.sh && cd deploy && ${deploy_y2u}"
#singularity exec --nv ${LARBYS_PYTORCH_CONTAINER} bash -c "source ${ROOTSCRIPT} && cd ${larflow_repodir_ic} && source configure.sh && cd deploy && ${deploy_y2v}"

# Infill crops to crops
# U,V,Y in one step
infill_checkpointdir=/tmp/larflow_weights
infill_tmp=`printf %s/output_infill.root ${jobdir}`
deploy_infill="python run_infill_wholeview.py -i ${convertoutput} -o ${infill_tmp} -cd ${infill_checkpointdir} -g ${gpuid} -b 1"
echo "Infill command: ${deploy_infill}"
#singularity exec --nv ${LARBYS_PYTORCH_CONTAINER} bash -c "source ${ROOTSCRIPT} && cd ${larflow_repodir_ic} && source configure.sh && cd deploy && ${deploy_infill}"

# Extended SSNet
# U,V,Y in one step
ssnet_checkpointdir=/tmp/larflow_weights
ssnet_tmp=`printf %s/output_ssnet.root ${jobdir}`
deploy_ssnet="python run_endptssnet_wholeview.py -i ${convertoutput} -o ${ssnet_tmp} -cd ${ssnet_checkpointdir} -g ${gpuid} -b 1"
echo "SSNet command: ${deploy_ssnet}"
#singularity exec --nv ${LARBYS_PYTORCH_CONTAINER} bash -c "source ${ROOTSCRIPT} && cd ${larflow_repodir_ic} && source configure.sh && cd deploy && ${deploy_ssnet}"

# Step 3: Hadd
# -------------
larflow_y2u_tmp=${WORKDIR_IC}/larflowout_y2u_masked.root
larflow_y2v_tmp=${WORKDIR_IC}/larflowout_y2v_masked.root
infill_tmp=${WORKDIR_IC}/output_infill_masked.root
ssnet_tmp=${WORKDIR_IC}/output_ssnet.root
output_hadd=${jobdir}/dlcosmictag-larcv.root
cmd_hadd="hadd -f ${output_hadd} ${larflow_y2u_tmp} ${larflow_y2v_tmp} ${infill_tmp} ${ssnet_tmp}"
#singularity exec ${LARBYS_PYTORCH_CONTAINER} bash -c "source ${ROOTSCRIPT} && cd ${larflow_repodir_ic} && source configure.sh && cd ${jobdir} && ${cmd_hadd}"

# Step 4: LArFlow Post-processor
# ------------------------------
# Produces larlite hits and output larcv with whole-view labels
output_flowhits_larcv=${jobdir}/output_pixflow_larcv.root
output_flowhits_larlite=${jobdir}/output_pixflow_larlite.root
cmd_postprocessor="./dev -su ${convertoutput} -re ${larlite_reco2d_ic} -mc ${larlite_mcinfo_ic} -op ${larlite_opreco_ic} -y2u ${larflow_y2u_tmp} -y2v ${larflow_y2v_tmp} -adc ${larflow_y2u_tmp} -in ${infill_tmp} -ss ${ssnet_tmp} -j ${jobid} -oll ${output_flowhits_larlite} -olc ${output_flowhits_larcv}"
echo "flow cluster match: ${cmd_postprocessor}"
#singularity exec ${LARBYS_PYTORCH_CONTAINER} bash -c "source ${ROOTSCRIPT} && cd ${larflow_repodir_ic} && source configure.sh && cd postprocessor && ${cmd_postprocessor}"

# Step 5: Truth cluster
# ---------------------
input_flowhits_tmp=${WORKDIR_IC}/output_pixflow_larlite.root
output_truthcluster=${jobdir}/output_truthcluster_larlite.root
cmd_truthcluster="./dev_truthcluster ${input_flowhits_tmp} ${output_truthcluster}"
#singularity exec ${LARBYS_PYTORCH_CONTAINER} bash -c "source ${ROOTSCRIPT} && cd ${larflow_repodir_ic} && source configure.sh && cd postprocessor/cluster && ${cmd_truthcluster}"

# Step 6: Flash-Match
# --------------------
output_flashmatch=${jobdir}/output_dev_flashmatch.root
input_truthcluster_tmp=${WORKDIR_IC}/output_truthcluster_larlite.root
cmd_flashmatch="./dev_flashmatch ${input_truthcluster_tmp} ${larlite_reco2d_ic} ${convertoutput} ${larlite_mcinfo_ic} ${output_flashmatch}"
singularity exec ${LARBYS_PYTORCH_CONTAINER} bash -c "source ${ROOTSCRIPT} && cd ${larflow_repodir_ic} && source configure.sh && cd postprocessor/flashmatch && ${cmd_flashmatch}"

# Transfer to output
# ------------------
