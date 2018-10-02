# @namespace dlleepubs.tagger
#  @ingroup dummy_dstream
#  @brief Defines a project tagger
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
PUBTAGGERDIR = PUBDIR+"/dlleepubs/tagger"

## @class tagger
#  @brief A dummy nu bin file xfer project
#  @details
#  This dummy project transfers dummy files created by dummy_daq project\n
#  It simply copies dummy nu bin files with a different file name under $PUB_TOP_DIR/data.
class tagger(ds_project_base):

    # Define project name as class attribute
    _project = 'tagger'

    ## @brief default ctor can take # runs to process for this instance
    def __init__(self,project_name):

        if project_name:
            self._project = project_name

        # Call base class ctor
        super(tagger,self).__init__()

        self._nruns = None
        self._out_dir = ''
        self._outfile_format = ''
        self._in_dir = ''
        self._infile_format = ''
        self._parent_project = ''

    ## @brief method to retrieve the project resource information if not yet done
    def get_resource(self):

        resource = self._api.get_resource(self._project)
        
        #self._nruns          = int(resource['NRUNS'])
        self._nruns          = 40
        self._parent_project = resource['SOURCE_PROJECT']
        self._out_dir        = resource['OUTDIR']
        self._outfile_format = resource['OUTFILE_FORMAT']
        self._filetable      = resource['FILETABLE']        
        self._grid_workdir   = resource['GRID_WORKDIR']
        self._tagger_cfg     = resource['TAGGERCFG']
        self._container      = resource['CONTAINER']
        #self._max_jobs       = int(resource['MAXJOBS'])
        self._max_jobs       = 250
        self._ismc           = int(resource['ISMC'])

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
        query = "select run,subrun from %s where status=2 order by run,subrun asc" %( self._project )
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        nremaining = self._max_jobs - len(results)
        
        if nremaining<=0:
            self.info("Already running (%d) max number of tagger jobs (%d)" % (len(results),self._max_jobs) )
            return jobslaunched

        if nremaining>self._nruns:
            nremaining = self._nruns

        # Fetch runs from DB and process for # runs specified for this instance.
        query =  "select t1.run,t1.subrun,supera,opreco,mcinfo"
        query += " from %s t1 join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun) join %s t3 on (t1.run=t3.run and t1.subrun=t3.subrun)" % (self._project,self._filetable,self._parent_project)
        query += " where t1.status=1 and t3.status=3 order by run, subrun desc limit %d" % (nremaining) 
        #print query

        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        for x in results:

            # for each:
            # a) make workdir
            # b) make input lists
            # c) make rerunlist.txt
            # d) copy over tagger config
            # e) generate submit script (or copy over)
            # f) launch and store job id
            # g) set status to 2: running

            run    = int(x[0])
            subrun = int(x[1])
            runmod100 = run%100
            rundiv100 = run/100
            subrunmod100 = subrun%100
            subrundiv100 = subrun/100
            
            dbdir = self._out_dir + "/%03d/%02d/%03d/%02d/"%(rundiv100,runmod100,subrundiv100,subrunmod100)
            larcvout   = dbdir + "/" + self._outfile_format%("taggeroutv2-larcv",run,subrun)
            larliteout = dbdir + "/" + self._outfile_format%("taggeroutv2-larlite",run,subrun)
            jobtag       = 10000*run + subrun
            workdir      = self._grid_workdir + "/%s/%s_%04d_%03d"%(self._project,self._project,run,subrun)
            inputlistdir = workdir + "/inputlists"

            # Corresponding directories for inside the container
            dbdir_ic = dbdir.replace('90-days-archive','')
            larcvout_ic = larcvout.replace('90-days-archive','')
            larliteout_ic = larliteout.replace('90-days-archive','')
            workdir_ic = workdir.replace('90-days-archive','')
            inputlistdir_ic = inputlistdir.replace('90-days-archive','')

            os.system("mkdir -p %s"%(inputlistdir))
            larcv_input   = open('%s/input_larcv_%09d.txt'%(inputlistdir,jobtag),'w')
            larlite_input = open('%s/input_larlite_%09d.txt'%(inputlistdir,jobtag),'w')
            rerunlist     = open('%s/rerunlist.txt'%(workdir),'w')
            print >> larcv_input,x[2].replace('90-days-archive','')
            print >> larlite_input,x[3].replace('90-days-archive','')
            if self._ismc==1:
                mcinfo = os.path.realpath(x[4])
                print >> larlite_input,mcinfo.replace('90-days-archive','')
            print >> rerunlist,jobtag
            larcv_input.close()
            larlite_input.close()

            os.system("cp %s %s/"%(self._tagger_cfg,workdir))
            os.system("cp %s/run_taggerpubs_job.sh %s/"%(PUBTAGGERDIR,workdir))

            # make submission script
            submitscript="""#!/bin/sh
#
#SBATCH --job-name=tagger_%d
#SBATCH --output=%s/log_tagger_%d_%d.txt
#SBATCH --ntasks=1
#SBATCH --time=480:00
#SBATCH --mem-per-cpu=4000

WORKDIR=%s
CONTAINER=%s
INPUTLISTDIR=${WORKDIR}/inputlists
JOBIDLIST=${WORKDIR}/rerunlist.txt
CONFIG=${WORKDIR}/%s
LARCV_OUTFILENAME=%s
LARLITE_OUTFILENAME=%s

module load singularity
srun singularity exec ${CONTAINER} bash -c "cd ${WORKDIR} && source run_taggerpubs_job.sh ${CONFIG} ${INPUTLISTDIR} ${LARCV_OUTFILENAME} ${LARLITE_OUTFILENAME} ${JOBIDLIST}"
"""
            submit = submitscript%(jobtag,workdir,run,subrun,workdir_ic,self._container,os.path.basename(self._tagger_cfg),larcvout_ic,larliteout_ic)
            submitout = open(workdir+"/submit.sh",'w')
            print >>submitout,submit
            submitout.close()

            psubmit = os.popen("sbatch %s/submit.sh"%(workdir))
            lsubmit = psubmit.readlines()
            submissionok = False
            submissionid = ""
            for l in lsubmit:
                l = l.strip()
                if "Submitted batch job" in l:
                    submissionid = l.split()[-1].strip()
                    submissionok = True
                    self.info("Launched tagger job for (%d,%d)"%(run,subrun))
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

        # get job listing
        #psinfo = os.popen( "squeue | grep tagger"%(os.environ["USER"]) )
        psinfo = os.popen( "squeue | grep tagger" )
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

        # check running jobs
        query = "select run,subrun,data from %s where status=2 and seq=0 order by run,subrun asc" %( self._project )
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        self.info("Number of tagger jobs in running state: %d"%(len(results)))
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
                self.info( "(%d,%d) not parsed"%(run,subrun)+": "+x[-1] )
                continue
            self.info( "(%d,%d) run ID %d"%(run,subrun,runid))
            if runid not in runningjobs:
                print "(%d,%d) no longer running. updating status,seq to 3,0" % (run,subrun)
                #slurmjid = int(dbdata.split(":")[1])
                psacct = os.popen("sacct --format=\"Elapsed\" -j %d"%(runid))
                data = "jobid:%d,elapsed:%s"%(runid,psacct.readlines()[2].strip())
                status = ds_status( project = self._project,
                                    run     = int(x[0]),
                                    subrun  = int(x[1]),
                                    seq     = 0,
                                    data    = data,
                                    status  = 3 )
                self.log_status( status )

        # check finished jobs
        # if good, then status 4, seq 0
        # if bad, then status 10, seq 0
        # check running jobs

        query =  "select t1.run,t1.subrun,supera,opreco"
        query += " from %s t1 join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun)" % (self._project,self._filetable)
        query += " where t1.status=3 order by run, subrun asc limit %d" % (10)
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        self.info("Number of tagger jobs in finished state: %d"%(len(results)))
        for x in results:
            run    = int(x[0])
            subrun = int(x[1])
            supera = x[2]
            opreco = x[3]

            # form output file names
            runmod100 = run%100
            rundiv100 = run/100
            subrunmod100 = subrun%100
            subrundiv100 = subrun/100
            dbdir = self._out_dir + "/%03d/%02d/%03d/%02d/"%(rundiv100,runmod100,subrundiv100,subrunmod100)
            larcvout   = dbdir + "/" + self._outfile_format%("taggeroutv2-larcv",run,subrun)
            larliteout = dbdir + "/" + self._outfile_format%("taggeroutv2-larlite",run,subrun)
            jobtag       = 10000*run + subrun
            workdir      = self._grid_workdir + "/%s/%s_%04d_%03d"%(self._project,self._project,run,subrun)
            
            # Corresponding directories for inside the container
            dbdir_ic = dbdir.replace('90-days-archive','')
            larcvout_ic = larcvout.replace('90-days-archive','')
            larliteout_ic = larliteout.replace('90-days-archive','')
            workdir_ic = workdir.replace('90-days-archive','')
            supera_ic = supera.replace('90-days-archive','')

            pcheck = os.popen("%s/./singularity_check_jobs.sh %s %s %s"%(PUBTAGGERDIR,larcvout_ic,larliteout_ic,supera_ic))
            lcheck = pcheck.readlines()
            good = False
            try:
                if lcheck[-1].strip()=="True":
                    good = True
            except:
                good = False
            self.info("Check job returned with %s state"%(str(good)))

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
        query = "select run,subrun from %s where status=10 order by run,subrun asc limit %d" %( self._project, self._nruns*10 )
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()

        # Fetch runs from DB and process for # runs specified for this instance.
        for x in results:
            # we clean out the workdir
            run = int(x[0])
            subrun = int(x[1])
            workdir      = self._grid_workdir + "/%s/%s_%04d_%03d"%(self._project,self._project,run,subrun)
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
        test_obj = tagger(sys.argv[1])
    else:
        test_obj = tagger()
     
    jobslaunched = False
    #jobslaunched = test_obj.process_newruns()
    if not jobslaunched:
        test_obj.validate()
        #test_obj.error_handle()
        
