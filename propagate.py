
# coding: utf-8

# In[ ]:

# Contact L.Samoylova <liubov.samoylova@xfel.eu>, A.Buzmakov <buzmakov@gmail.com>
# SPB S2E simulation project, European XFEL Hamburg <www.xfel.eu>
# May 2014
# Wave optics software is based on 
# SRW core library <https://github.com/ochubar/SRW>, and 
# WPG framework <https://github.com/samoylv/WPG>


# In[2]:

#$
import sys
import os
import errno

sys.path.insert(0,'/data/S2E/packages/WPG/')
#
# sys.path.insert(0,'../..')

import multiprocessing
from glob import glob

import h5py

#Import base wavefront class
from wpg import Wavefront
import wpg.optical_elements
from wpg.optical_elements import Use_PP
#from wpg.srwlib import srwl,SRWLOptD,SRWLOptA,SRWLOptC,SRWLOptT,SRWLOptL, SRWLOpt


# In[1]:

def mkdir_p(path):
    """
    Create directory tree, if not exists (mkdir -p)
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


# In[5]:

def add_history(wf_file_name, history_file_name):
    with h5py.File(wf_file_name) as wf_h5:
        with h5py.File(history_file_name) as history_h5:
            if 'history' in wf_h5:
                del wf_h5['history']
            
            wf_h5.create_group('/history/parent')
            
            for k in history_h5:
                if not k == 'data':
                   history_h5.copy(k,wf_h5['history']['parent'])
                else:
                   wf_h5['history']['parent']['data'] = h5py.ExternalLink(history_file_name,'/data')


# In[7]:

def propagate(in_fname, out_fname):
    print('Start propagating:'+in_fname)
    wf=Wavefront()
    wf.load_hdf5(in_fname)
    distance = 100.
    drift0 = wpg.optical_elements.Drift(distance)
    #srwl_bl0 = SRWLOptC([drift0, ], [Use_PP(semi_analytical_treatment=1,zoom=0.1,sampling=4)])
    #bl0 = wpg.Beamline(srwl_bl0)

    bl0 = wpg.Beamline()
    bl0.append(drift0, Use_PP(semi_analytical_treatment=1,zoom=0.1,sampling=4))

    wpg.srwlib.srwl.SetRepresElecField(wf._srwl_wf, 'f')
    bl0.propagate(wf)
    wpg.srwlib.srwl.SetRepresElecField(wf._srwl_wf, 't')

    wf.params.Mesh.xMin=wf.params.Mesh.xMin*1.e-4
    wf.params.Mesh.xMax=wf.params.Mesh.xMax*1.e-4
    wf.params.Mesh.yMin=wf.params.Mesh.yMin*1.e-4
    wf.params.Mesh.yMax=wf.params.Mesh.yMax*1.e-4


    print('Saving the wavefront data after propagating:'+out_fname)
    mkdir_p(os.path.dirname(out_fname))
    wf.store_hdf5(out_fname)
    add_history(out_fname, in_fname)


# In[11]:

def propagate_wrap(*params):
    in_fname, out_fname = params
    return propagate(in_fname, out_fname)


# In[3]:

def directory_process(in_dname, out_dname, cpu_number):
    input_files = glob(os.path.join(in_dname,'FELsource','*.h5'))
    out_files = []
    for name in input_files:
        in_file_name = os.path.split(name)[-1]
        out_file_name = in_file_name.replace('prop_in','prop_out')
        out_files.append(os.path.join(out_dname,'prop',out_file_name))
    
    batch_params = zip(input_files, out_files)
    print 'Found {} HDF5 files in {}'.format(len(input_files), in_dname)
    p=multiprocessing.Pool(processes=cpu_number)
    p.map(propagate_wrap, batch_params, chunksize=1)
    p.join()
    p.close()


# In[8]:

def main():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--input-file", dest="in_fname", help="Input wavefront file")
    parser.add_option("--out-file", dest="out_fname", help="Output wavefront file")
    
    parser.add_option("--input-directory", dest="in_dname", help="Input directory with wavefront files")
    parser.add_option("--output-directory", dest="out_dame", help="Output directory with wavefront files")
    parser.add_option("-n", "--cpu-number", dest="cpu_number", default=int((multiprocessing.cpu_count()+1)/2),
                      help="Number of cores for batch wavefronts propagation, default value NUMBER_OF_CPU/2")

    (options, args) = parser.parse_args()
    
    
    if not (options.in_fname or options.in_dname):   # if filename is not given
        parser.error('Input filename or directiry not specified, use -if or -id options')
        return 
    
    if not (options.out_fname or options.out_dname):   # if filename is not given
        parser.error('Output filename or directiry not specified, use -of or -od options')
        return
    
    if options.in_dname and options.out_dname:
        print 'Input directory {}, output directory {}, number of cores {}'.format(
            options.in_dname, options.out_dname,options.cpu_number)
        print 'Batch propagation started'
        directory_process(options.in_dname, options.out_dname, options.cpu_number)
        print 'Batch propagation finished'
        
    elif options.in_fname and options.out_fname:
        print 'Input file {}, output file {}'.format(options.in_fname, options.out_fname)
        propagate(options.in_fname, options.out_fname)


# In[ ]:

if __name__ == '__main__':
    main()

