#!/bin/bash

#
# cosmic
#
python dlpkl.py mcc8v4_cocktail_p00 test14 rst_comb_df 1> log/cocktail_p00_test14_rst_comb_df.log 2> err/cocktail_p00_test14_rst_comb_df.err
python dlpkl.py mcc8v4_cocktail_p01 test14 rst_comb_df 1> log/cocktail_p01_test14_rst_comb_df.log 2> err/cocktail_p01_test14_rst_comb_df.err
python dlpkl.py mcc8v4_cocktail_p02 test14 rst_comb_df 1> log/cocktail_p02_test14_rst_comb_df.log 2> err/cocktail_p02_test14_rst_comb_df.err
python dlpkl.py mcc8v4_cocktail_p03 test14 rst_comb_df 1> log/cocktail_p03_test14_rst_comb_df.log 2> err/cocktail_p03_test14_rst_comb_df.err
python dlpkl.py mcc8v4_cocktail_p04 test14 rst_comb_df 1> log/cocktail_p04_test14_rst_comb_df.log 2> err/cocktail_p04_test14_rst_comb_df.err

python dlpkl.py mcc8v6_extbnb test14 rst_comb_df 1> log/extbnb_test14_rst_comb_df.log 2> err/extbnb_test14_rst_comb_df.err
python dlpkl.py mcc8v6_nuecosmic_truth test14 rst_comb_df 1> log/nuededx_truth_test14_rst_comb_df.log 2> err/nuededx_truth_test14_rst_comb_df.err

python dlpkl.py mcc8v8_lee_signal test14 rst_comb_df 1> log/mcc8v8_lee_signal_test14_rst_comb_df.log 2> err/mcc8v8_lee_signal_test14_rst_comb_df.err


