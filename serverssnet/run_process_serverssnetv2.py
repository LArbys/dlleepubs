## @namespace dlleepubs.ssnet
#  @ingroup dummy_dstream
#  @brief Defines a project ssnet
#  @author twongjirad

# python include
import time, os, shutil, commands
# pub_dbi package include
from pub_dbi import DBException
# dstream class include
from dstream import DSException
from dstream import ds_project_base
from dstream import ds_status

PUBDIR = os.environ["PUB_TOP_DIR"]
PUBSSNETDIR = PUBDIR+"/dlleepubs/serverssnet"

## @class ssnet
#  @brief A dummy nu bin file xfer project
#  @details
#  This dummy project transfers dummy files created by dummy_daq project\n
#  It simply copies dummy nu bin files with a different file name under $PUB_TOP_DIR/data.
class ssnet(ds_project_base):

    # Define project name as class attribute
    _project = 'ssnet'

    ## @brief default ctor can take # runs to process for this instance
    def __init__(self,project_name):

        if project_name:
            self._project = project_name

        # Call base class ctor
        super(ssnet,self).__init__()

        self._nruns = None
        self._out_dir = ''
        self._outfile_format = ''
        self._in_dir = ''
        self._infile_format = ''
        self._parent_project = ''

    ## @brief method to retrieve the project resource information if not yet done
    def get_resource(self):

        resource = self._api.get_resource(self._project)
        
        self._parent_project = resource['SOURCE_PROJECT']
        self._filetable      = resource['FILETABLE']        
        self._out_dir        = resource['OUTDIR']
        self._outfile_format = resource['OUTFILE_FORMAT']
        self._grid_workdir   = resource['GRID_WORKDIR']
        self._container      = resource['CONTAINER']
        self._endofbroker_buffer_secs = float(resource['ENDOFBROKERLIFEBUFFER_SECS'])
        if 'IMAGE_PROCESSOR_CFG' in resource:
            self._processor_cfg = resource['IMAGE_PROCESSOR_CFG']
        else:
            self._processor_cfg = None

        #self._nruns    = int(resource['NRUNS'])
        #self._max_jobs = int(resource['MAXJOBS'])
        self._nruns = 5
        self._max_jobs = 20  # should be roughly 2*(number of workers)

        self._pgpu03_max_nworkers  = 6*3 #18
        self._pgpu01_max_nworkers  = 2*3 # 6
        self._pgpu02_max_nworkers  = 2*3 # 6
        self._ao_node_limit        = 1   # 1
        self._tot_workers = self._pgpu03_max_nworkers+self._pgpu01_max_nworkers+self._pgpu02_max_nworkers+2*self._ao_node_limit # 32
        

    ## @brief count the number of client jobs
    def get_number_of_current_jobs(self):
        pass


    ## @brief access DB and retrieves new runs and process
    def process_newruns(self):

        # Attempt to connect DB. If failure, abort
        if not self.connect():
	    self.error('Cannot connect to DB! Aborting...')
	    return

        # If resource info is not yet read-in, read in.
        if self._nruns is None:
            self.get_resource()

        # check how much time until the server will shut down
        f = open("%s/ssnetserver_broker_start.txt"%(PUBSSNETDIR),'r')
        server_tstamp = f.readlines()[0]
        self.info("Server start time: "+server_tstamp.strip())
        server_start = time.strptime( server_tstamp.strip(), "%a, %d %b %Y %H:%M:%S +0000" )
        secs_running = (time.mktime(time.localtime())-time.mktime(server_start))
        server_maxtime = 3*(24*3600) # 3 days
        secs_remaining = server_maxtime - secs_running
        self.info("Server time remaining: %.2f (secs) %.2f hours"%(secs_remaining,secs_remaining/3600))
        if secs_remaining < self._endofbroker_buffer_secs:
            self.info("We are within the end time of the server (%d). Do not launch jobs to prevent clients talking to nothing. Relaunch the server+workers!!"%(self._endofbroker_buffer_secs))
            return False

        # check if we're running the max number of jobs currently
        query = "select run,subrun from %s where status=2 order by run,subrun asc" %( self._project )
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        nremaining = self._max_jobs - len(results)
        jobslaunched = False
        
        if nremaining<=0:
            self.info("Already running (%d) max number of ssnet jobs (%d)" % (len(results),self._max_jobs) )
            return False

        if nremaining>self._nruns:
            nremaining = self._nruns

        # Fetch runs from DB and process for # runs specified for this instance.
        query =  "select t1.run,t1.subrun,supera"
        query += " from %s t1 join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun)" % (self._project, self._filetable)
        query += " join %s t3 on (t1.run=t3.run and t1.subrun=t3.subrun)" % (self._parent_project)
        query += " where t1.status=1 and t3.status=4 order by run, subrun desc limit %d" % (nremaining) 

        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()

        if len(results)==0:
            self.info("No jobs to run")

        ijob=0
        for x in results:
            #print x[0]

            # for each:
            # a) make workdir
            # b) make input lists
            # c) make rerunlist.txt
            # d) copy over ssnet config
            # e) generate submit script (or copy over)
            # f) launch and store job id
            # g) set status to 2: running

            # run id
            run    = int(x[0])
            subrun = int(x[1])
            runmod100 = run%100
            rundiv100 = run/100
            subrunmod100 = subrun%100
            subrundiv100 = subrun/100

            # job variables
            jobtag       = 10000*run + subrun            
            dbdir = self._out_dir + "/%03d/%02d/%03d/%02d/"%(rundiv100,runmod100,subrundiv100,subrunmod100)
            workdir      = self._grid_workdir + "/%s_%04d_%03d"%(self._project,run,subrun)
            ssnetout = dbdir + "/" + self._outfile_format%("ssnetserveroutv2-larcv",run,subrun)
            taggerin = dbdir + "/" + self._outfile_format%("taggeroutv2-larcv",run,subrun)

            # locations inside the container
#            dbdir_ic    = dbdir.replace("/90-days-archive","")
#            workdir_ic  = workdir.replace("/90-days-archive","")
#            ssnetout_ic = ssnetout.replace("/90-days-archive","")
#            taggerin_ic = taggerin.replace("/90-days-archive","")

            # image processor cfg file
            if self._processor_cfg is None:
                imgcfg = "input_croiprocessor_default.cfg"
            else:
                imgcfg = PUBSSNETDIR+"/processorcfg/"+self._processor_cfg
#                imgcfg_ic = imgcfg_ic.replace("/90-days-archive","").replace("/tufts/","/kappa/")

            # prepare workdir (allow people in same group to destroy it)
            os.system("mkdir -p %s"%(workdir))
            os.system("chmod -R g+rw %s"%(workdir))
            self.info("prepared workdir for (%d,%d) at %s"%(run,subrun,workdir))

            # make submission script for client
            submitscript="""#!/bin/sh
#
#SBATCH --job-name=ssnetclient_%d
#SBATCH --output=%s/log_ssnetclient_%d_%d.txt
#SBATCH --ntasks=1
#SBATCH --time=2:00:00
#SBATCH --mem-per-cpu=2560

# CONTAINER
#CONTAINER=/cluster/tufts/wongjiradlab/larbys/images/singularity-ssnetserver/singularity-ssnetserver-caffelarbys-cuda8.0_update080617.img
CONTAINER=/cluster/tufts/wongjiradlab/larbys/images/singularity-ssnetserver/singularity-ssnetserver-caffelarbys-cuda8.0.img

# LOCATION OF SSNETSERVER CODE (IN CONTAINER)
#SSS_BASEDIR=/cluster/tufts/wongjiradlab/larbys/ssnetserver # for debug
SSS_BASEDIR=/usr/local/ssnetserver # eventually use frozen code in container

# WORKING DIRECTORY
WORKDIR=%s
WORKDIR_IN_CONTAINER=%s

# PATHS (IN CONTAINER0
TAGGER_INPUTPATH=%s
SSNET_OUTPUTPATH=%s

# PROGRAM PARAMETERS
TREENAME=modimg
PORT=5559
BROKER=10.246.81.73 # PGPU03

# IMAGE CONFIG FILE
IMG_CFG=%s

mkdir -p ${WORKDIR}
module load singularity
singularity exec ${CONTAINER} bash -c "cd ${SSS_BASEDIR}/grid && ./run_caffe1client_pubs.sh ${SSS_BASEDIR} ${WORKDIR_IN_CONTAINER} ${BROKER} ${PORT} ${SSNET_OUTPUTPATH} ${TAGGER_INPUTPATH} ${TREENAME} ${IMG_CFG}"
"""

            submit = submitscript%(jobtag,workdir,run,subrun,workdir,workdir,taggerin,ssnetout,imgcfg)
            submitout = open(workdir+"/submit.sh",'w')
            print >>submitout,submit
            submitout.close()
            ijob += 1
            os.system("chmod -R g+rw %s"%(workdir)) # so others can destroy

            # for debug. skip submission and changing of status in DB
            #if True:
            #    continue

            submissionok = False
            psubmit = os.popen("sbatch %s/submit.sh"%(workdir))
            lsubmit = psubmit.readlines()
            submissionid = ""
            for l in lsubmit:
                l = l.strip()
                if "Submitted batch job" in l:
                    submissionid = l.split()[-1].strip()
                    submissionok = True

            # Create a status object to be logged to DB (if necessary)
            if submissionok:
                self.info("Submitted job for (%d,%d)."%(run,subrun))
                data = "jobid:"+submissionid
                status = ds_status( project = self._project,
                                    run     = int(x[0]),
                                    subrun  = int(x[1]),
                                    seq     = 0,
                                    data    = data,
                                    status  = 2 )
            
                # Log status
                self.log_status( status )
                jobslaunched = True

            # Break from loop if counter became 0
            #if not ctr: break
        if jobslaunched:
            return True
        else:
            return False

    ## @brief access DB and retrieves processed run for validation
    def validate(self):

        # Attempt to connect DB. If failure, abort
        if not self.connect():
	    self.error('Cannot connect to DB! Aborting...')
	    return

        # If resource info is not yet read-in, read in.
        if self._nruns is None:
            self.get_resource()

        # get job listing
        psinfo = os.popen( "squeue | grep ssnetcli" )
        lsinfo = psinfo.readlines()
        runningjobs = []
        for l in lsinfo:
            l = l.strip()
            info = l.split()
            if len(info)>=8:
                try:
                    jobid = int(info[0].strip())
                    runningjobs.append( jobid )
                except:
                    continue

        self.info("number of running jobs in slurm queue: %d"%(len(runningjobs)))
        #print runningjobs

        # check running jobs
        query = "select run,subrun,data from %s where status=2 and seq=0 order by run,subrun asc" %( self._project )
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        self.info("Number of ssnet jobs in running state: %d"%(len(results)))
        for x in results:
            run    = int(x[0])
            subrun = int(x[1])
            dbdata = x[2]

            try:
                if "," in dbdata:
                    runid = int(dbdata.split(",")[0].split("jobid:")[-1])
                else:
                    runid = int(dbdata.split("jobid:")[1].split()[0])
            except:
                self.info( "(%d,%d) not parsed"%(run,subrun)+": "+dbdata )
                continue
            if runid not in runningjobs:
                self.info("(%d,%d,%s) no longer running. updating status,seq to 3,0"%(run,subrun,self._project))
                #slurmjid = int(dbdata.split(":")[1])
                psacct = os.popen("sacct --format=\"Elapsed\" -j %d"%(runid))
                try:
                    data = "jobid:%d,elapsed:%s"%(runid,psacct.readlines()[2].strip())
                except:
                    data = "jobid:%d,elapsed:%s"%(runid,"--")
                status = ds_status( project = self._project,
                                    run     = int(x[0]),
                                    subrun  = int(x[1]),
                                    seq     = 0,
                                    data    = data,
                                    status  = 3 )
                self.log_status( status )

        # check finished jobs
        # if good, then status 3, seq 0
        # if bad, then status 1, seq 0
        # check running jobs

        query =  "select t1.run,t1.subrun,supera"
        query += " from %s t1 join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun)" % (self._project,self._filetable)
        query += " where t1.status=3 and t1.seq=0 order by run, subrun desc limit %d"%(self._nruns * 10)
        #query += " where t1.status=3 and t1.seq=0 order by run, subrun desc limit %d"%(100)
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        self.info("Number of ssnet jobs in finished state: %d"%(len(results)))
        

        for x in results:
            run    = int(x[0])
            subrun = int(x[1])
            supera = x[2]
#            supera_ic = supera.replace("/90-days-archive","")

            # form output file names
            runmod100 = run%100
            rundiv100 = run/100
            subrunmod100 = subrun%100
            subrundiv100 = subrun/100
            dbdir = self._out_dir + "/%03d/%02d/%03d/%02d/"%(rundiv100,runmod100,subrundiv100,subrunmod100)
            ssnetout     = dbdir + "/" + self._outfile_format%("ssnetserveroutv2-larcv",run,subrun)
#            ssnetout_ic  = ssnetout.replace("/90-days-archive","")
            jobtag       = 10000*run + subrun
            workdir      = self._grid_workdir + "/%s_%04d_%03d"%(self._project,run,subrun)            

            #pcheck = os.popen("%s/./singularity_check_jobs.sh %s %s %s"%(PUBSSNETDIR,ssnetout_ic,supera_ic,PUBSSNETDIR.replace("/cluster/tufts","/cluster/kappa")))
            pcheck = os.popen("%s/./singularity_check_jobs.sh %s %s %s"%(PUBSSNETDIR,ssnetout,supera,PUBSSNETDIR))
            lcheck = pcheck.readlines()
            good = False
            try:
                if lcheck[-1].strip()=="True":
                    good = True
            except:
                good = False

            if good:
                self.info("status of job for (%d,%d) is good"%(run,subrun))
                status = ds_status( project = self._project,
                                    run     = run,
                                    subrun  = subrun,
                                    seq     = 0,
                                    status  = 4 )
                cmd = "rm -rf %s"%(workdir)
                self.log_status(status)
                os.system(cmd)
                self.info(cmd)
            else:
                # set to error state
                self.info("status of job for (%d,%d) is bad"%(run,subrun))
                status = ds_status( project = self._project,
                                    run     = int(x[0]),
                                    subrun  = int(x[1]),
                                    seq     = 0,
                                    status  = 10 )                
            # enter status
            self.log_status(status)


    ## @brief access DB and retrieves runs for which 1st process failed. Clean up.
    def error_handle(self):

        # Attempt to connect DB. If failure, abort
        if not self.connect():
	    self.error('Cannot connect to DB! Aborting...')
	    return

        # If resource info is not yet read-in, read in.
        if self._nruns is None:
            self.get_resource()

        # check running jobs
        #query = "select run,subrun from %s where status=10 order by run,subrun asc limit %d" %( self._project, self._nruns*10 )
        query = "select run,subrun from %s where status=10 order by run,subrun asc" %( self._project )
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()

        # Fetch runs from DB and process for # runs specified for this instance.
        for x in results:
            # we clean out the workdir
            run = int(x[0])
            subrun = int(x[1])
            workdir      = self._grid_workdir + "/%s_%04d_%03d"%(self._project,run,subrun)
            os.system("rm -rf %s"%(workdir))
            # reset the status
            data = ''
            status = ds_status( project = self._project,
                                run     = int(x[0]),
                                subrun  = int(x[1]),
                                seq     = 0,
                                data    = data,
                                status  = 1 )
            self.log_status(status)

    ## @brief access DB and retrieves runs for which 1st process failed. Clean up.
    def modstatus(self):
        # WARNING, USED TO MODIFY SPECIFIC ENTRIES!!
        #fbroken = open("brokenssnet/ssnet_broken_entry_list_mcc8v6_extbnb.txt",'r')
        #fbroken = open("brokenssnet/ssnet_broken_entry_list_mcc8v6_bnb5e19.txt",'r')
        #fbroken = open("brokenssnet/ssnet_broken_entry_list_mcc8v7_nue_signal_overlay.txt",'r')
        #fbroken = open("brokenssnet/ssnet_broken_entry_list_mcc8v7_nue_intrinsic_overlay.txt",'r')
        #fbroken = open("brokenssnet/ssnet_broken_entry_list_mcc8v7_bnb_overlay_p00.txt",'r')
        #fbroken = open("brokenssnet/ssnet_broken_entry_list_mcc8v7_bnb_overlay_p01.txt",'r')
        #fbroken = open("brokenssnet/ssnet_broken_entry_list_mcc9tag1_bnb5e19.txt",'r')
        fbroken = open("brokenssnet/ssnet_broken_entry_list_mcc9tag2_nueintrinsic_corsika.txt",'r')
        lbroken = fbroken.readlines()
        rslist = []
        for l in lbroken:
            l = l.strip()
            #info = l.split(",")
            info = l.split()
            run = int(info[0])
            subrun = int(info[1])
            rs = (run,subrun)
            if rs not in rslist:
                rslist.append(rs)

        print "WARNING YOU ARE ABOUT TO OBLITERATE %d ENTRIES. PROCEED WITH CAUTION."%(len(rslist))
        print "Bail? [ENTER] to continue"
        raw_input()

        # Attempt to connect DB. If failure, abort
        if not self.connect():
	    self.error('Cannot connect to DB! Aborting...')
	    return

        # If resource info is not yet read-in, read in.
        if self._nruns is None:
            self.get_resource()

        # check running jobs
        query = "select run,subrun from %s where status>2 order by run,subrun asc" %( self._project )
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()

        # Fetch runs from DB and process for # runs specified for this instance.
        for x in results:
            # we clean out the workdir
            run = int(x[0])
            subrun = int(x[1])
            runmod100 = run%100
            rundiv100 = run/100
            subrunmod100 = subrun%100
            subrundiv100 = subrun/100

            rs = (run,subrun)
            if rs not in rslist:
                #print "ok, skip: ",rs
                continue
            dbdir = self._out_dir + "/%03d/%02d/%03d/%02d/"%(rundiv100,runmod100,subrundiv100,subrunmod100)
            ssnetout = dbdir + "/" + self._outfile_format%("ssnetserveroutv2-larcv",run,subrun)
            cmd = "rm -f "+ssnetout
            print "reset state for ",rs,": ",cmd
            # reset the status, delete the existing file
            if True:
                os.system(cmd)
                data = ''
                status = ds_status( project = self._project,
                                    run     = int(x[0]),
                                    subrun  = int(x[1]),
                                    seq     = 0,
                                    data    = data,
                                    status  = 1 )
                self.log_status(status)

# A unit test section
if __name__ == '__main__':

    import sys
    test_obj = None
    if len(sys.argv)>1:
        test_obj = ssnet(sys.argv[1])
    else:
        test_obj = ssnet()

    jobslaunched = False
    jobslaunched = test_obj.process_newruns()
    if not jobslaunched:
        test_obj.validate()
        #test_obj.error_handle()
        #test_obj.modstatus() # reset of DB state coupled with file deletion CAUTION!!!
        pass
