import os,sys

#pqueue = os.popen("squeue -u twongj01 | grep ssnetcli")
pqueue = os.popen("squeue -u lyates01 | grep ssnetcli")
lqueue = pqueue.readlines()

for l in lqueue:
    l = l.strip().split()
    cmd = "scancel %d"%(int(l[0].strip()))
    print cmd
    o = os.popen(cmd)
    for i in o.readlines():
        print i.strip()




