#!/bin/env python
import os,sys,json
from dstream.ds_api import death_star
from pub_dbi        import pubdb_conn_info
from pub_util       import pub_logger
from datetime import tzinfo, timedelta, datetime

PUB_DB_NAME=os.environ["PUB_PSQL_WRITER_DB"]

def insert_metadata( runtable, dbconn, logger, ds, metadata, folders ):

    ikeys = metadata.keys()
    ikeys.sort()

    for k in ikeys:
        entrydata = metadata[k]
        
        run = int(k.split(".")[0])
        subrun = int(k.split(".")[1])

        complete = True
        if "larcv-file" in entrydata:
            larcvsam  = entrydata["larcv-file"]
            larcv     = folders["larcv"]+"/"+larcvsam        
        else:
            larcvsam = ""
            larcv = ""
            complete = False
        if "opreco-file" in entrydata:
            oprecosam  = entrydata["opreco-file"]
            opreco     = folders["opreco"]+"/"+oprecosam        
        else:
            oprecosam = ""
            opreco = ""
            complete = False
        if "reco2d-file" in entrydata:
            reco2dsam  = entrydata["reco2d-file"]
            reco2d     = folders["reco2d"]+"/"+reco2dsam        
        else:
            reco2dsam = ""
            reco2d = ""
            complete = False


        ismc = False
        if "mcinfo-file" in entrydata and entrydata["mcinfo-file"] is not None:
            mcinfosam = entrydata["mcinfo-file"]
            mcinfo    = folders["mcinfo"]+"/"+mcinfosam
            ismc = True
        else:
            mcinfosam = ""
            mcinfo = ""
            ismc = False

        if "larcvtruth-file" in entrydata and entrydata["larcvtruth-file"] is not None:
            larcvtruthsam = entrydata["larcvtruth-file"]
            larcvtruth    = folders["larcvtruth"]+"/"+larcvtruthsam
        else:
            larcvtruthsam = ""
            larcvtruth    = ""

        event_count = -1
        if "event_count" in entrydata:
            event_count = int( entrydata["event_count"] )

        runlist = ""
        nfiles = -1
        if "listruns" in entrydata:
            rl = entrydata["listruns"]
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

        print "inserting ",k
        os.system("psql -U tufts-pubs -h nudot.lns.mit.edu %s -c \"INSERT INTO %s_paths %s VALUES %s;\""
                  % (PUB_DB_NAME,runtable,tabledef,valuestr) )


if __name__ == "__main__":
    
    print "PUB interfaces start"

    runtable     = sys.argv[1]
    metadatafile = sys.argv[2]
    # we list the folders where the files are parked on tufts (or where symlinks are)
    folders = {"larcv":"/cluster/tufts/wongjiradlab/wselig01/larcv_full",
               "opreco":"/cluster/tufts/wongjiradlab/wselig01/larlite_full",
               "reco2d":"/cluster/tufts/wongjiradlab/wselig01/larlite_full"}

    # set environment variables for PUBS database
    os.system("$PUB_TOP_DIR/sbin/remove_runtable %s"%(runtable))
    
    # drop the existing runtable
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
        os.system("$PUB_TOP_DIR/sbin/create_runtable %s"%(runtable))
        tabledef =  "( run integer, subrun integer, numevents integer, numfiles integer, runlist text, ismc boolean, complete boolean,"
        tabledef += " supera text, opreco text, reco2d text, mcinfo text, larcvtruth text," # current db paths
        tabledef += " superasam text, oprecosam text, reco2dsam text, mcinfosam text, larcvtruthsam text)" # samweb unique names
        os.system("psql -U tufts-pubs -h nudot.lns.mit.edu %s -c 'CREATE TABLE %s_paths %s;'"%(PUB_DB_NAME,runtable,tabledef))

    logger = pub_logger.get_logger('death_star')
    dbconn = pubdb_conn_info.admin_info()
    ds =death_star( dbconn, logger )
    if not ds.connect():
        sys.exit(1)

    # load the metadata json file
    metadata = json.load( open(metadatafile,'r') )

    # put the information into the database table
    insert_metadata( runtable, dbconn, logger, ds, metadata, folders )


