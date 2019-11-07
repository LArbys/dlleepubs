import os, sys, pwd, commands, time, random, getpass, json, argparse
from pub_dbi import DBException
from dstream import DSException
from dstream import ds_project_base
from dstream import ds_status

sys.path.insert(0,os.path.join(os.environ["PUB_TOP_DIR"],"dlleepubs"))
from utils.downstream_utils import *

class showerreco(ds_project_base):

    # Define project name as class attribute
    _project = 'showerreco'

    ## @brief default ctor can take # runs to process for this instance
    def __init__(self,project_name):

        if project_name:
            self._project = project_name

        # Call base class ctor
        super(showerreco,self).__init__()

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
        self._ismc             = None
        self._names            = []
        
    ## @brief method to retrieve the project resource information if not yet done
    def get_resource(self):

        resource = self._api.get_resource(self._project)
        
        self._nruns             = 10
        self._max_jobs          = 50

        self._filetable         = str(resource['FILETABLE'])
        self._parent_vertex_project = str(resource['SOURCE_VERTEX_PROJECT'])
        self._dllee_unified_dir = str(resource['DLLEE_UNIFIED_DIR'])
        self._file_format       = str(resource['FILE_FORMAT'])
        self._out_dir           = str(resource['OUTDIR'])
        self._grid_workdir      = str(resource['GRID_WORKDIR'])
        self._container         = str(resource['CONTAINER'])
        self._runtag            = str(resource['OUT_RUNTAG'])
        self._usenames          = int(str(resource['ACCOUNT_SHARE']))
        self._ismc              = int(str(resource['ISMC']))
        self._vertex_dbname     = str(resource['VERTEXDBNAME'])
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
        """ data about slurm queue pertaining to showerreco jobs"""
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
    def process_newruns(self,nruns=None,max_jobs=None):

        # Attempt to connect DB. If failure, abort
        if not self.connect():
	    self.error('Cannot connect to DB! Aborting...')
	    return

        # If resource info is not yet read-in, read in.
        if self._nruns is None:
            self.get_resource()

        if nruns is None:
            nruns = self._nruns

        if max_jobs is None:
            max_jobs = self._max_jobs

        # check if we're running the max number of jobs currently
        query = "select run,subrun from %s where status=2 order by run,subrun asc" %( self._project )

        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        nremaining  = max_jobs - len(results)
        projectdata = self._api.project_info(self._project)

        self.info(nremaining)

        jobslaunched = False
        
        if nremaining<=0:
            self.info("Already running (%d) max number of showerreco jobs (%d)" % (len(results),max_jobs) )
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
        query =  "select t1.run,t1.subrun,t2.supera,t2.reco2d,t1.data,tvertex.data"
        query += " from %s t1 join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun)"     % (self._project, self._filetable)
        query += " join %s tvertex  on (t1.run=tvertex.run and t1.subrun=tvertex.subrun)"  % (self._parent_vertex_project)
        query += " where t1.status=1 and tvertex.status=4 order by run, subrun desc limit %d" % (nremaining) 
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
            supera = x[2]
            reco2d = x[3]

            if x[4] is None:
                db_data = {}
            else:
                db_data = json.loads( x[4] )

            db_data_vertex = json.loads( x[5] )    

            # job variables
            jobtag,inputdbdir,outdbdir = cast_run_subrun(run,subrun,
                                                         self._runtag,self._file_format,
                                                         self._input_dir,self._out_dir)
            
            # prepare work dir
            self.info("Making work directory")
            workdir      = os.path.join(self._grid_workdir,"showerreco",self._project,"%s_%04d_%03d"%(self._project,run,subrun))
            cmd("mkdir -p %s"%(workdir))
            self.info("...made workdir for (%d,%d) at %s"%(run,subrun,workdir))
            cmd("chmod a+w -R %s"%(workdir))


            # make output dir
            self.info("Making output directory @dir=%s" % str(outdbdir))
            cmd("mkdir -p %s" % (outdbdir))
            cmd("chmod g+w -R %s"%(outdbdir))

            # output file names
            nueid_lcv_out   = os.path.join(outdbdir,self._file_format%("nueid-larcv",self._project,run,subrun))
            nueid_ll_out    = os.path.join(outdbdir,self._file_format%("nueid-larlite",self._project,run,subrun))
            nueid_ana_out   = os.path.join(outdbdir,self._file_format%("nueid-ana",self._project,run,subrun))
            shower_reco_out = os.path.join(outdbdir,self._file_format%("showerreco-larlite",self._project,run,subrun))
            shower_ana_out  = os.path.join(outdbdir,self._file_format%("showerreco-ana",self._project,run,subrun))
            db_data["nueid-larcv"]   = nueid_lcv_out
            db_data["nueid-larlite"] = nueid_ll_out
            db_data["nueid-ana"]     = nueid_ana_out
            db_data["shower-reco"]   = shower_reco_out
            db_data["shower-ana"]    = shower_ana_out

            # write submission script
            submitscript="""#!/bin/sh
#SBATCH --job-name=showerreco_{jobtag}
#SBATCH --output={workdir}/log_{jobtag}.txt
#SBATCH --time=03:00:00
#SBATCH --mem-per-cpu=2000

CONTAINER={container}
WORKDIR={workdir}
OUTPUTDIR={outputdir}
DLLEE_DIR={dllee_dir}
SUPERA={supera}
RECO2D={reco2d}
VERTEXER={vertexer}

OUT_NUEID_LARCV={nueid_larcv}
OUT_NUEID_LARLITE={nueid_larlite}
OUT_NUEID_ANA={nueid_ana}
OUT_SHOWER_RECO={shower_reco}
OUT_SHOWER_ANA={shower_ana}

NUEID_DIR=$DLLEE_DIR/larlitecv/app/LLCVProcessor/InterTool/Sel/NueID/mac/
NUEID_CONFIG=$NUEID_DIR/inter_nue_mc_mcc9_tufts.cfg

SHOWER_MAC_DIR=$DLLEE_DIR/larlitecv/app/LLCVProcessor/DLHandshake/mac/
SHOWER_CONFIG=$SHOWER_MAC_DIR/config_nueid.cfg
SHOWER_DQDS=$SHOWER_MAC_DIR/dqds_mc_xyz.txt

CHECK_SCRIPT=/cluster/tufts/wongjiradlab/larbys/pubs/dlleepubs/showerreco/check_files.py

mkdir -p $OUTPUTDIR
module load singularity
CONFIG_SETUP="cd $DLLEE_DIR && source setup_tufts_container.sh && source configure.sh && cd $WORKDIR"
RUN_NUEID="python $NUEID_DIR/inter_ana_nue_server.py -c $NUEID_CONFIG -mc -d -id 0 -od ./ -re $RECO2D $VERTEXER $SUPERA" 
RUN_SHOWER="python $SHOWER_MAC_DIR/reco_recluster_shower.py -c $SHOWER_CONFIG -mc -id 0 -od ./ --reco2d $RECO2D -dqds $SHOWER_DQDS nueid_lcv_out_0.root"
RUN_SQUALITY="python $SHOWER_MAC_DIR/run_ShowerQuality.py shower_reco_out_0.root $RECO2D INVALID ."
COPY_NUEID="cp nueid_lcv_out_0.root $OUT_NUEID_LARCV && cp nueid_ll_out_0.root $OUT_NUEID_LARLITE && cp nueid_ana_0.root $OUT_NUEID_ANA"
COPY_SHOWER="cp shower_reco_out_0.root $OUT_SHOWER_RECO && cp showerqualsingle_0.root $OUT_SHOWER_ANA"
CHECK_CMD="python $CHECK_SCRIPT $OUT_NUEID_LARCV $OUT_NUEID_LARLITE $OUT_NUEID_ANA $OUT_SHOWER_RECO $OUT_SHOWER_ANA $SUPERA"
srun singularity exec $CONTAINER bash -c "$CONFIG_SETUP && $RUN_NUEID && $RUN_SHOWER && $RUN_SQUALITY && $COPY_NUEID && $COPY_SHOWER && $CHECK_CMD"
"""
            fsubmit = open(workdir+"/submit.sh",'w')
            inputmap = {"jobtag":jobtag,
                        "workdir":workdir,
                        "container":self._container,
                        "outputdir":os.path.dirname(outdbdir),
                        "dllee_dir":self._dllee_unified_dir,
                        "supera":supera,
                        "reco2d":reco2d,
                        "vertexer":db_data_vertex[self._vertex_dbname],
                        "nueid_larcv":nueid_lcv_out,
                        "nueid_larlite":nueid_ll_out,
                        "nueid_ana":nueid_ana_out,
                        "shower_reco":shower_reco_out,
                        "shower_ana":shower_ana_out,}

            print>>fsubmit,submitscript.format( **inputmap )

            fsubmit.close()
            ijob += 1
            submissionok = False

            if True: # use this bool to turn off for testing
                
                SSH_PREFIX = "ssh %s@fastx-dev \"%s\""
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
                db_data["jobid"] = "jobid:"+submissionid
                status = ds_status( project = self._project,
                                    run     = int(x[0]),
                                    subrun  = int(x[1]),
                                    seq     = 0,
                                    data    = json.dumps(db_data),
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
        psinfo = os.popen("squeue | grep showerre")
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
        self.info("Number of showerreco jobs in running state: %d"%(len(results)))
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
        self.info("Number of showerreco jobs in finished state: %d"%(len(results)))
        for x in results:
            run    = int(x[0])
            subrun = int(x[1])
            dbdata = json.loads(x[3])

            # form output file names/workdir
            jobtag,inputdbdir,outdbdir = cast_run_subrun(run,subrun,
                                                         self._runtag,self._file_format,
                                                         self._input_dir,self._out_dir)
            workdir      = os.path.join(self._grid_workdir,"showerreco",self._project,"%s_%04d_%03d"%(self._project,run,subrun))

            # check files exist
            allmade = True
            for fname in ["nueid-larcv","nueid-larlite","nueid-ana","shower-reco","shower-ana"]:
                if not os.path.exists( dbdata[fname] ):
                    allmade = False
                    self.info("missing %s: %s"%(fname, dbdata[fname]))
            
            checkok = True
            if not os.path.exists( os.path.join(workdir,"checkfile") ):
                checkok = False

            success = allmade & checkok

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
            workdir = os.path.join(self._grid_workdir,"vertex",self._runtag,self._project,"%s_%04d_%03d"%(self._project,run,subrun))
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

    ## @brief access DB and retrieves runs for which 1st process failed. Clean up.
    def reset_status(self,nruns=None):
        # WARNING, USED TO MODIFY SPECIFIC ENTRIES!!
        print "WARNING YOU ARE ABOUT TO RESET THIS PROJECT/DELETING OLD FILES. PROCEED WITH **EXTREME** CAUTION."
        print "Bail? [ENTER] to continue"
        raw_input()

        print "Are you sure? Bail? [ENTER] to continue"
        raw_input()

        print "Are you REALLY sure? Bail? [ENTER] to continue"
        raw_input()

        # Attempt to connect DB. If failure, abort
        if not self.connect():
	    self.error('Cannot connect to DB! Aborting...')
	    return

        # If resource info is not yet read-in, read in.
        if self._nruns is None:
            self.get_resource()

        if nruns is None:
            nruns = self._nruns

        # check running jobs
        query = "select run,subrun,data from %s where status!=1 order by run,subrun asc limit %d" %( self._project, nruns )
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

            try:
                dbdata = json.loads(x[2])
            except:
                self.info("could not load file database info for (%d,%d)"%(run,subrun))
                continue
 
            if True:
                for outfile in ["dltaggerlarcv","dltaggerlarlite","dltaggerana"]:
                    if outfile in dbdata:
                        cmd = "rm -f "+dbdata[outfile]
                        self.info("remove outfile[%s]: %s"%(outfile,cmd))
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

    parser = argparse.ArgumentParser(description='Process Vertexer w/ SparseSSNet jobs')
    parser.add_argument('project',type=str,help="Project Name")
    parser.add_argument('--val',action='store_true',default=False,help='Run Valididate')
    parser.add_argument('--new-jobs',action='store_true',default=False,help='Launch New Jobs')
    parser.add_argument('--err',action='store_true',default=False,help='Handle Jobs in Error state')
    parser.add_argument('--nruns',default=10,type=int,help='Number of runs to process')
    parser.add_argument('--max-jobs',default=100,type=int,help='Maximum number of jobs to be running of this process type')
    parser.add_argument("--reset",action="store_true",default=False,help="Reset project")

    args = parser.parse_args(sys.argv[1:])
    dbinterface = showerreco(args.project)

    jobslaunched = False
    if args.new_jobs:
        jobslaunched = dbinterface.process_newruns(nruns=args.nruns,max_jobs=args.max_jobs)
    elif args.reset:
        jobslaunched = True # to skip other steps
        #dbinterface.reset_status(nruns=args.nruns) # SCARY -- BECAREFUL

    if not jobslaunched:
        if args.val:
            dbinterface.validate(nruns=10)
        if args.err:
            dbinterface.error_handle()
            #dbinterface.modstatus() # reset of DB state coupled with file deletion CAUTION!!!
            pass
