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


    def restart_and_clean_entries(self,entrylist,projectstemname):

        # Attempt to connect DB. If failure, abort
        if not self.connect():
	    self.error('Cannot connect to DB! Aborting...')
	    return

        # get entries from list
        entrydict = {}

        fentry = open(entrylist,'r')
        lentry = fentry.readlines()
        for l in lentry:
            l = l.strip()
            info = l.split()
            run = int(info[0])
            subrun = int(info[1])
            entrydict[(run,subrun)] = {"ssnetfile":info[2]}
        fentry.close()

        runlist = entrydict.keys()
        runlist.sort()
        for run,subrun in runlist:
            ssnetcommand = "update ssnet_%s set status=1 where run=%d and subrun=%d"%(projectstemname,run,subrun)
            taggercommand = "update tagger_%s set status=1 where run=%d and subrun=%d"%(projectstemname,run,subrun)
            freetaggercommand = "update freetaggercv_%s set status=1 where run=%d and subrun=%d"%(projectstemname,run,subrun)
            rmcommand = "rm -f %s"%(entrydict[(run,subrun)]["ssnetfile"])
            taggerrm = "rm -f %s/tagger*"%( os.path.dirname(entrydict[(run,subrun)]["ssnetfile"]) )
            print rmcommand
            print taggerrm 
            os.system(rmcommand)
            os.system(taggerrm)
            self._api.commit(taggercommand)
            self._api.commit(ssnetcommand)
            self._api.commit(freetaggercommand)
        return


# A unit test section
if __name__ == '__main__':

    import sys

    test_obj = dlleepubsutils("X")
    test_obj.restart_and_clean_entries( "bnbcosmic_detsys_cv_badvertex.txt", "bnbcosmic_detsys_cv" )

