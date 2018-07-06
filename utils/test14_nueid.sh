#!/bin/bash

#
# cosmic
#
#python dlhadd.py mcc8v4_cocktail_p00 test14_nueid nueid_ana 1> log/cocktail_p00_test14_nueid_ana.log 2> err/cocktail_p00_test14_nueid_ana.err
#python dlhadd.py mcc8v4_cocktail_p01 test14_nueid nueid_ana 1> log/cocktail_p01_test14_nueid_ana.log 2> err/cocktail_p01_test14_nueid_ana.err
#python dlhadd.py mcc8v4_cocktail_p02 test14_nueid nueid_ana 1> log/cocktail_p02_test14_nueid_ana.log 2> err/cocktail_p02_test14_nueid_ana.err
#python dlhadd.py mcc8v4_cocktail_p03 test14_nueid nueid_ana 1> log/cocktail_p03_test14_nueid_ana.log 2> err/cocktail_p03_test14_nueid_ana.err
#python dlhadd.py mcc8v4_cocktail_p04 test14_nueid nueid_ana 1> log/cocktail_p04_test14_nueid_ana.log 2> err/cocktail_p04_test14_nueid_ana.err

# python dlhadd.py corsika_mcc8v3_p00 test14_nueid nueid_ana 1> log/corsika_mcc8v3_p00_test14_nueid_ana.log 2> err/corsika_mcc8v3_p00_test14_nueid_ana.err
# python dlhadd.py corsika_mcc8v3_p01 test14_nueid nueid_ana 1> log/corsika_mcc8v3_p01_test14_nueid_ana.log 2> err/corsika_mcc8v3_p01_test14_nueid_ana.err
# python dlhadd.py corsika_mcc8v3_p02 test14_nueid nueid_ana 1> log/corsika_mcc8v3_p02_test14_nueid_ana.log 2> err/corsika_mcc8v3_p02_test14_nueid_ana.err

# python dlhadd.py mcc8v6_bnb5e19 test14_nueid nueid_ana 1> log/bnb5e19_test14_nueid_ana.log 2> err/bnb5e19_test14_nueid_ana.err
python dlhadd.py mcc8v6_extbnb test14_nueid nueid_ana 1> log/extbnb_test14_nueid_ana.log 2> err/extbnb_test14_nueid_ana.err
python dlhadd.py mcc8v6_nuecosmic_truth test14_nueid nueid_ana 1> log/nuededx_truth_test14_nueid_ana.log 2> err/nuededx_truth_test14_nueid_ana.err

# python dlhadd.py overlay_bnbcosmic_full test14_nueid nueid_ana 1> log/overlay_bnbcosmic_full_test14_nueid_ana.log 2> err/overlay_bnbcosmic_full_test14_nueid_ana.err

python dlhadd.py mcc8v8_lee_signal test14_nueid nueid_ana 1> log/mcc8v8_lee_signal_test14_nueid_ana.log 2> err/mcc8v8_lee_signal_test14_nueid_ana.err
# python dlhadd.py mcc8v8_lee_signal_noprecuts test14_nueid nueid_ana 1> log/mcc8v8_lee_signal_noprecuts_test14_nueid_ana.log 2> err/mcc8v8_lee_signal_noprecuts_test14_nueid_ana.err


