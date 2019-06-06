import os,sys
import ROOT as rt

def check_job( out, supera ):
    
    post_dict = {}
    supera_dict = {}
    
    rfile_post = rt.TFile( out )
    tree = rfile_post.Get("image2d_hitflow_tree")
    for i in xrange(tree.GetEntries()):
        tree.GetEntry(i)
        run = tree.GetLeaf("_run").GetValue()
        subrun = tree.GetLeaf("_subrun").GetValue()
        event = tree.GetLeaf("_event").GetValue()
        post_dict[run, subrun, event] = 1
    nentries_post = tree.GetEntries()
    rfile_post.Close()
                
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
    print "nentries_post: ", nentries_post
    print "unique rses in supera: ", len(supera_dict)
    print "unique rses in post: ", len(post_dict)

    if nentries_supera!=nentries_post or len(supera_dict)!=len(post_dict) or nentries_post==0:
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

