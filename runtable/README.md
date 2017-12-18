## Steps to define a run table

* Change `submit.sh` to point to the supera and larlite folders
* Run the script on the grid using

      sbatch submit.sh

  This will produce `filelist.txt`. You can check the progress of the job with `tail -f log_prepflist.txt`.
* Run the python script to define a new runtable.

      python define_project.py [runtable name] filelist.txt

   For example, [runtable name] for the MCC8.4 cocktail p00 is defined as mcc8v4_cocktail_p00.  (you cannot use punctuation like '.')