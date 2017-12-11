import os,sys
import ROOT as rt

def check_job( taggerlarcvout, taggerlarliteout, supera ):
    
    rfile_larcv = rt.TFile( taggerlarcvout )
    tree = rfile_larcv.Get("image2d_modimg_tree")
    nentries_larcv = tree.GetEntries()
    rfile_larcv.Close()
                
    rfile_larlite = rt.TFile( taggerlarliteout )
    tree = rfile_larlite.Get("larlite_id_tree")
    nentries_larlite = tree.GetEntries()
    rfile_larlite.Close()

    rfile_supera = rt.TFile( supera )
    tree = rfile_supera.Get("image2d_wire_tree")
    nentries_supera = tree.GetEntries()
    rfile_supera.Close()

    if nentries_larcv!=nentries_larlite or nentries_larcv==0 or nentries_larlite==0 or nentries_larcv!=nentries_supera:
        return False
    return True


if __name__=="__main__":

    taggerlarcvout = sys.argv[1]
    taggerlarliteout = sys.argv[2]
    superain = sys.argv[3]
    
    result = check_job( taggerlarcvout, taggerlarliteout, superain )

    if result:
        print "True"
    else:
        print "False"

