## @namespace dlleepubs.tagger
#  @ingroup dummy_dstream
#  @brief Defines a project dummy_nubin_xfer
#  @author kazuhiro

# python include
import time, os, shutil
# pub_dbi package include
from pub_dbi import DBException
# dstream class include
from dstream import DSException
from dstream import ds_project_base
from dstream import ds_status
import psycopg2 as psql

## @class xfer_input
#  @brief Transfers file from initial location to fixed location for DB
#  @details
#  Moves the file to [datafolder]/runtablename/db/[runnumber%100]/[runnumber/100]/[subrun%100]/[subrun/100]/
#  It simply copies dummy nu bin files with a different file name under $PUB_TOP_DIR/data.
class xfer_input(ds_project_base):

    # Define project name as class attribute
    _project = 'dummy_nubin_xfer'

    ## @brief default ctor can take # runs to process for this instance
    def __init__(self,project_name):

        if project_name:
            self._project = project_name

        # Call base class ctor
        super(xfer_input,self).__init__()

        self._nruns = None
        self._out_dir = ''
        self._outfile_format = ''
        self._in_dir = ''
        self._infile_format = ''
        self._parent_project = ''

    ## @brief method to retrieve the project resource information if not yet done
    def get_resource(self):

        # Get process configuration
        resource = self._api.get_resource(self._project)
        
        self._nruns = int(resource['NRUNS'])
        self._out_dir        = resource['OUTDIR']
        self._outfile_format = resource['OUTFILE_FORMAT']
        self._filetable      = resource['FILETABLE']

    ## @brief access DB and retrieves new runs and process
    def process_newruns(self):

        # Attempt to connect DB. If failure, abort
        if not self.connect():
	    self.error('Cannot connect to DB! Aborting...')
	    return

        # If resource info is not yet read-in, read in.
        if self._nruns is None:
            self.get_resource()

        # Fetch runs from DB and process for # runs specified for this instance.
        ctr = self._nruns
        print "Cursor: ",self._api._cursor

        # Get Runs with status=1 (0=disable,2=done)
        runs = self.get_runs(self._project,1)
        
        query = "select %s.run,%s.subrun,supera,opreco,reco2d,mcinfo from %s join %s on (%s.run=%s.run and %s.subrun=%s.subrun) where status=1" 
        query = query % (self._project,self._project,self._project,self._filetable,self._project,self._filetable,self._project,self._filetable)

        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        for x in results:
            print x


        return
        
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
            #status = ds_status( project = self._project,
            #                    run     = int(x[0]),
            #                    subrun  = int(x[1]),
            #                    seq     = int(x[2]),
            #                    status  = status )
            
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
        test_obj = xfer_input(sys.argv[1])
    else:
        raise ValueError("require project name argument")
        sys.exit(-1)
        
    test_obj.process_newruns()

    #test_obj.error_handle()

    #test_obj.validate()

