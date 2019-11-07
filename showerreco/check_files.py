import os,sys

import ROOT as rt

nueid_larcv   = sys.argv[1]
nueid_larlite = sys.argv[2]
nueid_ana     = sys.argv[3]
shower_larlite = sys.argv[4]
shower_ana     = sys.argv[5]
supera         = sys.argv[6]

fsupera = rt.TFile(supera)
img_tree = fsupera.Get("image2d_wire_tree")
nentries = img_tree.GetEntries()

out_entries = []

fnueid_larcv = rt.TFile(nueid_larcv)
nueid_larcv_tree = fnueid_larcv.Get("pgraph_inter_par_tree")
out_entries.append( nueid_larcv_tree.GetEntries() )

fnueid_larlite = rt.TFile( nueid_larlite )
nueid_larlite_tree = fnueid_larlite.Get("track_inter_track_tree")
out_entries.append( nueid_larlite_tree.GetEntries() )

fshower_larlite = rt.TFile( shower_larlite )
shower_tree = fshower_larlite.Get("shower_dl_tree")
out_entries.append( shower_tree.GetEntries() )

fshower_ana = rt.TFile( shower_ana )
shower_ana_tree = fshower_ana.Get( "ShowerQuality_DL" )
#out_entries.append( shower_ana_tree.GetEntries() )

allgood = True
for i,n in enumerate(out_entries):
    if nentries != n:
        allgood = False
        print "[",i,"] Not good: ",n," vs ",nentries," (supera)"

if allgood:
    print "All good"
    f = open("checkfile",'w')
    print>>f,"CHECKOK"
    f.close()
else:
    print "Bad check"
