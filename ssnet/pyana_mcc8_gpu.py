# import os,sys,time

# import ROOT as rt
# rt.gSystem.Load("libGeo2D_Core.so")
# from larcv import larcv
# import caffe
# from caffe.image2d_data_layer import Image2DLayer as il
# caffe.set_mode_gpu()

# # Check GPU availability before heavy lib loading
# from choose_gpu import pick_gpu
# GPUMEM = 10000
# #GPUID = pick_gpu(mem_min=GPUMEM,caffe_gpuid=True)
# GPUID=0
# if GPUID < 0:
#     sys.stderr.write('No GPU available with memory > %d\n' % GPUMEM)
#     sys.stderr.flush()
#     sys.exit(1)

# caffe.set_device(GPUID)


# import numpy as np
# #import matplotlib 
# #matplotlib.use('Agg')
# import matplotlib.pyplot as plt
# os.environ['GLOG_minloglevel'] = '2' # set message level to warning 

# print "MODULES LOADED"

# VICS LOADING
from ROOT import geo2d
import caffe
import matplotlib
matplotlib.use('agg')
import os,sys,time
os.environ["GLOG_minloglevel"]='2'
import numpy as np
import ROOT as rt
from ROOT import larcv
import matplotlib.pyplot as plt
from caffe.image2d_data_layer import Image2DLayer as il

PROTO  = None
MODEL  = None
OUTCFG = 'pyana_out.cfg'
MASK_ADC = True
MASK_THRESH = 10.
SKIP_CH = [0]

#MODELDIR='/cluster/kappa/90-days-archive/wongjiradlab/grid_jobs/ssnet-tuftscluster-scripts'
MODELDIR='/cluster/kappa/wongjiradlab/larbys/ssnet_models/v1'
MODELMAP={'plane0' : MODELDIR+'/segmentation_pixelwise_ikey_plane0_iter_75500.caffemodel',
          'plane1' : MODELDIR+'/segmentation_pixelwise_ikey_plane1_iter_65500.caffemodel',
          'plane2' : MODELDIR+'/segmentation_pixelwise_ikey_plane2_iter_68000.caffemodel'}

PLANEID=''
MODEL=''
OUTFILESTEM='larcv_fcn'
try:
    GPUID = int(sys.argv[1])
except:
    raise Exception()

flist=rt.std.vector('string')()
for argv in sys.argv:
    if argv.find('.prototxt') >= 0:
        PROTO = argv
    elif argv.endswith('.root'):
        flist.push_back(argv)
    elif argv == 'plane0':
        PLANEID=argv
        MODEL=MODELMAP['plane0']
    elif argv == 'plane1':
        PLANEID=argv
        MODEL=MODELMAP['plane1']
    elif argv == 'plane2':
        PLANEID=argv
        MODEL=MODELMAP['plane2']
    elif argv=="%d"%(GPUID):
        continue
    else:
        OUTFILESTEM=argv

if not PLANEID or not MODEL:
    print 'Valid plane id not provided!'
    raise Exception()

# Check GPU availability before heavy lib loading
from choose_gpu import pick_gpu
GPUMEM = 6000
if GPUID==-1:
    GPUID = pick_gpu(mem_min=GPUMEM,caffe_gpuid=True)
if GPUID < 0:
    sys.stderr.write('No GPU available with memory > %d\n' % GPUMEM)
    sys.stderr.flush()
    raise Exception()
    sys.exit(1)
caffe.set_device(GPUID)
caffe.set_mode_gpu()

INCFG  = 'pyana_in_%s.cfg' % PLANEID
print "Using input config:",INCFG
debug = 'debug' in sys.argv
print "Out file stem: ",OUTFILESTEM
print "GPU MODE: using GPU #",GPUID

out_proc = larcv.ProcessDriver('OutputProcessDriver')
out_proc.configure(OUTCFG)
py_image_maker = out_proc.process_ptr(out_proc.process_id("PyImageStitcher"))
py_image_maker.set_producer_name('uburn_%s' % PLANEID)
out_proc.override_output_file('%s_%s.root'%(OUTFILESTEM,PLANEID) )
out_proc.initialize()

in_proc = larcv.ProcessDriver('InputProcessDriver')
in_proc.configure(INCFG)
in_proc.override_input_file(flist)

# put copy of input file in same folder as output
inputcopy_path = os.path.dirname( '%s_%s.root'%(OUTFILESTEM,PLANEID) ) + "/ssnet_input.root"
in_proc.override_output_file(inputcopy_path)
in_proc.initialize()

cropper = in_proc.process_ptr(in_proc.process_id("MultiROICropper"))
il._rows = cropper.target_rows()
il._cols = cropper.target_cols()

print "Loading Net"
print "  Proto: ",PROTO
print "  Model: ",MODEL

net = caffe.Net( PROTO, MODEL, caffe.TEST)

num_events = in_proc.io().get_n_entries()

print
print 'Total number of events:',num_events
print

event_counter = 0
stop_counter  = None

num_event_with_roi = 0.
num_roi = 0.

while event_counter < num_events:
    in_proc.process_entry(event_counter,True)

    img_v = cropper.get_cropped_image()
    sys.stdout.write('Processing entry %d/%d w/ %d ROIs        \r' % (event_counter,num_events,img_v.size()))
    sys.stdout.flush()
    
    num_roi += img_v.size()
    if img_v.size() > 0: num_event_with_roi+=1
    else: 
        # --------------------------------------------------------------------------------------
        # block in container processing to handle empty images
        in_proc.io().read_entry(event_counter,True)
        event_croi = in_proc.io().get_data( larcv.kProductROI, "croi" )
        (run,subrun,event) = (event_croi.run(), event_croi.subrun(), event_croi.event())
        print 'run',run,'subrun',subrun,'event',event," num rois=",event_croi.ROIArray().size()
        py_image_maker.set_id(run, subrun, event)
        out_proc.process_entry()
        in_proc.io().save_entry()
        # ----------------------------------------------------------------------------------------
        event_counter += 1
        continue

    for roi_idx in xrange(img_v.size()):

        il._image2d = img_v[roi_idx]
        net.forward()

        adcimg  = net.blobs["data"].data
        softmax = net.blobs["softmax"].data

        if debug:
            adcpng = plt.imshow(adcimg[0][0])
            adcpng.write_png('entry%04d_%04d.png' % (event_counter,roi_idx))

        img_array = softmax[0]
        out_ch = 0
        for ch in xrange(len(img_array)):
            if ch in SKIP_CH: continue

            img = img_array[ch]
            if MASK_ADC:
                img *= (adcimg[0][0] > MASK_THRESH)

            #py_image_maker.append_ndarray_meta(img.transpose(),img_v[roi_idx].meta(),out_ch)
            py_image_maker.append_ndarray_meta(img,img_v[roi_idx].meta(),out_ch)
            out_ch += 1
            
            if debug:
                png=plt.imshow(img)
                png.write_png('entry%06d_ch%02d.png' % ((ibatch * BATCH_CTR),ch))

    event_id = in_proc.io().last_event_id()
    #event_id = in_proc.io().event_id()
    (run,subrun,event) = (event_id.run(), event_id.subrun(), event_id.event())
    print 'run',run,'subrun',subrun,'event',event," num rois=",img_v.size()

    py_image_maker.set_id(run, subrun, event)
    out_proc.process_entry()
    event_counter += 1

    if stop_counter and event_counter >= stop_counter:
        break

if event_counter>0:
    frac_event_with_roi = (int(float(num_event_with_roi)/float(event_counter)*10000.))/100.
    average_num_roi_total = num_roi / float(event_counter)
else:
    frac_event_with_roi   = 0.0
    average_num_roi_total = 0.0
    
if num_event_with_roi>0:
    average_num_roi = num_roi / float(num_event_with_roi)
else:
    average_num_roi = 0.0

print
print '# events processed:',event_counter
print '# event w/ ROI:    ',num_event_with_roi,'(',frac_event_with_roi,'% )'
print '# ROI processed:   ',num_roi,'(',average_num_roi,'ROI per event, or total average',average_num_roi_total,')'
print

out_proc.finalize()
in_proc.finalize()
sys.exit(0)
