#!/bin/sh

psql -U tufts-pubs -h nudot.lns.mit.edu procdb -c "\\dt" | grep tagger


