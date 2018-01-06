#!/bin/sh


# Wrapper script for run_reco_job_template.sh
jobdir=$1
inputlist_dir=$2
output_dir=.
jobid_list=$3
vtxoutpath=$4
vtxpicklepath=$5
let jobid=`sed -n 1 ${jobid_list}`

# setup container
source /usr/local/bin/thisroot.sh
cd /usr/local/share/dllee_unified/
source configure.sh
cd $jobdir

# expect to be in the workdir
source prepscript.sh

# above leaves us at vertex-tuftscluster-scripts/mac 
# also leaves us with the run_reco_job.sh script

source run_reco_job.sh $jobdir $inputlist_dir $output_dir $jobid_list || exit
outfile_ana=`printf vertexana_%05d.root ${jobid}`
outfile_out=`printf vertexout_%05d.root ${jobid}`
cp $output_dir/$outfile_ana $vtxoutpath
cp $output_dir/$outfile_out $vtxpicklepath

