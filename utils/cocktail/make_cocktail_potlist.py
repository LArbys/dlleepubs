import os
import ROOT as rt

#tout = rt.TFile("mcc8v4_cocktail_pot_summary.root", "recreate")

tsum = rt.TChain("potsummary_generator_tree")

files = []
for p in range(5):
    f = open("mcc8v5_cocktail_mcinfo_p%02d_list.txt"%(p),'r')
    ll = f.readlines()
    for l in ll:
        l = l.strip().split()[-1].strip()
        l = l.replace("/cluster/kappa","/tmp")
        print "adding ",l
        files.append(l)
    f.close()

files.sort()
for f in files:
    tsum.Add(f.strip())

print "Number of entries: ",tsum.GetEntries()
print "Save....",
tsum.Merge("mcc8v4_cocktail_pot_summary.root")
print "done."

tout.Close()

