Hello, this is the Start-to-End simulation workflow!

Sources hosted at git repository https://github.com/samoylv/prop.git

***** DESCRIPTION OF SCRIPTS *****

propagate.py - simple script for propagation with support of wavefront history.

Usage (propagate.py -h) 
python propagate.py --input-file input_file_name --output-file ouput_file_name


Batch mode takes FELsource_out*.h5 files from input_directory_name, put processed prop_out*.h5 in ouput_directory_name
python propagate.py --input-directory input_directory_name --output-directory ouput_directory_name



Proppagation with custom beamlines:

python propagate-mod.py --input-directory=simulation_test/FELsource --output-directory=simulation_test/prop/ -n 1 --beamline-file=my_beamline.py 

my_beamline.py (or some other file) should define **get_beamline** function.