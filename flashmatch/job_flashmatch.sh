#!/bin/bash

WORKDIR=$1
LARBYS_PYTORCH_CONTAINER=$2

# INPUTS
# (remember that supera is LARCV2 at this point)
SUPERA_INPUT_IC=$3
INPUT_FLOWHITS=$4
OPRECO_INPUT_IC=$5
MCINFO_INPUT_IC=$6

# OUTPUTS
TRUTHCLUSTER_OUTPUT=$7
LARCV_OUTFILE=$8
LARLITE_OUTFILE=$9
ANA_OUTFILE=${10}

ROOTSCRIPT=/usr/local/root/release/bin/thisroot.sh
WORKDIR_IC=`echo ${WORKDIR} | sed 's/90-days-archive//g'`

larflow_repodir=/cluster/kappa/90-days-archive/wongjiradlab/twongj01/dev/larflow
larflow_repodir_ic=/cluster/kappa/wongjiradlab/twongj01/dev/larflow

# CREATE JOBDIR
jobdir=/tmp/dlfashmatch_${SLURM_JOB_ID}
mkdir -p $jobdir
cd $jobdir

# LOAD UP SINGULARITY
module load singularity

# CREATE TWO FILES: ClUSTER+FLASHMATCH

# Truth Clustering
# ---------------------
tmp_truthcluster=${jobdir}/output_truthcluster.root
cmd_truthcluster="./dev_truthcluster ${INPUT_FLOWHITS} ${tmp_truthcluster}"
echo "TRUTH CLUSTER: ${cmd_truthcluster}"
singularity exec ${LARBYS_PYTORCH_CONTAINER} bash -c "source ${ROOTSCRIPT} && cd ${larflow_repodir_ic} && source configure.sh && cd postprocessor/cluster && ${cmd_truthcluster}" || exit

# Flash-Match
# --------------------
output_flashmatch_larcv=${jobdir}/output_larcv_flashmatch.root
output_flashmatch_larlite=${jobdir}/output_larlite_flashmatch.root
output_flashmatch_ana=${jobdir}/output_ana_flashmatch.root
CMD="./dev_flashmatch ${tmp_truthcluster} ${OPRECO_INPUT_IC} ${SUPERA_INPUT_IC} ${MCINFO_INPUT_IC} ${output_flashmatch_larlite} ${output_flashmatch_larcv} ${output_flashmatch_ana}"
echo "FLASHMATCH: ${CMD}"
singularity exec ${LARBYS_PYTORCH_CONTAINER} bash -c "cd ${WORKDIR_IC} && source ${ROOTSCRIPT} && cd ${larflow_repodir_ic} && source configure.sh && cd postprocessor/flashmatch && ${CMD}" || exit

scp ${tmp_truthcluster}        ${TRUTHCLUSTER_OUTPUT}
scp $output_flashmatch_larcv   ${LARCV_OUTFILE}
scp $output_flashmatch_larlite ${LARLITE_OUTFILE}
scp $output_flashmatch_ana     ${ANA_OUTFILE}

cd /tmp
rm -rf $jobdir


