input_list = "bad_ssnet.list"
output_script = "killer.sh"

with open(input_list, 'r') as flist:
    with open(output_script, 'w') as killer:

        for f in flist:

            killer.write("rm -f " + f)
