"""
File saving routines for plots.

Typically called using save_plotgroup in commands/analysis.py, but these
objects can also be instantiated explicitly, to save a series of plots.
"""

import Image
import numpy

import param
from param import normalize_path

import topo


# Consider using PIL's ImageFont module

class PlotGroupSaver(param.Parameterized):
    """
    Allows a PlotGroup to be saved as a set of bitmap files on disk.
    """
    file_format = param.String(default="png",doc="""
        Bitmap image file format to use.""")

    filename_prefix = param.String(default="",doc="""
        Optional prefix that can be used in the filename_format command
        to disambiguate different simulations or conditions.""")

    filename_suffix = param.String(default="",doc="""
        Optional suffix that can be used in the filename_format command
        to disambiguate different simulations or conditions.""")

    filename_format = param.String(default=
        "%(filename_prefix)s%(basename)s_%(plot_label)s%(filename_suffix)s.%(file_format)s",doc="""
        Format string to use for generating filenames for plots.  This
        string will be evaluated in the context of a dictionary that
        defines various items commonly used when generating filenames,
        including::

          basename:    the default sim.basename(), usually name+time()
          time:        the current simulation time (topo.sim.time())
          sim_name:    the name of the current simulation (topo.sim.name)
          plot_label:  the label specfied in the PlotGroup for this plot
          file_format: the bitmap image file format for this type of plot
          plotgroup_name: the name of this PlotGroup
      """)
    # Should move this out of plotfilesaver to get the same filenames in the GUI.
    # Should also allow each template in topo/command/analysis.py to have a nice
    # short filename format, perhaps as an option.

    def __init__(self,plotgroup,**params):
        super(PlotGroupSaver,self).__init__(**params)
        self.plotgroup = plotgroup


    def strip(self,filename):
        """Strip inappropriate characters from a filename."""
        return filename\
            .replace('\n','_')\
            .replace('\t','_')\
            .replace(' ','_')\
            .replace('&','And')


    def filename(self,label,**params):
        """Calculate a specific filename from the filename_format."""
        varmap = dict(self.get_param_values())
        varmap.update(self.__dict__)
        varmap['basename']= topo.sim.basename()
        varmap['sim_name']= topo.sim.name
        varmap['time']=topo.sim.time()
        varmap['plot_label']=label
        varmap['plotgroup_name']=self.plotgroup.name
        varmap.update(params)

        return self.strip(self.filename_format % varmap)


    def save_to_disk(self,**params):
        for p,l in zip(self.plotgroup.plots,self.plotgroup.labels):
            p.bitmap.image.save(normalize_path(self.filename(l,**params)))






# Could move this elsewhere if it will be useful.
#
# Adapted from:
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/412982
def make_contact_sheet(imgs, (marl,mart,marr,marb), padding):
    """
    Make a contact sheet (image grid) from a 2D array of PIL images::

      imgs     2D array of images

      marl     The left margin in pixels
      mart     The top margin in pixels
      marr     The right margin in pixels
      marb     The bottom margin in pixels

      padding  The padding between images in pixels

    Returns a PIL image object.
    """
    # should make sure imgs is numpy array

    # CB: *** should do this in numpy without the conversion to list and back! ***
    nrows,ncols = imgs.shape
    i_widths  = numpy.array([i.size[0] for i in imgs.ravel()]).reshape(nrows,ncols)
    i_heights = numpy.array([i.size[1] for i in imgs.ravel()]).reshape(nrows,ncols)

    col_widths = i_widths.max(axis=0)
    row_heights = i_heights.max(axis=1)

    marw = marl+marr
    marh = mart+ marb

    padw = (ncols-1)*padding
    padh = (nrows-1)*padding

    isize = (col_widths.sum()+marw+padw, row_heights.sum()+marh+padh)

    # Create the new image. The background doesn't have to be white.
    white = (255,255,255)
    inew = Image.new('RGB',isize,white)

    # CB: should be replaced with a more numpy technique.
    for irow in range(nrows):
        for icol in range(ncols):
            # if different widths in a col, or different heights in a
            # row, each image will currently just go at top left
            # defined by largest in col/row (should be centered
            # instead)
            left = marl+col_widths[0:icol].sum()+icol*padding
            right = left+i_widths[irow,icol]
            upper = mart+row_heights[0:irow].sum()+irow*padding
            lower = upper+i_heights[irow,icol]
            inew.paste(imgs[irow,icol],(left,upper,right,lower))
    return inew




class CFProjectionPlotGroupSaver(PlotGroupSaver):
    """
    Allows a CFProjectionPlotGroup to be saved as a bitmap file,
    concatenating all the CF plots into a single image.
    """
    def save_to_disk(self,**params):
        imgs = numpy.array([p.bitmap.image
                            for p in self.plotgroup.plots],
                           dtype=object).reshape(
            self.plotgroup.proj_plotting_shape)
        img = make_contact_sheet(imgs, (3,3,3,3), 3)
        img.save(normalize_path(self.filename(
            self.plotgroup.sheet.name+"_"+
            self.plotgroup.projection.name,**params)))
