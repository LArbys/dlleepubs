import os,sys
import ROOT as rt

def check_job( ssnetout, supera ):
    
    ssnet_dict = {}
    supera_dict = {}
    
    rfile_ssnet = rt.TFile( ssnetout )
    tree = rfile_ssnet.Get("image2d_uburn_plane2_tree")
    #for i in xrange(tree.GetEntries()):
    #    tree.GetEntry(i)
    #    run = tree.GetLeaf("_run").GetValue()
    #    subrun = tree.GetLeaf("_subrun").GetValue()
    #    event = tree.GetLeaf("_event").GetValue()
    #    ssnet_dict[run, subrun, event] = 1
    nentries_ssnet = tree.GetEntries()
    rfile_ssnet.Close()
                
    rfile_supera = rt.TFile( supera )
    tree = rfile_supera.Get("image2d_wire_tree")
    #for i in xrange(tree.GetEntries()):
    #    tree.GetEntry(i)
    #    run = tree.GetLeaf("_run").GetValue()
    #    subrun = tree.GetLeaf("_subrun").GetValue()
    #    event = tree.GetLeaf("_event").GetValue()
    #    supera_dict[run, subrun, event] = 1
    nentries_supera = tree.GetEntries()
    rfile_supera.Close()

    print "nentries_supera: ", nentries_supera
    print "nentries_ssnet: ", nentries_ssnet
    #print "unique rses in supera: ", len(supera_dict)
    #print "unique rses in ssnet: ", len(ssnet_dict)

    #if nentries_supera!=nentries_ssnet or len(supera_dict)!=len(ssnet_dict) or nentries_ssnet==0:
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

