import os, sys, pwd, commands, time, random, getpass, json
from pub_dbi import DBException
from dstream import DSException
from dstream import ds_project_base
from dstream import ds_status

sys.path.insert(0,os.path.join(os.environ["PUB_TOP_DIR"],"dlleepubs"))
from utils.downstream_utils import *

class vertex_reco(ds_project_base):

    # Define project name as class attribute
    _project = 'vertex_reco'

    ## @brief default ctor can take # runs to process for this instance
    def __init__(self,project_name):

        if project_name:
            self._project = project_name

        # Call base class ctor
        super(vertex_reco,self).__init__()

        self._nruns            = None
        self._parent_project   = ""
        self._input_dir        = ""
        self._file_format      = ""
        self._out_dir          = ""
        self._filetable        = ""
        self._grid_workdir     = ""
        self._container        = ""
        self._vtxcfg           = ""
        self._run_script       = ""
        self._sub_script       = ""
        self._runtag           = ""
        self._max_jobs         = None
        self._usenames         = 0
        self._names            = []
        
    ## @brief method to retrieve the project resource information if not yet done
    def get_resource(self):

        resource = self._api.get_resource(self._project)
        
        self._nruns            = 500
        self._parent_project   = str(resource['SOURCE_PROJECT'])
        self._input_dir        = str(resource['STAGE1DIR'])
        self._file_format      = str(resource["FILE_FORMAT"])
        self._larcv_file_format = str(resource['LARCV_FILE_FORMAT'])
        self._ana_file_format  = str(resource['ANA_FILE_FORMAT'])
        self._out_dir          = str(resource['OUTDIR'])
        self._dllee_unified_dir = str(resource['DLLEE_UNIFIED_DIR'])
        self._filetable        = str(resource['FILETABLE'])    
        self._grid_workdir     = str(resource['GRID_WORKDIR'])
        self._container        = str(resource['CONTAINER'])
        self._vtxcfg           = str(resource['VTXCFG'])
        self._run_script       = os.path.join(SCRIPT_DIR,str(resource['RUN_SCRIPT']))
        self._runtag           = str(resource['RUNTAG'])
        self._max_jobs         = 500
        self._usenames         = int(str(resource['ACCOUNT_SHARE']))
        self._usenames = 0

        if self._usenames == 1:
            self._names = ["vgenty01",
                           "cbarne06",
                           "jmoon02",
                           "ran01",
                           "lyates01",
                           "ahourl01",
                           "adiaz09"]


    def query_queue(self):
        """ data about slurm queue pertaining to vertex_reco jobs"""
        psqueue = commands.getoutput("squeue | grep vertex")
        lsqueue = psqueue.split('\n')

        info = {"numjobs":0,"jobids":[]}
        for l in lsqueue:
            if l.strip()!="":
                jobid = int(l.split()[0])
                info["jobids"].append(jobid)
        info["numjobs"] = len(info["jobids"])
        return info

    ## @brief access DB and retrieves new runs and process
    def process_newruns(self,nruns=None):

        # Attempt to connect DB. If failure, abort
        if not self.connect():
	    self.error('Cannot connect to DB! Aborting...')
	    return

        # If resource info is not yet read-in, read in.
        if self._nruns is None:
            self.get_resource()

        if nruns is None:
            nruns = self._nruns

        # check if we're running the max number of jobs currently
        query = "select run,subrun from %s where status=2 order by run,subrun asc" %( self._project )

        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        nremaining = self._max_jobs - len(results)
        projectdata = self._api.project_info(self._project)

        self.info(nremaining)

        jobslaunched = False
        
        if nremaining<=0:
            self.info("Already running (%d) max number of vertex_reco jobs (%d)" % (len(results),self._max_jobs) )
            return

        if nremaining>nruns:
            nremaining = nruns

        # get queue status
        qinfo = self.query_queue()
        #print qinfo
        
        #
        # ...this is not the pubs way, pray it's right...
        #

        # Fetch runs from DB and process for # runs specified for this instance.
        query =  "select t1.run,t1.subrun,t2.supera,t1.data,t3.data,t4.data"
        query += " from %s t1 join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun)" % (self._project, self._filetable)
        query += " join %s t3 on (t1.run=t3.run and t1.subrun=t3.subrun)" % (self._parent_project)
        query += " join %s t4 on (t1.run=t4.run and t1.subrun=t4.subrun)" % ("taggerv2_"+projectdata._runtable)
        query += " join %s t5 on (t1.run=t5.run and t1.subrun=t5.subrun)" % ("vertex_"+projectdata._runtable)
        query += " where t1.status=1 and t3.status=4 and t4.status=4 and t5.status=4 order by run, subrun desc limit %d" % (nremaining) 
        self.info(query)
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        ijob = 0

        self.info("nremaining = %s" % nremaining)
        self.info("len results = %s" % len(results) )

        for x in results:

            # run id
            run    = int(x[0])
            subrun = int(x[1])

            db_data_sparsessnet = json.loads( x[4] )
            #db_data_tagger      = json.loads( x[5] )
            if x[3] is None:
                db_data_vertex = {}
            else:
                db_data_vertex = json.loads( x[3] )

            # job variables
            jobtag,inputdbdir,outdbdir = cast_run_subrun(run,subrun,
                                                         self._runtag,self._file_format,
                                                         self._input_dir,self._out_dir)
            
            # prepare work dir
            self.info("Making work directory")
            workdir      = os.path.join(self._grid_workdir,"vertex",self._runtag,"%s_%04d_%03d"%(self._project,run,subrun))
            inputlistdir = os.path.join(workdir,"inputlists")
            cmd("mkdir -p %s"%(inputlistdir))
            self.info("...made workdir for (%d,%d) at %s"%(run,subrun,workdir))

            #
            # prepare input lists
            #
            superainput = x[2]
            ssnetinput  = db_data_sparsessnet["sparsessnetlarcv"]
            taggerinput  = os.path.join(inputdbdir,self._file_format%("taggeroutv2-larcv",run,subrun))
            taggerinput += ".root"

            # output file name
            # new style
            vertexout_larcv = os.path.join(outdbdir,self._larcv_file_format%(self._project,run,subrun))
            vertexout_ana   = os.path.join(outdbdir,self._ana_file_format%(self._project,run,subrun))
            # old style
            #vertexout_larcv = os.path.join(outdbdir,"vertexout_%d.root"%())
            #vertexout_ana = os.path.join(outdbdir,"vertexana_%d.root"%())
            db_data_vertex["vertexlarcv"]  = vertexout_larcv
            db_data_vertex["vertexana"]    = vertexout_ana
            db_data_vertex["vertexdf"] = vertexout_ana.replace("ana","vertdf").replace("root","pkl")
            db_data_vertex["combdf"] = vertexout_ana.replace("ana","combdf").replace("root","pkl")
            db_data_vertex["truthdf"] = vertexout_ana.replace("ana","truthdf").replace("root","pkl")

            # make output dir
            self.info("Making output directory @dir=%s" % str(outdbdir))
            cmd("mkdir -p %s" % (outdbdir))

            # copy reco script to workdir
            self.info("copy template")
            cmd("scp -r %s %s" % (self._run_script,workdir))
            run_script = os.path.join(workdir,os.path.basename(self._run_script))

            # write submission script
            submitscript="""#!/bin/sh
#SBATCH --job-name=vertex_{jobtag}
#SBATCH --output={workdir}/log_{jobtag}.txt
#SBATCH --time=03:00:00
#SBATCH --mem-per-cpu=2000

CONTAINER={container}
WORKDIR={workdir}
OUTPUTDIR={outputdir}
DLLEE_DIR={dllee_dir}
CONFIG={config}
SUPERA={supera}
TAGGER={tagger}
SSNET={ssnet}
OUTLARCV={out_larcv}
OUTANA={out_ana}
OUTVERTDF={out_df}
OUTCOMBDF={out_combdf}
OUTTRUTHDF={out_truthdf}

mkdir -p $OUTPUTDIR
module load singularity
srun singularity exec $CONTAINER bash -c "cd $WORKDIR && source {runscript} $DLLEE_DIR $WORKDIR $CONFIG $SUPERA $TAGGER $SSNET $OUTLARCV $OUTANA $OUTVERTDF $OUTCOMBDF $OUTTRUTHDF"

"""
            fsubmit = open(workdir+"/submit.sh",'w')
            inputmap = {"jobtag":jobtag,
                        "workdir":workdir,
                        "container":self._container,
                        "outputdir":os.path.dirname(vertexout_larcv),
                        "dllee_dir":self._dllee_unified_dir,
                        "config":self._vtxcfg,
                        "supera":superainput,
                        "tagger":taggerinput,
                        "ssnet":ssnetinput,
                        "out_larcv":vertexout_larcv,
                        "out_ana":vertexout_ana,
                        "out_df":db_data_vertex["vertexdf"],
                        "out_combdf":db_data_vertex["combdf"],
                        "out_truthdf":db_data_vertex["truthdf"],
                        "runscript":os.path.basename(self._run_script) }
            print>>fsubmit,submitscript.format( **inputmap )

            fsubmit.close()
            ijob += 1
            submissionok = False

            if True: # use this bool to turn off for testing

                interactive = False

                if interactive == True:
                    SS = "%s &" % os.path.join(workdir,"submit_pubs_job_interactive.sh")
                    psubmit = os.popen(SS)
                    print "Sleeping..."
                    time.sleep(5)
                    print "...slept"
                    lsubmit = None
                    with open(os.path.join(workdir,"job.id"),'r') as f:
                        lsubmit = f.read()

                    lsubmit = lsubmit.strip()
                    submissionid = lsubmit.split("=")[-1]
                    submissionok = True
                else:
                    SSH_PREFIX = "ssh %s@fastx-dev \"%s\""
                    #SSH_PREFIX = "ssh %s@xfer.cluster.tufts.edu \"%s\""
                    SS = "sbatch %s" % os.path.join(workdir,"submit.sh")
                    
                    name = ""
                    if len(self._names) == 0:
                        name = str(getpass.getuser())
                    else:
                        name = random.choice(self._names)

                    SSH_PREFIX = SSH_PREFIX % (name,SS)
                    print "Submitted as name=%s" % name
                    psubmit = os.popen(SSH_PREFIX)
                    lsubmit = psubmit.readlines()
                    submissionid = ""
                    for l in lsubmit:
                        l = l.strip()
                        print l
                        if "Submitted batch job" in l:
                            submissionid = l.split()[-1].strip()
                            submissionok = True

            # Create a status object to be logged to DB (if necessary)
            if submissionok:
                self.info("Submitted job for (%d,%d): %s"%(run,subrun,submissionid))
                db_data_vertex["jobid"] = "jobid:"+submissionid
                status = ds_status( project = self._project,
                                    run     = int(x[0]),
                                    subrun  = int(x[1]),
                                    seq     = 0,
                                    data    = json.dumps(db_data_vertex),
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
    def validate(self,nruns=None):

        # Attempt to connect DB. If failure, abort
        if not self.connect():
	    self.error('Cannot connect to DB! Aborting...')
	    return

        # If resource info is not yet read-in, read in.
        if self._nruns is None:
            self.get_resource()

        if nruns is None:
            nruns = self._nruns

        # get job listing
        psinfo = os.popen("squeue | grep vertex")
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
        self.info("Number of vertex_reco jobs in running state: %d"%(len(results)))
        for x in results:
            run    = int(x[0])
            subrun = int(x[1])
            dbdata = json.loads(x[2])
            try:
                runid = int(dbdata["jobid"].split("jobid:")[1].split()[0])
            except:
                self.info( "(%d,%d) not parsed"%(run,subrun)+": %s"%(x[-1]))
                continue
            if runid not in runningjobs:
                self.info("(%d,%d) no longer running. updating status,seq to 3,0"%(run,subrun))
                psacct = os.popen("sacct --format=\"Elapsed\" -j %d"%(runid))
                try:
                    dbdata["elapsed"] = psacct.readlines()[2].strip()
                except:
                    dbdata["elapsed"] = "---"
                status = ds_status( project = self._project,
                                    run     = int(x[0]),
                                    subrun  = int(x[1]),
                                    seq     = 0,
                                    data    = json.dumps(dbdata),
                                    status  = 3 )
                self.log_status( status )

        # check finished jobs
        # if good, then status 3, seq 0
        # if bad, then status 1, seq 0
        # check running jobs

        query =  "select t1.run,t1.subrun,supera,data"
        query += " from %s t1 join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun)" % (self._project,self._filetable)
        query += " where t1.status=3 and t1.seq=0 order by run, subrun desc"
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        self.info("Number of vertex_reco jobs in finished state: %d"%(len(results)))
        for x in results:
            run    = int(x[0])
            subrun = int(x[1])
            dbdata = json.loads(x[3])

            # form output file names/workdir
            jobtag,inputdbdir,outdbdir = cast_run_subrun(run,subrun,
                                                         self._runtag,self._file_format,
                                                         self._input_dir,self._out_dir)
            # link
            #vertex_pkl1    = os.path.join(outdbdir,"ana_comb_df_%d.pkl" % jobtag)
            #self.info("verify exists=%s" % vertex_pkl1)
            #vertex_out = os.path.join(outdbdir, "vertexout_%d.root" % jobtag)
            vertex_out  = dbdata["vertexlarcv"]
            vertex_ana  = dbdata["vertexana"]

            workdir      = os.path.join(self._grid_workdir,"vertex",self._runtag,"%s_%04d_%03d"%(self._project,run,subrun))

            #success = os.path.exists(vertex_pkl1)
            success = os.path.exists(vertex_out) and os.path.exists(vertex_ana)

            if success == True:
                self.info("status of job for (%d,%d) is good"%(run,subrun))
                status = ds_status( project = self._project,
                                    run     = run,
                                    subrun  = subrun,
                                    seq     = 0,
                                    status  = 4 )
                self.info("remove working dir: %s"%(workdir))
                os.system("rm -rf %s"%(workdir))
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

        # check running jobs
        query = "select run,subrun from %s where status=10 order by run,subrun asc limit %d" %( self._project, self._nruns*10 )
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()

        # Fetch runs from DB and process for # runs specified for this instance.
        for x in results:
            # we clean out the workdir
            run     = int(x[0])
            subrun  = int(x[1])
            workdir = os.path.join(self._grid_workdir,"vertex",self._runtag,"%s_%04d_%03d"%(self._project,run,subrun))
            ##os.system("/cluster/kappa/90-days-archive/wongjiradlab/bin/grm %s"%(workdir))            
            SS = "rm -rf %s" % (workdir)
            self.info(SS)
            os.system(SS)
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

    test_obj = vertex_reco(sys.argv[1])
    jobslaunched = False
    jobslaunched = test_obj.process_newruns(nruns=100)
    #if jobslaunched == False:
    #test_obj.validate()
    #test_obj.error_handle()
