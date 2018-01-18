## @namespace dlleepubs.freetaggercv
#  @ingroup dummy_dstream
#  @brief Defines a project freetaggercv
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
PUBFREETAGGERCVDIR = PUBDIR+"/dlleepubs/freetaggercv"

## @class freetaggercv
#  @brief A dummy nu bin file xfer project
#  @details
#  This dummy project transfers dummy files created by dummy_daq project\n
#  It simply copies dummy nu bin files with a different file name under $PUB_TOP_DIR/data.
class freetaggercv(ds_project_base):

    # Define project name as class attribute
    _project = 'freetaggercv'

    ## @brief default ctor can take # runs to process for this instance
    def __init__(self,project_name):

        if project_name:
            self._project = project_name

        # Call base class ctor
        super(freetaggercv,self).__init__()

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
        self._parent_project = resource['SOURCE_PROJECT']
        self._out_dir        = resource['OUTDIR']
        self._outfile_format = resource["OUTFILE_FORMAT"]
        self._filetable      = resource['FILETABLE']        
        self._max_jobs       = 20


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


        # Fetch runs from DB and process for # runs specified for this instance.
        #self._nruns = 1
        query =  "select t1.run,t1.subrun"
        query += " from %s t1 join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun) join %s t3 on (t1.run=t3.run and t1.subrun=t3.subrun)" % (self._project,self._filetable,self._parent_project)
        query += " where t1.status=1 and t3.status=4 order by run, subrun desc limit %d" % (self._nruns) 
        #print query

        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        for x in results:

            # for each:
            # delete taggerout-larcv, replace with symlink
            run    = int(x[0])
            subrun = int(x[1])
            runmod100 = run%100
            rundiv100 = run/100
            subrunmod100 = subrun%100
            subrundiv100 = subrun/100
            
            dbdir = self._out_dir + "/%03d/%02d/%03d/%02d/"%(rundiv100,runmod100,subrundiv100,subrunmod100)
            larcvout   = dbdir + "/" + self._outfile_format%("taggerout-larcv",run,subrun)
            ssnetout = dbdir + "/" + self._outfile_format%("ssnetout-larcv",run,subrun)

            rmlarcv = "rm %s"%(larcvout)
            linklarcv = "ln -s %s %s"%(ssnetout,larcvout)
            os.system(rmlarcv)
            os.system(linklarcv)
            self.info(rmlarcv)
            self.info(linklarcv)

            data = ""
            status = ds_status( project = self._project,
                                run     = int(x[0]),
                                subrun  = int(x[1]),
                                seq     = 0,
                                data    = data,
                                status  = 4 )
            self.log_status( status )


        return True

    ## @brief access DB and retrieves processed run for validation
    def validate(self):

        # Attempt to connect DB. If failure, abort
        if not self.connect():
	    self.error('Cannot connect to DB! Aborting...')
	    return

        # If resource info is not yet read-in, read in.
        if self._nruns is None:
            self.get_resource()



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
        test_obj = freetaggercv(sys.argv[1])
    else:
        test_obj = freetaggercv()
     
    jobslaunched = False
    jobslaunched = test_obj.process_newruns()
    #if not jobslaunched:
    #    test_obj.validate()
    #    #test_obj.error_handle()
        
