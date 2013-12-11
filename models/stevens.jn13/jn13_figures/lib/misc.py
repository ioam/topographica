"""
Misc

A small number of helper functions used for convolving image patches
and for displaying data in IPython Notebook.
"""

import topo
import numpy as np
import os, copy, glob, math, json
import imagen
import pandas
import lancet
import Image

from topo.misc.commandline import gui

def open_gui():
    get_ipython().magic('%gui tk')
    gui(exit_on_quit=False)


def convolve(filename, kernel_pattern, trim=True):
    """
    Given a filename and a kernel pattern, returns the convolution of the image with the kernel
    as a PIL image.
    """
    kernel = kernel_pattern()
    im = Image.open(filename)
    im = im.convert(mode='RGB')
    arr_RGB = np.array(im)
    arr = arr_RGB[...,0]
    
    fft1 = np.fft.fft2(arr / 255.0)
    fft2 = np.fft.fft2(kernel, s=arr.shape)
    convolved_raw = np.fft.ifft2( fft1 * fft2).real
    k_rows, k_cols = kernel.shape
    rolled = np.roll(np.roll(convolved_raw, -(k_cols//2), axis=-1), -(k_rows//2), axis=-2)
    convolved = rolled / float(kernel.sum()) 
    if trim:
        padding = (arr.shape[0] - kernel.shape[0]) / 2
        width = arr.shape[0] - 2 * padding
        convolved = convolved[padding-1:padding+width, padding-1:padding+width]
    return Image.fromarray(np.uint8(convolved * 255.0))

def generate_GR(images_dir, kernel_pattern, name='V_GR', trim=True):
    """
    Generates a convolved dataset using the anisotropy given by the aspect_ratio
    """
    for filename in glob.glob(os.path.join(images_dir, 'shouval','combined*.png')):
        basepath, ext = os.path.splitext(filename)
        savename = '%s_%s%s' % (os.path.basename(basepath), name, ext)
        savedir = os.path.join(images_dir, name)
        if not os.path.isdir(savedir): os.makedirs(savedir)
        convolve(filename, kernel_pattern,trim=trim).save(os.path.join(savedir, savename), format='png')

# For viewing the model
def view_weights(projections, coords=(0,0), transpose=True):
    """
    View the weights for the given projection as a pandas DataFrame.
    """
    names = ['%s (%s to %s)' % (proj.name, proj.src.name, proj.dest.name) for proj in projections]
    views = [proj.get_view(*coords).top for proj in projections]
    dframe = pandas.DataFrame({'weights':views})
    labelled = dframe.set_index([names])
    lancet.ViewFrame(labelled.T if transpose else labelled)
    
def view_activities(sheets, coords=(0,0), transpose=True):
    """
    View the neural activities weights for a given sheet as a pandas DataFrame.
    """
    names = [sheet.name for sheet in sheets]
    dframe = pandas.DataFrame({'activities':sheets})
    labelled = dframe.set_index([names])
    lancet.ViewFrame(labelled.T if transpose else labelled)
    
def view_patterns(pattern, num=3, transpose=True, radius=1.0):
    """
    View num instances of the given Pattern Generator object as a
    pandas DataFrame.
    """
    bounds = imagen.boundingregion.BoundingBox(radius=radius)
    views = []
    pat = copy.deepcopy(pattern)
    topo.sim.state_push()
    for i in range(num):
        arr = pat(xdensity=256,  ydensity=256, bounds=bounds)
        views.append(imagen.views.SheetView(arr, bounds))
        # views.append(topo.base.sheetview.SheetView((..., bounds)))
        topo.sim.run(1)
    topo.sim.state_pop()
    dframe = pandas.DataFrame({'patterns':views})
    lancet.ViewFrame(dframe.T if transpose else dframe)




def cleanup_notebook(input_notebook, output_notebook):
    
    content = json.load(open(input_notebook, 'r'))

    for worksheet in content['worksheets']:
        for cell in worksheet['cells']:
            if cell['cell_type'] == 'code':
                outputs = []
                for output in cell['outputs']:
                    html = output.get('html',None)
                    if html and html[0].endswith("width:0%\">&nbsp;</div></div>"):
                        new_html = html[0].replace("width:0%", "width:100%")
                        #new_output = output.copy()
                        output['html'] = [new_html]
                        outputs.append(output)
                        continue
                    val = output.get('output_type',None)
                    if ((val is not None) and (val == 'display_data') 
                        and output.get("javascript", [""])[0].startswith("$('div#")): pass
                    else:
                        outputs.append(output)
                cell['outputs'] = outputs  
                
    json.dump(content, open(output_notebook, 'w'))
