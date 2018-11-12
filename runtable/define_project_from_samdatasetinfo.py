#!/bin/env python
import os,sys,json
from dstream.ds_api import death_star
from pub_dbi        import pubdb_conn_info
from pub_util       import pub_logger
from datetime import tzinfo, timedelta, datetime

PUB_DB_NAME=os.environ["PUB_PSQL_WRITER_DB"]

def insert_metadata( runtable, ds, metadata, folder_dict ):

    ikeys = metadata.keys()
    ikeys.sort()

    for k in ikeys:
        print "key: ",k
        entrydata = metadata[k]
        
        run = int(k[0])
        subrun = int(k[1])

        complete = True
        if "larcv-file" in entrydata:
            larcvsam  = os.path.basename(entrydata["larcv-file"])
            larcv     = folder_dict["larcv"]+"/"+larcvsam
        else:
            larcvsam = ""
            larcv = ""
            complete = False
        if "opreco-file" in entrydata:
            oprecosam  = os.path.basename(entrydata["opreco-file"])
            opreco     = folder_dict["opreco"]+"/"+oprecosam
        else:
            oprecosam = ""
            opreco = ""
            complete = False
        if "reco2d-file" in entrydata:
            reco2dsam  = os.path.basename(entrydata["reco2d-file"])
            reco2d     = folder_dict["reco2d"]+"/"+reco2dsam
        else:
            reco2dsam = ""
            reco2d = ""
            complete = False


        ismc = False
        if "mcinfo-file" in entrydata and entrydata["mcinfo-file"] is not None:
            mcinfosam = os.path.basename(entrydata["mcinfo-file"])
            mcinfo    = folder_dict["mcinfo"]+"/"+mcinfosam
            ismc = True
        else:
            mcinfosam = ""
            mcinfo = ""
            ismc = False

        if "larcvtruth-file" in entrydata and entrydata["larcvtruth-file"] is not None:
            larcvtruthsam = os.path.basename(entrydata["larcvtruth-file"])
            larcvtruth    = folder_dict["larcvtruth"]+"/"+larcvtruthsam
        else:
            larcvtruthsam = ""
            larcvtruth    = ""

        event_count = 0
        if "event_count" in entrydata:
            event_count = int( entrydata["event_count"] )

        runlist = ""
        nfiles = -1
        if "runs" in entrydata:
            rl = entrydata["runs"] # should be a list
            # make a string describing runs
            for r in rl:
                runlist += "%d.%d"%(r[0],r[1])
                if r !=rl[-1]:
                    runlist +=";"
            nfiles = len(rl)


        ts     = (datetime.now()+timedelta(seconds= 0)).strftime('%Y-%m-%d %H:%M:%S')
        te     = (datetime.now()+timedelta(seconds=60)).strftime('%Y-%m-%d %H:%M:%S')
    
        # insert into runtable
        ds.insert_into_death_star( runtable, run, subrun, ts, te)
    
        # insert into filepath table
        tabledef = "( run, subrun, numevents, numfiles, runlist, ismc, complete,"
        tabledef += " supera, opreco, reco2d, mcinfo, larcvtruth," # current db paths
        tabledef += " superasam, oprecosam, reco2dsam, mcinfosam, larcvtruthsam)" # samweb unique names
        values = (run,subrun,event_count,nfiles,runlist,str(ismc).lower(),str(complete).lower(),larcv,opreco,reco2d,mcinfo,larcvtruth,larcvsam,oprecosam,reco2dsam,mcinfosam,larcvtruthsam)
        valuestr = "(%d,%d,%d,%d,'%s',%s,%s,'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')"%values

        #print "inserting ",k,":",tabledef
        #print "  values: ",valuestr
        os.system("psql -U tufts-pubs -h nudot.lns.mit.edu %s -c \"INSERT INTO %s_paths %s VALUES %s;\""
                  % (PUB_DB_NAME,runtable,tabledef,valuestr) )

def parse_dataset_dict( metadatalist, larcvtypes=["larcv","opreco","reco2d"], ismc=False ):
    import pickle
    metadata = [ pickle.load( open(f, 'rb') ) for f in metadatalist ]
    index = metadata[0].keys()
    index.sort()

    if ismc:
        larcvtypes.append("mcinfo")

    mergedmeta = {}
    for idx in index:
        #print "idx: ",idx
        inall = True
        for n,x in enumerate(metadata):
            if idx not in x:
                inall = False

        if not inall:
            print "skipping: ",idx
            continue

        entrydata = [ x[idx] for x in metadata ]

        mergedentry = {}
        for ftype,mergeddata in zip(larcvtypes,entrydata):
            mergedentry["%s-file"%(ftype)] = mergeddata['path']

        count_agrees = True
        for imeta in xrange(1,3):
            if entrydata[0]['event_count']!=entrydata[imeta]['event_count']:
                raise RuntimeError("disagreement in number of events for {}".format(idx))
        mergedentry["event_count"] = entrydata[0]['event_count']
        mergedentry["runs"] = entrydata[0]['runs']
        
        #print mergedentry
        mergedmeta[ idx ] = mergedentry
    

    return mergedmeta

if __name__ == "__main__":
    
    print "PUB interfaces start"

    #runtable     = sys.argv[1]
    #metadatalist = sys.argv[2:]

    # for testing
    #runtable = "mcc8_extbnb_compare"
    #metadatalist = ["../../../data/mcc9/tag0/pathlist_mcc8compare_larcv.txt.pkl",
    #                "../../../data/mcc9/tag0/pathlist_mcc8compare_opreco.txt.pkl",
    #                "../../../data/mcc9/tag0/pathlist_mcc8compare_reco2d.txt.pkl"]

    runtable = "mcc9tag1_bnb5e19"
    metadatalist = ["../../../data/mcc9/bnb5e19_tag1/pathlist_data_bnb_run1_unblind_mcc9_beta1_oct_reco_2d_larcv_wholeview.pkl",
                    "../../../data/mcc9/bnb5e19_tag1/pathlist_data_bnb_run1_unblind_mcc9_beta1_oct_reco_2d_larlite_opreco.pkl",
                    "../../../data/mcc9/bnb5e19_tag1/pathlist_data_bnb_run1_unblind_mcc9_beta1_oct_reco_2d_larlite_reco2d.pkl"]

    print "BUILD TABLE FOR ",runtable," USING SAM META-DATA"
    metadata = parse_dataset_dict( metadatalist )

    # we list the folders where the files are parked on tufts (or where symlinks are)
    folders = {"larcv":"/cluster/tufts/wongjiradlab/larbys/data/mcc9/bnb5e19_tag1/data/larcv",
               "opreco":"/cluster/tufts/wongjiradlab/larbys/data/mcc9/bnb5e19_tag1/data/larlite",
               "reco2d":"/cluster/tufts/wongjiradlab/larbys/data/mcc9/bnb5e19_tag1/data/larlite"}

    ## set environment variables for PUBS database
    os.system("$PUB_TOP_DIR/sbin/remove_runtable %s"%(runtable))
    
    ## drop the existing runtable
    os.system("psql -U tufts-pubs -h nudot.lns.mit.edu %s -c 'DROP TABLE %s_paths;'"%(PUB_DB_NAME,runtable))

    dumptablescmd = "psql -U tufts-pubs -h nudot.lns.mit.edu %s -c '\dt'"%(PUB_DB_NAME)
    pdump = os.popen(dumptablescmd)
    ldump = pdump.readlines()

    hastable = False
    for l in ldump:
        l = l.strip()
        if "table" not in l:
            continue
        if runtable in l:
            hastable = True

    if hastable:
        print runtable," found"
    else:
        print runtable," not found"

    # for debug to destroy table
    #hastable = False

    if not hastable:
        # define table
        os.system("$PUB_TOP_DIR/sbin/create_runtable %s"%(runtable))
        tabledef =  "( run integer, subrun integer, numevents integer, numfiles integer, runlist text, ismc boolean, complete boolean,"
        tabledef += " supera text, opreco text, reco2d text, mcinfo text, larcvtruth text," # current db paths
        tabledef += " superasam text, oprecosam text, reco2dsam text, mcinfosam text, larcvtruthsam text)" # samweb unique names
        os.system("psql -U tufts-pubs -h nudot.lns.mit.edu %s -c 'CREATE TABLE %s_paths %s;'"%(PUB_DB_NAME,runtable,tabledef))

    logger = pub_logger.get_logger('death_star')
    dbconn = pubdb_conn_info.admin_info()
    ds =death_star( dbconn, logger )
    if not ds.connect():
        print "Could not connect"
        sys.exit(1)

    # # put the information into the database table
    insert_metadata( runtable, ds, metadata, folders )

