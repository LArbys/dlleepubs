## @namespace dlleepubs.tagger
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
        
        self._nruns = int(resource['NRUNS'])
        self._nruns = 1
        self._parent_project = resource['SOURCE_PROJECT']
        self._out_dir        = resource['OUTDIR']
        self._outfile_format = resource['OUTFILE_FORMAT']
        self._filetable      = resource['FILETABLE']        
        self._grid_workdir   = resource['GRID_WORKDIR']
        self._tagger_cfg     = resource['TAGGERCFG']
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
        
        if nremaining<=0:
            self.info("Already running (%d) max number of tagger jobs (%d)" % (len(results),self._nruns) )
            return

        # Fetch runs from DB and process for # runs specified for this instance.
        query =  "select t1.run,t1.subrun,supera,opreco,mcinfo"
        query += " from %s t1 join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun) join %s t3 on (t1.run=t3.run and t1.subrun=t3.subrun)" % (self._project,self._filetable,self._parent_project)
        query += " where t1.status=1 and t3.status=3 order by run, subrun desc limit %d" % (nremaining) 
        print query

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
            larcvout   = dbdir + "/" + self._outfile_format%("taggerout-larcv",run,subrun)
            larliteout = dbdir + "/" + self._outfile_format%("taggerout-larlite",run,subrun)

            print x
            jobtag       = 10000*run + subrun
            workdir      = self._grid_workdir + "/%s_%04d_%03d"%(self._project,run,subrun)
            inputlistdir = workdir + "/inputlists"
            os.system("mkdir -p %s"%(inputlistdir))
            larcv_input   = open('%s/input_larcv_%09d.txt'%(inputlistdir,jobtag),'w')
            larlite_input = open('%s/input_larlite_%09d.txt'%(inputlistdir,jobtag),'w')
            rerunlist     = open('%s/rerunlist.txt'%(workdir),'w')
            print >> larcv_input,x[2]
            print >> larlite_input,x[3]
            print >> larlite_input,x[4]
            print >> rerunlist,jobtag
            larcv_input.close()
            larlite_input.close()


            os.system("cp %s %s/"%(self._tagger_cfg,workdir))
            os.system("cp run_taggerpubs_job.sh %s/"%(workdir))

            # make submission script
            submitscript="""#!/bin/sh
#
#SBATCH --job-name=tagger_%d
#SBATCH --output=log_tagger_%d_%d.txt
#SBATCH --ntasks=1
#SBATCH --time=480:00
#SBATCH --mem-per-cpu=4000

WORKDIR=%s
CONTAINER=%s
INPUTLISTDIR=${WORKDIR}/inputlists
JOBIDLIST=${WORKDIR}/rerunlist.txt
CONFIG=%s
LARCV_OUTFILENAME=%s
LARLITE_OUTFILENAME=%s

module load singularity
srun singularity exec ${CONTAINER} bash -c "cd ${WORKDIR} && source run_taggerpubs_job.sh ${CONFIG} ${INPUTLISTDIR} ${LARCV_OUTFILENAME} ${LARLITE_OUTFILENAME} ${JOBIDLIST}"
"""
            submit = submitscript%(jobtag,run,subrun,workdir,self._container,self._tagger_cfg,larcvout,larliteout)
            submitout = open(workdir+"/submit.sh",'w')
            print >>submitout,submit
            submitout.close()

            psubmit = os.popen("sbatch %s/submit.sh"%(workdir))
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

            # Break from loop if counter became 0
            #if not ctr: break

    ## @brief access DB and retrieves processed run for validation
    def validate(self):

        # Attempt to connect DB. If failure, abort
        if not self.connect():
	    self.error('Cannot connect to DB! Aborting...')
	    return

        # If resource info is not yet read-in, read in.
        if self._nruns is None:
            self.get_resource()

        # Fetch runs from DB and process for # runs specified for this instance.
        ctr = self._nruns
        for x in self.get_runs(self._project,2):

            # Counter decreases by 1
            ctr -=1

            (run, subrun) = (int(x[0]), int(x[1]))

            # Report starting
            self.info('validating run: run=%d, subrun=%d ...' % (run,subrun))

            status = 1
            in_file = '%s/%s' % (self._in_dir,self._infile_format % (run,subrun))
            out_file = '%s/%s' % (self._out_dir,self._outfile_format % (run,subrun))

            if os.path.isfile(out_file):
                os.system('rm %s' % in_file)
                status = 0
            else:
                status = 100

            # Pretend I'm doing something
            time.sleep(1)

            # Create a status object to be logged to DB (if necessary)
            status = ds_status( project = self._project,
                                run     = int(x[0]),
                                subrun  = int(x[1]),
                                seq     = int(x[2]),
                                status  = status )
            
            # Log status
            self.log_status( status )

            # Break from loop if counter became 0
            if not ctr: break

    ## @brief access DB and retrieves runs for which 1st process failed. Clean up.
    def error_handle(self):

        # Attempt to connect DB. If failure, abort
        if not self.connect():
	    self.error('Cannot connect to DB! Aborting...')
	    return

        # If resource info is not yet read-in, read in.
        if self._nruns is None:
            self.get_resource()

        # Fetch runs from DB and process for # runs specified for this instance.
        ctr = self._nruns
        for x in self.get_runs(self._project,100):

            # Counter decreases by 1
            ctr -=1

            (run, subrun) = (int(x[0]), int(x[1]))

            # Report starting
            self.info('cleaning failed run: run=%d, subrun=%d ...' % (run,subrun))

            status = 1

            out_file = '%s/%s' % (self._out_dir,self._outfile_format % (run,subrun))

            if os.path.isfile(out_file):
                os.system('rm %s' % out_file)

            # Pretend I'm doing something
            time.sleep(1)

            # Create a status object to be logged to DB (if necessary)
            status = ds_status( project = self._project,
                                run     = int(x[0]),
                                subrun  = int(x[1]),
                                seq     = 0,
                                data    = data,
                                status  = status )
            
            # Log status
            self.log_status( status )

            # Break from loop if counter became 0
            if not ctr: break

# A unit test section
if __name__ == '__main__':

    import sys
    test_obj = None
    if len(sys.argv)>1:
        test_obj = tagger(sys.argv[1])
    else:
        test_obj = tagger()
        
    test_obj.process_newruns()

    #test_obj.error_handle()

    #test_obj.validate()

