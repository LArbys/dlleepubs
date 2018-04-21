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

    def query_queue(self):
        """ data about slurm queue pertaining to ssnet jobs"""
        # PGPU01 jobs
        pgpu1 = commands.getoutput("squeue | grep twongj01 | grep ssnet | grep pgpu01")
        lgpu1 = pgpu1.split('\n')

        # PGPU02 jobs
        pgpu2 = commands.getoutput("squeue | grep twongj01 | grep ssnet | grep pgpu02")
        lgpu2 = pgpu2.split('\n')

        # alpha025 jobs
        palpha = commands.getoutput("squeue | grep twongj01 | grep ssnet | grep alpha025")
        lalpha = palpha.split('\n')

        # omega025 jobs
        pomega = commands.getoutput("squeue | grep twongj01 | grep ssnet | grep omega025")
        lomega = pomega.split('\n')

        lv = lgpu1+lgpu2+lalpha+lomega

        info = {"NPGPU01":len(lgpu1),"NPGPU02":len(lgpu2),"NALPHA025":len(lalpha),"NOMEGA025":len(lomega),"jobids":[]}
        for l in lv:
            if l.strip()!="":
                jobid = int(l.split()[0])
                info["jobids"].append(jobid)
        
        return info

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
        #query =  "select t1.run,t1.subrun,supera,opreco,reco2d,mcinfo"
        query =  "select t1.run,t1.subrun,supera,opreco,reco2d,mcinfo,superasam,oprecosam,reco2dsam,mcinfosam"
        query += " from %s t1 join %s t2 on (t1.run=t2.run and t1.subrun=t2.subrun)" % (projects[-1], self._filetable)
        query += " where t1.status=%d order by run, subrun asc" % (good_status[-1]) 

        self._api._cursor.execute(query)
        results = self._api._cursor.fetchall()

        rundict = {}
        for x in results:
            run = int(x[0])
            subrun = int(x[1])
            filedict = {"supera":x[2],"opreco":x[3],"reco2d":x[4],"mcinfo":x[5],"superasam":x[6],"oprecosam":x[7],"reco3dsam":x[8],"mcinfosam":x[9]}
            datafolder = os.path.dirname(x[2])
            filedict["tagger-larlite"] = datafolder+"/taggerout-larlite-Run%06d-SubRun%06d.root"%(run,subrun)
            filedict["tagger-larcv"] = datafolder+"/taggerout-larcv-Run%06d-SubRun%06d.root"%(run,subrun)
            filedict["ssnet-larcv"] = datafolder+"/ssnetout-larcv-Run%06d-SubRun%06d.root"%(run,subrun)
            rundict[(run,subrun)] = filedict
        return rundict

    ## @brief get completed runs and make symlinks
    def make_symlinks(self,topdir,runtable,endpath="ssnet"):

        completed = self.fetch_completed_entries(runtable,endpath)
        folders = ["supera","larlite","tagger","ssnet"]
        folderpaths = {}
        for f in folders:
            folderpaths[f] = "%s/%s"%(topdir,f)
            os.system("mkdir -p %s"%(folderpaths[f]))

        runlist = completed.keys()
        runlist.sort()
        
        for runidx in runlist:
            run = runidx[0]
            subrun = runidx[1]
            jobid = run*10000 + subrun
            
            flist = completed[runidx]
            print "Symlinks for (%d,%d)"%(run,subrun)
            for ftype in ["supera","opreco","reco2d","mcinfo","tagger-larcv","tagger-larlite","ssnet-larcv"]:
                dirtype = ftype.split("-")[0]
                if dirtype in ["opreco","reco2d","mcinfo"]:
                    dirtype = "larlite"
                forig = flist[ftype]
                fname = ftype
                if fname=="ssnet-larcv":
                    fname = "ssnetout_larcv"
                flink = folderpaths[dirtype] + "/"+fname+"_%d.root"%(jobid)
                if not os.path.exists(flink):
                    cmd = "ln -s %s %s"%(forig,flink)
                    os.system(cmd)
        return

    def make_samweb_list(self,runtable,fileout,inputfiletype,endpath="likelihood",endstatus=4):
        completed = self.fetch_completed_entries(runtable,endpath,endstatus)
        self.info( "[Make Samweb list] Number of entries completed to %s (w/ status=%d): %d"%(endpath,endstatus,len(completed)) )

        f = open(fileout,'w')
        indices = completed.keys()
        indices.sort()
        for index in indices:
            print >> f,completed[index][inputfiletype]
        f.close()

        self.info("[Make Samweb list] wrote list of source samweb files (%s) to %s"%(inputfiletype,fileout))
        
        return 


# A unit test section
if __name__ == '__main__':

    import sys
    test_obj = None
    if len(sys.argv)>1:
        test_obj = dlleepubsutils(sys.argv[1])
    else:
        print "Need project stem (the name of the base run table)"

    #completed = test_obj.fetch_completed_entries( sys.argv[1] )
    #print "Number of completed entries: ",len(completed)

    #test_obj.make_symlinks( "/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/symlinks/mcc8v4_cocktail_p00", "mcc8v4_cocktail_p00" )
    #test_obj.make_symlinks( "/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/symlinks/mcc8v4_cocktail_p00", "mcc8v4_cocktail_p00" )
    #test_obj.make_symlinks( "/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/symlinks/mcc8v4_cocktail_p01", "mcc8v4_cocktail_p01" )
    #test_obj.make_symlinks( "/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/symlinks/mcc8v4_cocktail_p02", "mcc8v4_cocktail_p02" )
    #test_obj.make_symlinks( "/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/symlinks/mcc8v4_cocktail_p03", "mcc8v4_cocktail_p03" )
    #test_obj.make_symlinks( "/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/symlinks/mcc8v4_cocktail_p04", "mcc8v4_cocktail_p04" )
    #test_obj.make_symlinks( "/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/symlinks/mcc8v3_corsika_p00", "corsika_mcc8v3_p00" )
    #test_obj.make_symlinks( "/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/symlinks/mcc8v3_corsika_p01", "corsika_mcc8v3_p01" )
    #test_obj.make_symlinks( "/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/symlinks/mcc8v3_corsika_p02", "corsika_mcc8v3_p02" )

    test_obj.make_samweb_list( "mcc8v6_bnb5e19", "mcc8v6_bnb5e19_samweb_larcv2.txt", "superasam", "vertex", 4 )

    


