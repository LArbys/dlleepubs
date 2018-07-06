#!/usr/bin/python

import sys,os,gc
import tempfile

BASE_PATH = os.path.realpath(__file__)
BASE_PATH = os.path.dirname(BASE_PATH)
sys.path.insert(0,BASE_PATH)
from downstream_utils import exec_system, cmd

IMAGE = "/cluster/kappa/90-days-archive/wongjiradlab/vgenty/vertex/vertex_04092018_p00/image/singularity-dllee-unified-04092018_revert.img"
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

    #SS  = "srun -p interactive singularity exec %s bash -c "
    SS  = "singularity exec %s bash -c " 
    SS += "\"source /usr/local/bin/thisroot.sh; hadd -k -f root/%s.root %s\""
    #SS = "hadd -k -f root/%s.root %s"
    
    DATADIR = os.path.join(DBDIR,PROJECT,"stage2",TAG)
    print "Searching... %s" % DATADIR
    if os.path.isdir(DATADIR) == False: 
        print "Data directory for Project=%s with Tag=%s does not exist" % (PROJECT,TAG)
    
    RR = ["find",DATADIR,"-name",TARGET + "*.root"]
    print " ".join(RR)
    res_v = exec_system(RR)
    print "Returned %d files" % len(res_v)
    fd, path = tempfile.mkstemp()
    tmp = os.fdopen(fd, 'w')
    for res in res_v:
        tmp.write(res)
        tmp.write("\n")
    tmp.close()
    print fd,path
    SS = SS % (IMAGE,PROJECT + "_" + TAG + "_" + TARGET,"@%s" % path)
    #SS = SS % (PROJECT + "_" + TAG + "_" + TARGET,"@%s" % path)
    cmd(SS,True)
    #os.remove(path)
    return

if __name__ == '__main__':
    main(sys.argv)
    sys.exit(0)

