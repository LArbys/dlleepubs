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
class dlleePathTableFixer(ds_project_base):

    # Define project name as class attribute
    _project = 'dlleePathTableFixer'

    ## @brief default ctor can take # runs to process for this instance
    def __init__(self,project_name=""):

        if project_name:
            self._project = project_name

        # Call base class ctor
        super(dlleePathTableFixer,self).__init__()


    def fetch_missing_entries(self,runtable):

        # Attempt to connect DB. If failure, abort
        if not self.connect():
	    self.error('Cannot connect to DB! Aborting...')
	    return

        pathtable = runtable+"_paths"
        query =  "select run,subrun,superasam,oprecosam,reco2dsam,mcinfosam"
        query += " from %s " % (pathtable)
        query += " where (superasam IS NULL or superasam=\'\') order by run, subrun asc"
        
        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()
        print "entries with missing superasam: ",len(results)

        return results

    def parse_flist(self,flist):
        f = open(flist,'r')

        rse_data = {}

        for l in f.readlines():
            l = l.strip()
            if l=="":
                continue
            data = l.split()

            run = int(data[0])
            subrun = int(data[1])
            
            rse_data[(run,subrun)] = data[2:]

        print "Entries in file list: ",len(rse_data)
        return rse_data

    def fill_missing_samname(self,runtable,flist):
        missing = self.fetch_missing_entries(runtable)
        data = self.parse_flist(flist)

        if not self.connect():
	    self.error('Cannot connect to DB! Aborting...')
	    return

        for entry in missing:
            run = int(entry[0])
            subrun = int(entry[1])

            if (run,subrun) not in data:
                continue

            print "Can fill (%d,%d)"%(run,subrun)

            filldata = data[(run,subrun)]

            ftypes = ["supera","opreco","reco2d"]
            fnames = {}
            for d in filldata:
                d = d.strip()
                if ":" not in d or d[-1]==":":
                    continue
                dname = d.split(":")[0].strip()
                dpath = os.path.basename(d.split(":")[1].strip())
                if dname in ftypes:
                    fnames[dname] = dpath.strip()

            cmd = "update %s set (superasam,oprecosam,reco2dsam)=(\'%s\',\'%s\',\'%s\') where run=%d and subrun=%d"%(runtable+"_paths",fnames["supera"],fnames["opreco"],fnames["reco2d"],run,subrun)
            print cmd

            self._api._cursor.execute(cmd)
            self._api.commit(cmd)
            

        #self._api.commit()


# A unit test section
if __name__ == '__main__':

    import sys
    test_obj = dlleePathTableFixer()

    #rse_data = test_obj.parse_flist( sys.argv[1] )
    #print "Entries in file list: ",len(rse_data)

    #test_obj.fetch_missing_entries( "mcc8v6_bnb5e19" )

    #test_obj.fill_missing_samname( "mcc8v6_bnb5e19", "bnbrun1open_p01.txt" )
    test_obj.fill_missing_samname( "mcc8v6_extbnb", "extbnb_run1_filelist.txt" )
    

    


