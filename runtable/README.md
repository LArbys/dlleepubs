# Defining a PUBS Run Table

## Assumptions

* We have transfered some files from FNAL into a set of folders. Typically, a `supera` folder holding larcv images and a `larlite` folder holding various larlite files make by litemaker. 
* The run table expects there to be one larcv file and opreco, reco2d, mcinfo larlite files per entry.
* The scripts do not use the filenames to the group the files into entries, it uses the first (run,subrun) in each file to match them.

## Steps to define a run table

* Change `submit.sh` to point to the supera and larlite folders
* Run the script on the grid using

      sbatch submit.sh

  This will produce `filelist.txt`. You can check the progress of the job with `tail -f log_prepflist.txt`.
* Run the python script to define a new runtable.

      python define_project.py [runtable name] filelist.txt

   For example, [runtable name] for the MCC8.4 cocktail p00 is defined as mcc8v4_cocktail_p00.  (you cannot use punctuation like '.')