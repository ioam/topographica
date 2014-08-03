"""
Line-based and matrix-based plotting commands using MatPlotLib.

Before importing this file, you will probably want to do something
like:

  from matplotlib import rcParams
  rcParams['backend']='TkAgg'

to select a backend, or else select an appropriate one in your
matplotlib.rc file (if any).  There are many backends available for
different GUI or non-GUI uses.
"""

try:
    from matplotlib import pylab as plt
except ImportError:
    import param
    param.Parameterized(name=__name__).warning("Could not import matplotlib; module will not be useable.")
    from topo.command import ImportErrorRaisingFakeModule
    plt = ImportErrorRaisingFakeModule("matplotlib")  # pyflakes:ignore (try/except import)

import param

import numpy as np
from numpy.fft.fftpack import fft2
from numpy.fft.helper import fftshift

import topo
from topo.base.sheet import Sheet
from topo.base.arrayutil import wrap

from topo.plotting.plot import make_template_plot
from param import ParameterizedFunction, normalize_path
from param.parameterized import ParamOverrides

from dataviews import DataOverlay
from dataviews.plots import DataPlot, GridLayout, CurvePlot

from topo.command import Command



class PylabPlotCommand(Command):
    """Parameterized command for plotting using Matplotlib/Pylab."""

    file_dpi = param.Number(
        default=100.0,bounds=(0,None),softbounds=(0,1000),doc="""
        Default DPI when rendering to a bitmap.
        The nominal size * the dpi gives the final image size in pixels.
        E.g.: 4"x4" image * 80 dpi ==> 320x320 pixel image.""")

    file_format = param.String(default="png",doc="""
        Which image format to use when saving images.
        The output can be png, ps, pdf, svg, or any other format
        supported by Matplotlib.""")

    # JABALERT: Should replace this with a filename_format and
    # associated parameters, as in PlotGroupSaver.
    # Also should probably allow interactive display to be controlled
    # separately from the filename, to make things work more similarly
    # with and without a GUI.
    filename = param.String(default=None,doc="""
        Optional base of the filename to use when saving images;
        if None the plot will be displayed interactively.

        The actual name is constructed from the filename base plus the
        suffix plus the current simulator time plus the file_format.""")

    filename_suffix = param.String(default="",doc="""
        Optional suffix to be used for disambiguation of the filename.""")

    title = param.String(default=None,doc="""
        Optional title to be used when displaying the plot interactively.""")

    display_window = param.Boolean(default=True, doc="""
        Whether to open a display window containing the plot when
        Topographica is running in a non-batch mode.""")

    __abstract = True


    def _set_windowtitle(self,title):
        """
        Helper function to set the title (if not None) of this PyLab plot window.
        """

        # At the moment, PyLab does not offer a window-manager-independent
        # means for controlling the window title, so what we do is to try
        # what should work with Tkinter, and then suppress all errors.  That
        # way we should be ok when rendering to a file-based backend, but
        # will get nice titles in Tk windows.  If other toolkits are in use,
        # the title can be set here using a similar try/except mechanism, or
        # else there can be a switch based on the backend type.
        if title is not None:
            try:
                manager = plt.get_current_fig_manager()
                manager.window.title(title)
            except:
                pass


    def _generate_figure(self,p):
        """
        Helper function to display a figure on screen or save to a file.

        p should be a ParamOverrides instance containing the current
        set of parameters.
        """

        plt.show._needmain=False
        if p.filename is not None:
            # JABALERT: need to reformat this as for other plots
            fullname=p.filename+p.filename_suffix+str(topo.sim.time())+"."+p.file_format
            plt.savefig(normalize_path(fullname), dpi=p.file_dpi)
        elif p.display_window:
            self._set_windowtitle(p.title)
            plt.show()
        else:
            plt.close(plt.gcf())



class vectorplot(PylabPlotCommand):
    """
    Simple line plotting for any vector or list of numbers.

    Intended for interactive debugging or analyzing from the command
    prompt.  See MatPlotLib's pylab functions to create more elaborate
    or customized plots; this is just a simple example.

    An optional string can be supplied as a title for the figure, if
    desired.  At present, this is only used for the window, not the
    actual body of the figure (and will thus not appear when the
    figure is saved).

    The style argument allows different line/linespoints style for
    the plot: 'r-' for red solid line, 'bx' for blue x-marks, etc.
    See http://matplotlib.sourceforge.net/matplotlib.pylab.html#-plot
    for more possibilities.

    The label argument can be used to identify the line in a figure legend.

    Ordinarily, the x value for each point on the line is the index of
    that point in the vec array, but a explicit list of xvalues can be
    supplied; it should be the same length as vec.

    Execution of multiple vectorplot() commands with different styles
    will result in all those styles overlaid on a single plot window.
    """

    # JABALERT: All but the first two arguments should probably be Parameters
    def __call__(self,vec,xvalues=None,style='-',label=None,**params):
        p=ParamOverrides(self,params)

        fig = plt.figure()
        if xvalues is not None:
            plt.plot(xvalues, vec, style, label=label)
        else:
            plt.plot(vec, style, label=label)

        plt.grid(True)
        self._generate_figure(p)
        return fig



class matrixplot(PylabPlotCommand):
    """
    Simple plotting for any matrix as a bitmap with axes.

    Like MatLab's imagesc, scales the values to fit in the range 0 to 1.0.
    Intended for interactive debugging or analyzing from the command
    prompt.  See MatPlotLib's pylab functions to create more elaborate
    or customized plots; this is just a simple example.
    """

    plot_type = param.Callable(default=plt.gray,doc="""
        Matplotlib command to generate the plot, e.g. plt.gray or plt.hsv.""")

    extent = param.Parameter(default=None,doc="""
        Subregion of the matrix to plot, as a tuple (l,b,r,t).""")

    # JABALERT: All but the first two should probably be Parameters
    def __call__(self, mat, aspect=None, colorbar=True, **params):
        p = ParamOverrides(self, params)

        fig = plt.figure(figsize=(5, 5))
        p.plot_type()

        # Swap lbrt to lrbt to match pylab
        if p.extent is None:
            extent = None
        else:
            (l, b, r, t) = p.extent
            extent = (l, r, b, t)

        plt.imshow(mat, interpolation='nearest', aspect=aspect, extent=extent)
        if colorbar and (mat.min() != mat.max()): plt.colorbar()
        self._generate_figure(p)
        return fig


class matrixplot3d(PylabPlotCommand):
    """
    Simple plotting for any matrix as a 3D wireframe with axes.

    Uses Matplotlib's beta-quality features for 3D plotting.  These
    usually work fine for wireframe plots, although they don't always
    format the axis labels properly, and do not support removal of
    hidden lines.  Note that often the plot can be rotated within the
    window to make such problems go away, and then the best result can
    be saved if needed.

    Other than the default "wireframe", the type can be "contour" to
    get a contour plot, or "surface" to get a solid surface plot, but
    surface plots currently fail in many cases, e.g. for small
    matrices.

    If you have trouble, you can try matrixplot3d_gnuplot instead.
    """

    def __call__(self, mat, type="wireframe", **params):
        p = ParamOverrides(self, params)

        from mpl_toolkits.mplot3d import axes3d

        fig = plt.figure()
        ax = axes3d.Axes3D(fig)

        # Construct matrices for r and c values
        rn, cn = mat.shape
        c = np.outer(np.ones(rn), np.arange(cn * 1.0))
        r = np.outer(np.arange(rn * 1.0), np.ones(cn))

        if type == "wireframe":
            ax.plot_wireframe(r, c, mat)
        elif type == "surface":
            # Sometimes fails for no obvious reason
            ax.plot_surface(r, c, mat)
        elif type == "contour":
            # Works but not usually very useful
            ax.contour3D(r, c, mat)
        else:
            raise ValueError("Unknown plot type " + str(type))

        ax.set_xlabel('R')
        ax.set_ylabel('C')
        ax.set_zlabel('Value')

        self._generate_figure(p)


class matrixplot3dx3(PylabPlotCommand):
    """
    Plot three matching matrices x,y,z as a 3D wireframe with axes.
    See matrixplot3d for caveats and description; this plot is the
    same but instead of using implicit r,c values of the matrix, allows
    them to be specified directly, thus plotting a series of 3D points.
    """

    def __call__(self,x,y,z,labels=["X","Y","Z"],type="wireframe",**params):
        p = ParamOverrides(self, params)

        from mpl_toolkits.mplot3d import axes3d

        fig = plt.figure()
        ax = axes3d.Axes3D(fig)

        if type == "wireframe":
            ax.plot_wireframe(x, y, z)
        elif type == "surface":
            ax.plot_surface(x, y, z)
        elif type == "contour":
            ax.contour3D(x, y, z)
        else:
            raise ValueError("Unknown plot type " + str(type))

        ax.set_xlabel(labels[0])
        ax.set_ylabel(labels[1])
        ax.set_zlabel(labels[2])

        self._generate_figure(p)
        return fig


class histogramplot(PylabPlotCommand):
    """
    Compute and plot the histogram of the supplied data.

    See help(plt.hist) for help on the histogram function itself.

    If given, colors is an iterable collection of matplotlib.colors
    (see help (matplotlib.colors) ) specifying the bar colors.

    Example use:
        histogramplot([1,1,1,2,2,3,4,5],title='hist',colors='rgb',bins=3,normed=1)
    """

    # JABALERT: All but the first two arguments should probably be Parameters
    def __call__(self, data, colors=None, **params):
        p = ParamOverrides(self, params, allow_extra_keywords=True)

        fig = plt.figure(figsize=(4, 2))
        n, bins, bars = plt.hist(data, **(p.extra_keywords()))

        # if len(bars)!=len(colors), any extra bars won't have their
        # colors changed, or any extra colors will be ignored.
        if colors: [bar.set_fc(color) for bar, color in zip(bars, colors)]

        self._generate_figure(p)
        return fig


class gradientplot(matrixplot):
    """
    Compute and show the gradient plot of the supplied data.
    Translated from Octave code originally written by Yoonsuck Choe.

    If the data is specified to be cyclic, negative differences will
    be wrapped into the range specified (1.0 by default).
    """

    # JABALERT: All but the first two arguments should probably be Parameters
    def __call__(self, data, cyclic_range=1.0, **params):
        p = ParamOverrides(self, params)

        r, c = data.shape
        dx = np.diff(data, 1, axis=1)[0:r - 1, 0:c - 1]
        dy = np.diff(data, 1, axis=0)[0:r - 1, 0:c - 1]

        if cyclic_range is not None: # Wrap into the specified range
            # Convert negative differences to an equivalent positive value
            dx = wrap(0, cyclic_range, dx)
            dy = wrap(0, cyclic_range, dy)
            #
            # Make it increase as gradient reaches the halfway point,
            # and decrease from there
            dx = 0.5 * cyclic_range - np.abs(dx - 0.5 * cyclic_range)
            dy = 0.5 * cyclic_range - np.abs(dy - 0.5 * cyclic_range)

        return super(gradientplot, self).__call__(np.sqrt(dx*dx + dy*dy), **p)



class fftplot(matrixplot):
    """
    Compute and show the 2D Fast Fourier Transform (FFT) of the supplied data.

    Example:: fftplot(topo.sim["V1"].views.Maps["OrientationPreference"].data,filename="out")
    """

    def __call__(self, data, **params):
        p = ParamOverrides(self, params)
        fft_plot = 1 - np.abs(fftshift(fft2(data - 0.5, s=None, axes=(-2, -1))))
        return super(fftplot, self).__call__(fft_plot, **p)


class autocorrelationplot(matrixplot):
    """
    Compute and show the 2D autocorrelation of the supplied data.
    Requires the external SciPy package.

    Example:: autocorrelationplot(topo.sim["V1"].views.Maps["OrientationPreference"].data,filename="out")
    """

    plot_type = param.Callable(default=plt.autumn)

    def __call__(self, data, **params):
        p = ParamOverrides(self, params)
        import scipy.signal

        mat = scipy.signal.correlate2d(data, data)
        return super(autocorrelationplot, self).__call__(mat, **p)


class activityplot(matrixplot):
    """
    Plots the activity in a sheet with axis labels in Sheet (not matrix) coordinates.

    Same as matrixplot, but only for matrices associated with a Sheet.
    By default plots the Sheet's activity, but any other matrix of the
    same size may be supplied for plotting in these coordinates instead.
    """

    def __call__(self, sheet, mat=None, **params):
        p = ParamOverrides(self, params)
        if p.extent is None: p.extent = sheet.bounds.aarect().lbrt()
        if mat is None: mat = sheet.activity
        return super(activityplot, self).__call__(mat, **p)


class xy_grid(PylabPlotCommand):
   """
    By default, plot the x and y coordinate preferences as a grid.
    """

   axis = param.Parameter(default=[-0.5,0.5,-0.5,0.5],doc="""
        Four-element list of the plot bounds, i.e. [xmin, xmax, ymin, ymax].""")

   skip = param.Integer(default=1,bounds=[1,None],softbounds=[1,10],doc="""
        Plot every skipth line in each direction.
        E.g. skip=4 means to keep only every fourth horizontal line
        and every fourth vertical line, except that the first and last
        are always included. The default is to include all data points.""")

   x = param.Array(doc="Numpy array of x positions in the grid.")

   y = param.Array(doc= "Numpy array of y positions in the grid." )

   def __call__(self, **params):

       p = ParamOverrides(self, params)
       fig = plt.figure(figsize=(5, 5))

       # This one-liner works in Octave, but in matplotlib it
       # results in lines that are all connected across rows and columns,
       # so here we plot each line separately:
       #   plt.plot(x,y,"k-",transpose(x),transpose(y),"k-")
       # Here, the "k-" means plot in black using solid lines;
       # see matplotlib for more info.
       isint = plt.isinteractive() # Temporarily make non-interactive for
       # plotting
       plt.ioff()
       for r, c in zip(p.y[::p.skip], p.x[::p.skip]):
           plt.plot(c, r, "k-")
       for r, c in zip(np.transpose(p.y)[::p.skip],np.transpose(p.x)[::p.skip]):
           plt.plot(c, r, "k-")

       # Force last line avoid leaving cells open
       if p.skip != 1:
           plt.plot(p.x[-1], p.y[-1], "k-")
           plt.plot(np.transpose(p.x)[-1], np.transpose(p.y)[-1], "k-")

       plt.xlabel('x')
       plt.ylabel('y')
       # Currently sets the input range arbitrarily; should presumably figure out
       # what the actual possible range is for this simulation (which would presumably
       # be the maximum size of any GeneratorSheet?).
       plt.axis(p.axis)

       if isint: plt.ion()
       self._generate_figure(p)
       return fig


class topographic_grid(xy_grid):
    """
    By default, plot the XPreference and YPreference preferences for all
    Sheets for which they are defined, using MatPlotLib.

    If sheet_views other than XPreference and YPreference are desired,
    the names of these can be passed in as arguments.
    """

    xsheet_view_name = param.String(default='XPreference',doc="""
        Name of the SheetView holding the X position locations.""")

    ysheet_view_name = param.String(default='YPreference',doc="""
        Name of the SheetView holding the Y position locations.""")

    # Disable and hide parameters inherited from the base class
    x = param.Array(constant=True, precedence=-1)
    y = param.Array(constant=True, precedence=-1)

    def __call__(self, **params):
        p = ParamOverrides(self, params)

        for sheet in topo.sim.objects(Sheet).values():
            if ((p.xsheet_view_name in sheet.views.Maps) and
                    (p.ysheet_view_name in sheet.views.Maps)):
                x = sheet.views.Maps[p.xsheet_view_name].last.data
                y = sheet.views.Maps[p.ysheet_view_name].last.data

                filename_suffix = "_" + sheet.name
                title = 'Topographic mapping to ' + sheet.name + ' at time ' \
                        + topo.sim.timestr()
                super(topographic_grid, self).__call__(x=x, y=y, title=title,
                                                       filename_suffix=filename_suffix)


class overlaid_plot(PylabPlotCommand):
   """
    Use matplotlib to make a plot combining a bitmap and line-based
    overlays for a single plot template and sheet.
    """

   plot_template = param.Dict(default={'Hue': 'OrientationPreference'}, doc="""
        Template for the underlying bitmap plot.""")

   overlay = param.List(default=[('contours', 'OcularPreference', 0.5, 'black'),
                                 ('arrows', 'DirectionPreference',
                                  'DirectionSelectivity', 'white')],
                        doc="""
        List of overlaid plots, where each list item may be a 4-tuple
        specifying either a contour line or a field of arrows::

          ('contours',map-name,contour-value,line-color)

          ('arrows',arrow-location-map-name,arrow-size-map-name,arrow-color)

        Any number or combination of contours and arrows may be supplied.""")

   normalize = param.Boolean(default='Individually', doc="""
        Type of normalization, if any, to use. Options include 'None',
        'Individually', and 'AllTogether'. See
        topo.plotting.plotgroup.TemplatePlotGroup.normalize for more
        details.""")

   sheet = param.ClassSelector(class_=topo.base.sheet.Sheet, doc="""
        The sheet from which sheetViews are to be obtained for plotting.""")

   def __call__(self, **params):

       p=ParamOverrides(self,params)
       name=p.plot_template.keys().pop(0)
       plot=make_template_plot(p.plot_template,
                               p.sheet.views.Maps, p.sheet.xdensity,p.sheet.bounds,
                               p.normalize,name=p.plot_template[name])
       fig = plt.figure(figsize=(5,5))
       if plot:
           bitmap=plot.bitmap
           isint=plt.isinteractive() # Temporarily make non-interactive for plotting
           plt.ioff()                                         # Turn interactive mode off

           plt.imshow(bitmap.image,origin='lower',interpolation='nearest')
           plt.axis('off')

           for (t,pref,sel,c) in p.overlay:
               v = plt.flipud(p.sheet.views.Maps[pref].view()[0])
               if (t=='contours'):
                   plt.contour(v,[sel,sel],colors=c,linewidths=2)

               if (t=='arrows'):
                   s = plt.flipud(p.sheet.views.Maps[sel].view()[0])
                   scale = int(np.ceil(np.log10(len(v))))
                   X = np.array([x for x in xrange(len(v)/scale)])
                   v_sc = np.zeros((len(v)/scale,len(v)/scale))
                   s_sc = np.zeros((len(v)/scale,len(v)/scale))
                   for i in X:
                       for j in X:
                           v_sc[i][j] = v[scale*i][scale*j]
                           s_sc[i][j] = s[scale*i][scale*j]
                   plt.quiver(scale*X, scale*X, -np.cos(2*np.pi*v_sc)*s_sc,
                              -np.sin(2*np.pi*v_sc)*s_sc, color=c,
                              edgecolors=c, minshaft=3, linewidths=1)

           p.title='%s overlaid with %s at time %s' %(plot.name,pref,topo.sim.timestr())
           if isint: plt.ion()
           p.filename_suffix="_"+p.sheet.name
           self._generate_figure(p)
           return fig



class overlaid_plots(overlaid_plot):
    """
    Use matplotlib to make a plot combining a bitmap and line-based overlays.
    """

    plot_template = param.List(default=[{'Hue':'OrientationPreference'}],doc="""
        Template for the underlying bitmap plot.""")

    # Disable and hide parameters inherited from the base class
    sheet = param.ClassSelector(class_=topo.base.sheet.Sheet, constant=True,  precedence=-1)


    def __call__(self,**params):
        p=ParamOverrides(self,params)

        for template in p.plot_template:
            for sheet in topo.sim.objects(Sheet).values():
                if getattr(sheet, "measure_maps", False):
                    super(overlaid_plots, self).__call__(sheet=sheet, plot_template=template,
                                                         overlay=p.overlay, normalize=p.normalize)



class tuning_curve(PylabPlotCommand):
    """
    Plot a tuning curve for a feature, such as orientation, contrast, or size.

    The curve datapoints are collected from the curve_dict for
    the units at the specified coordinates in the specified sheet
    (where the units and sheet may be set by a GUI, using
    topo.analysis.featureresponses.UnitCurveCommand.sheet and
    topo.analysis.featureresponses.UnitCurveCommand.coords,
    or by hand).
    """

    center = param.Boolean(default=True, doc="""
        Centers the tuning curve around the maximally responding feature.""")

    coords = param.List(default=[(0 , 0)], doc="""
        List of coordinates of units to measure.""")

    group_by = param.List(default=['Contrast'], doc="""
        Feature dimensions for which curves are overlaid.""")

    legend = param.Boolean(default=True, doc="""
        Whether or not to include a legend in the plot.""")

    relative_labels = param.Boolean(default=False, doc="""
        Relabel the x-axis with values relative to the preferred.""")

    sheet = param.ObjectSelector(default=None, doc="""
        Name of the sheet to use in measurements.""")

    x_axis = param.String(default='', doc="""
        Feature to plot on the x axis of the tuning curve""")

    # Disable and hide parameters inherited from the base class
    coord = param.NumericTuple(constant=True,  precedence=-1)

    def __call__(self, **params):
        p = ParamOverrides(self, params, allow_extra_keywords=True)

        x_axis = p.x_axis.capitalize()
        stack = p.sheet.views.Curves[x_axis.capitalize()+"Tuning"]
        time = stack.dim_range('Time')[1]

        curves = []
        if stack.dimension_labels[0] == 'X':
            for coord in p.coords:
                x, y = coord
                current_stack = stack[x, y, time, :, :, :]
                curve_stack = current_stack.sample(X=x, Y=y).collate(p.x_axis.capitalize())
                curves.append(curve_stack.overlay_dimensions(p.group_by))
        else:
            current_stack = stack[time, :, :, :]
            curve_stack = current_stack.sample(coords=p.coords).collate(p.x_axis.capitalize())
            overlaid_curves = curve_stack.overlay_dimensions(p.group_by)
            if not isinstance(curves, GridLayout): curves = [overlaid_curves]

        figs = []
        for coord, curve in zip(p.coords,curves):
            fig = plt.figure()
            ax = plt.subplot(111)
            plot = DataPlot if isinstance(curve.last, DataOverlay) else CurvePlot
            plot(curve, center=p.center, relative_labels=p.relative_labels,
                 show_legend=p.legend)(ax)
            self._generate_figure(p, fig)
            figs.append((coord, fig))

        return figs


    def _generate_figure(self, p, fig):
        """
        Helper function to display a figure on screen or save to a file.

        p should be a ParamOverrides instance containing the current
        set of parameters.
        """

        plt.show._needmain=False
        if p.filename is not None:
            # JABALERT: need to reformat this as for other plots
            fullname=p.filename+p.filename_suffix+str(topo.sim.time())+"."+p.file_format
            fig.savefig(normalize_path(fullname), dpi=p.file_dpi)
        elif p.display_window:
            self._set_windowtitle(p.title)
            fig.show()
        else:
            fig.close()


cyclic_tuning_curve = tuning_curve

def cyclic_unit_tuning_curve(coord=(0, 0), **kwargs):
    return tuning_curve(coords=[coord], **kwargs)[0]



def plot_cfproj_mapping(dest,proj='Afferent',style='b-'):
    """
    Given a CF sheet receiving a CFProjection, plot
    the mapping of the dests CF centers on the src sheet.
    """
    if isinstance(dest,str):
        from topo import sim
        dest = sim[dest]
    plot_coord_mapping(dest.projections()[proj].coord_mapper,
                       dest,style=style)


# JABALERT: not sure whether this is currently used
def plot_coord_mapping(mapper,sheet,style='b-'):
    """
    Plot a coordinate mapping for a sheet.

    Given a CoordinateMapperFn (as for a CFProjection) and a sheet
    of the projection, plot a grid showing where the sheet's units
    are mapped.
    """

    from pylab import plot,hold,ishold

    xs = sheet.sheet_rows()
    ys = sheet.sheet_cols()

    hold_on = ishold()
    if not hold_on:
        plot()
    hold(True)

    for y in ys:
        pts = [mapper(x,y) for x in xs]
        plot([u for u,v in pts],
             [v for u,v in pts],
             style)

    for x in xs:
        pts = [mapper(x,y) for y in ys]
        plot([u for u,v in pts],
             [v for u,v in pts],
             style)

    hold(hold_on)

import types
__all__ = list(set([k for k,v in locals().items()
                    if isinstance(v,types.FunctionType) or
                    (isinstance(v,type) and issubclass(v,ParameterizedFunction))
                    and not v.__name__.startswith('_')]))
