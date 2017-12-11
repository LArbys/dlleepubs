#!/bin/env python
import os,sys
from dstream.ds_api import death_star
from pub_dbi        import pubdb_conn_info
from pub_util       import pub_logger
from datetime import tzinfo, timedelta, datetime

def insert( runtable, dbconn, logger, ds, entryline ):

    entryline = entryline.strip()
    data = entryline.split('\t')
    run    = int(data[0])
    subrun = int(data[1])
    larcv  = data[3].split(":")[-1]
    opreco = data[4].split(":")[-1]
    reco2d = data[5].split(":")[-1]
    ismc = False
    if "mcinfo" in entryline:
        mcinfo = data[5].split(":")[-1]
        ismc = True
    else:
        mcinfo = "NULL"
    ts     = (datetime.now()+timedelta(seconds= 0)).strftime('%Y-%m-%d %H:%M:%S')
    te     = (datetime.now()+timedelta(seconds=60)).strftime('%Y-%m-%d %H:%M:%S')
    
    # insert into runtable
    ds.insert_into_death_star( runtable, run, subrun, ts, te)
    
    # insert into filepath table
    os.system("psql -U tufts-pubs -h nudot.lns.mit.edu procdb -c \"INSERT INTO %s_paths (run, subrun, ismc, supera, opreco, reco2d, mcinfo) VALUES (%d,%d,%s,'%s','%s','%s','%s');\""
              % (runtable,run,subrun,str(ismc).lower(),larcv,opreco,reco2d,mcinfo ) )


print "PUB interfaces start"

runtable = sys.argv[1]
flist    = sys.argv[2]

os.system("~/pubs/sbin/remove_runtable %s"%(runtable))
os.system("psql -U tufts-pubs -h nudot.lns.mit.edu procdb -c 'DROP TABLE %s_paths;'"%(runtable))

dumptablescmd = "psql -U tufts-pubs -h nudot.lns.mit.edu procdb -c '\dt'"
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
    os.system("~/pubs/sbin/create_runtable %s"%(runtable))
    os.system("psql -U tufts-pubs -h nudot.lns.mit.edu procdb -c 'CREATE TABLE %s_paths ( run integer, subrun integer, ismc boolean, supera text, opreco text, reco2d text, mcinfo text );'"%(runtable))

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

