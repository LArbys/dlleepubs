import os,sys
import ROOT as rt

def check_job( out, supera ):
    
    infill_dict = {}
    supera_dict = {}
    
    rfile_infill = rt.TFile( out )
    tree = rfile_infill.Get("image2d_infill_tree")
    for i in xrange(tree.GetEntries()):
        tree.GetEntry(i)
        run = tree.GetLeaf("_run").GetValue()
        subrun = tree.GetLeaf("_subrun").GetValue()
        event = tree.GetLeaf("_event").GetValue()
        infill_dict[run, subrun, event] = 1
    nentries_infill = tree.GetEntries()
    rfile_infill.Close()
                
    rfile_supera = rt.TFile( supera )
    tree = rfile_supera.Get("image2d_wire_tree")
    for i in xrange(tree.GetEntries()):
        tree.GetEntry(i)
        run = tree.GetLeaf("_run").GetValue()
        subrun = tree.GetLeaf("_subrun").GetValue()
        event = tree.GetLeaf("_event").GetValue()
        supera_dict[run, subrun, event] = 1
    nentries_supera = tree.GetEntries()
    rfile_supera.Close()

    print "nentries_supera: ", nentries_supera
    print "nentries_infill: ", nentries_infill
    print "unique rses in supera: ", len(supera_dict)
    print "unique rses in infill: ", len(infill_dict)

    if nentries_supera!=nentries_infill or len(supera_dict)!=len(infill_dict) or nentries_infill==0:
        return False
    return True


if __name__=="__main__":

    out      = sys.argv[1]
    superain = sys.argv[2]
    
    result = check_job( out, superain )

    if result:
        print "True"
    else:
        print "False"

