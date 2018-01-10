import os

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
    #ssnetinput  = os.path.join(inputdbdir,input_format%("ssnetout-larcv",run,subrun))
    #ssnetinput += ".root"
    outputdbdir = os.path.join(output_dir,"%s/%03d/%02d/%03d/%02d/"%(runtag,rundiv100,runmod100,subrundiv100,subrunmod100))

    return jobtag, inputdbdir, outputdbdir

def cmd(SS):
    print SS
    os.system(SS)
    return