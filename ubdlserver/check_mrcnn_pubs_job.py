from __future__ import print_function
import os,sys
import ROOT as rt

def check_job( out, supera ):
    
    mrcnn_dict = {}
    supera_dict = {}
    
    rfile_mrcnn = rt.TFile( out )
    tree = rfile_mrcnn.Get("clustermask_mrcnn_masks_tree")
    for i in range(tree.GetEntries()):
        tree.GetEntry(i)
        run = tree.GetLeaf("_run").GetValue()
        subrun = tree.GetLeaf("_subrun").GetValue()
        event = tree.GetLeaf("_event").GetValue()
        mrcnn_dict[run, subrun, event] = 1
    nentries_mrcnn = tree.GetEntries()
    rfile_mrcnn.Close()
                
    rfile_supera = rt.TFile( supera )
    tree = rfile_supera.Get("image2d_wire_tree")
    for i in range(tree.GetEntries()):
        tree.GetEntry(i)
        run = tree.GetLeaf("_run").GetValue()
        subrun = tree.GetLeaf("_subrun").GetValue()
        event = tree.GetLeaf("_event").GetValue()
        supera_dict[run, subrun, event] = 1
    nentries_supera = tree.GetEntries()
    rfile_supera.Close()

    print("nentries_supera: ", nentries_supera)
    print( "nentries_mrcnn: ", nentries_mrcnn)
    print( "unique rses in supera: ", len(supera_dict))
    print( "unique rses in mrcnn: ", len(mrcnn_dict))

    if nentries_supera!=nentries_mrcnn or len(supera_dict)!=len(mrcnn_dict) or nentries_mrcnn==0:
        return False
    return True


if __name__=="__main__":

    out      = sys.argv[1]
    superain = sys.argv[2]
    
    result = check_job( out, superain )

    if result:
        print("True")
    else:
        print("False")

