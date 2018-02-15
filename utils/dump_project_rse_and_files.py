## @namespace dlleepubs.dlleepubsutils
#  @ingroup dummy_dstream
#  @brief Defines a project dlleepubsutils
#  @author twongjirad

# python include
import time, os, shutil, commands
# pub_dbi package include
from pub_dbi import DBException
# dstream class include
from dstream import DSException
from dstream import ds_project_base
from dstream import ds_status

PUBDIR = os.environ["PUB_TOP_DIR"]
PUBDLUTILSDIR = PUBDIR+"/dllee_dstream/utils"

## @class dlleepubsutils
#  @brief A dummy nu bin file xfer project
#  @details
#  This dummy project transfers dummy files created by dummy_daq project\n
#  It simply copies dummy nu bin files with a different file name under $PUB_TOP_DIR/data.
class dlleepubsutils(ds_project_base):

    # Define project name as class attribute
    _project = 'dlleepubsutils'

    ## @brief default ctor can take # runs to process for this instance
    def __init__(self,project_name):

        if project_name:
            self._project = project_name

        # Call base class ctor
        super(dlleepubsutils,self).__init__()


    def fetch_completed_entries(self,runtable,endpath="ssnet",endstatus=4):

        # Attempt to connect DB. If failure, abort
        if not self.connect():
	    self.error('Cannot connect to DB! Aborting...')
	    return

        #project_prefixes = ["xferinput","tagger","ssnet"]
        #good_status      = [3,4,4]
        projects = [endpath+"_"+runtable]
        good_status = [endstatus]
        #for prefix in project_prefixes:
        #    projects.append( prefix+"_"+runtable )
        
        self._filetable = runtable + "_paths"
        #runlist = self.get_xtable_runs(projects,good_status)

        # Get files

        # Fetch runs from DB and process for # runs specified for this instance.
        query =  "select t1.run,t1.subrun,supera,opreco,reco2d,mcinfo"
        #query =  "select t1.run,t1.subrun,supera,opreco,reco2d,mcinfo,superasam,oprecosam,reco2dsam,mcinfosam"
        query += " from %s t1 join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun)" % (projects[-1], self._filetable)
        query += " where t1.status=%d order by run, subrun asc" % (good_status[-1]) 

        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()

        rundict = {}
        for x in results:
            run = int(x[0])
            subrun = int(x[1])
            if len(x)>6:
                filedict = {"supera":x[2],"opreco":x[3],"reco2d":x[4],"mcinfo":x[5],"superasam":x[6],"oprecosam":x[7],"reco3dsam":x[8],"mcinfosam":x[9]}
            else:
                filedict = {"supera":x[2],"opreco":x[3],"reco2d":x[4],"mcinfo":x[5]}
            datafolder = os.path.dirname(x[2])
            filedict["tagger-larlite"] = datafolder+"/taggerout-larlite-Run%06d-SubRun%06d.root"%(run,subrun)
            filedict["tagger-larcv"] = datafolder+"/taggerout-larcv-Run%06d-SubRun%06d.root"%(run,subrun)
            filedict["ssnet-larcv"] = datafolder+"/ssnetout-larcv-Run%06d-SubRun%06d.root"%(run,subrun)
            rundict[(run,subrun)] = filedict
        return rundict


# A unit test section
if __name__ == '__main__':

    import sys

    runtable = sys.argv[1]
    filetype = sys.argv[2]
    outfile  = sys.argv[3]
    status = 4

    
    test_obj = dlleepubsutils("X")
    rundict = test_obj.fetch_completed_entries( runtable, endpath="ssnet", endstatus=status )

    rslist = rundict.keys()
    rslist.sort()

    out = open(outfile,'w')
    
    for rs in rslist:
        print >>out,"%d %d %s"%(rs[0],rs[1], rundict[rs][filetype])
    
    out.close()


