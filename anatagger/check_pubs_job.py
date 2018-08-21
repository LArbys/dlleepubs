import os,sys
import ROOT as rt

def check_job( taggeranaout, supera ):
    
    rfile_larcv = rt.TFile( taggeranaout )
    tree = rfile_larcv.Get("pixanav2")
    nentries_larcv = tree.GetEntries()
    rfile_larcv.Close()
                
    rfile_supera = rt.TFile( supera )
    tree = rfile_supera.Get("image2d_wire_tree")
    nentries_supera = tree.GetEntries()
    rfile_supera.Close()

    if nentries_larcv==0 or nentries_larcv!=nentries_supera:
        return False
    return True


if __name__=="__main__":

    taggeranaout = sys.argv[1]
    superain = sys.argv[2]
    
    result = check_job( taggeranaout, superain )

    if result:
        print "True"
    else:
        print "False"

