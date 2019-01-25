#!/bin/bash

# we are not in the container

CONVERT_CONTAINER=$1
LARBYS_PYTORCH_CONTAINER=$2
larcv1_supera_path=$3
OUTPUT_DIRECTORY=$4
WEIGHTS_DIR=$5
WORKDIR=$6
gpuid=$7 # currently gets it from pubs launch processor -- fragile! can only run 6 jobs at a time

jobid=${SLURM_ARRAY_TASK_ID}
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

# debug: copy past root files to work dir
echo "debug: copy past root files from work dir to job dir"
scp ${WORKDIR}/*.root ${jobdir}/


# Step One: conversion from larcv1 to larcv2
# ------------------------------------------
# define paths and parameters for conversion job
PRODUCTLIST_SUPERA="image2d:wire chstatus:wire"
PRODUCTLIST_MCTRUTH="image2d:ancestor image2d:segment chstatus:wiremc"
larcv1_mctruth_path=`echo ${larcv1_supera_path} | sed 's/supera/larcvtruth/g'`
larcv1_supera=$(basename ${larcv1_supera_path})
larcv1_mctruth=$(basename ${larcv1_mctruth_path})
feed_dir=`printf /tmp/feedjobid%d ${SLURM_JOBID}`
feed_dirp=`printf /tmp/feedjobid%dp ${SLURM_JOBID}`

# larlite files -- we reference network drive locations
larlite_opreco_ic=`echo ${larcv1_supera_path} | sed 's/supera/opreco/g' | sed 's/90-days-archive//'`
larlite_reco2d_ic=`echo ${larcv1_supera_path} | sed 's/supera/reco2d/g' | sed 's/90-days-archive//'`
# mcc9 uses backtracker/reco2d file
larlite_mcinfo_ic=`echo ${larcv1_supera_path} | sed 's/supera/reco2d/g' | sed 's/90-days-archive//'`
# mcc8 has mcinfo file
larlite_mcinfo_ic=`echo ${larcv1_supera_path} | sed 's/supera/mcinfo/g' | sed 's/90-days-archive//'`

larcv2_supera=`echo ${larcv1_supera} | sed 's/supera/supera-larcv2/g'`
larcv2_mctruth=`echo ${larcv1_mctruth} | sed 's/supera/larcvtruth-larcv2/g'`
supera_convert_output=`printf %s/%s ${jobdir} ${larcv2_supera}`
mctruth_convert_output=`printf %s/%s ${jobdir} ${larcv2_mctruth}`
a
# copy input to jobdir
scp ${larcv1_supera_path} ${jobdir}/
scp ${larcv1_mctruth_path} ${jobdir}/

# SUPERA conversion
singularity exec ${CONVERT_CONTAINER} /bin/bash -c "source ${ROOTSCRIPT} && cd /usr/local/convertlarcv/ && python convert_larcv1_to_larcv2.py ${jobdir}/${larcv1_supera} ${supera_convert_output} jobid${SLURM_JOBID}p${SLURM_ARRAY_TASK_ID} ${PRODUCTLIST_SUPERA}" || exit

# LARCV-TRUTH conversion
singularity exec ${CONVERT_CONTAINER} /bin/bash -c "source ${ROOTSCRIPT} && cd /usr/local/convertlarcv/ && python convert_larcv1_to_larcv2.py ${jobdir}/${larcv1_mctruth} ${mctruth_convert_output} jobid${SLURM_JOBID}p${SLURM_ARRAY_TASK_ID} ${PRODUCTLIST_MCTRUTH}" || exit

# Step Two: produce different neural network output
# -------------------------------------------------

# LArFlow wholeview to cropped images
# Y2U
# Y2V

# debug: copy of larflow on network drive
larflow_repodir=/cluster/kappa/90-days-archive/wongjiradlab/twongj01/larflow
larflow_repodir_ic=/cluster/kappa/wongjiradlab/twongj01/larflow
# container copy of larflow
#larflow_repodir_ic=/usr/local/larflow

outfile_larflowy2u=`printf %s/larflowout_y2u.root ${jobdir}`
outfile_larflowy2v=`printf %s/larflowout_y2v.root ${jobdir}`
checkpoint_larflow_y2u="/tmp/larflow_weights/devfiltered_larflow_y2u_832x512_32inplanes.tar"
checkpoint_larflow_y2v="/tmp/larflow_weights/devfiltered_larflow_y2v_832x512_32inplanes.tar"
deploy_y2u="python run_larflow_wholeview.py -i ${supera_convert_output} -o ${outfile_larflowy2u} -c ${checkpoint_larflow_y2u} -f Y2U -g ${gpuid} -b 2 --saveadc --workdir=${jobdir}/"
deploy_y2v="python run_larflow_wholeview.py -i ${supera_convert_output} -o ${outfile_larflowy2v} -c ${checkpoint_larflow_y2v} -f Y2V -g ${gpuid} -b 2 --workdir=${jobdir}/"
echo "Y2U command: ${deploy_y2u}"
echo "Y2V command: ${deploy_y2v}"
singularity exec --nv ${LARBYS_PYTORCH_CONTAINER} bash -c "source ${ROOTSCRIPT} && cd ${larflow_repodir_ic} && source configure.sh && cd deploy && ${deploy_y2u}" || exit
singularity exec --nv ${LARBYS_PYTORCH_CONTAINER} bash -c "source ${ROOTSCRIPT} && cd ${larflow_repodir_ic} && source configure.sh && cd deploy && ${deploy_y2v}" || exit

# Infill on crops
# U,V,Y in one step
infill_checkpointdir=/tmp/larflow_weights
infill_out=`printf %s/output_infill.root ${jobdir}`
deploy_infill="python run_infill_wholeview.py -i ${supera_convert_output} -o ${infill_out} -cd ${infill_checkpointdir} -g ${gpuid} -b 1"
echo "Infill command: ${deploy_infill}"
singularity exec --nv ${LARBYS_PYTORCH_CONTAINER} bash -c "source ${ROOTSCRIPT} && cd ${larflow_repodir_ic} && source configure.sh && cd deploy && ${deploy_infill}" || exit

# Extended SSNet
# U,V,Y in one step
ssnet_checkpointdir=/tmp/larflow_weights
ssnet_out=`printf %s/output_ssnet.root ${jobdir}`
deploy_ssnet="python run_endptssnet_wholeview.py -i ${supera_convert_output} -o ${ssnet_out} -cd ${ssnet_checkpointdir} -g ${gpuid} -b 1"
echo "SSNet command: ${deploy_ssnet}"
singularity exec --nv ${LARBYS_PYTORCH_CONTAINER} bash -c "source ${ROOTSCRIPT} && cd ${larflow_repodir_ic} && source configure.sh && cd deploy && ${deploy_ssnet}" || exit

# Step 3: Hadd
# -------------
# debug
#larflow_y2u_tmp=${WORKDIR_IC}/larflowout_y2u_masked.root
#larflow_y2v_tmp=${WORKDIR_IC}/larflowout_y2v_masked.root
#infill_tmp=${WORKDIR_IC}/output_infill_masked.root
#ssnet_tmp=${WORKDIR_IC}/output_ssnet.root
output_hadd_basename=`echo ${larcv1_supera} | sed 's/supera/dlcosmictag-larcv2/g'`
output_hadd=${jobdir}/${output_hadd_basename}
cmd_hadd="hadd -f ${output_hadd} ${outfile_larflowy2u} ${outfile_larflowy2v} ${infill_out} ${ssnet_out}"
singularity exec ${LARBYS_PYTORCH_CONTAINER} bash -c "source ${ROOTSCRIPT} && cd ${larflow_repodir_ic} && source configure.sh && cd ${jobdir} && ${cmd_hadd}" || exit

# Step 4: LArFlow Post-processor
# ------------------------------
# Produces larlite hits and output larcv with whole-view labels
output_flowhits_larcv_basename=`echo ${larcv1_supera} | sed 's/supera/larflowhits-larcv2/g'`
output_flowhits_larlite_basename=`echo ${larcv1_supera} | sed 's/supera/larflowhits-larlite/g'`
output_flowhits_larcv=${jobdir}/${output_flowhits_larcv_basename}
output_flowhits_larlite=${jobdir}/${output_flowhits_larlite_basename}
#cmd_postprocessor="./dev -su ${convertoutput} -re ${larlite_reco2d_ic} -mc ${larlite_mcinfo_ic} -op ${larlite_opreco_ic} -y2u ${larflow_y2u_tmp} -y2v ${larflow_y2v_tmp} -adc ${larflow_y2u_tmp} -in ${infill_out} -ss ${ssnet_tmp} -j ${jobid} -oll ${output_flowhits_larlite} -olc ${output_flowhits_larcv}"
cmd_postprocessor="./dev -su ${supera_convert_output} -mc ${larlite_reco2d_ic} -re ${larlite_reco2d_ic} -op ${larlite_opreco_ic} -y2u ${outfile_larflowy2u} -y2v ${outfile_larflowy2v} -adc ${outfile_larflowy2u} -in ${infill_out} -ss ${ssnet_out} -j ${jobid} -oll ${output_flowhits_larlite} -olc ${output_flowhits_larcv} -lcvt ${mctruth_convert_output} --use-ancestor-img --has-infill"
echo "LARFLOW HITS: ${cmd_postprocessor}"
singularity exec ${LARBYS_PYTORCH_CONTAINER} bash -c "source ${ROOTSCRIPT} && cd ${larflow_repodir_ic} && source configure.sh && cd postprocessor && ${cmd_postprocessor}" || exit

# Step 5: Truth cluster
# ---------------------
output_truthcluster_larlite_basename=`echo ${larcv1_supera} | sed 's/supera/truthcluster-larlite/g'`
#input_flowhits=${WORKDIR_IC}/output_pixflow_larlite.root
input_flowhits=${output_flowhits_larlite}
output_truthcluster=${jobdir}/${output_truthcluster_larlite_basename}
cmd_truthcluster="./dev_truthcluster ${input_flowhits} ${output_truthcluster}"
#echo "TRUTH CLUSTER: ${cmd_truthcluster}"
#singularity exec ${LARBYS_PYTORCH_CONTAINER} bash -c "source ${ROOTSCRIPT} && cd ${larflow_repodir_ic} && source configure.sh && cd postprocessor/cluster && ${cmd_truthcluster}" || exit

# Step 6: Flash-Match
# --------------------
output_flashmatch=${jobdir}/output_dev_flashmatch.root
#input_truthcluster=${WORKDIR_IC}/${output_truthcluster_larlite_basename}
input_truthcluster=${output_truthcluster}/${output_truthcluster_larlite_basename}
cmd_flashmatch="./dev_flashmatch ${input_truthcluster} ${larlite_reco2d_ic} ${supera_convert_output} ${larlite_mcinfo_ic} ${output_flashmatch}"
#echo "FLASHMATCH: ${cmd_flashmatch}"
#singularity exec ${LARBYS_PYTORCH_CONTAINER} bash -c "source ${ROOTSCRIPT} && cd ${larflow_repodir_ic} && source configure.sh && cd postprocessor/flashmatch && ${cmd_flashmatch}" || exit

# Transfer to output
# ------------------

finaloutput_supera_larcv2=`printf %s/%s ${OUTPUT_DIRECTORY} ${larcv2_supera}`
finaloutput_mctruth_larcv2=`printf %s/%s ${OUTPUT_DIRECTORY} ${larcv2_mctruth}`
finaloutput_hadd_larcv=${OUTPUT_DIRECTORY}/${output_hadd_basename}
finaloutput_flowhits_larcv=${OUTPUT_DIRECTORY}/${output_flowhits_larcv_basename}
finaloutput_flowhits_larlite=${OUTPUT_DIRECTORY}/${output_flowhits_larlite_basename}
finaloutput_truthcluster_larlite=${OUTPUT_DIRECTORY}/${output_truthcluster_larlite_basename}

mkdir -p ${OUTPUT_DIRECTORY}

scp ${supera_convert_output} ${finaloutput_supera_larcv2} || exit
scp ${mctruth_convert_output} ${finaloutput_mctruth_larcv2} || exit
scp ${output_hadd} ${finaloutput_hadd_larcv} || exit
scp ${output_flowhits_larcv} ${finaloutput_flowhits_larcv} || exit
scp ${output_flowhits_larlite} ${finaloutput_flowhits_larlite} || exit
#scp ${output_truthcluster} ${finaloutput_truthcluster_larlite} || exit

# clean up
# ---------
echo "clean up"
rm -rf ${jobdir}
rm -rf ${feed_dir}
rm -rf ${feed_dirp}
