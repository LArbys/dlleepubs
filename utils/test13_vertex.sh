#!/bin/bash

#
# dllee_vertex
#

python dlhadd.py mcc8v4_cocktail_p00 test13 dllee_vertex 1> log/cocktail_p00_test13_dllee_vertex.log 2> log/cocktail_p00_test13_dllee_vertex.err
python dlhadd.py mcc8v4_cocktail_p01 test13 dllee_vertex 1> log/cocktail_p01_test13_dllee_vertex.log 2> log/cocktail_p01_test13_dllee_vertex.err
python dlhadd.py mcc8v4_cocktail_p02 test13 dllee_vertex 1> log/cocktail_p02_test13_dllee_vertex.log 2> log/cocktail_p02_test13_dllee_vertex.err
python dlhadd.py mcc8v4_cocktail_p03 test13 dllee_vertex 1> log/cocktail_p03_test13_dllee_vertex.log 2> log/cocktail_p03_test13_dllee_vertex.err
python dlhadd.py mcc8v4_cocktail_p04 test13 dllee_vertex 1> log/cocktail_p04_test13_dllee_vertex.log 2> log/cocktail_p04_test13_dllee_vertex.err

python dlhadd.py corsika_mcc8v3_p00 test13 dllee_vertex 1> log/corsika_mcc8v3_p00_test13_dllee_vertex.log 2> log/corsika_mcc8v3_p00_test13_dllee_vertex.err
python dlhadd.py corsika_mcc8v3_p01 test13 dllee_vertex 1> log/corsika_mcc8v3_p01_test13_dllee_vertex.log 2> log/corsika_mcc8v3_p01_test13_dllee_vertex.err
python dlhadd.py corsika_mcc8v3_p02 test13 dllee_vertex 1> log/corsika_mcc8v3_p02_test13_dllee_vertex.log 2> log/corsika_mcc8v3_p02_test13_dllee_vertex.err

python dlhadd.py mcc8v6_bnb5e19 test13 dllee_vertex 1> log/bnb5e19_test13_dllee_vertex.log 2> log/bnb5e19_test13_dllee_vertex.err
python dlhadd.py mcc8v6_extbnb test13 dllee_vertex 1> log/extbnb_test13_dllee_vertex.log 2> log/extbnb_test13_dllee_vertex.err
python dlhadd.py overlay_bnbcosmic_full test13 dllee_vertex 1> log/overlay_bnbcosmic_full_dllee_vertex.log 2> log/overlay_bnbcosmic_full_dllee_vertex.log
python dlhadd.py mcc8v6_nuecosmic_truth test13 dllee_vertex 1> log/mcc8v6_nuecosmic_truth_dllee_vertex.log 2> log/mcc8v6_nuecosmic_truth_dllee_vertex.log

python dlhadd.py mcc8v8_lee_signal test13 dllee_vertex 1> log/mcc8v8_lee_signal_dllee_vertex.log 2> log/mcc8v8_lee_signal_dllee_vertex.log
python dlhadd.py mcc8v8_lee_signal_noprecuts test13 dllee_vertex 1> log/mcc8v8_lee_signal_noprecuts_dllee_vertex.log 2> log/mcc8v8_lee_signal_noprecuts_dllee_vertex.log