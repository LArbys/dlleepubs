import sys

print "-----------------------"
print "| DL MCTRUTH ALIGN    |"
print "-----------------------"

if len(sys.argv) != 4:
    print ""
    print "FOLDER         = str(sys.argv[1])"
    print "WIRE_PREFIX    = str(sys.argv[2])"
    print "SEGMENT_PREFIX = str(sys.argv[3])"
    print ""
    sys.exit(1)

import os, time, subprocess, csv, getpass

def exec_system(input_):
    return subprocess.Popen(input_,stdout=subprocess.PIPE).communicate()[0].split("\n")[:-1]

def njobs():
    ret = exec_system(["squeue","-u",getpass.getuser()])
    ret = [r for r in ret if "interacti" in r]
    return int(len(ret))

def main() :
    FOLDER         = str(sys.argv[1])
    WIRE_PREFIX    = str(sys.argv[2])
    SEGMENT_PREFIX = str(sys.argv[3])

    print
    print "FOLDER=%s" % FOLDER
    print "WIRE_PREFIX=%s" % WIRE_PREFIX
    print "SEGMENT_PREFIX=%s" % SEGMENT_PREFIX
    print

    #
    # execute
    #
    CONTAINER  = "/cluster/tufts/wongjiradlab/vgenty/vertex/vertex_03152018_p00/image/"
    CONTAINER += "singularity-dllee-unified-03152018_revert.img"

    SS_v = []
    FOLDER = os.path.realpath(FOLDER)
    folder_v = [os.path.join(FOLDER,f) for f in os.listdir(FOLDER) if "start" not in f]
    
    for folder in folder_v:
        
        contents = [f for f in os.listdir(folder) if f.endswith(".root")]
        
        SEGMENT_FILE = [f for f in contents if f.startswith(SEGMENT_PREFIX)]
        SEGMENT_FILE = str(SEGMENT_FILE[0])

        WIRE_FILE = [f for f in contents if f.startswith(WIRE_PREFIX)]
        WIRE_FILE = [f for f in WIRE_FILE if f != SEGMENT_FILE]
        WIRE_FILE = str(WIRE_FILE[0])

        OUT_TXT = "rse.txt"
        FILTER_FILE = SEGMENT_FILE.split(".")[0] + "_filter.root"

        SEGMENT_FILE = os.path.join(folder,SEGMENT_FILE)
        WIRE_FILE    = os.path.join(folder,WIRE_FILE)
        OUT_TXT      = os.path.join(folder,OUT_TXT)
        FILTER_FILE  = os.path.join(folder,FILTER_FILE)

        SS = ""
        SS += "module load singularity" 
        SS += " && "
        SS += "srun -p interactive --job-name align_ singularity exec %s bash -c "
        SS += "\"source /usr/local/bin/thisroot.sh 1>/dev/null 2>/dev/null"
        SS += " && "
        SS += "cd /usr/local/share/dllee_unified/ 1>/dev/null 2>/dev/null"
        SS += " && " 
        SS += "source configure.sh 1>/dev/null 2>/dev/null"
        SS += " && "
        SS += "bash /usr/local/share/dllee_unified/LArCV/app/LArOpenCVHandle/ana/rse/txt_dump/txt_dump.sh %s %s %s %s %s %s"
        SS += "\""
    
        SS = SS % (CONTAINER, 
                   WIRE_FILE,
                   OUT_TXT,
                   SEGMENT_FILE,
                   OUT_TXT,
                   WIRE_FILE,
                   FILTER_FILE)

        SS_v.append(SS)

    while 1:
        if njobs() < 50:
            SS = SS_v.pop()
            SS += " &"
            print SS
            os.system(SS)
            print "Exec @ interactive node njobs=%d" % njobs()
        else:
            time.sleep(1)
            print "...sleep..."
        if len(SS_v) == 0: break

    return

if __name__ == '__main__':
    main()
    print "... all done ..."
    sys.exit(0)

