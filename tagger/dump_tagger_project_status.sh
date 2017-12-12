#!/bin/sh

projectname=$1

psql -U tufts-pubs -h nudot.lns.mit.edu procdb -c "select * from $1 order by run,subrun ASC;"


