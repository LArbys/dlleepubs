import os, sys, pwd, commands, time, random, getpass, json, argparse
from pub_dbi import DBException
from dstream import DSException
from dstream import ds_project_base
from dstream import ds_status

sys.path.insert(0,os.path.join(os.environ["PUB_TOP_DIR"],"dlleepubs"))
from utils.downstream_utils import *

class mergedlfiles(ds_project_base):

    # Define project name as class attribute
    _project = 'mergedlfiles'

    ## @brief default ctor can take # runs to process for this instance
    def __init__(self,project_name):

        if project_name:
            self._project = project_name

        # Call base class ctor
        super(mergedlfiles,self).__init__()

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
        self._parent_tagger_project = str(resource['SOURCE_TAGGER_PROJECT'])
        self._parent_vertex_project = str(resource['SOURCE_VERTEX_PROJECT'])
        self._parent_track_project  = str(resource['SOURCE_TRACKER_PROJECT'])
        self._parent_shower_project = str(resource['SOURCE_SHOWER_PROJECT'])
        self._dllee_unified_dir = str(resource['DLLEE_UNIFIED_DIR'])
        self._file_format       = str(resource['FILE_FORMAT'])
        self._out_dir           = str(resource['OUTDIR'])
        self._grid_workdir      = str(resource['GRID_WORKDIR'])
        self._container         = str(resource['CONTAINER'])
        self._runtag            = str(resource['OUT_RUNTAG'])
        self._usenames          = int(str(resource['ACCOUNT_SHARE']))
        self._ismc              = int(str(resource['ISMC']))
        self._vertex_dbname_larcv   = str(resource['VERTEX_DBNAME_LARCV'])
        self._tagger_dbname_larlite = str(resource['TAGGER_DBNAME_LARLITE'])
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
        """ data about slurm queue pertaining to mergedlfiles jobs"""
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
            self.info("Already running (%d) max number of mergedlfiles jobs (%d)" % (len(results),max_jobs) )
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
        query =  "select t1.run,t1.subrun,t1.data,t2.supera,t2.opreco,t2.reco2d,tvertex.data,ttrack.data,tshower.data,ttagger.data"
        query += " from %s t1 join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun)"       % (self._project, self._filetable)
        query += " join %s ttagger  on (t1.run=ttagger.run and t1.subrun=ttagger.subrun)"  % (self._parent_tagger_project)
        query += " join %s tvertex  on (t1.run=tvertex.run and t1.subrun=tvertex.subrun)"  % (self._parent_vertex_project)
        query += " join %s ttrack   on (t1.run=ttrack.run  and t1.subrun=ttrack.subrun)"   % (self._parent_track_project)
        query += " join %s tshower  on (t1.run=tshower.run and t1.subrun=tshower.subrun)"  % (self._parent_shower_project)
        query += " where t1.status=1 and tvertex.status=4 and ttagger.status=4 and ttrack.status=4 and tshower.status=4 order by run, subrun desc limit %d" % (nremaining) 
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

            if x[2] is None:
                db_data = {}
            else:
                db_data = json.loads( x[2] )

            supera = x[3]
            opreco = x[4]
            reco2d = x[5]

            db_data_vertex = json.loads( x[6] )
            db_data_track  = json.loads( x[7] )
            db_data_shower = json.loads( x[8] )
            db_data_tagger = json.loads( x[9] )

            # job variables
            jobtag,inputdbdir,outdbdir = cast_run_subrun(run,subrun,
                                                         self._runtag,self._file_format,
                                                         self._input_dir,self._out_dir)

            # prepare work dir
            self.info("Making work directory")
            workdir      = os.path.join(self._grid_workdir,"mergedlfiles",self._project,"%s_%04d_%03d"%(self._project,run,subrun))
            cmd("mkdir -p %s"%(workdir))
            self.info("...made workdir for (%d,%d) at %s"%(run,subrun,workdir))
            cmd("chmod a+w -R %s"%(workdir))

            # make output dir
            self.info("Making output directory @dir=%s" % str(outdbdir))
            cmd("mkdir -p %s" % (outdbdir))
            cmd("chmod g+w -R %s"%(outdbdir))

            # output file names
            out_dlmerged    = os.path.join(outdbdir,self._file_format%(self._project,run,subrun))
            db_data["dlmerged"] = out_dlmerged

            # write submission script
            submitscript="""#!/bin/sh
#SBATCH --job-name=mergedlfiles_{jobtag}
#SBATCH --output={workdir}/log_{jobtag}.txt
#SBATCH --time=03:00:00
#SBATCH --mem-per-cpu=2000

CONTAINER={container}
WORKDIR={workdir}
OUTPUTDIR={outputdir}
DLLEE_DIR={dllee_dir}

OUT_DLMERGED={out_dlmerged}

# LARCV
SUPERA={supera}
VERTEXER={vertexer}
NUEID_LARCV={nueid_larcv}

# LARLITE
OPRECO={opreco}
RECO2D={reco2d}
TAGGER_LARLITE={tagger_larlite}
TRACKER_LARLITE={tracker_larlite}
NUEID_LARLITE={nueid_larlite}
SHOWER_LARLITE={shower_larlite}

# ANA
NUEID_ANA={nueid_ana}
SHOWER_ANA={shower_ana}
TRACKER_ANA={tracker_ana}

MERGE_LARCV_FILES="$VERTEXER $NUEID_LARCV"
MERGE_ANA_FILES="$NUEID_ANA $SHOWER_ANA $TRACKER_ANA"
#MERGE_LARLITE_FILES="$OPRECO $RECO2D $TAGGER_LARLITE $TRACKER_LARLITE $NUEID_LARLITE $SHOWER_LARLITE"
MERGE_LARLITE_FILES="$OPRECO $RECO2D tagger_larlite.root tracker_larlite.root nueid_larlite.root shower_larlite.root"

CHECK_SCRIPT=/cluster/tufts/wongjiradlab/larbys/pubs/dlleepubs/mergedlfiles/check_files.py
APPEND_CHSTATUS_SCRIPT=$DLLEE_DIR/dlreco_scripts/bin/append_chstatus.py

mkdir -p $OUTPUTDIR
module load singularity
CONFIG_SETUP="cd $DLLEE_DIR && source setup_tufts_container.sh && source configure.sh && cd $WORKDIR"
LINK_IN="ln -s $TAGGER_LARLITE tagger_larlite.root && ln -s $TRACKER_LARLITE tracker_larlite.root && ln -s $NUEID_LARLITE nueid_larlite.root && ln -s $SHOWER_LARLITE shower_larlite.root"
RUN_LARLITE_MERGE="python $DLLEE_DIR/dlreco_scripts/bin/combine_larlite.py -o dlmerged_larlite.root $MERGE_LARLITE_FILES"
RUN_HADD="hadd -f dlmerged_reco.root $MERGE_LARCV_FILES $MERGE_ANA_FILES dlmerged_larlite.root"
APPEND_CHSTATUS="python $APPEND_CHSTATUS_SCRIPT dlmerged_reco.root $SUPERA"
COPY_CMD="cp dlmerged_reco.root $OUT_DLMERGED"
srun singularity exec $CONTAINER bash -c "$CONFIG_SETUP && $LINK_IN && $RUN_LARLITE_MERGE && $RUN_HADD && $APPEND_CHSTATUS && $COPY_CMD"
"""
            fsubmit = open(workdir+"/submit.sh",'w')
            inputmap = {"jobtag":jobtag,
                        "workdir":workdir,
                        "container":self._container,
                        "outputdir":os.path.dirname(outdbdir),
                        "dllee_dir":self._dllee_unified_dir,
                        "supera":supera,
                        "vertexer":db_data_vertex[self._vertex_dbname_larcv],
                        "nueid_larcv":db_data_shower["nueid-larcv"],
                        "opreco":opreco,
                        "reco2d":reco2d,
                        "tagger_larlite":db_data_tagger[self._tagger_dbname_larlite],
                        "nueid_larlite":db_data_shower["nueid-larlite"],
                        "shower_larlite":db_data_shower["shower-reco"],
                        "tracker_larlite":db_data_track["tracker-larlite"],
                        "nueid_ana":db_data_shower["nueid-ana"],
                        "shower_ana":db_data_shower["shower-ana"],
                        "tracker_ana":db_data_track["tracker-ana"],
                        "out_dlmerged":out_dlmerged,
                        }

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
        psinfo = os.popen("squeue | grep mergedl")
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
        self.info("Number of mergedlfiles jobs in running state: %d"%(len(results)))
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
        self.info("Number of mergedlfiles jobs in finished state: %d"%(len(results)))
        for x in results:
            run    = int(x[0])
            subrun = int(x[1])
            dbdata = json.loads(x[3])

            # form output file names/workdir
            jobtag,inputdbdir,outdbdir = cast_run_subrun(run,subrun,
                                                         self._runtag,self._file_format,
                                                         self._input_dir,self._out_dir)
            workdir      = os.path.join(self._grid_workdir,"mergedlfiles",self._project,"%s_%04d_%03d"%(self._project,run,subrun))

            # check files exist
            success = os.path.exists( dbdata["dlmerged"] )

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
    dbinterface = mergedlfiles(args.project)

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
