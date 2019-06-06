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

def check_job( superain, flashmatch, truthcluster, flashana ):
    
    _,nsupera_entries = check_n_entries( superain, "image2d_wire_tree" )

    ok,nflashevs = check_n_entries( flashmatch, ["larflowcluster_intimeflashmatched_tree"], reference_numevents=nsupera_entries )
    if not ok:
        return False

    ok,ntruthevs = check_n_entries( truthcluster, ["larflowcluster_flowtruthclusters_tree"], reference_numevents=nsupera_entries )
    if not ok:
        return False

    ok,nana = check_n_entries( flashana, ["anaflashtree"] )
    if not ok:
        return False

    return True

if __name__=="__main__":

    superain     = sys.argv[1]
    flashmatch   = sys.argv[2]
    truthcluster = sys.argv[3]
    flashana     = sys.argv[4]
    
    result = check_job( superain, flashmatch, truthcluster, flashana )

    if result:
        print "True"
    else:
        print "False"

