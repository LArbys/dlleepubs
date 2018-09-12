import os, sys, pwd, commands, time, random, getpass
from pub_dbi import DBException
from dstream import DSException
from dstream import ds_project_base
from dstream import ds_status

sys.path.insert(0,os.path.join(os.environ["PUB_TOP_DIR"],"dlleepubs"))
from utils.downstream_utils import *

class nueid_reco(ds_project_base):

    # Define project name as class attribute
    _project = 'nueid_reco'

    ## @brief default ctor can take # runs to process for this instance
    def __init__(self,project_name):

        if project_name:
            self._project = project_name

        # Call base class ctor
        super(nueid_reco,self).__init__()

        self._nruns           = None
        self._parent_project  = ""
        self._input_dir1      = ""
        self._input_dir2      = ""
        self._file_format     = ""
        self._out_dir         = ""
        self._filetable       = ""
        self._grid_workdir    = ""
        self._container       = ""
        self._run_script      = ""
        self._sub_script      = ""
        self._nueidcfg        = ""
        self._shrcfg          = ""
        self._shranacfg       = ""
        self._pidcfg          = ""
        self._flashcfg        = ""
        self._vtx_runtag      = ""
        self._out_runtag      = ""
        self._script          = ""
        self._max_jobs        = None
        self._usenames        = ""
        self._ismc            = ""
        self._names           = []

    ## @brief method to retrieve the project resource information if not yet done
    def get_resource(self):

        resource = self._api.get_resource(self._project)
        
        self._nruns = int(500)
        self._parent_project   = str(resource['SOURCE_PROJECT'])
        self._input_dir1       = str(resource['STAGE1DIR'])
        self._input_dir2       = str(resource['STAGE2DIR'])
        self._file_format      = str(resource['FILE_FORMAT'])
        self._out_dir          = str(resource['OUTDIR'])
        self._filetable        = str(resource['FILETABLE'])    
        self._grid_workdir     = str(resource['GRID_WORKDIR'])
        self._container        = str(resource['CONTAINER'])
        self._run_script       = os.path.join(SCRIPT_DIR,str(resource['RUN_SCRIPT']))
        self._sub_script       = os.path.join(SCRIPT_DIR,"submit_pubs_job.sh")
        self._nueidcfg         = os.path.join(CFG_DIR,"nueid",str(resource['NUEIDCFG']))
        self._michelidcfg      = os.path.join(CFG_DIR,"nueid",str(resource['MICHELIDCFG']))
        self._shrcfg           = os.path.join(CFG_DIR,"shower",str(resource['SHRCFG']))
        self._shranacfg        = os.path.join(CFG_DIR,"truth",str(resource['SHRANACFG']))
        self._pidcfg           = os.path.join(CFG_DIR,"network",str(resource['PIDCFG']))
        self._flashcfg         = os.path.join(CFG_DIR,"flash",str(resource['FLASHCFG']))
        self._vtx_runtag       = str(resource['VTX_RUNTAG'])
        self._out_runtag       = str(resource['OUT_RUNTAG'])
        self._max_jobs         = int(1e3)
        self._ismc             = int(str(resource['ISMC']))
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
        """ data about slurm queue pertaining to nueid_reco jobs"""
        psqueue = commands.getoutput("squeue | grep nue_")
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
            self.info("Already running (%d) max number of nueid_reco jobs (%d)" % (len(results),self._max_jobs) )
            return

        if nremaining>self._nruns:
            nremaining = self._nruns

        # get queue status
        qinfo = self.query_queue()
        
        #
        # ...this is not the pubs way, pray it's right...
        #

        # Fetch runs from DB and process for # runs specified for this instance.
        query =  "select t1.run,t1.subrun"
        query += " from %s t1 join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun)" % (self._project, self._filetable)

        query += " join %s t3 on (t1.run=t3.run and t1.subrun=t3.subrun)" % (self._parent_project)
        query += " where t1.status=1 and t3.status=4 order by run, subrun desc limit %d" % (nremaining) 

        # query += " where t1.status=1 order by run, subrun desc limit %d" % (nremaining) 
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        ijob = 0
        for x in results:

            # run id
            run    = int(x[0])
            subrun = int(x[1])
            _     , inputdbdir0,           _ = cast_run_subrun(run,subrun,              "","", self._input_dir1,""           )
            _     ,           _, inputdbdir1 = cast_run_subrun(run,subrun,self._vtx_runtag,"",               "",self._out_dir)
            jobtag,           _, outdbdir    = cast_run_subrun(run,subrun,self._out_runtag,"",               "",self._out_dir)
            
            
            # prepare work dir
            self.info("Making work directory")
            workdir      = os.path.join(self._grid_workdir,"nue",self._out_runtag,"%s_%04d_%03d"%(self._project,run,subrun))
            inputlistdir = os.path.join(workdir,"inputlists")
            stat,out = commands.getstatusoutput("mkdir -p %s"%(inputlistdir))
            self.info("...made workdir for (%d,%d) at %s"%(run,subrun,workdir))
            self.info("..... %d %s"%(stat,out))

            #
            # prepare input lists
            #
            supera_input  = os.path.join(inputdbdir0,self._file_format%("supera",run,subrun))
            supera_input += ".root"

            #ssnet_input  = os.path.join(inputdbdir0,self._file_format%("ssnetserverout-larcv",run,subrun))
            ssnet_input  = os.path.join(inputdbdir0,self._file_format%("ssnetserveroutv2-larcv",run,subrun))
            ssnet_input  += ".root"

            #tagger_input  = os.path.join(inputdbdir0,self._file_format%("taggerout-larcv",run,subrun))
            tagger_input  = os.path.join(inputdbdir0,self._file_format%("taggeroutv2-larcv",run,subrun))
            tagger_input += ".root"

            opreco_input  = os.path.join(inputdbdir0,self._file_format%("opreco",run,subrun))
            opreco_input += ".root"

            reco2dinput  = os.path.join(inputdbdir0,self._file_format%("reco2d",run,subrun))
            reco2dinput += ".root"

            vertexout_input = os.path.join(inputdbdir1,"vertexout_%d.root" % jobtag)

            # supera
            inputlist_f = open(os.path.join(inputlistdir,"supera_inputlist_%05d.txt"% int(jobtag)),"w+")
            inputlist_f.write("%s" % supera_input.replace("90-days-archive",""))
            inputlist_f.close()

            # ssnet
            inputlist_f = open(os.path.join(inputlistdir,"ssnet_inputlist_%05d.txt"% int(jobtag)),"w+")
            inputlist_f.write("%s" % ssnet_input.replace("90-days-archive",""))
            inputlist_f.close()

            # tagger
            inputlist_f = open(os.path.join(inputlistdir,"tagger_inputlist_%05d.txt"% int(jobtag)),"w+")
            inputlist_f.write("%s" % tagger_input.replace("90-days-archive",""))
            inputlist_f.close()
            
            # opreco
            inputlist_f = open(os.path.join(inputlistdir,"opreco_inputlist_%05d.txt"% int(jobtag)),"w+")
            inputlist_f.write("%s" % opreco_input.replace("90-days-archive",""))
            inputlist_f.close()

            # vertex
            inputlist_f = open(os.path.join(inputlistdir,"vertex_inputlist_%05d.txt"% int(jobtag)),"w+")
            inputlist_f.write("%s" % vertexout_input.replace("90-days-archive",""))
            inputlist_f.close()

            # reco2d
            inputlist_f = open(os.path.join(inputlistdir,"reco2d_inputlist_%05d.txt"% int(jobtag)),"w+")
            inputlist_f.write("%s" % reco2dinput.replace("90-days-archive",""))
            inputlist_f.close()

            # runlist
            self.info("Filling runlist with jobtag=%s" % str(jobtag))
            runlist_f = open(os.path.join(workdir,"runlist.txt"),"w+")
            runlist_f.write("%s" % jobtag)
            runlist_f.close()

            # rerunlist
            self.info("Filling rerunlist with jobtag=%s" % str(jobtag))
            rerunlist_f = open(os.path.join(workdir,"rerunlist.txt"),"w+")
            rerunlist_f.write("%s" % jobtag)
            rerunlist_f.close()

            # make output dir
            self.info("Making output directory @dir=%s" % str(outdbdir))
            stat,out = commands.getstatusoutput("mkdir -p %s" % (outdbdir))

            # copy reco job template over
            stat,out = commands.getstatusoutput("scp %s %s" % (self._run_script,workdir))
            run_script = os.path.join(workdir,os.path.basename(self._run_script))

            stat,out = commands.getstatusoutput("scp -r %s %s" % (self._nueidcfg,workdir))
            nueidcfg = os.path.join(workdir,os.path.basename(self._nueidcfg))

            stat,out = commands.getstatusoutput("scp -r %s %s" % (self._michelidcfg,workdir))
            michelidcfg = os.path.join(workdir,os.path.basename(self._michelidcfg))

            stat,out = commands.getstatusoutput("scp -r %s %s" % (self._shrcfg,workdir))
            shrcfg = os.path.join(workdir,os.path.basename(self._shrcfg))

            stat,out = commands.getstatusoutput("scp -r %s %s" % (self._shranacfg,workdir))
            shranacfg = os.path.join(workdir,os.path.basename(self._shranacfg))

            stat,out = commands.getstatusoutput("scp -r %s %s" % (self._pidcfg,workdir))
            pidcfg = os.path.join(workdir,os.path.basename(self._pidcfg))

            stat,out = commands.getstatusoutput("scp -r %s %s" % (self._flashcfg,workdir))
            flashcfg = os.path.join(workdir,os.path.basename(self._flashcfg))

            run_data = ""
            with open(run_script,"r") as f: run_data = f.read()
            run_data = run_data.replace("KKK",os.path.basename(shrcfg))
            run_data = run_data.replace("RRR",os.path.basename(shranacfg))
            run_data = run_data.replace("EEE",os.path.basename(pidcfg))
            run_data = run_data.replace("FFF",os.path.basename(nueidcfg))
            run_data = run_data.replace("GGG",os.path.basename(flashcfg))
            run_data = run_data.replace("HHH",os.path.basename(michelidcfg))
            run_data = run_data.replace("BBB",str(self._ismc))
            with open(run_script,"w") as f: f.write(run_data)

            # copy submission script over
            stat,out = commands.getstatusoutput("scp %s %s" % (self._sub_script,workdir))
            self.info("..... %d %s"%(stat,out))
            sub_script = os.path.join(workdir,os.path.basename(self._sub_script))
            
            sub_data = ""
            with open(sub_script,"r") as f: sub_data = f.read()
            sub_data=sub_data.replace("AAA","nue_reco_%s" % str(jobtag))
            sub_data=sub_data.replace("BBB",os.path.join(workdir,"log.txt"))
            sub_data=sub_data.replace("CCC","1")
            sub_data=sub_data.replace("DDD",self._container)
            sub_data=sub_data.replace("EEE",workdir.replace("90-days-archive",""))
            sub_data=sub_data.replace("FFF",outdbdir)
            sub_data=sub_data.replace("GGG",os.path.basename(run_script))
            sub_data=sub_data.replace("HHH",outdbdir.replace("90-days-archive",""))
            with open(sub_script,"w") as f: f.write(sub_data)

            ijob += 1

            submissionok = False

            self.info("...submitting...")

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
                    #SSH_PREFIX = "ssh %s@xfer.cluster.tufts.edu \"%s\""
                    SSH_PREFIX = "ssh %s@fastx-dev.cluster.tufts.edu \"%s\""
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
        psinfo = os.popen( "squeue | grep nue_")
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
        self.info("Number of nueid_reco jobs in running state: %d"%(len(results)))
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
        self.info("Number of nueid_reco jobs in finished state: %d"%(len(results)))
        for x in results:
            run    = int(x[0])
            subrun = int(x[1])

            # form output file names/workdir
            jobtag,inputdbdir2,outdbdir = cast_run_subrun(run,subrun,
                                                          self._out_runtag,self._file_format,
                                                          self._input_dir1,self._out_dir)
            # link
            ana = os.path.join(outdbdir,"nueid_comb_df_%d.pkl" % jobtag)
            success = os.path.exists(ana)

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
        self.info("got nruns=%s" % self._nruns)
        query = "select run,subrun from %s where status=10 order by run,subrun asc limit %d" %( self._project, self._nruns*10 )
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()

        # Fetch runs from DB and process for # runs specified for this instance.
        for x in results:
            # we clean out the workdir
            run     = int(x[0])
            subrun  = int(x[1])
            workdir = os.path.join(self._grid_workdir,"nue",self._out_runtag,"%s_%04d_%03d"%(self._project,run,subrun))
            self.info("deleting... %s" % workdir)
            SS="rm -rf %s"%(workdir)
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

    test_obj = nueid_reco(sys.argv[1])
    jobslaunched = False
    jobslaunched = test_obj.process_newruns()
    test_obj.validate()
    # test_obj.error_handle()
    
