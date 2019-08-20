#!/bin/sh

# REMEMBER, WE ARE IN THE CONTAINER RIGHT NOW
# This means we access the next work drives through some mounted folders
# The submit command also moved us to right local folder

# expect to be in cloned repo of vertex-tuftcluster-scripts
# example, for taritree this is in: ~/grid_jobs/vertex-tuftcluster-scripts

# Get arguments
jobdir=$1
inputlist_dir=$2
output_dir=$3
jobid_list=$4

# setup the container software
# ----------------------------

# setup uboonecode
source /products/setup
setup uboonecode v06_26_01_24 -q e10:prof
setup mrb
export MRB_PROJECT=larsoft
cd /usr/local/share/ew/
source localProducts_larsoft_v06_26_01_15_e10_prof/setup
source fix_build.sh
cd /usr/local/share/sw/ 
source larlite/config/setup_dl.sh


# go to job dir
# -------------
cd $jobdir

echo "CURRENT DIR: "$PWD

# check that the process number is greater than the number of job ids
let NUM_PROCS=`cat ${jobid_list} | wc -l`
echo "number of processes: $NUM_PROCS"
if [ "$NUM_PROCS" -lt "${SLURM_PROCID}" ]; then
    echo "No Procces ID to run."
    return
fi

#
# get job id
#
let "proc_line=${SLURM_PROCID}+1"
let jobid=`sed -n ${proc_line}p ${jobid_list}`
echo "JOBID ${jobid}"

#
# make path to input lists
#
mcinfo_inputlist=`printf ${inputlist_dir}/mcinfo_inputlist_%05d.txt ${jobid}`

#
# get input files
#
input_mcinfo_file=`sed -n 1p ${mcinfo_inputlist}`

#
# make slurm folder
#
slurm_folder=`printf slurm_ew_job%05d ${jobid}`
mkdir -p ${slurm_folder}
cd ${slurm_folder}

#
# make log file
#
logfile=`printf log_ew_%05d.txt ${jobid}`
touch ${logfile}


#
# fcl configs
#
reader_fcl1=${jobdir}/KKK
reader_fcl1_name=KKK
cat $reader_fcl1>> $logfile
cp $reader_fcl1 .

reader_fcl2=${jobdir}/RRR
reader_fcl2_name=RRR
cat $read_fcl2 >> $logfile
cp $reader_fcl2 .

#
# echo into it
#
echo "RUNNING LL JOB ${jobid}" > $logfile

#
# go to work directory
#
segment_dir=/usr/local/share/sw/scripts/mcdump/
andy_dir=/usr/local/share/sw/scripts/andy/

#
# Permissions
#
chmod -R 777 ${output_dir}
chmod -R 777 `pwd -P`
chmod -R 777 `pwd -P`/../

#
# mc_information dump
#
echo " "
echo " "
echo " "
echo " "

echo "run segment dump" >> $logfile
echo "${segment_dir}/run_MCDump ${input_mcinfo_file} ${jobid}" >> $logfile
${segment_dir}/run_MCDump ${input_mcinfo_file} ${jobid} >> $logfile 2>&1
rc=$?;
chmod 777 *
echo "return code=${rc}" >> $logfile
if [[ $rc != 0 ]]; then exit $rc; fi
echo "... segment dump complete" >> $logfile

echo " "
echo " "
echo " "
echo " "

#
# mc_tree dump
#
echo " "
echo " "
echo " "
echo " "

echo "run andy dump..." >> $logfile
echo "python ${andy_dir}/make_andy.py mc_information_${jobid}.root ${jobid} ." >> $logfile
python ${andy_dir}/make_andy.py mc_information_${jobid}.root ${jobid} . >> $logfile 2>&1
rc=$?;
chmod 777 *
echo "return code=${rc}" >> $logfile
if [[ $rc != 0 ]]; then exit $rc; fi
echo "... andy dump complete" >> $logfile

echo " "
echo " "
echo " "
echo " "

#
# mc_tree maker
#
echo " "
echo " "
echo " "
echo " "

echo "run larsoft event weight..." >> $logfile
echo "lar -c ${reader_fcl1_name} -s andy_out_${jobid}.root -o evweight_art_${jobid}.root" >> $logfile
lar -c ${reader_fcl1_name} -s andy_out_${jobid}.root -o evweight_art_${jobid}.root 1> /dev/null 2>/dev/null
rc=$?;
echo "return code=${rc}" >> $logfile
chmod 777 *
if [[ $rc != 0 ]]; then exit $rc; fi
echo "... larsoft event weight complete" >> $logfile

echo " "
echo " "
echo " "
echo " "


#
# Copy to output
#
echo "copying..." >> $logfile
rsync -av *.root ${output_dir}
rsync -av *.fcl ${output_dir}
chmod -R 777 ${output_dir}
chmod -R 777 `pwd -P`
chmod -R 777 `pwd -P`/.pylardcache
chmod -R 777 `pwd -P`/../
rm -rf *.root
rm -rf *.fcl
rm -rf .pylardcache
echo "...copied" >> $logfile
