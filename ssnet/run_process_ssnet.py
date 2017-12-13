## @namespace dlleepubs.ssnet
#  @ingroup dummy_dstream
#  @brief Defines a project ssnet
#  @author twongjirad

# python include
import time, os, shutil
# pub_dbi package include
from pub_dbi import DBException
# dstream class include
from dstream import DSException
from dstream import ds_project_base
from dstream import ds_status

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
        
        self._nruns = int(resource['NRUNS'])
        self._nruns = 5
        self._parent_project = resource['SOURCE_PROJECT']
        self._out_dir        = resource['OUTDIR']
        self._outfile_format = resource['OUTFILE_FORMAT']
        self._filetable      = resource['FILETABLE']        
        self._grid_workdir   = resource['GRID_WORKDIR']
        self._container      = resource['CONTAINER']

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
        nremaining = self._nruns - len(results)
        jobslaunched = False
        
        if nremaining<=0:
            self.info("Already running (%d) max number of ssnet jobs (%d)" % (len(results),self._nruns) )
            return

        # do we have room on the cards?
        

        # Fetch runs from DB and process for # runs specified for this instance.
        query =  "select t1.run,t1.subrun,supera"
        query += " from %s t1 join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun) join %s t3 on (t1.run=t3.run and t1.subrun=t3.subrun)" % (self._project,self._filetable,self._parent_project)
        query += " where t1.status=1 and t3.status=4 order by run, subrun desc limit %d" % (nremaining) 
        print query

        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        for x in results:
            print x[0]

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
            ssnetout = dbdir + "/" + self._outfile_format%("ssnetout-larcv",run,subrun)
            taggerin = dbdir + "/" + self._outfile_format%("taggerout-larcv",run,subrun)

            # prepare workdir
            inputlistdir = workdir + "/inputlists"
            os.system("mkdir -p %s"%(inputlistdir))
            self.info("prepared workdir for (%d,%d) at %s"%(run,subrun,workdir))

            inputlist   = open('%s/inputlist_%09d.txt'%(inputlistdir,jobtag),'w')
            print >> inputlist,x[2]
            print >> inputlist,taggerin
            inputlist.close()

            rerunlist   = open('%s/rerunlist.txt'%(workdir),'w')
            print >> rerunlist,jobtag
            rerunlist.close()

            os.system("cp manage_tufts_gpu_jobs.py %s/"%(workdir))  # waits for open gpu slot and runs script
            os.system("cp choose_gpu.py %s/"%(workdir))             # gpu utility
            os.system("cp run_pubsgpu_job.sh %s/"%(workdir))        # setups inputs, handles output, calls gpu python program
            os.system("cp run_ssnet_mcc8.py %s/"%(workdir))         # runs the three planes
            os.system("cp pyana_mcc8_gpu.py %s/"%(workdir))         # python script that runs caffe for one plane
            os.system("cp pyana_mcc8_small.prototxt %s/"%(workdir)) # ssnet prototxt and weights
            os.system("cp *.caffemodel %s/"%(workdir))              # ssnet model weights (60 MB each/180 MB total transfer -- can i be smarter?)
            os.system("cp *.cfg %s/"%(workdir))                     # larcv configurations

            # make submission script
            submitscript="""#!/bin/sh
#
#SBATCH --job-name=ssnet_%d
#SBATCH --output=%s/log_ssnet_%d_%d.txt
#SBATCH --ntasks=1
#SBATCH --time=480:00
#SBATCH --mem-per-cpu=4000

WORKDIR=%s
CONTAINER=%s
SSNET_OUTFILENAME=%s

module load singularity
srun python manage_tufts_gpu_jobs.py ${CONTAINER} ${WORKDIR} ${SSNET_OUTFILENAME}
"""
            submit = submitscript%(jobtag,workdir,run,subrun,workdir,self._container,ssnetout)
            submitout = open(workdir+"/submit.sh",'w')
            print >>submitout,submit
            submitout.close()

            psubmit = os.popen("sbatch -p gpu --nodelist=pgpu[01-02] %s/submit.sh"%(workdir))
            lsubmit = psubmit.readlines()
            submissionok = False
            submissionid = ""
            for l in lsubmit:
                l = l.strip()
                print l
                if "Submitted batch job" in l:
                    submissionid = l.split()[-1].strip()
                    submissionok = True

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
        psinfo = os.popen( "squeue | grep twongj01" )
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
        print runningjobs

        # check running jobs
        query = "select run,subrun,data from %s where status=2 and seq=0 order by run,subrun asc" %( self._project )
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        self.info("Number of ssnet jobs in running state: %d"%(len(results)))
        for x in results:
            run    = int(x[0])
            subrun = int(x[1])

            try:
                runid = int(x[-1].split("jobid:")[1].split()[0])
            except:
                print "(%d,%d) not parsed"%(run,subrun),": ",x[-1]
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

        query =  "select t1.run,t1.subrun,supera,opreco"
        query += " from %s t1 join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun)" % (self._project,self._filetable)
        query += " where t1.status=3 and t1.seq=0 order by run, subrun desc"
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        self.info("Number of ssnet jobs in finished state: %d"%(len(results)))
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
            ssnetout   = dbdir + "/" + self._outfile_format%("ssnetout-larcv",run,subrun)
            jobtag       = 10000*run + subrun
            workdir      = self._grid_workdir + "/%s_%04d_%03d"%(self._project,run,subrun)            

            pcheck = os.popen("./singularity_check_jobs.sh %s %s"%(ssnetout,supera))
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

        # get job listing
        psinfo = os.popen( "sinfo | grep twongj01" )
        lsinfo = psinfo.readlines()
        for l in lsinfo:
            l = l.strip()
            print l

        # check running jobs
        #query = "select run,subrun from %s where status=2 order by run,subrun asc" %( self._project )
        #self._api._cursor.execute(query)
        #results = self._api._cursor.fetchall()

        # Fetch runs from DB and process for # runs specified for this instance.
        #query =  "select t1.run,t1.subrun,supera,opreco,mcinfo"
        #query += " from %s t1 join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun) join %s t3 on (t1.run=t3.run and t1.subrun=t3.subrun)" % (self._project,self._filetable,self._parent_project)
        #query += " where t1.status=1 and t3.status=3 order by run, subrun desc limit %d" % (nremaining) 
        #print query

# A unit test section
if __name__ == '__main__':

    import sys
    test_obj = None
    if len(sys.argv)>1:
        test_obj = ssnet(sys.argv[1])
    else:
        test_obj = ssnet()
        
    jobslaunched = test_obj.process_newruns()

    #test_obj.error_handle()

    if not jobslaunched:
        test_obj.validate()

