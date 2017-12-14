import os,sys,time
import commands

MAX_NUM_JOBS=8

### taken from pubs script, fetch gpu info, not for users to understand
def ls_gpu():
    output = commands.getoutput('nvidia-smi | grep MiB')
    mem_usage = {}
    num_jobs  = {}
    mem_max   = []
    for l in output.split('\n'):
        words=l.split()
        if len(words) < 4: continue
    
        if words[1].isdigit():
            gpu_id  = int(words[1])
            if not gpu_id in mem_usage:
                mem_usage[gpu_id] = 0
            if not gpu_id in num_jobs:
                num_jobs[gpu_id] = 0
            mem_usage[gpu_id] += int(words[-2].replace('MiB',''))
            num_jobs[gpu_id] += 1
        else:
            mem_max.append(int(words[-5].replace('MiB','')))

    for i in xrange(len(mem_max)):
        if not i in mem_usage:
            mem_usage[i] = 0
            num_jobs[i]  = 0

    for i in mem_usage:
        assert i < len(mem_max)

    return (mem_usage,mem_max,num_jobs)

### taken from pubs script, pick an available gpu, not for users to understand
def pick_gpu(mem_min=1,caffe_gpuid=False):
    gpu_info = ls_gpu()
    for gpu in gpu_info[0]:
        mem_available = gpu_info[1][gpu] - gpu_info[0][gpu]
        print "GPU #",gpu," mem available: ",mem_available
        if mem_available > mem_min and gpu_info[2][gpu]<MAX_NUM_JOBS:
            if caffe_gpuid:
                return (len(gpu_info[0])-1) - gpu
            else:
                return gpu
    return -1

### launch job until space found on node
def run_job(CONTAINER,WORKDIR,OUTFILE,STARTPAUSE,max_tries=360, waitsec=10):
    
    itry = 0
    print "Pausing %d before starting to prevent collision"%(STARTPAUSE)
    time.sleep(STARTPAUSE) # so jobs don't collide

    while itry<max_tries or max_tries<0:

        (mem_usage,mem_max,num_jobs) = ls_gpu()

        print "----------------------------------------"
        print "GPU STATUS UPDATE [attempt %d]"%(itry)
        #print "mem usage:",mem_usage
        #print "mem max: ",mem_max
        #print "num_jobs: ",num_jobs
        gpuids = mem_usage.keys()
        gpuids.sort()
        for gpuid in gpuids:
            print "  [GPU %d] Memory Usage: %d  Num Jobs: %d" % (gpuid,mem_usage[gpuid],num_jobs[gpuid])

        gpuid = pick_gpu(mem_min=2000)
        nrunning = num_jobs[gpuid]
        if gpuid<0 or nrunning>=MAX_NUM_JOBS:
            print "Max number of jobs. Waiting for jobs to complete."
            print "--------------------------------------------------"
            time.sleep(waitsec)
            itry+=1
            continue

        
        print "Available GPU (",gpuid,")"
        print "Run Job"
        procid = 0
        # run_pubsgpu_job [workdir] [inputlist dir] [output file] [jobidlist] [gpuid]
        cmd = "singularity exec --nv %s bash -c " % (CONTAINER)
        cmd += "\"cd %s && source run_pubsgpu_job.sh %s %s/inputlists %s %s/rerunlist.txt %d \""%(WORKDIR,WORKDIR,WORKDIR,OUTFILE,WORKDIR,gpuid)
        os.system( cmd )
        break


if __name__=="__main__":

    container = sys.argv[1]
    workdir   = sys.argv[2]
    outfile   = sys.argv[3]
    startwait = int(sys.argv[4])
    
    run_job( container, workdir, outfile, startwait )
