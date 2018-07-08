# DLLEE PUBS

PUBS projects that mamke up the Production Code for the DL LEE Analysis

## Current chain of projects (as of 7/8/17)

The chain is divided into two stages, 'stage 1' and 'stage 2'. The first stages involve
setting up the run table, copying/renaming files into the production convention,
and running the slowest parts of the chain: the tagger and SSNet.

The files to be processed are indexed in the database via the first `RUN:SUBRUN` values in the file.
The chain is run for every `RUN:SUBRUN` entry.

### Stage 1

* `runtable`: register files transfered to Tufts into the pubs database. 
  These go into PUBS runtables and serve as the source files for projects or chain of projects.
  The paths to the files are stored in the run tables initially
* `xferinput`: copy the files to the official DB directory and rename the files into
  some standard pattern. the paths in the runtable also get changed to this new name.
* `tagger`: run the cosmic tagger and CROI finder. Also run the PMT precuts. 
  Events that don't pass the precuts are given empty CROIs.
* `ssnet`: run ssnet within the CROI regions. Events with empty CROIs do not run SSNet.
* `freetaggercv`: because the ssnet output file contains a copy of the tagger stage output, 
  we delete the tagger stage output to save a significant amount of space. Note that once this
  stage is complete for a given `RUN:SUBRUN`, one must restart the chain from the tagger.

### Stage 2

* `vertex`: use ssnet and track intersections to find candidate neutrino vertices
* `trackshower`: for every vertex perform 3D reconstruction of tracks and showers coming from the vertex
* `likelihood`: given reconstructed quantities around vertices, calculate likelihood values used for selection

## Other folders

* `utils`: utility scripts such as one for extracting a list of files from the DB for a given stage and meeting certain status requirements (usually that it was processed successfully)
* `monitor`: dumps the status of the projects for each dataset. This project runs regularly on the nudot machien to produce the monitor page found [here](http://nudot.lns.mit.edu/taritree/dlleepubsummary.html).
* `cfg`: configuration files for the various pubs projects. there is a configuration for every dataset.