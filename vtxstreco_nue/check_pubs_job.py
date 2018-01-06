import os,sys
import ROOT as rt

def check_job( vtxout, vtxana, supera ):
    """ we check if all events processed """

                
    rfile_supera = rt.TFile( supera )
    tree = rfile_supera.Get("image2d_wire_tree")
    nentries_supera = tree.GetEntries()
    rfile_supera.Close()

    rfile_vtx = rt.TFile( vtxout )
    tree = rfile_vtx.Get("pixel2d_test_img_tree")
    nentries_vtx = tree.GetEntries()
    rfile_vtx.Close()

    rfile_ana = rt.TFile( vtxana )
    tree = rfile_ana.Get("EventVertexTree")
    nentries_ana = tree.GetEntries()
    rfile_ana.Close()

    print "Supera=%d Vtx-out=%d Vtx-ana=%d"%(nentries_supera, nentries_vtx, nentries_ana)
    #if nentries_supera!=nentries_vtx or nentries_supera!=nentries_ana:
    if nentries_supera!=nentries_vtx:
        return False
    return True


if __name__=="__main__":

    vtxout   = sys.argv[1]
    vtxana   = sys.argv[2]
    superain = sys.argv[3]
    
    
    result = check_job( vtxout, vtxana, superain )

    if result:
        print "True"
    else:
        print "False"

