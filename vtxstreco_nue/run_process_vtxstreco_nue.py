## @namespace dlleepubs.vtxstreconue
#  @ingroup dummy_dstream
#  @brief Defines a project vtxstreconue
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
PUBVTXSTRECONUEDIR = PUBDIR+"/dllee_dstream/vtxstreco_nue"

## @class vtxstreconue
#  @brief A dummy nu bin file xfer project
#  @details
#  This dummy project transfers dummy files created by dummy_daq project\n
#  It simply copies dummy nu bin files with a different file name under $PUB_TOP_DIR/data.
class vtxstreconue(ds_project_base):

    # Define project name as class attribute
    _project = 'vtxstreconue'

    ## @brief default ctor can take # runs to process for this instance
    def __init__(self,project_name):

        if project_name:
            self._project = project_name

        # Call base class ctor
        super(vtxstreconue,self).__init__()

        self._nruns = None
        self._out_dir = ''
        self._outfile_format = ''
        self._in_dir = ''
        self._infile_format = ''
        self._parent_project = ''

    ## @brief method to retrieve the project resource information if not yet done
    def get_resource(self):

        resource = self._api.get_resource(self._project)
        
        self._nruns = int(resource['NRUNS'])
        self._nruns = 5
        self._parent_project = resource['SOURCE_PROJECT']
        self._input_dir      = resource['STAGE1DIR']
        self._input_format   = resource['SSNET_INPUT_FORMAT']
        self._out_dir        = resource['OUTDIR']
        self._outfile_format = resource['OUTFILE_FORMAT']
        self._outpickle_format = resource['OUTPICKLE_FORMAT']
        self._filetable      = resource['FILETABLE']        
        self._grid_workdir   = resource['GRID_WORKDIR']
        self._container      = resource['CONTAINER']
        self._cfgtag         = resource['CFGTAG']
        self._scriptstag     = resource['SCRIPTSTAG']
        self._vtxcfg         = resource['VTXCFG']
        self._trackercfg     = resource['TRACKERCFG']
        self._showercfg      = resource['MCSHOWERCFG']
        self._reclusterflag  = resource['RECLUSTERFLAG']
        self._runtag         = "pubstest"
        self._max_jobs       = 38

    def query_queue(self):
        """ data about slurm queue pertaining to vtxstreconue jobs"""
        psqueue = commands.getoutput("squeue | grep twongj01 | grep vtxstreconue")
        lsqueue = psqueue.split('\n')

        info = {"numjobs":0,"jobids":[]}
        for l in lsqueue:
            if l.strip()!="":
                jobid = int(l.split()[0])
                info["jobids"].append(jobid)
        info["numjobs"] = len(info["jobids"])
        return info

    def get_input_output( self, run, subrun, jobtag ):
        """ return input and output filenames for run,subrun file """
        runmod100 = run%100
        rundiv100 = run/100
        subrunmod100 = subrun%100
        subrundiv100 = subrun/100

        # job variables
        jobtag          = 10000*run + subrun
        inputdbdir      = self._input_dir + "/%03d/%02d/%03d/%02d/"%(rundiv100,runmod100,subrundiv100,subrunmod100)
        ssnetinput      = inputdbdir + "/" + self._input_format%("ssnetout-larcv",run,subrun)
        outdbdir        = self._out_dir + "%s/%03d/%02d/%03d/%02d/"%(self._runtag,rundiv100,runmod100,subrundiv100,subrunmod100)
        vtxstreconueout = outdbdir + "/" + self._outfile_format%("vtxstreconue-out",run,subrun)
        vtxstreconueana = outdbdir + "/" + self._outfile_format%("vtxstreconue-ana",run,subrun)
        vtxstreconuepickle = outdbdir + "/" + self._outpickle_format%("vtxstreconue-pickle",run,subrun)
        
        return ssnetinput, vtxstreconueout, vtxstreconueana, vtxstreconuepickle, inputdbdir, outdbdir

    ## @brief access DB and retrieves new runs and process
    def process_newruns(self):

        # Attempt to connect DB. If failure, abort
        if not self.connect():
	    self.error('Cannot connect to DB! Aborting...')
	    return

        # If resource info is not yet read-in, read in.
        if self._nruns is None:
            self.get_resource()

        # check if we're running the max number of jobs currently
        query = "select run,subrun from %s where status=2 order by run,subrun asc" %( self._project )
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        nremaining = self._max_jobs - len(results)
        jobslaunched = False
        
        if nremaining<=0:
            self.info("Already running (%d) max number of vtxstreconue jobs (%d)" % (len(results),self._max_jobs) )
            return

        if nremaining>self._nruns:
            nremaining = self._nruns

        # get queue status
        qinfo = self.query_queue()
        print qinfo

        # Fetch runs from DB and process for # runs specified for this instance.
        query =  "select t1.run,t1.subrun"
        query += " from %s t1 join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun)" % (self._project, self._filetable)
        query += " join %s t3 on (t1.run=t3.run and t1.subrun=t3.subrun)" % (self._parent_project)
        query += " where t1.status=1 and t3.status=4 order by run, subrun desc limit %d" % (nremaining) 

        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        ijob=0
        for x in results:
            print x

            # for each:
            # a) make workdir
            # b) make input lists
            # c) make runlist.txt
            # d) copy over vtxstreconue config
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
            jobtag          = 10000*run + subrun
            inputdbdir      = self._input_dir + "/%03d/%02d/%03d/%02d/"%(rundiv100,runmod100,subrundiv100,subrunmod100)
            ssnetinput      = inputdbdir + "/" + self._input_format%("ssnetout-larcv",run,subrun)
            outdbdir        = self._out_dir + "%s/%03d/%02d/%03d/%02d/"%(self._runtag,rundiv100,runmod100,subrundiv100,subrunmod100)
            vtxstreconueout = outdbdir + "/" + self._outfile_format%("vtxstreconue-out",run,subrun)
            vtxstreconueana = outdbdir + "/" + self._outfile_format%("vtxstreconue-ana",run,subrun)
            vtxstreconuepickle = outdbdir + "/" + self._outpickle_format%("vtxstreconue-pickle",run,subrun)

            # PREPARE WORKDIR
            workdir      = self._grid_workdir + "/%s_%04d_%03d"%(self._project,run,subrun)
            inputlistdir = workdir + "/inputlists"
            os.system("mkdir -p %s"%(inputlistdir))
            self.info("prepared workdir for (%d,%d) at %s"%(run,subrun,workdir))

            # inputlist (jobid %05d matches run_reco_job_template.sh)
            inputlist   = open('%s/inputlist_%05d.txt'%(inputlistdir,jobtag),'w')
            print >> inputlist,ssnetinput
            inputlist.close()

            # runlist
            rerunlist   = open('%s/runlist.txt'%(workdir),'w')
            print >> rerunlist,jobtag
            rerunlist.close()

            # make output dir
            os.system("mkdir -p %s"%(outdbdir))

            # wrapper script
            os.system("cp %s/wrapper_reco_job.sh %s"%(PUBVTXSTRECONUEDIR,workdir))

            # prep script: sets up vertex repo
            prepscript = """#!/bin/sh
cd %s
git clone https://github.com/LArbys/vertex-tuftscluster-scripts.git
cd vertex-tuftscluster-scripts
git checkout -b %s %s
cd ..
git clone https://github.com/LArbys/Production_Config.git cfgrepo
cd cfgrepo
git checkout -b %s %s
cd ..
cp cfgrepo/cfg/%s .
ln -s %s vertex-tuftscluster-scripts/image/%s
cp wrapper_reco_job.sh vertex-tuftscluster-scripts/mac/
cd vertex-tuftscluster-scripts/mac
python py/gen_templates.py `pwd -P`/../
cp template/run_reco_job_template.sh run_reco_job.sh
sed -i -e 's/XXX/%s/g' run_reco_job.sh
chmod a+x run_reco_job.sh
mv run_reco_job.sh ../../
cd ../..
"""%(workdir,self._scriptstag,self._scriptstag,self._cfgtag,self._cfgtag,self._vtxcfg,self._container,os.path.basename(self._container),self._vtxcfg)
            prepscriptpath = "%s/prepscript.sh"%(workdir)
            prepscriptfile = open(prepscriptpath,'w')
            print >> prepscriptfile, prepscript

            # make submission script
            submitscript="""#!/bin/sh
#
#SBATCH --job-name=vtxstreconue_%d
#SBATCH --output=%s/log_vtxstreconue_%d_%d.txt
#SBATCH --ntasks=1
#SBATCH --time=480:00
#SBATCH --mem-per-cpu=4000

CONTAINER=%s
WORKDIR=%s
INPUTLISTDIR=%s
JOBID_LIST=%s
VTXSTRECONUE_OUTFILENAME=%s
VTXSTRECONUE_ANAFILENAME=%s
VTXPICKLE_OUTFILENAME=%s

module load singularity
srun singularity exec ${CONTAINER} bash -c "cd ${WORKDIR} && source wrapper_reco_job.sh ${WORKDIR} ${INPUTLISTDIR} ${JOBID_LIST} ${VTXSTRECONUE_OUTFILENAME} ${VTXSTRECONUE_ANAFILENAME} ${VTXPICKLE_OUTFILENAME}"
"""
            submit = submitscript%(jobtag,workdir,run,subrun,self._container,workdir,inputlistdir,workdir+"/runlist.txt",vtxstreconueout,vtxstreconueana,outdbdir)
            submitout = open(workdir+"/submit.sh",'w')
            print >>submitout,submit
            submitout.close()
            ijob += 1

            submissionok = False
            if True: # use this bool to turn off for testing
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
                self.info("Submitted job for (%d,%d)"%(run,subrun))
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
            #if True: break
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
        psinfo = os.popen( "squeue | grep twongj01 | grep vtxstreconue" )
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
        self.info("Number of vtxstreconue jobs in running state: %d"%(len(results)))
        for x in results:
            run    = int(x[0])
            subrun = int(x[1])

            try:
                runid = int(x[-1].split("jobid:")[1].split()[0])
            except:
                self.info( "(%d,%d) not parsed"%(run,subrun)+": %s"%(x[-1]))
                continue
            if runid not in runningjobs:
                self.info("(%d,%d) no longer running. updating status,seq to 3,0"%(run,subrun))
                status = ds_status( project = self._project,
                                    run     = int(x[0]),
                                    subrun  = int(x[1]),
                                    seq     = 0,
                                    status  = 3 )
                self.log_status( status )

        # check finished jobs
        # if good, then status 3, seq 0
        # if bad, then status 1, seq 0
        # check running jobs

        query =  "select t1.run,t1.subrun,supera"
        query += " from %s t1 join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun)" % (self._project,self._filetable)
        query += " where t1.status=3 and t1.seq=0 order by run, subrun desc"
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        self.info("Number of vtxstreconue jobs in finished state: %d"%(len(results)))
        for x in results:
            run    = int(x[0])
            subrun = int(x[1])
            supera = x[2]

            # form output file names/workdir
            jobtag       = 10000*run + subrun
            ssnetinput, vtxstreconueout, vtxstreconueana, vtxstreconuepickle, inputdbdir, outputdbdir = self.get_input_output( run, subrun, jobtag )
            workdir      = self._grid_workdir + "/%s_%04d_%03d"%(self._project,run,subrun)

            pcheck = os.popen("%s/./singularity_check_jobs.sh %s %s %s"%(PUBVTXSTRECONUEDIR,vtxstreconueout,vtxstreconueana,supera))
            lcheck = pcheck.readlines()
            print "---- check results -----"
            for l in lcheck:
                print l.strip()
            print "------------------------"
            
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
                if False:
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
                                    status  = 2 )                

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
        query = "select run,subrun from %s where status=10 order by run,subrun asc limit %d" %( self._project, self._nruns*10 )
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

# A unit test section
if __name__ == '__main__':

    import sys
    test_obj = None
    if len(sys.argv)>1:
        test_obj = vtxstreconue(sys.argv[1])
    else:
        test_obj = vtxstreconue()

    jobslaunched = False
    #jobslaunched = test_obj.process_newruns()
    if not jobslaunched:
        test_obj.validate()
    #    #test_obj.error_handle()


