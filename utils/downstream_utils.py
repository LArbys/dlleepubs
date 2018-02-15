import os
import subprocess

PUB_TOP_DIR = os.environ["PUB_TOP_DIR"]
DLLEE_DIR   = os.path.join(PUB_TOP_DIR,"dlleepubs")
VERTEX_DIR  = os.path.join(DLLEE_DIR,"vertex")
CFG_DIR     = os.path.join(DLLEE_DIR,"downstream","Production_Config","cfg")
SCRIPT_DIR  = os.path.join(DLLEE_DIR,"downstream","vertex-tuftscluster-scripts","mac","template","base")


def cast_run_subrun(run,subrun,
                    runtag,input_format,
                    input_dir,output_dir):

    runmod100    = run%100
    rundiv100    = run/100
    subrunmod100 = subrun%100
    subrundiv100 = subrun/100
    
    jobtag      = 10000*run + subrun
    inputdbdir  = os.path.join(input_dir,"%03d/%02d/%03d/%02d/"%(rundiv100,runmod100,subrundiv100,subrunmod100))
    outputdbdir = os.path.join(output_dir,"%s/%03d/%02d/%03d/%02d/"%(runtag,rundiv100,runmod100,subrundiv100,subrunmod100))

    return jobtag, inputdbdir, outputdbdir

def cmd(SS,print_=True):
    if print_==True: print SS
    os.system(SS)
    return


#
# subprocess execute
#
def exec_system(input_):
    return subprocess.Popen(input_,stdout=subprocess.PIPE).communicate()[0].split("\n")[:-1]

#
# ssh command 
#
def exec_ssh(who,where,what):
    SS = ["ssh","-oStrictHostKeyChecking=no","-oGSSAPIAuthentication=yes","-T","-x","%s@%s"%(who,where),what]
    return exec_system(SS)
