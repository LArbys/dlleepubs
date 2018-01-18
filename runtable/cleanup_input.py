import os,sys
import psycopg2


project = "bnb5e19"

f = open("bnb_5e19_filelist_p01.txt",'r')
r = f.readlines()

rsedict = {}

for l in r:
    l = l.strip()
    if l=="":
        continue

    data = l.split()
    run    = int(data[0])
    subrun = int(data[1])
    event  = int(data[2])

    rse = (run,subrun,event)
    fdict = {"supera":data[3].split(":")[-1].strip(),
             "opreco":data[4].split(":")[-1].strip(),
             "reco2d":data[5].split(":")[-1].strip()}
    rsedict[rse] = fdict


# check its in the database
import psycopg2

conn = psycopg2.connect("dbname=procdb user=tufts-pubs host=nudot.lns.mit.edu")
cursor = conn.cursor()

rselist = rsedict.keys()
rselist.sort()

del_list = []

for rse in rselist:

    cursor.execute("select run,subrun,status from xferinput_%s where run=%d and subrun=%d;"%(project,rse[0],rse[1]))
    out = cursor.fetchall()
    if len(out)>1:
        print "(run,subrun) not unique!"
        print out
        break
    dbentry = out[0]
    if dbentry[2]==3:
        #print rse," transerred into db"
        rsedict[rse]["rse"] = rse
        del_list.append( rsedict[rse] )


for rseinfo in del_list:
    print "removing rse=",rseinfo["rse"]

    print "  rm ",rseinfo["supera"]
    if os.path.exists(rseinfo["supera"]):
        os.system("rm %s"%(rseinfo["supera"]))

    print "  rm ",rseinfo["opreco"]
    if os.path.exists(rseinfo["opreco"]):
        os.system("rm %s"%(rseinfo["opreco"]))

    print "  rm ",rseinfo["reco2d"]
    if os.path.exists(rseinfo["reco2d"]):
        os.system("rm %s"%(rseinfo["reco2d"]))


print "Number transferred: ",len(del_list)
