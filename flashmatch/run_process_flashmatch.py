# @namespace dlleepubs.dlcosmictag
#  @ingroup dummy_dstream
#  @brief Defines a project dlcosmictag
#  @author twongjirad

# python include
import time, os, shutil
# pub_dbi package include
from pub_dbi import DBException
# dstream class include
from dstream import DSException
from dstream import ds_project_base
from dstream import ds_status

PUBDIR = os.environ["PUB_TOP_DIR"]
PUB_FLASHMATCH_DIR = PUBDIR+"/dlleepubs/flashmatch"

## @class flashmatch
#  @brief A dummy nu bin file xfer project
#  @details
#  This dummy project transfers dummy files created by dummy_daq project\n
#  It simply copies dummy nu bin files with a different file name under $PUB_TOP_DIR/data.
class flashmatch(ds_project_base):

    # Define project name as class attribute
    _project = 'flashmatch'

    ## @brief default ctor can take # runs to process for this instance
    def __init__(self,project_name):

        if project_name:
            self._project = project_name

        # Call base class ctor
        super(flashmatch,self).__init__()

        self._nruns = None
        self._out_dir = ''
        self._outfile_format = ''
        self._in_dir = ''
        self._infile_format = ''
        self._parent_project = ''

    ## @brief method to retrieve the project resource information if not yet done
    def get_resource(self):

        resource = self._api.get_resource(self._project)
        
        self._nruns          = int(resource['NRUNS'])
        self._parent_project    = resource['SOURCE_PROJECT']
        self._out_dir           = resource['OUTDIR']
        self._supera_dir        = resource['SUPERADIR']
        self._dlcosmic_dir      = resource['DLCOSMICDIR']
        self._outfile_format    = resource['OUTFILE_FORMAT']
        self._filetable         = resource['FILETABLE']        
        self._grid_workdir      = resource['GRID_WORKDIR']
        self._container_larflow = resource['CONTAINER_LARFLOW']
        self._max_jobs       = 10
        self._ismc           = 1
        self._nruns          = 5

    def check_running_jobs(self):
        # check running jobs. return number still running.

        # get job listing
        psinfo = os.popen( "squeue | grep flashmat" )
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
        self.info("Number of running jobs on queue: %d"%(len(runningjobs)))

        query = "select run,subrun,data from %s where status=2 and seq=0 order by run,subrun asc" %( self._project )
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        nrunning = len(results)
        nfinished = 0
        self.info("Number of flashmatch jobs in running state according to DB: %d"%(len(results)))
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
                self.info( "(%d,%d) not parsed"%(run,subrun)+": {}".format(x) )
                continue
            self.info( "(%d,%d) run ID %d"%(run,subrun,runid))
            if runid not in runningjobs:
                #print "(%d,%d) no longer running. updating status,seq to 3,0" % (run,subrun)
                psacct = os.popen("sacct --format=\"Elapsed\" -j %d"%(runid))
                data = "jobid:%d,elapsed:%s"%(runid,psacct.readlines()[2].strip())
                status = ds_status( project = self._project,
                                    run     = int(x[0]),
                                    subrun  = int(x[1]),
                                    seq     = 0,
                                   data    = data,
                                    status  = 3 )
                self.log_status( status )
                nrunning += -1
                nfinished += 1
        #print "number of jobs still running: ",nrunning
        return nrunning,nfinished

    
    def get_project_input_filenames( self, run, subrun, supera_path ):
        """ builds the input filenames """
        pass

    def get_project_output_filenames( self, run, subrun, supera_path ):
        """ builds the input filenames """
        pass


    ## @brief access DB and retrieves new runs and process
    def process_newruns(self):

        jobslaunched = False

        # Attempt to connect DB. If failure, abort
        if not self.connect():
	    self.error('Cannot connect to DB! Aborting...')
	    return

        # If resource info is not yet read-in, read in.
        if self._nruns is None:
            self.get_resource()

        # check if we're running the max number of jobs currently
        nrunning,nfinished = self.check_running_jobs()
        nremaining = self._max_jobs - nrunning

        if nfinished>=self._max_jobs:
            # give a chance to validate files
            return False
        
        #if nremaining<=0:
        #    self.info("Already running (%d) max number of flashmatch jobs (%d)" % (nrunning,self._max_jobs) )
        #    return jobslaunched

        if nremaining>self._nruns:
            nremaining = self._nruns

        # Fetch runs from DB and process for # runs specified for this instance.
        query =  "select t1.run,t1.subrun,supera,opreco,mcinfo"
        query += " from %s t1 join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun) join %s t3 on (t1.run=t3.run and t1.subrun=t3.subrun)" % (self._project,self._filetable,self._parent_project)
        query += " where t1.status=1 and t3.status=4 order by run, subrun desc limit %d" % (nremaining) 


        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        #print "number of jobs to run from query: ",len(results)

        for arrayid,x in enumerate(results):

            # for each:
            # a) make workdir
            # b) make input lists
            # c) make rerunlist.txt
            # d) copy over flashmatch config
            # e) generate submit script (or copy over)
            # f) launch and store job id
            # g) set status to 2: running

            run    = int(x[0])
            subrun = int(x[1])
            runmod100 = run%100
            rundiv100 = run/100
            subrunmod100 = subrun%100
            subrundiv100 = subrun/100
            jobtag       = 10000*run + subrun

            # directories
            dbdir       = self._out_dir + "/%03d/%02d/%03d/%02d/"%(rundiv100,runmod100,subrundiv100,subrunmod100)
            superadir   = self._supera_dir + "/%03d/%02d/%03d/%02d/"%(rundiv100,runmod100,subrundiv100,subrunmod100)
            dlcosmicdir = self._dlcosmic_dir + "/%03d/%02d/%03d/%02d/"%(rundiv100,runmod100,subrundiv100,subrunmod100)
            workdir     = self._grid_workdir + "/%s_%04d_%03d"%(self._project,run,subrun)
            
            # output file paths
            larcvout     = dbdir + "/" + self._outfile_format%("flashmatch-larcv",run,subrun)
            larliteout   = dbdir + "/" + self._outfile_format%("flashmatch-larlite",run,subrun)
            anaout       = dbdir + "/" + self._outfile_format%("flashmatch-ana",run,subrun)
            truthcluster = dbdir + "/" + self._outfile_format%("truthcluster-larlite",run,subrun)

            # input file paths
            supera       = dlcosmicdir + "/" + self._outfile_format%("supera-larcv2",run,subrun)
            opreco       = x[3]
            flowhits     = dlcosmicdir + "/" + self._outfile_format%("larflowhits-larlite",run,subrun)
            if self._ismc==1:
                mcinfo = os.path.realpath(x[4])

            # Corresponding directories for inside the container
            workdir_ic      = workdir.replace('90-days-archive','')
            dbdir_ic        = dbdir.replace('90-days-archive','')

            larcvout_ic     = larcvout.replace('90-days-archive','')
            larliteout_ic   = larliteout.replace('90-days-archive','')
            anaout_ic       = anaout.replace('90-days-archive','')
            truthcluster_ic = truthcluster.replace('90-days-archive','')

            flowhits_ic     = flowhits.replace('90-days-archive','')
            supera_ic       = supera.replace('90-days-archive','')
            opreco_ic       = opreco.replace('90-days-archive','')
            if self._ismc==1:
                mcinfo_ic   = mcinfo.replace('90-days-archive','')

            # create working directory, copy job script
            #print "make workdir: ",workdir
            os.system("mkdir -p %s"%(workdir))
            os.system("cp %s/job_flashmatch.sh %s/"%(PUB_FLASHMATCH_DIR,workdir))

            # make submission script
            submitscript="""#!/bin/sh
#
#SBATCH --job-name=flashmatch_%d
#SBATCH --output=%s/log_flashmatch_%d_%d.txt
#SBATCH --ntasks=1
#SBATCH --time=20:00
#SBATCH --mem-per-cpu=2000
#SBATCH --cpus-per-task=1
#SBATCH --partition=batch

WORKDIR=%s
WORKDIR_IC=%s
CONTAINER=%s

#INPUTS
SUPERA=%s
FLOWHITS=%s
OPRECO=%s
MCINFO=%s
INPUTS="${SUPERA} ${FLOWHITS} ${OPRECO} ${MCINFO}"

#OUTPUTS
TRUTHCLUSTER=%s
LARCV_OUTFILE=%s
LARLITE_OUTFILE=%s
ANA_OUTFILE=%s
OUTDIR=%s
OUTPUTS="${TRUTHCLUSTER} ${LARCV_OUTFILE} ${LARLITE_OUTFILE} ${ANA_OUTFILE}"

srun echo ${WORKDIR} && cd ${WORKDIR} && mkdir -p ${OUTDIR} && ./job_flashmatch.sh ${WORKDIR} ${CONTAINER} ${INPUTS} ${OUTPUTS}
"""
            submit = submitscript%(jobtag,workdir,run,subrun,
                                   workdir, workdir_ic,self._container_larflow,
                                   supera_ic,flowhits_ic,opreco_ic,mcinfo_ic,
                                   truthcluster,larcvout,larliteout,anaout,
                                   dbdir)
                                   
            submitout = open(workdir+"/submit.sh",'w')
            print >>submitout,submit
            submitout.close()

            if False:
                print "exit for debug"
                sys.exit(-1)

            psubmit = os.popen("sbatch %s/submit.sh"%(workdir))
            lsubmit = psubmit.readlines()
            submissionok = False
            submissionid = ""
            for l in lsubmit:
                l = l.strip()
                if "Submitted batch job" in l:
                    submissionid = l.split()[-1].strip()
                    submissionok = True
                    self.info("Launched flashmatch job for (%d,%d)"%(run,subrun))
                    jobslaunched = True

            # Create a status object to be logged to DB (if necessary)
            if submissionok:
                data = "jobid:"+submissionid
                status = ds_status( project = self._project,
                                    run     = int(x[0]),
                                    subrun  = int(x[1]),
                                    seq     = 0,
                                    data    = data,
                                    status  = 2 )
            
                # Log status
                self.log_status( status )

            # Break from loop if counter became 0
            #if not ctr: break
        return jobslaunched

    ## @brief access DB and retrieves processed run for validation
    def validate(self):


        # Attempt to connect DB. If failure, abort
        if not self.connect():
	    self.error('Cannot connect to DB! Aborting...')
	    return

        # If resource info is not yet read-in, read in.
        if self._nruns is None:
            self.get_resource()



        # check finished jobs
        nrunning,nfinished = self.check_running_jobs()
        # if good, then status 4, seq 0
        # if bad, then status 10, seq 0
        # check running jobs

        query =  "select t1.run,t1.subrun,supera,opreco"
        query += " from %s t1 join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun)" % (self._project,self._filetable)
        query += " where t1.status=3 order by run, subrun asc limit %d" % (self._nruns)
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        self.info("Number of flashmatch jobs in finished state: %d"%(len(results)))
        for x in results:
            run    = int(x[0])
            subrun = int(x[1])
            supera = x[2]

            # form output file names
            runmod100 = run%100
            rundiv100 = run/100
            subrunmod100 = subrun%100
            subrundiv100 = subrun/100
            dbdir   = self._out_dir + "/%03d/%02d/%03d/%02d/"%(rundiv100,runmod100,subrundiv100,subrunmod100)
            workdir = self._grid_workdir + "/%s_%04d_%03d"%(self._project,run,subrun)

            larliteout    = dbdir + "/" + self._outfile_format%("flashmatch-larlite",run,subrun)
            anaout        = dbdir + "/" + self._outfile_format%("flashmatch-ana",run,subrun)
            truthcluster  = dbdir + "/" + self._outfile_format%("truthcluster-larlite",run,subrun)

            larliteout_ic   = larliteout.replace("90-days-archive","")
            truthcluster_ic = truthcluster.replace("90-days-archive","")
            supera_ic       = supera.replace("90-days-archive","")
            anaout_ic       = anaout.replace("90-days-archive","")
            
            pcheck = os.popen("%s/./singularity_check_jobs.sh %s %s %s %s"%(PUB_FLASHMATCH_DIR,
                                                                            supera_ic,
                                                                            larliteout_ic,
                                                                            truthcluster_ic,
                                                                            anaout_ic))
            lcheck = pcheck.readlines()
            good = False
            try:
                if lcheck[-1].strip()=="True":
                    good = True
            except:
                good = False
            self.info("Check job returned with %s state"%(str(good)))

            if False:
                # for debug
                for l in lcheck:
                    print l.strip()
                # for debug
                sys.exit(-1)

            if good:
                status = ds_status( project = self._project,
                                    run     = int(x[0]),
                                    subrun  = int(x[1]),
                                    seq     = 0,
                                    status  = 4 )
                cmd = "rm -rf %s"%(workdir)
                os.system(cmd)
                self.info(cmd)
            else:
                # set to error state
                status = ds_status( project = self._project,
                                    run     = int(x[0]),
                                    subrun  = int(x[1]),
                                    seq     = 0,
                                    status  = 10 )
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
        query = "select run,subrun from %s where status=10 order by run,subrun asc limit %d" %( self._project, self._nruns*1000 )
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
    def clean_goodjob_workdir(self):

        # Attempt to connect DB. If failure, abort
        if not self.connect():
	    self.error('Cannot connect to DB! Aborting...')
	    return

        # If resource info is not yet read-in, read in.
        if self._nruns is None:
            self.get_resource()


        # check running jobs
        query = "select run,subrun from %s where status=4 order by run,subrun asc limit %d" %( self._project, self._nruns*1000 )
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()

        # Fetch runs from DB and process for # runs specified for this instance.
        for x in results:
            # we clean out the workdir
            run = int(x[0])
            subrun = int(x[1])
            workdir      = self._grid_workdir + "/%s_%04d_%03d"%(self._project,run,subrun)
            print "cleaning up: ",workdir
            os.system("rm -rf %s"%(workdir))
            

# A unit test section
if __name__ == '__main__':

    import sys
    test_obj = None
    if len(sys.argv)>1:
        test_obj = flashmatch(sys.argv[1])
    else:
        test_obj = flashmatch()
     
    jobslaunched = False
    jobslaunched = test_obj.process_newruns()
    if not jobslaunched:
        test_obj.validate()
        test_obj.error_handle()
    #test_obj.clean_goodjob_workdir()
