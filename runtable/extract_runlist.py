import os,sys
import ROOT as rt
from larcv import larcv

def extract_rse_larcv( rootfilepath, iopset ):
    if not type(rootfilepath) is str:
        raise ValueError("rootfilepath should be a string")

    io = larcv.IOManager( iopset )
    io.add_in_file( rootfilepath )
    io.initialize()
    io.read_entry(0)

    imgdata = io.get_data( larcv.kProductImage2D, "wire" )
    run     = int(imgdata.run())
    subrun  = int(imgdata.subrun())
    event   = int(imgdata.event())
    io.finalize()

    jobid=int(os.path.basename(rootfilepath).split("_")[1].split(".")[0])

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
            if ".root" not in f or "larcv" not in f:
                continue
            fpath = folder + "/" + f.strip()
    
            try:
                rse,jobid = extract_rse_larcv( fpath, iopset )
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
            ftype = f.split("_")[1]
    
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
    
    folders = []
    for i in sys.argv[1:]:
        folders.append(i)

    print folders
    larcviocfg="""Name: IOManager Verbosity: 02 IOMode: 0 ReadOnlyDataType: ["wire"]  ReadOnlyDataName: [0]"""

    iopset = larcv.PSet("IOManager",larcviocfg)

    filedict = {}
    jobid2rse = {}
    catalog_supera_files( folders, iopset, filedict, jobid2rse )
    catalog_larlite_files( folders, filedict )

    rselist = filedict.keys()
    rselist.sort()

    f = open('filelist.txt','w')

    for rse in rselist:
        fdict = filedict[rse]
        print rse,fdict
        print >> f,rse[0],'\t',rse[1],'\t',rse[2],'\t',"supera:"+fdict["supera"],'\t',"opreco:"+fdict["opreco"],'\t',"reco2d:"+fdict["reco2d"],
        if "mcinfo" in fdict:
            print >> f,'\t',"mcinfo:"+fdict["mcinfo"],
        print >>f,'\n'

    f.close()
            


