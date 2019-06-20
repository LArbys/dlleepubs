import os, sys, pwd, commands, time, random, getpass
from pub_dbi import DBException
from dstream import DSException
from dstream import ds_project_base
from dstream import ds_status

sys.path.insert(0,os.path.join(os.environ["PUB_TOP_DIR"],"dlleepubs"))
from utils.downstream_utils import *

class likelihood_reco(ds_project_base):

    # Define project name as class attribute
    _project = 'likelihood_reco'

    ## @brief default ctor can take # runs to process for this instance
    def __init__(self,project_name):

        if project_name:
            self._project = project_name

        # Call base class ctor
        super(likelihood_reco,self).__init__()

        self._nruns           = None
        self._parent_project1 = ""
        self._input_dir1      = ""
        self._input_dir2      = ""
        self._file_format     = ""
        self._out_dir         = ""
        self._filetable       = ""
        self._grid_workdir    = ""
        self._container       = ""
        self._run_script      = ""
        self._sub_script      = ""
        self._vtx_runtag      = ""
        self._trk_runtag      = ""
        self._out_runtag      = ""
        self._precut_cfg      = ""
        self._is_mc           = ""
        self._max_jobs        = None
        self._usenames        = ""
        self._names = []

    ## @brief method to retrieve the project resource information if not yet done
    def get_resource(self):

        resource = self._api.get_resource(self._project)
        
        self._nruns            = int(500)
        self._parent_project1  = str(resource['SOURCE_PROJECT1'])
        self._input_dir1       = str(resource['STAGE1DIR'])
        self._input_dir2       = str(resource['STAGE2DIR'])
        self._file_format      = str(resource['FILE_FORMAT'])
        self._out_dir          = str(resource['OUTDIR'])
        self._filetable        = str(resource['FILETABLE'])    
        self._grid_workdir     = str(resource['GRID_WORKDIR'])
        self._container        = str(resource['CONTAINER'])
        self._run_script       = os.path.join(SCRIPT_DIR,str(resource['RUN_SCRIPT']))
        self._sub_script       = os.path.join(SCRIPT_DIR,"submit_pubs_job.sh")
        self._vtx_runtag       = str(resource['VTX_RUNTAG'])
        self._trk_runtag       = str(resource['TRK_RUNTAG'])
        self._out_runtag       = str(resource['OUT_RUNTAG'])
        self._precut_cfg       = str(resource['PRECUT_CFG'])
        self._is_mc            = int(str(resource['IS_MC']))
        self._max_jobs         = int(100e3) 
        self._usenames         = int(str(resource['ACCOUNT_SHARE']))
        
        if self._usenames == 1:
            self._names = ["vgenty01",
                           "cbarne06",
                           "jmoon02",
                           "ran01",
                           "lyates01",
                           "ahourl01",
                           "adiaz09"]


    def query_queue(self):
        """ data about slurm queue pertaining to likelihood_reco jobs"""
        psqueue = commands.getoutput("squeue | grep likeliho")
        lsqueue = psqueue.split('\n')

        info = {"numjobs":0,"jobids":[]}
        for l in lsqueue:
            if l.strip()!="":
                jobid = int(l.split()[0])
                info["jobids"].append(jobid)
        info["numjobs"] = len(info["jobids"])
        return info

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
            self.info("Already running (%d) max number of likelihood_reco jobs (%d)" % (len(results),self._max_jobs) )
            return

        if nremaining>self._nruns:
            nremaining = self._nruns

        # get queue status
        qinfo = self.query_queue()
        #print qinfo
        
        #
        # ...this is not the pubs way, pray it's right...
        #

        # Fetch runs from DB and process for # runs specified for this instance.
        query  = "select t1.run,t1.subrun"
        query += " from %s t1" % (self._project)
        query += " join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun)" % (self._filetable)
        query += " join %s t3 on (t1.run=t3.run and t1.subrun=t3.subrun)" % (self._parent_project1)
        query += " where t1.status=1 and t3.status=4"
        query += " order by run, subrun desc limit %d" % (nremaining) 

        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        ijob = 0
        for x in results:

            # run id
            run    = int(x[0])
            subrun = int(x[1])
            _     , inputdbdir0, _ = cast_run_subrun(run,subrun,              "","", self._input_dir1,""   )
            _     , _, inputdbdir1 = cast_run_subrun(run,subrun,self._vtx_runtag,"","",self._out_dir)
            _     , _, inputdbdir2 = cast_run_subrun(run,subrun,self._trk_runtag,"","",self._out_dir)
            jobtag, _, outdbdir    = cast_run_subrun(run,subrun,self._out_runtag,"","",self._out_dir)
            
            
            # prepare work dir
            workdir      = os.path.join(self._grid_workdir,"ll",self._out_runtag,"%s_%04d_%03d"%(self._project,run,subrun))
            inputlistdir = os.path.join(workdir,"inputlists")
            stat,out = commands.getstatusoutput("mkdir -p %s"%(inputlistdir))
            self.info("...made workdir for (%d,%d) at %s"%(run,subrun,workdir))
            
            #
            # prepare input lists
            #
            oprecoinput = os.path.join(inputdbdir0,self._file_format%("opreco",run,subrun))
            oprecoinput+= ".root"

            mcinfoinput = os.path.join(inputdbdir0,self._file_format%("mcinfo",run,subrun))
            mcinfoinput+= ".root"

            tagger_lcv_input  = os.path.join(inputdbdir0,self._file_format%("taggerout-larcv",run,subrun))
            tagger_lcv_input += ".root"

            tagger_ll_input  = os.path.join(inputdbdir0,self._file_format%("taggerout-larlite",run,subrun))
            tagger_ll_input += ".root"
            
            vertexana_input  = os.path.join(inputdbdir1,"vertexana_%d.root" % jobtag)
            vertexout_input  = os.path.join(inputdbdir1,"vertexout_%d.root" % jobtag)
            trackerana_input = os.path.join(inputdbdir2,"tracker_anaout_%d.root" % jobtag)
            vertexpklinput   = os.path.join(inputdbdir1,"ana_comb_df_%d.pkl" % jobtag)

            
            #
            # write the text files to inputlist folder
            #


            # tagger_lcv_input
            inputlist_f = open(os.path.join(inputlistdir,"tagger_lcv_inputlist_%05d.txt"% int(jobtag)),"w+")
            inputlist_f.write("%s" % os.path.realpath(tagger_lcv_input))
            inputlist_f.close()

            # tagger_ll_input
            inputlist_f = open(os.path.join(inputlistdir,"tagger_ll_inputlist_%05d.txt"% int(jobtag)),"w+")
            inputlist_f.write("%s" % os.path.realpath(tagger_ll_input))
            inputlist_f.close()

            # vertexana
            inputlist_f = open(os.path.join(inputlistdir,"vertex_ana_inputlist_%05d.txt"% int(jobtag)),"w+")
            inputlist_f.write("%s" % os.path.realpath(vertexana_input))
            inputlist_f.close()

            # vertexout
            inputlist_f = open(os.path.join(inputlistdir,"vertex_out_inputlist_%05d.txt"% int(jobtag)),"w+")
            inputlist_f.write("%s" % os.path.realpath(vertexout_input))
            inputlist_f.close()

            # tracker ana
            inputlist_f = open(os.path.join(inputlistdir,"tracker_ana_inputlist_%05d.txt"% int(jobtag)),"w+")
            inputlist_f.write("%s" % os.path.realpath(trackerana_input))
            inputlist_f.close()
            
            # mcinfo
            inputlist_f = open(os.path.join(inputlistdir,"mcinfo_inputlist_%05d.txt"% int(jobtag)),"w+")
            if self._is_mc == 1:
                inputlist_f.write("%s" % os.path.realpath(mcinfoinput))
            else:
                inputlist_f.write("%s" % "INVALID")
            inputlist_f.close()

            # opreco
            inputlist_f = open(os.path.join(inputlistdir,"opreco_inputlist_%05d.txt"% int(jobtag)),"w+")
            inputlist_f.write("%s" % os.path.realpath(oprecoinput))
            inputlist_f.close()

            # vertex pkl
            inputlist_f = open(os.path.join(inputlistdir,"vertex_pkl_inputlist_%05d.txt"% int(jobtag)),"w+")
            inputlist_f.write("%s" % os.path.realpath(vertexpklinput))
            inputlist_f.close()

            # runlist
            runlist_f = open(os.path.join(workdir,"runlist.txt"),"w+")
            runlist_f.write("%s" % jobtag)
            runlist_f.close()

            # rerunlist
            rerunlist_f = open(os.path.join(workdir,"rerunlist.txt"),"w+")
            rerunlist_f.write("%s" % jobtag)
            rerunlist_f.close()

            # make output dir
            self.info("Making output directory @dir=%s" % str(outdbdir))
            stat,out = commands.getstatusoutput("mkdir -p %s" % (outdbdir))

            # copy reco job template over
            stat,out = commands.getstatusoutput("scp -r %s %s" % (self._run_script,workdir))
            run_script = os.path.join(workdir,os.path.basename(self._run_script))

            # copy configs over
            precut_dir = "/cluster/tufts/wongjiradlab/larbys/pubs/dlleepubs/downstream/Production_Config/cfg/precuts/"
            self._precut_cfg = os.path.join(precut_dir,self._precut_cfg)
            stat,out = commands.getstatusoutput("scp -r %s %s" % (self._precut_cfg,workdir))
            precut_cfg = os.path.join(workdir,os.path.basename(self._precut_cfg))

            run_data = ""
            with open(run_script,"r") as f: run_data = f.read()
            run_data = run_data.replace("RRR",os.path.basename(precut_cfg))
            with open(run_script,"w") as f: f.write(run_data)
            
            # copy submission script over
            stat,out = commands.getstatusoutput("scp -r %s %s" % (self._sub_script,workdir))
            sub_script = os.path.join(workdir,os.path.basename(self._sub_script))
            
            sub_data = ""
            with open(sub_script,"r") as f: sub_data = f.read()
            sub_data=sub_data.replace("AAA","likelihood_reco_%s" % str(jobtag))
            sub_data=sub_data.replace("BBB",os.path.join(workdir,"log.txt"))
            sub_data=sub_data.replace("CCC","1")
            sub_data=sub_data.replace("DDD",self._container)
            sub_data=sub_data.replace("EEE",workdir)
            sub_data=sub_data.replace("FFF",outdbdir)
            sub_data=sub_data.replace("GGG",os.path.basename(run_script))
            sub_data=sub_data.replace("HHH",outdbdir)
            with open(sub_script,"w") as f: f.write(sub_data)

            ijob += 1

            submissionok = False
            
            # sys.exit(1)
            
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
                    # SSH_PREFIX = "ssh %s@xfer.cluster.tufts.edu \"%s\""
                    SSH_PREFIX = "ssh %s@fastx-dev \"%s\""
                    SS = "sbatch %s" % os.path.join(workdir,"submit_pubs_job.sh")

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
        psinfo = os.popen( "squeue | grep likeliho")
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
        self.info("Number of likelihood_reco jobs in running state: %d"%(len(results)))
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
        self.info("Number of likelihood_reco jobs in finished state: %d"%(len(results)))
        for x in results:
            run    = int(x[0])
            subrun = int(x[1])

            # form output file names/workdir
            jobtag,inputdbdir2,outdbdir = cast_run_subrun(run,subrun,
                                                          self._out_runtag,self._file_format,
                                                          self._input_dir1,self._out_dir)
            # link
            st_pkl1 = os.path.join(outdbdir,"FinalVertexVariables_%d.root" % jobtag)
            #print st_pkl1
            success = os.path.exists(st_pkl1)

            if success == True:
                self.info("status of job for (%d,%d) is good"%(run,subrun))
                status = ds_status( project = self._project,
                                    run     = run,
                                    subrun  = subrun,
                                    seq     = 0,
                                    status  = 4 )
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
            workdir = os.path.join(self._grid_workdir,"ll",self._out_runtag,"%s_%04d_%03d"%(self._project,run,subrun))
            SS = "rm -rf %s"%(workdir)
            self.info(SS)
            os.system(SS)
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

    test_obj = likelihood_reco(sys.argv[1])
    jobslaunched = False
    jobslaunched = test_obj.process_newruns()
    test_obj.validate()
    test_obj.error_handle()

