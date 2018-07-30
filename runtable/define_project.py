#!/bin/env python
import os,sys
from dstream.ds_api import death_star
from pub_dbi        import pubdb_conn_info
from pub_util       import pub_logger
from datetime import tzinfo, timedelta, datetime

PUB_DB_NAME=os.environ["PUB_PSQL_WRITER_DB"]

def insert( runtable, dbconn, logger, ds, entryline ):

    entryline = entryline.strip()
    data = entryline.split('\t')
    run    = int(data[0])
    subrun = int(data[1])
    larcv  = data[3].split(":")[-1]
    opreco = data[4].split(":")[-1]
    reco2d = data[5].split(":")[-1]
    larcvsam = os.path.basename(larcv)
    oprecosam = os.path.basename(opreco)
    reco2dsam = os.path.basename(reco2d)

    ismc = False
    if "mcinfo" in entryline:
        mcinfo = data[6].split(":")[-1]
        mcinfosam = os.path.basename(mcinfo)
        ismc = True
    else:
        mcinfo = ""
        mcinfosam = ""

    if "larcvtruth" in entryline:
        larcvtruth = data[6].split(":")[-1]
        larcvtruthsam = os.path.basename(larcvtruthsam)
    else:
        larcvtruth = ""
        larcvtruthsam = ""
    
    if "backtracker" in entryline:
        mcinfo = data[5].split(":")[-1]
        mcinfosam = os.path.basename(mcinfo)
        ismc = True
    else:
        mcinfo = ""
        mcinfosam = ""


    ts     = (datetime.now()+timedelta(seconds= 0)).strftime('%Y-%m-%d %H:%M:%S')
    te     = (datetime.now()+timedelta(seconds=60)).strftime('%Y-%m-%d %H:%M:%S')
    
    # insert into runtable
    ds.insert_into_death_star( runtable, run, subrun, ts, te)
    
    # insert into filepath table
    tabledef = "( run, subrun, ismc, supera, opreco, reco2d, mcinfo, larcvtruth," # current db paths
    tabledef += " superasam, oprecosam, reco2dsam, mcinfosam, larcvtruthsam)" # samweb unique names
    values = (run,subrun,str(ismc).lower(),larcv,opreco,reco2d,mcinfo,larcvtruth,larcvsam,oprecosam,reco2dsam,mcinfosam,larcvtruthsam)
    valuestr = "(%d,%d,%s,'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')"%values

    os.system("psql -U tufts-pubs -h nudot.lns.mit.edu %s -c \"INSERT INTO %s_paths %s VALUES %s;\""
              % (PUB_DB_NAME,runtable,tabledef,valuestr) )


print "PUB interfaces start"

runtable = sys.argv[1]
flist    = sys.argv[2]

os.system("$PUB_TOP_DIR/sbin/remove_runtable %s"%(runtable))
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

hastable = False

if not hastable:
    os.system("$PUB_TOP_DIR/sbin/create_runtable %s"%(runtable))
    tabledef = "( run integer, subrun integer, ismc boolean, supera text, opreco text, reco2d text, mcinfo text, larcvtruth text," # current db paths
    tabledef += " superasam text, oprecosam text, reco2dsam text, mcinfosam text, larcvtruthsam text)" # samweb unique names
    os.system("psql -U tufts-pubs -h nudot.lns.mit.edu %s -c 'CREATE TABLE %s_paths %s;'"%(PUB_DB_NAME,runtable,tabledef))

logger = pub_logger.get_logger('death_star')
dbconn = pubdb_conn_info.admin_info()
ds =death_star( dbconn, logger )
if not ds.connect():
    sys.exit(1)


# fill the table
f = open(flist,'r')
for l in f.readlines():
    l = l.strip()
    data = l.split('\t')
    if len(data)<=1:
        continue
    insert( runtable, dbconn, logger, ds, l )

f.close()

