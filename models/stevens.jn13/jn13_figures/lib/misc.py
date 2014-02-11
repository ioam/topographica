"""
Misc

A small number of helper functions used for convolving image patches
and for displaying data in IPython Notebook.
"""

import numpy as np
import os, math, glob
import Image
import imagen

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

anisotropic_kernel = imagen.Gaussian(aspect_ratio=10.0, size=0.05, xdensity=128, ydensity=128,
                                     orientation=math.pi/2.0)

def generate_GR(images_dir, kernel_pattern=anisotropic_kernel,
                name='V_GR', trim=True):
    """
    Generates a convolved dataset using the given kernel. Returns a
    list of the convolved image filenames.

    If no kernel is supplied, uses the default kernel of vertical
    anisotropic blur to simulate the vertical goggle rearing
    condition.
    """
    convolved_files = []
    shouval_files = glob.glob(os.path.join(images_dir, 'shouval','combined*.png'))
    for filename in sorted(shouval_files):
        basepath, ext = os.path.splitext(filename)
        savename = '%s_%s%s' % (os.path.basename(basepath), name, ext)
        savedir = os.path.join(images_dir, name)
        if not os.path.isdir(savedir): os.makedirs(savedir)
        save_path = os.path.join(savedir, savename)
        convolve(filename, kernel_pattern,trim=trim).save(save_path, format='png')
        convolved_files.append(save_path)
    return convolved_files
