
# coding: utf-8

# In[ ]:

isS2E = True  # True if running at S2E server
isIpynb = False # True if ipython notebook, in python script should be false 


# In[ ]:

#$
import sys
import os
import errno

if isS2E:
    sys.path.insert(0,'/data/S2E/packages/WPG/')
else:
#    sys.path.insert(0,'/home/makov/workspace/my/xfel/WPG/')
    sys.path.insert(0,'../..')

import multiprocessing
from glob import glob

import h5py
import numpy as np

#Import base wavefront class
from wpg import Wavefront
import wpg.optical_elements
from wpg.optical_elements import Use_PP
#from wpg.srwlib import srwl,SRWLOptD,SRWLOptA,SRWLOptC,SRWLOptT,SRWLOptL, SRWLOpt


# In[ ]:

def mkdir_p(path):
    """
    Create directory tree, if not exists (mkdir -p)
    
    :param path: Path to be created
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


# In[ ]:

def add_history(wf_file_name, history_file_name):
    """
    Add history from pearent file to propagated file
    
    :param wf_file_name: output file
    :param history_file_name: peraent file
    """
    with h5py.File(wf_file_name) as wf_h5:
        with h5py.File(history_file_name) as history_h5:
            if 'history' in wf_h5:
                del wf_h5['history']
            
            wf_h5.create_group('/history/parent/')
            wf_h5.create_group('/history/parent/detail')
            
            for k in history_h5:
                if k=='history':
                    try:
                        history_h5.copy('/history/parent', wf_h5['history']['parent'])
                    except KeyError:
                        pass
                        
                elif not k == 'data':
                    history_h5.copy(k,wf_h5['history']['parent']['detail'])
                else:
                    wf_h5['history']['parent']['detail']['data'] = h5py.ExternalLink(history_file_name,'/data')


# In[ ]:

def calculate_fwhm(wfr):
    """
    Calculate FWHM of the beam calculating number of point bigger then max/2 throuhgt center of the image
    
    :param wfr:  wavefront
    :return: {'fwhm_x':fwhm_x, 'fwhm_y': fwhm_y} in [m]
    """
#    intens = wfr.get_intensity(polarization='total')
    intens = wfr.get_intensity(polarization='total').sum(axis=-1);


    mesh = wfr.params.Mesh
    dx = (mesh.xMax-mesh.xMin)/mesh.nx
    dy = (mesh.yMax-mesh.yMin)/mesh.ny

    x_center = intens[intens.shape[0]//2,:]
    fwhm_x = len(x_center[x_center>x_center.max()/2])*dx

    y_center = intens[:,intens.shape[1]//2]
    fwhm_y = len(y_center[y_center>y_center.max()/2])*dy
    return {'fwhm_x':fwhm_x, 'fwhm_y': fwhm_y}


# In[ ]:

def get_intensity_on_axis(wfr):
    """
    Calculate intensity (spectrum in frequency domain) along z-axis (x=y=0)

    :param wfr:  wavefront
    :return: [z,s0] in [a.u.] if frequency domain
    """

    wf_intensity = wfr.get_intensity(polarization='horizontal')
    mesh = wfr.params.Mesh;
    zmin = mesh.sliceMin;
    zmax = mesh.sliceMax;
    sz = np.zeros((mesh.nSlices, 2), dtype='float64')
    sz[:,0] = np.linspace(zmin, zmax, mesh.nSlices);
    sz[:,1] = wf_intensity[mesh.nx/2, mesh.ny/2, :] / wf_intensity.max()

    return sz


# In[ ]:

def propagate(in_fname, out_fname):
    """
    Propagate wavefront
    
    :param in_file: input wavefront file
    :param out_file: output file
    """
    print('Start propagating:' + in_fname)
    wf=Wavefront()
    wf.load_hdf5(in_fname)
    distance = 300.
    f_hfm    = 3.0       # nominal focal length for HFM KB
    f_vfm    = 1.9       # nominal focal length for VFM KB
    distance_hfm_vfm = f_hfm - f_vfm
    distance_foc =  1. /(1./f_vfm + 1. / (distance + distance_hfm_vfm))
    theta_kb = 3.5e-3 # KB mirrors incidence angle 
    
    drift0 = wpg.optical_elements.Drift(distance)
    drift_in_kb = wpg.optical_elements.Drift(distance_hfm_vfm)
    drift_to_foc = wpg.optical_elements.Drift(distance_foc)
    
    aperture = wpg.optical_elements.Aperture('r','a', 0.9*theta_kb, 0.9*theta_kb)
    hfm    = wpg.optical_elements.Mirror_elliptical(_p=distance, _q=(distance_hfm_vfm+distance_foc), _ang_graz=theta_kb,                                                     _r_sag=1.e+40, _size_tang=0.9, _nvx=cos(theta_kb),  _nvy=0,                                                     _nvz=-sin(theta_kb), _tvx=-sin(theta_kb), _tvy=0, _x=0, _y=0,                                                     _treat_in_out=1)     
    vfm    = wpg.optical_elements.Mirror_elliptical(_p=(distance+distance_hfm_vfm), _q=distance_foc, _ang_graz=theta_kb,                                                     _r_sag=1.e+40, _size_tang=0.9, _nvx=0, _nvy=cos(theta_kb),                                                     _nvz=-sin(theta_kb), _tvx=0, _tvy=-sin(theta_kb), _x=0, _y=0,                                                     _treat_in_out=1) 

    bl0 = wpg.Beamline()
    bl0.append(drift0,      Use_PP(semi_analytical_treatment=0, zoom=14.4, sampling=1/2.))
    bl0.append(aperture,    Use_PP(zoom=3.6, sampling=1/5.))
    bl0.append(hfm, Use_PP())
    bl0.append(drift_in_kb, Use_PP(semi_analytical_treatment=1))
    bl0.append(vfm, Use_PP())
    bl0.append(drift_to_foc, Use_PP(semi_analytical_treatment=1))
    if isIpynb:
        print bl0
    
    wpg.srwlib.srwl.SetRepresElecField(wf._srwl_wf, 'f')
    
    sz0 = get_intensity_on_axis(wf);
    wf.custom_fields['/misc/spectrum0'] = sz0
    
    bl0.propagate(wf)
    
    sz1 = get_intensity_on_axis(wf);
    wf.custom_fields['/misc/spectrum1'] = sz1
    
    wpg.srwlib.srwl.SetRepresElecField(wf._srwl_wf, 't')

    #Resizing: decreasing Range of Horizontal and Vertical Position:
    wpg.srwlib.srwl.ResizeElecField(wf._srwl_wf, 'c', [0, 0.25, 1, 0.25,  1]);
    
    fwhm = calculate_fwhm(wf)
    
    wf.custom_fields['/misc/xFWHM'] = fwhm['fwhm_x']
    wf.custom_fields['/misc/yFWHM'] = fwhm['fwhm_y']
    wf.custom_fields['/params/beamline/printout'] = str(bl0)
    
    wf.custom_fields['/info/contact'] = [
        'Name: Liubov Samoylova', 'Email: liubov.samoylova@xfel.eu',
        'Name: Alexey Buzmakov', 'Email: buzmakov@gmail.com']
    wf.custom_fields['/info/data_description'] = 'This dataset contains infromation about wavefront propagated through beamline (WPG and SRW frameworks).'
    wf.custom_fields['/info/method_description'] = """WPG, WaveProperGator (http://github.com/samoylv/WPG)is an interactive simulation framework for coherent X-ray wavefront propagation.\nSRW, Synchrotron Radiation Workshop (http://github.com/ochubar/SRW),  is a physical optics computer code  for simulation of the radiation wavefront propagation through optical systems of beamlines as well as  detailed characteristics of Synchrotron Radiation (SR) generated by relativistic electrons in magnetic fields of arbitrary configuration."""
    wf.custom_fields['/info/package_version'] = '2014.1'
    
    print('Saving the wavefront data after propagation:' + out_fname)
    mkdir_p(os.path.dirname(out_fname))
    wf.store_hdf5(out_fname)
    add_history(out_fname, in_fname)


# In[ ]:

def propagate_wrapper(params):
    """
    Wrapper for passing parameters as a tupple from multiprocessing module
    """
    (in_fname, out_fname) = params
    return propagate(in_fname, out_fname)


# In[ ]:

def directory_process(in_dname, out_dname, cpu_number):
    """
    Process directory with in_dname\FELsource_out*.h5 files and store it after propagation in out_dname\prop_out*.h5 files
    
    :param in_dname: input directory name
    :param out_dname: ouput directory name
    :param cpu_number: NUmber of CPUs for parallel computing
    
    """
    input_dir = in_dname
    input_files = glob(os.path.join(input_dir, 'FELsource_out*.h5'))
    out_files = []
    for name in input_files:
        in_file_name = os.path.split(name)[-1]
        out_file_name = in_file_name.replace('FELsource_out','prop_out')
        print 'out_file_name:',out_file_name
        out_files.append(os.path.join(out_dname, out_file_name))
    
    print 'Found {} HDF5 files in {}'.format(len(input_files), in_dname)
    
    batch_params = zip(input_files, out_files)
    
    p=multiprocessing.Pool(processes=cpu_number)
#     map(propagate_wrapper, batch_params)
    p.map(propagate_wrapper, batch_params, chunksize=1)
    p.close()
    p.join()


# In[ ]:

def main():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--input-file", dest="in_fname", help="Input wavefront file")
    parser.add_option("--output-file", dest="out_fname", help="Output wavefront file")
    
    parser.add_option("--input-directory", dest="in_dname", help="Input directory with wavefront files")
    parser.add_option("--output-directory", dest="out_dname", help="Output directory with wavefront files")
    parser.add_option("-n", "--cpu-number", dest="cpu_number", default=int((multiprocessing.cpu_count()+1)/2),
                      help="Number of cores for batch wavefronts propagation, default value NUMBER_OF_CPU/2")

    (options, args) = parser.parse_args()
    
    
    if not (options.in_fname or options.in_dname):   # if filename is not given
        parser.error('Input filename or directiry not specified, use --input-file or --input-directory options')
        return 
    
    if not (options.out_fname or options.out_dname):   # if filename is not given
        parser.error('Output filename or directiry not specified, use --output-file or --output-directory options')
        return
    
    if options.in_dname and options.out_dname:
        print 'Input directory {}, output directory {}, number of cores {}'.format(
            options.in_dname, options.out_dname, options.cpu_number)
        print 'Batch propagation started'
        directory_process(options.in_dname, options.out_dname, int(options.cpu_number))
        print 'Batch propagation finished'
        
    elif options.in_fname and options.out_fname:
        print 'Input file {}, output file {}'.format(options.in_fname, options.out_fname)
        propagate(options.in_fname, options.out_fname)


# In[ ]:

if not isIpynb:
    if __name__ == '__main__':
        main()
else:
    FID = 2
    data_dir = '/diskmnt/a/exflwgs03/lsamoylv/code/sim_data'
    in_fname  = data_dir + '/FELsource/FELsource_out_' + str(FID).zfill(7) + '.h5'
    out_fname = data_dir + '/prop/prop_out_'           + str(FID).zfill(7) + '.h5'
    propagate(in_fname, out_fname)


# In[ ]:

#A.B. testing commands
# !rm simulation_test/prop/*
# directory_process('simulation_test/FELsource/','simulation_test/prop/',4)

