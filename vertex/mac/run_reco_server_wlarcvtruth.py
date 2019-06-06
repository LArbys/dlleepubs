import os, sys

if len(sys.argv) != 9:
    print 
    print "CFG     = str(sys.argv[1])"
    print "ANAFILE = str(sys.argv[2])"
    print "PGRFILE = str(sys.argv[3])"
    print "INFILE1 = str(sys.argv[4])"
    print "INFILE2 = str(sys.argv[5])"
    print "INFILE3 = str(sys.argv[6])"
    print "INFILE4 = str(sys.argv[7])"
    print "OUTDIR  = str(sys.argv[8])" 
    print 
    sys.exit(1)

BASE_PATH = os.path.realpath(__file__)
BASE_PATH = os.path.dirname(BASE_PATH)
sys.path.insert(0,BASE_PATH)

CFG     = str(sys.argv[1])
ANAFILE = str(sys.argv[2])
PGRFILE = str(sys.argv[3])
INFILE1 = str(sys.argv[4])
INFILE2 = str(sys.argv[5])
INFILE3 = str(sys.argv[6])
INFILE4 = str(sys.argv[7])
OUTDIR  = str(sys.argv[8])

from larcv import larcv
import ROOT
from ROOT import std

proc = larcv.ProcessDriver('ProcessDriver')
proc.configure(CFG)
flist=ROOT.std.vector('std::string')()
flist.push_back(ROOT.std.string(INFILE1))
flist.push_back(ROOT.std.string(INFILE2))
flist.push_back(ROOT.std.string(INFILE3))
flist.push_back(ROOT.std.string(INFILE4))
proc.override_input_file(flist)
proc.override_ana_file(os.path.join(OUTDIR,ANAFILE))
proc.override_output_file(os.path.join(OUTDIR,PGRFILE))
proc.initialize()
proc.batch_process()
proc.finalize()

sys.exit(0)
