import os,sys
import ROOT as rt
from larcv import larcv

def extract_rse_larcv( rootfilepath, iopset, producer="wire" ):
    if not type(rootfilepath) is str:
        raise ValueError("rootfilepath should be a string")

    io = larcv.IOManager( iopset )
    io.add_in_file( rootfilepath )
    io.initialize()

    nentries = io.get_n_entries()

    io.read_entry(0)

    imgdata = io.get_data( larcv.kProductImage2D, producer )
    run     = int(imgdata.run())
    subrun  = int(imgdata.subrun())
    event   = int(imgdata.event())
    io.finalize()

    # Close all open root files
    for f in rt.gROOT.GetListOfFiles():
        f.Close()

    try:
        jobid=int(os.path.basename(rootfilepath).split("_")[1].split(".")[0])
    except:
        jobid=run*10000+subrun

    return (run,subrun,event),jobid

def match_rse_to_fname( rootfilepath, jobid2rse ):
    jobid=int(os.path.basename(rootfilepath).split("_")[1].split(".")[0])
    if jobid in jobid2rse:
        return jobid2rse
    return None

def extract_rse_larlite( rootfilepath ):
    if not type(rootfilepath) is str:
        raise ValueError("rootfilepath should be a string")

    io = rt.TFile(rootfilepath)
    idtree = io.Get("larlite_id_tree")
    idtree.GetEntry(0)

    run     = idtree._run_id
    subrun  = idtree._subrun_id
    event   = idtree._event_id
    io.Close()

    return (run,subrun,event)


def catalog_supera_files( filefolders, iopset, filedict, jobid2rse ):
    folderlist = filefolders
    if type(filefolders) is str:
        folderlist = []
        folderlist.append(filefolders)

    for folder in folderlist:
        superafiles = os.listdir( folder )
        for f in superafiles:
            if ".root" not in f or "larcv" not in f or "larcv_mctruth" in f:
                continue
            fpath = folder + "/" + f.strip()
    
            try:
                rse,jobid = extract_rse_larcv( fpath, iopset, "wire" )
            except:
                print "Trouble parsing for larcv",fpath
                continue
            print "supera",rse,jobid,f
            if rse not in filedict:
                filedict[rse] = {}
            if jobid not in jobid2rse:
                jobid2rse[jobid] = rse
            filedict[rse]["supera"] = fpath
    return

def catalog_larcvtruth_files( filefolders, iopset, filedict, jobid2rse, fname_stem="larcv_mctruth" ):
    folderlist = filefolders
    if type(filefolders) is str:
        folderlist = []
        folderlist.append(filefolders)

    for folder in folderlist:
        superafiles = os.listdir( folder )
        for f in superafiles:
            if ".root" not in f or fname_stem not in f:
                continue
            fpath = folder + "/" + f.strip()
    
            try:
                rse,jobid = extract_rse_larcv( fpath, iopset, "segment" )
            except:
                print "Trouble parsing for larcv",fpath
                continue
            print "larcvtruth",rse,jobid,f
            if rse not in filedict:
                filedict[rse] = {}
            if jobid not in jobid2rse:
                jobid2rse[jobid] = rse
            filedict[rse]["larcvtruth"] = fpath
    return

def catalog_larlite_files( filefolders, filedict ):
    folderlist = filefolders
    if type(filefolders) is str:
        folderlist = []
        folderlist.append(filefolders)

    for folder in folderlist:
        larlitefiles = os.listdir( folder )
        for f in larlitefiles:
            if ".root" not in f or "larlite" not in f:
                continue
            fpath = folder + "/" + f.strip()
            #ftype = f.split("_")[1]
            if "opreco" in f: ftype = "opreco"
            elif "reco2d" in f: ftype = "reco2d"
            elif "mcinfo" in f: ftype = "mcinfo"
            elif "backtracker" in f: ftype = "backtracker"

            try:
                rse = extract_rse_larlite( fpath )
            except:
                print "Trouble parsing for larlite: ",fpath
                continue

            print ftype,rse,f
            if rse not in filedict:
                filedict[rse] = {}

            filedict[rse][ftype] = fpath
    return


if __name__=="__main__":
    
    #folders = []
    #for i in sys.argv[1:]:
    #    folders.append(i)

    print len(sys.argv),sys.argv
    
    if len(sys.argv)!=3 and len(sys.argv)!=4:
        print "usage: extract_runlist [larcv folder] [larlite folder] [larcv-truth folder]"
        sys.exit(-1)

    larcv_folder = []
    larcvtruth_folder = []
    larlite_folder = []
    larcv_folder.append( sys.argv[1] )
    larlite_folder.append( sys.argv[2] )
    if len(sys.argv)==4:
        larcvtruth_folder.append( sys.argv[3] )
        print "found larcv_mctruth folder"


    larcviocfg="""Name: IOManager Verbosity: 02 IOMode: 0 ReadOnlyDataType: ["wire"]  ReadOnlyDataName: [0]"""

    iopset = larcv.PSet("IOManager",larcviocfg)

    filedict = {}
    jobid2rse = {}
    catalog_supera_files( larcv_folder, iopset, filedict, jobid2rse )
    catalog_larlite_files( larlite_folder, filedict )
    if len(larcvtruth_folder)>0:
        catalog_larcvtruth_files( larcvtruth_folder, iopset, filedict, jobid2rse )

    rselist = filedict.keys()
    rselist.sort()

    f = open('filelist.txt','w')

    g = open('incomplete.txt','w')

    for rse in rselist:
        fdict = filedict[rse]
        print rse,fdict
        if ("supera" not in fdict or "opreco" not in fdict or "reco2d" not in fdict) and ("supera" not in fdict or "opreco" not in fdict or "backtracker" not in fdict):
            print rse," not complete"
            print >> g,fdict
            continue
        print >> f,rse[0],'\t',rse[1],'\t',rse[2],'\t',"supera:"+fdict["supera"],'\t',"opreco:"+fdict["opreco"],
        if "reco2d" in fdict:
            print >> f,'\t',"reco2d:"+fdict["reco2d"],
        if "backtracker" in fdict:
            print >> f,'\t',"backtracker:"+fdict["backtracker"],
        if "mcinfo" in fdict:
            print >> f,'\t',"mcinfo:"+fdict["mcinfo"],
        if "larcvtruth" in fdict:
            print >> f,'\t',"larcvtruth:"+fdict["larcvtruth"],
        print >>f,'\n'
            

    f.close()
    g.close()
