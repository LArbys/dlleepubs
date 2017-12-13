import os,sys
import ROOT as rt

def check_job( ssnetout, supera ):
    
    rfile_ssnet = rt.TFile( ssnetout )
    tree = rfile_ssnet.Get("image2d_uburn_plane2_tree")
    nentries_ssnet = tree.GetEntries()
    rfile_ssnet.Close()
                
    rfile_supera = rt.TFile( supera )
    tree = rfile_supera.Get("image2d_wire_tree")
    nentries_supera = tree.GetEntries()
    rfile_supera.Close()

    if nentries_supera!=nentries_ssnet or nentries_ssnet==0:
        return False
    return True


if __name__=="__main__":

    ssnetout = sys.argv[1]
    superain = sys.argv[2]
    
    result = check_job( ssnetout, superain )

    if result:
        print "True"
    else:
        print "False"

