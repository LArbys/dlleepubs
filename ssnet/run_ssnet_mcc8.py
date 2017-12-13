import os, sys
import numpy as np

flist=[]
if len(sys.argv) < 5:
    print 'Usage:',sys.argv[0],'PROCID GPUID OUTPUT_FILE','INPUT_FILE0, INPUTFILE1, ...'
    sys.exit(1)

# manage_gpu_job will track the status of this job using message in the log file
PROCID=int(sys.argv[1])
statusfile = open("job_ssnet_status_%d.txt"%(PROCID),'w')
print>>statusfile,"LOADING"

GPUID=int(sys.argv[2])

outfile = sys.argv[3]
if os.path.isfile(outfile):
    print 'output file already present:',outfile
    print outfile
    print >>statusfile,"ERROR"
    sys.exit(1)
if outfile[-5:]!=".root":
    print "output file does not end with .root"
    print outfile
    print >>statusfile,"ERROR"
    sys.exit(1)

for argv in sys.argv:
    if argv == outfile: continue
    elif argv=="%d"%(PROCID): continue
    if not argv.endswith('.root'): continue
    flist.append(argv)


outlist=[]
ERROR=False
input_copy_dir=os.path.dirname(outfile)
for plane in ['plane0','plane1','plane2']:
    print >>statusfile,plane
    try:
        print 'Processing',plane
        fname_stem = outfile.replace(".root","")
        cmd = 'python pyana_mcc8_gpu.py %d pyana_mcc8_small.prototxt %s %s '%(GPUID,fname_stem, plane)
        for f in flist:
            cmd += '%s ' % f

        print cmd
        return_code = int(os.system(cmd))
    
        fname = outfile.replace(".root","_%s.root"%(plane))
        if return_code:
            sys.stderr.write('Failed with return code %d\n' % return_code)
            raise Exception

        if not os.path.isfile(fname):
            sys.stderr.write('Expected output not found: %s\n' % fname)
            raise Exception
        outlist.append(fname)

    except Exception:
        print 'Error occurred! cleaning...'
        for f in outlist:
            os.remove(f)
        ERROR=True
        print >>statusfile,"ERROR"
        break
if ERROR:
    if os.path.isfile(input_copy_dir+'/ssnet_input.root'):
        os.remove(input_copy_dir+'/ssnet_input.root')
    print >>statusfile,"ERROR"
    sys.exit(1)
outlist.append(input_copy_dir+'/ssnet_input.root')
cmd='hadd %s ' % outfile
print cmd
for f in outlist:
    cmd += ' %s' % f
os.system(cmd)

for f in outlist:
    os.remove(f)
print >>statusfile,"SUCCESS"
sys.exit(0)
