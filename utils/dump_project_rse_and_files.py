#!/bin/env python
## @namespace dlleepubs.dlleepubsutils
#  @ingroup dummy_dstream
#  @brief Defines a project dlleepubsutils
#  @author twongjirad

# python include
import time, os, shutil, commands, argparse
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

    parser = argparse.ArgumentParser( description="dump project rse and files.\n  returns \"RUN SUBRUN EVENT FILE1 FILE2 ...\" provided some criteria" )
    parser.add_argument( "runtable", type=str, 
                         help="runtable from which the projects derive, e.g. 'mcc8v6_extbnb'. see http://nudot.lns.mit.edu/taritree/dlleepubsummary.html for list." )
    parser.add_argument( "project",  type=str, help="project name for which we check status to make our selection, e.g. 'tagger','ssnet','vertex'" )
    parser.add_argument( "status",   type=int, help="status of project. typical values: {0:unprocessed, 4:OK, 10:error}. (exception 'xferinput' where OK=3)" )
    parser.add_argument( "-f", "--files",    default="__all__", nargs='+', type=str, help="file names to dump out paths for. e.g. supera, opreco, reco2d, mcinfo" )

    args = parser.parse_args( sys.argv[1:] )

    # run table: the stem name for a whole chain of projects. 
    #            ex. mcc8v6_bnb5e19, a project would be ssnet_mcc8v6_bnb5e19
    # status: status of files for a given stage to check
    # endpath: stage to check status of files
    # filetypes: list of file types to return, e.g. supera, opreco, reco2d (stage1 only at the moment)

    test_obj = dlleepubsutils("X")
    rundict = test_obj.fetch_completed_entries( args.runtable, endpath=args.project, endstatus=args.status )

    rslist = rundict.keys()
    rslist.sort()

    for rs in rslist:
        print "%d %d"%(rs[0],rs[1]),
        if args.files=="__all__":
            for filetype,path in rundict[rs].items():
                print rundict[rs][filetype],
        else:
            for filetype in args.files:
                print rundict[rs][filetype],
        print
    



