1;4402;0c# Defining a PUBS Run Table

## Assumptions

* We have transfered some files from FNAL into a set of folders. Typically, a `supera` folder holding larcv images and a `larlite` folder holding various larlite files make by litemaker. 
* The run table expects there to be one larcv file and opreco, reco2d, mcinfo larlite files per entry.
* The scripts do not use the filenames to the group the files into entries, it uses the first (run,subrun) in each file to match them.


## Steps to define a run table via *samweb metadata* [preferred]

* go to your favorite uboonegpvm
* go to your uboone app folder and clone the samweb info extraction script:

      git clone https://github.com/querysam

* go to your folder on Tufts where the transferred files live
* make a list of just the file names (e.g. larcv_wholeview_ffc9b002-4798-4580-97be-9f55670e2f24.root) for example:

      ls > flist_mysample_larcv.txt

  Note: the files need to be in the sam database. You can check if it is by going to 
  the [Definition Editor](http://samweb.fnal.gov:8480/sam/uboone/definition_editor/) and querying
  for the filename using

      file_name=larcv_wholeview_ffc9b002-4798-4580-97be-9f55670e2f24.root

  If a page pops up with info about the file, then it's in the samweb DB

* transfer the file list to `querysam` folder
* use `make_flist_from_sam.py` to extract a bunch of sam metadata. 
  Provide the filename of the file list. The other arguments are name of output files.
* make file list and extract the samweb DB info. with 'make_flist_from_same.py` for each type of file
* when all files have sam metadata, transfer that info to `dlleepubs/runtable`
* [to be continued]

## Steps to define a run table via *file matching*

* Change `submit.sh` to point to the supera and larlite folders
* Run the script on the grid using

      sbatch submit.sh

  This will produce `filelist.txt`. You can check the progress of the job with `tail -f log_prepflist.txt`.
* Run the python script to define a new runtable.

      python define_project.py [runtable name] filelist.txt

   For example, [runtable name] for the MCC8.4 cocktail p00 is defined as mcc8v4_cocktail_p00.  (you cannot use punctuation like '.')

