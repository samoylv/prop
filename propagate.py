
# coding: utf-8

# Contact L.Samoylova <liubov.samoylova@xfel.eu>, A.Buzmakov <buzmakov@gmail.com>
# SPB S2E simulation project, European XFEL Hamburg <www.xfel.eu>
# May 2014
# Wave optics software is based on 
# SRW core library <https://github.com/ochubar/SRW>, and 
# WPG framework <https://github.com/samoylv/WPG>

# In[1]:

#$
import sys
import os
import errno

sys.path.insert(0,'/data/S2E/packages/WPG/')
#
# sys.path.insert(0,'../..')

import shutil
import numpy
import h5py

#Import base wavefront class
from wpg import Wavefront
import wpg.optical_elements
from wpg.optical_elements import Use_PP
#from wpg.srwlib import srwl,SRWLOptD,SRWLOptA,SRWLOptC,SRWLOptT,SRWLOptL, SRWLOpt


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

    wf.params.Mesh.xMin = wf.params.Mesh.xMin*1.e-4
    wf.params.Mesh.xMax = wf.params.Mesh.xMax*1.e-4
    wf.params.Mesh.yMin = wf.params.Mesh.yMin*1.e-4
    wf.params.Mesh.yMax = wf.params.Mesh.yMax*1.e-4
    wf.data.arrEver = wf.data.arrEver*1e4

    print('Saving the wavefront data after propagating:'+out_fname)
    wf.store_hdf5(out_fname)
    add_history(out_fname, in_fname)


# In[8]:

def main():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-i", "--input-file", dest="in_fname", help="Input wavefront file", )
    parser.add_option("-o", "--out-file", dest="out_fname", help="Output wavefront file")

    (options, args) = parser.parse_args()
    
    if not options.in_fname:   # if filename is not given
        parser.error('Input filename not given')
   
    if not options.out_fname:   # if filename is not given
        parser.error('Out filename not given')
    
    propagate(options.in_fname, options.out_fname)


# In[ ]:

if __name__ == '__main__':
    main()

