#!/bin/bash

# we are not in the container at the start of this script

# collect arguments
WORKDIR=$1

CONTAINER_LARFLOW=$2
CONTAINER_DLLEE=$3

INPUT_SUPERA_LARCV1=$4
INPUT_SUPERA_LARCV2=$5
INPUT_FLASHMATCH=$6
INPUT_DLCOSMICTAG=$7

OUTPUT_FILLMASK=$8
OUTPUT_DLSTITCH=$9
OUTPUT_DLVERTEX=${10}
OUTPUT_DLVERTEXANA=${11}

jobid=${SLURM_ARRAY_TASK_ID}

ROOTSCRIPT_LARFLOW=/usr/local/root/release/bin/thisroot.sh
ROOTSCRIPT_DLLEE=/usr/local/bin/thisroot.sh

LARFLOW_DIR_IC=/cluster/kappa/wongjiradlab/twongj01/larflow
DLLEE_DIR_IC=/cluster/kappa/wongjiradlab/twongj01/dllee_unified

WORKDIR_IC=`echo ${WORKDIR} | sed 's/90-days-archive//g'`
supera_larcv1_ic=`echo ${INPUT_SUPERA_LARCV1} | sed 's/90-days-archive//g'`
supera_larcv2_ic=`echo ${INPUT_SUPERA_LARCV2} | sed 's/90-days-archive//g'`
flashmatch_larlite_ic=`echo ${INPUT_FLASHMATCH} | sed 's/90-days-archive//g'`
dlcosmictag_larcv2_ic=`echo ${INPUT_DLCOSMICTAG} | sed 's/90-days-archive//g'`

echo "SLURM JOBID: ${SLURM_JOB_ID}"
echo "WORKDIR IN CONTAINER: ${WORKDIR_IC}"

# step zero: prep

# setup singularity
module load singularity

# go to workdir
cd $WORKDIR

# Step one: fillmask
# ------------------
echo "FILLMASK"
tmpout_fillmask=${WORKDIR_IC}/fillmask-larlite.root
log_fillmask=${WORKDIR_IC}/log_fillmask.log
cmd_fillmask="./dev_fillcluster ${flashmatch_larlite_ic} ${supera_larcv2_ic} ${tmpout_fillmask}"
cmd_setupenv="source ${ROOTSCRIPT_LARFLOW} && cd ${LARFLOW_DIR_IC} && source configure.sh && cd postprocessor/cluster"
echo $cmd_fillmask
singularity exec ${CONTAINER_LARFLOW} bash -c "${cmd_setupenv} && ${cmd_fillmask} > ${log_fillmask}"

# Step two: dlstitch
# ------------------
echo "DLSTITCH"
tmpout_dlstitch=${WORKDIR_IC}/dlstitch-larlite.root
log_dlstitch=${WORKDIR_IC}/log_dlstitch.log
cmd_dlstitch="./stitch_dlcosmic_images ${dlcosmictag_larcv2_ic} ${supera_larcv2_ic} ${tmpout_dlstitch}"
cmd_setupenv_dlstitch="source ${ROOTSCRIPT_LARFLOW} && cd ${LARFLOW_DIR_IC} && source configure.sh && cd postprocessor/imgstitch"
echo $cmd_dlstitch
singularity exec ${CONTAINER_LARFLOW} bash -c "${cmd_setupenv_dlstitch} && ${cmd_dlstitch} > ${log_dlstitch}"

# step three: vertex
# ------------------
echo "VERTEX"
# define filenames
tmpout_dlvertex=${WORKDIR_IC}/dlvertex-larcv.root
tmpout_dlvertexana=${WORKDIR_IC}/dlvertex-ana.root
log_dlvertex=${WORKDIR_IC}/log_dlvertex.log
template_dlvertex=${WORKDIR}/dlcosmictag_vertexreco_template.cfg
cfg_dlvertex=${WORKDIR}/dlcosmictag_vertexreco.cfg
cfg_dlvertex_ic=${WORKDIR_IC}/dlcosmictag_vertexreco.cfg

# substitute portions of the config with filenames
protect_fillmask=`echo ${tmpout_fillmask} | sed 's|\/|\\\/|g'`
protect_dlstitch=`echo ${tmpout_dlstitch} | sed 's|\/|\\\/|g'`
protect_dlvertexana=`echo ${tmpout_dlvertexana} | sed 's|\/|\\\/|g'`

sub_fillmask="s/XXXX/${protect_fillmask}/g"
sub_dlstitch="s/YYYY/${protect_dlstitch}/g"
sub_dlvertexana="s/ZZZZ/${protect_dlvertexana}/g"
sed -e ${sub_fillmask} ${template_dlvertex} > ${cfg_dlvertex}
sed -i -e ${sub_dlstitch} ${cfg_dlvertex}
sed -i -e ${sub_dlvertexana} ${cfg_dlvertex}
sed -i -e 's/90-days-archive//g' ${cfg_dlvertex}

cmd_dlvertex="./run_test ${supera_larcv1_ic} ${cfg_dlvertex_ic} ${tmpout_dlvertex}"
cmd_setupenv_dlvertex="source ${ROOTSCRIPT_DLLEE} && cd ${DLLEE_DIR_IC} && source configure.sh && cd LArCV/app/DLCosmicTag/tests"

# run it
singularity exec ${CONTAINER_DLLEE} bash -c "${cmd_setupenv_dlvertex} && ${cmd_dlvertex} > ${log_dlvertex}"

# copy output to db dir
# ---------------------
scp ${WORKDIR}/$(basename $tmpout_fillmask) ${OUTPUT_FILLMASK}
scp ${WORKDIR}/$(basename $tmpout_dlstitch) ${OUTPUT_DLSTITCH}
scp ${WORKDIR}/$(basename $tmpout_dlvertex) ${OUTPUT_DLVERTEX}
scp ${WORKDIR}/$(basename $tmpout_dlvertexana) ${OUTPUT_DLVERTEXANA}

# clean up
# ---------

