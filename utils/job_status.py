import os, sys, subprocess, re

def exec_system(input_):
    return subprocess.Popen(input_,stdout=subprocess.PIPE).communicate()[0].split("\n")[:-1]

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

if __name__ == '__main__':
    
    if len(sys.argv) != 2:
        print
        print "......................."
        print
        print "USER = str(sys.argv[1])"
        print
        print "......................."
        print

    USER = str(sys.argv[1])
    squeue = exec_system(["squeue","-u",USER])
    squeue = squeue[1:]

    names   = ["Vertex     ","TrackShower","Likelihood "]
    stages  = ["vertex_","st_","ll_"]
    running = [0,0,0]
    queued  = [0,0,0]
    
    for job in squeue:
        for ix,stage in enumerate(stages):
            res = re.search(stage,job)
            if res == None: continue
            job_v = job.split(" ")
            job_v = [j for j in job_v if j != '']
            if job_v[4] == "R":
                running[ix]+=1
            else:
                queued[ix]+=1

    nrunning = 0
    nqueued  = 0
    print
    print "\t   Batch jobs for " + bcolors.OKBLUE + USER + bcolors.ENDC
    print
    print bcolors.UNDERLINE + "\t   Stage   \tRunning\tQueued" + bcolors.ENDC
    for ix,name in enumerate(names):
        print "\t" + bcolors.WARNING + name + bcolors.OKGREEN + "\t%d" % running[ix] + bcolors.FAIL + "\t%d" % queued[ix] + bcolors.ENDC
        nrunning += running[ix]
        nqueued  += queued[ix]
    print "\t" + bcolors.BOLD + "Total     "+ bcolors.OKGREEN + "\t%d" % nrunning + bcolors.FAIL + "\t%d" % nqueued + bcolors.ENDC
    print
    sys.exit(0)
