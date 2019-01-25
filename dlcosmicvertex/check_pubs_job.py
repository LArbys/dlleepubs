import os,sys
import ROOT as rt

def check_n_entries( rfilename, treenames, reference_numevents=None ):

    if not os.path.exists(rfilename):
        print rfilename," not found"
        return False,0

    if type(treenames) is str:
        treenames = [treenames]

    rfile = rt.TFile( rfilename )
    numentries = []
    for t in treenames:
        #print "check %s:%s"%(rfilename,t)
        try:
            tree  = rfile.Get( t )
            numentries.append( tree.GetEntries() )
        except:
            print "Trouble opening tree %s from %s"%(t,rfilename)
            return False,0

    if reference_numevents is None:
        reference_numevents = numentries[0]

    for n in numentries:
        if n!=reference_numevents:
            return False,0

    # passes
    return True,reference_numevents

def check_job( superain, dlvertex ):
    
    _,nsupera_entries = check_n_entries( superain, "image2d_wire_tree" )

    # probably want to drop this one in the future
    ok,nvertex_entries   = check_n_entries( dlvertex, ["pgraph_test_tree"], nsupera_entries )

    return ok

if __name__=="__main__":

    superain     = sys.argv[1]
    dlvertex     = sys.argv[2]
    
    result = check_job( superain, dlvertex )

    if result:
        print "True"
    else:
        print "False"

