#!/usr/bin/python

import sys,os,gc
import tempfile

BASE_PATH = os.path.realpath(__file__)
BASE_PATH = os.path.dirname(BASE_PATH)
sys.path.insert(0,BASE_PATH)
from downstream_utils import exec_system

DBDIR = "/cluster/kappa/90-days-archive/wongjiradlab/larbys/data/db"

def main(argv):

    if len(argv) != 4:
        print 
        print "......................"
        print "PROJECT = str(sys.argv[1])"
        print "TAG     = str(sys.argv[2])"
        print "TARGET  = str(sys.argv[3])"
        print "......................"
        print 
        sys.exit(1)

    
    PROJECT = str(sys.argv[1])
    TAG     = str(sys.argv[2])
    TARGET  = str(sys.argv[3])

    DATADIR = os.path.join(DBDIR,PROJECT,"stage2",TAG)
    print "Searching... %s" % DATADIR
    if os.path.isdir(DATADIR) == False: 
        print "Data directory for Project=%s with Tag=%s does not exist" % (PROJECT,TAG)
    
    RR = ["find",DATADIR,"-name",TARGET + "*.pkl"]
    print " ".join(RR)
    res_v = exec_system(RR)
    print "Returned %d files" % len(res_v)

    FNAME   = PROJECT + "_" + TAG + "_" + TARGET + ".dat"
    OFOLDER = PROJECT + "_" + TAG

    path = open(FNAME,'w+')

    for res in res_v:
        SS  = "scp vgenty01@xfer.cluster.tufts.edu:"
        SS += res
        SS += " "
        SS += OFOLDER
        path.write(SS)
        path.write("\n")

    path.close()
    return

if __name__ == '__main__':
    main(sys.argv)
    sys.exit(0)

