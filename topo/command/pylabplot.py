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

import param

try:
    import matplotlib.ticker
    from matplotlib import pylab as plt
except ImportError:
    param.Parameterized(name=__name__).warning("Could not import matplotlib; module will not be useable.")
    from topo.command import ImportErrorRaisingFakeModule
    plt = ImportErrorRaisingFakeModule("matplotlib")  # pyflakes:ignore (try/except import)

from math import pi

import numpy as np
from numpy.fft.fftpack import fft2
from numpy.fft.helper import fftshift

import topo
from topo.base.sheetview import SheetView
from topo.base.arrayutil import centroid, wrap
from topo.base.sheet import Sheet
from topo.misc.util import frange
import topo.analysis.vision
from topo.plotting.plot import make_template_plot
import param
from param import ParameterizedFunction,normalize_path
from param.parameterized import ParamOverrides
from topo.pattern import SineGrating, OrientationContrast
from topo.plotting.plotgroup import create_plotgroup
from topo.base.cf import CFSheet

from topo.analysis.featureresponses import Feature, PatternPresenter
from topo.analysis.featureresponses import PositionMeasurementCommand, FeatureCurveCommand, UnitCurveCommand


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
        else:
            self._set_windowtitle(p.title)
            plt.show()



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

        if xvalues is not None:
            plt.plot(xvalues, vec, style, label=label)
        else:
            plt.plot(vec, style, label=label)

        plt.grid(True)
        self._generate_figure(p)



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
    def __call__(self,mat,aspect=None,colorbar=True,**params):
        p=ParamOverrides(self,params)

        plt.figure(figsize=(5,5))
        p.plot_type()

        # Swap lbrt to lrbt to match pylab
        if p.extent is None:
            extent = None
        else:
            (l,b,r,t)=p.extent
            extent=(l,r,b,t)

        plt.imshow(mat,interpolation='nearest',aspect=aspect,extent=extent)
        if colorbar and (mat.min()!= mat.max()): plt.colorbar()
        self._generate_figure(p)


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

    def __call__(self,mat,type="wireframe",**params):
        p=ParamOverrides(self,params)

        from mpl_toolkits.mplot3d import axes3d

        fig = plt.figure()
        ax = axes3d.Axes3D(fig)

        # Construct matrices for r and c values
        rn,cn = mat.shape
        c = np.outer(np.ones(rn),np.arange(cn*1.0))
        r = np.outer(np.arange(rn*1.0),np.ones(cn))

        if type=="wireframe":
            ax.plot_wireframe(r,c,mat)
        elif type=="surface":
            # Sometimes fails for no obvious reason
            ax.plot_surface(r,c,mat)
        elif type=="contour":
            # Works but not usually very useful
            ax.contour3D(r,c,mat)
        else:
            raise ValueError("Unknown plot type "+str(type))

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
        p=ParamOverrides(self,params)
    
        from mpl_toolkits.mplot3d import axes3d

        fig = plt.figure()
        ax = axes3d.Axes3D(fig)
    
        if type=="wireframe":
            ax.plot_wireframe(x,y,z)
        elif type=="surface":
            ax.plot_surface(x,y,z)
        elif type=="contour":
            ax.contour3D(x,y,z)
        else:
            raise ValueError("Unknown plot type "+str(type))
            
        ax.set_xlabel(labels[0])
        ax.set_ylabel(labels[1])
        ax.set_zlabel(labels[2])
    
        self._generate_figure(p)



def matrixplot3d_gnuplot(mat,title=None,outputfilename="tmp.ps"):
    """
    Simple plotting for any matrix as a 3D surface with axes.

    Currently requires the gnuplot-py package to be installed, plus
    the external gnuplot program; likely to be removed once Matplotlib
    supports 3D plots better.

    Unlikely to work on non-UNIX systems.

    Should return when it completes, but for some reason the Topographica
    prompt is not available until this command finishes.
    """
    import Gnuplot
    from os import system

    psviewer="gv" # Should be a parameter, or handled better somehow
    g = Gnuplot.Gnuplot(debug=0) #debug=1: output commands to stderr
    r,c = mat.shape
    x = np.arange(r*1.0)
    y = np.arange(c*1.0)
    # The .tolist() command is necessary to avoid bug in gnuplot-py,
    # which will otherwise convert a 2D float array into integers (!)
    m = np.asarray(mat,dtype="float32").tolist()
    #g("set parametric")
    g("set data style lines")
    g("set hidden3d")
    g("set xlabel 'R'")
    g("set ylabel 'C'")
    g("set zlabel 'Value'")
    if title: g.title(title)

    if outputfilename:
        g("set terminal postscript eps color solid 'Times-Roman' 14")
        g("set output '"+outputfilename+"'")
        g.splot(Gnuplot.GridData(m,x,y, binary=1))
        #g.hardcopy(outputfilename, enhanced=1, color=1)
        system(psviewer+" "+outputfilename+" &")

    else:
        g.splot(Gnuplot.GridData(m,x,y, binary=1))
        raw_input('Please press return to continue...\n')



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
    def __call__(self,data,colors=None,**params):
        p=ParamOverrides(self,params,allow_extra_keywords=True)

        plt.figure(figsize=(4,2))
        n,bins,bars = plt.hist(data,**(p.extra_keywords()))

        # if len(bars)!=len(colors), any extra bars won't have their
        # colors changed, or any extra colors will be ignored.
        if colors: [bar.set_fc(color) for bar,color in zip(bars,colors)]

        self._generate_figure(p)



class gradientplot(matrixplot):
    """
    Compute and show the gradient plot of the supplied data.
    Translated from Octave code originally written by Yoonsuck Choe.

    If the data is specified to be cyclic, negative differences will
    be wrapped into the range specified (1.0 by default).
    """

    # JABALERT: All but the first two arguments should probably be Parameters
    def __call__(self,data,cyclic=True,cyclic_range=1.0,**params):
        p=ParamOverrides(self,params)

        r,c = data.shape
        dx = np.diff(data,1,axis=1)[0:r-1,0:c-1]
        dy = np.diff(data,1,axis=0)[0:r-1,0:c-1]

        if cyclic: # Wrap into the specified range
            # Convert negative differences to an equivalent positive value
            dx = wrap(0,cyclic_range,dx)
            dy = wrap(0,cyclic_range,dy)
            #
            # Make it increase as gradient reaches the halfway point,
            # and decrease from there
            dx = 0.5*cyclic_range-np.abs(dx-0.5*cyclic_range)
            dy = 0.5*cyclic_range-np.abs(dy-0.5*cyclic_range)

        super(gradientplot,self).__call__(np.sqrt(dx*dx+dy*dy),**p)



class fftplot(matrixplot):
    """
    Compute and show the 2D Fast Fourier Transform (FFT) of the supplied data.

    Example:: fftplot(topo.sim["V1"].sheet_views["OrientationPreference"].view()[0],filename="out")
    """

    def __call__(self,data,**params):
        p=ParamOverrides(self,params)
        fft_plot=1-np.abs(fftshift(fft2(data-0.5, s=None, axes=(-2,-1))))
        super(fftplot,self).__call__(fft_plot,**p)


class autocorrelationplot(matrixplot):
    """
    Compute and show the 2D autocorrelation of the supplied data.
    Requires the external SciPy package.

    Example:: autocorrelationplot(topo.sim["V1"].sheet_views["OrientationPreference"].view()[0],filename="out")
    """

    plot_type = param.Callable(default=plt.autumn)

    def __call__(self,data,**params):
        p=ParamOverrides(self,params)
        import scipy.signal
        mat=scipy.signal.correlate2d(data,data)
        super(autocorrelationplot,self).__call__(mat,**p)


class activityplot(matrixplot):
    """
    Plots the activity in a sheet with axis labels in Sheet (not matrix) coordinates.

    Same as matrixplot, but only for matrices associated with a Sheet.
    By default plots the Sheet's activity, but any other matrix of the
    same size may be supplied for plotting in these coordinates instead.
    """
    def __call__(self,sheet,mat=None,**params):
        p=ParamOverrides(self,params)
        if p.extent is None: p.extent=sheet.bounds.aarect().lbrt()
        if mat is None: mat = sheet.activity
        super(activityplot,self).__call__(mat,**p)



class topographic_grid(PylabPlotCommand):
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

    axis = param.Parameter(default=[-0.5,0.5,-0.5,0.5],doc="""
        Four-element list of the plot bounds, i.e. [xmin, xmax, ymin, ymax].""")

    skip = param.Integer(default=1,bounds=[1,None],softbounds=[1,10],doc="""
        Plot every skipth line in each direction.
        E.g. skip=4 means to keep only every fourth horizontal line
        and every fourth vertical line, except that the first and last
        are always included. The default is to include all data points.""")

    def __call__(self,**params):
        p=ParamOverrides(self,params)

        for sheet in topo.sim.objects(Sheet).values():
            if ((p.xsheet_view_name in sheet.sheet_views) and
                (p.ysheet_view_name in sheet.sheet_views)):

                x = sheet.sheet_views[p.xsheet_view_name].view()[0]
                y = sheet.sheet_views[p.ysheet_view_name].view()[0]

                plt.figure(figsize=(5,5))

                # This one-liner works in Octave, but in matplotlib it
                # results in lines that are all connected across rows and columns,
                # so here we plot each line separately:
                #   plt.plot(x,y,"k-",transpose(x),transpose(y),"k-")
                # Here, the "k-" means plot in black using solid lines;
                # see matplotlib for more info.
                isint=plt.isinteractive() # Temporarily make non-interactive for plotting
                plt.ioff()
                for r,c in zip(y[::p.skip],x[::p.skip]):
                    plt.plot(c,r,"k-")
                for r,c in zip(np.transpose(y)[::p.skip],np.transpose(x)[::p.skip]):
                    plt.plot(c,r,"k-")

                # Force last line avoid leaving cells open
                if p.skip != 1:
                    plt.plot(x[-1],y[-1],"k-")
                    plt.plot(np.transpose(x)[-1],np.transpose(y)[-1],"k-")

                plt.xlabel('x')
                plt.ylabel('y')
                # Currently sets the input range arbitrarily; should presumably figure out
                # what the actual possible range is for this simulation (which would presumably
                # be the maximum size of any GeneratorSheet?).
                plt.axis(p.axis)
                p.title='Topographic mapping to '+sheet.name+' at time '+topo.sim.timestr()

                if isint: plt.ion()
                p.filename_suffix="_"+sheet.name
                self._generate_figure(p)


class overlaid_plots(PylabPlotCommand):
    """
    Use matplotlib to make a plot combining a bitmap and line-based overlays.
    """

    plot_template = param.List(default=[{'Hue':'OrientationPreference'}],doc="""
        Template for the underlying bitmap plot.""")

    overlay = param.List(default=[('contours','OcularPreference',0.5,'black'),
                                ('arrows','DirectionPreference','DirectionSelectivity','white')],doc="""
        List of overlaid plots, where each list item may be a 4-tuple
        specifying either a contour line or a field of arrows::

          ('contours',map-name,contour-value,line-color)

          ('arrows',arrow-location-map-name,arrow-size-map-name,arrow-color)

        Any number or combination of contours and arrows may be supplied.""")

    normalize = param.Boolean(default='Individually',doc="""
        Type of normalization, if any, to use. Options include 'None',
        'Individually', and 'AllTogether'. See
        topo.plotting.plotgroup.TemplatePlotGroup.normalize for more
        details.""")


    def __call__(self,**params):
        p=ParamOverrides(self,params)

        for template in p.plot_template:

            for sheet in topo.sim.objects(Sheet).values():
                name=template.keys().pop(0)
                plot=make_template_plot(template,sheet.sheet_views,sheet.xdensity,sheet.bounds,p.normalize,name=template[name])
                if plot:
                    bitmap=plot.bitmap
                    plt.figure(figsize=(5,5))
                    isint=plt.isinteractive() # Temporarily make non-interactive for plotting
                    plt.ioff()                                         # Turn interactive mode off

                    plt.imshow(bitmap.image,origin='lower',interpolation='nearest')
                    plt.axis('off')

                    for (t,pref,sel,c) in p.overlay:
                        v = np.flipud(sheet.sheet_views[pref].view()[0])

                        if (t=='contours'):
                            plt.contour(v,[sel,sel],colors=c,linewidths=2)

                        if (t=='arrows'):
                            s = np.flipud(sheet.sheet_views[sel].view()[0])
                            scale=int(np.ceil(np.log10(len(v))))
                            X=np.array([x for x in xrange(len(v)/scale)])
                            v_sc=np.zeros((len(v)/scale,len(v)/scale))
                            s_sc=np.zeros((len(v)/scale,len(v)/scale))
                            for i in X:
                                for j in X:
                                    v_sc[i][j]=v[scale*i][scale*j]
                                    s_sc[i][j]=s[scale*i][scale*j]
                            plt.quiver(scale*X,scale*X,-np.cos(2*pi*v_sc)*s_sc,-np.sin(2*pi*v_sc)*s_sc,color=c,edgecolors=c,minshaft=3,linewidths=1)

                    p.title='%s overlaid with %s at time %s' %(plot.name,pref,topo.sim.timestr())
                    if isint: plt.ion()
                    p.filename_suffix="_"+sheet.name
                    self._generate_figure(p)



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

    coords = param.List(default=[(0,0)],doc="""
        List of coordinates of units to measure.""")

    sheet = param.ObjectSelector(
        default=None,doc="""
        Name of the sheet to use in measurements.""")

    x_axis = param.String(default="",doc="""
        Feature to plot on the x axis of the tuning curve""")

    # Can we list some alternatives here, if there are any
    # useful ones?
    plot_type = param.Callable(default=plt.plot,doc="""
        Matplotlib command to generate the plot.""")

    unit = param.String(default="",doc="""
        String to use in labels to specify the units in which curves are plotted.""")

    legend=param.Boolean(default=True, doc="""
        Whether or not to include a legend in the plot.""")

    __abstract = True


    def _format_x_tick_label(self,x):
        return "%3.1f" % x

    def _rotate(self, seq, n=1):
        n = n % len(seq) # n=hop interval
        return seq[n:] + seq[:n]

    def _curve_values(self, i_value, j_value, curve):
        """Return the x, y, and x ticks values for the specified curve from the curve_dict"""
        x_values=sorted(curve.keys())
        y_values=[curve[key].view()[0][i_value,j_value] for key in x_values]
        return x_values,y_values,x_values

    def _reduce_ticks(self,ticks):
        x = [];
        y=  [];
        num_ticks = 5;
        y.append(ticks[0])
        x.append(self.x_values[0])
        for i in xrange(0,num_ticks):
            y.append(y[-1]+np.pi/(num_ticks+1));
            x.append(x[-1]+np.pi/(num_ticks+1));
        y.append(y[-1]+np.pi/(num_ticks+1));
        x.append(self.x_values[-1])
        return (x,y)


    def __call__(self,**params):
        p=ParamOverrides(self,params)
        sheet = p.sheet
        for coordinate in p.coords:
            i_value,j_value=sheet.sheet2matrixidx(coordinate[0],coordinate[1])

            plt.figure(figsize=(7,7))
            isint=plt.isinteractive()
            plt.ioff()

            plt.ylabel('Response',fontsize='large')
            plt.xlabel('%s (%s)' % (p.x_axis.capitalize(),p.unit),fontsize='large')
            plt.title('Sheet %s, coordinate(x,y)=(%0.3f,%0.3f) at time %s' %
                        (sheet.name,coordinate[0],coordinate[1],topo.sim.timestr()))
            p.title='%s: %s Tuning Curve' % (topo.sim.name,p.x_axis.capitalize())

            self.first_curve=True
            for curve_label in sorted(sheet.curve_dict[p.x_axis].keys()):
                x_values,y_values,ticks=self._curve_values(i_value,j_value,sheet.curve_dict[p.x_axis][curve_label])

                x_tick_values,ticks = self._reduce_ticks(ticks)
                labels = [self._format_x_tick_label(x) for x in ticks]
                plt.xticks(x_tick_values, labels,fontsize='large')
                plt.yticks(fontsize='large')
                p.plot_type(x_values, y_values, label=curve_label,lw=3.0)
                self.first_curve=False

            if isint: plt.ion()
            if p.legend: plt.legend(loc=2)
            self._generate_figure(p)



class cyclic_tuning_curve(tuning_curve):
    """
    Same as tuning_curve, but rotates the curve so that minimum y
    values are at the minimum x value to make the plots easier to
    interpret.  Such rotation is valid only for periodic quantities
    like orientation or direction, and only if the correct period
    is set.

    At present, the y_values and labels are rotated by an amount
    determined by the minmum y_value for the first curve plotted
    (usually the lowest contrast curve).
    """

    cyclic_range = param.Number(default=pi,bounds=(0,None),softbounds=(0,10),doc="""
        Range of the cyclic quantity (e.g. pi for the orientation of
        a symmetric stimulus, or 2*pi for motion direction or the
        orientation of a non-symmetric stimulus).""")

    unit = param.String(default="degrees",doc="""
        String to use in labels to specify the units in which curves are plotted.""")

    recenter = param.Boolean(default=True,doc="""
        Centers the tuning curve around the maximally responding feature.""")

    def __call__(self,**params):
        p=ParamOverrides(self,params)
        if p.recenter:
            self.peak_argmax = 0
            sheet = p.sheet
            max_y = 0.0
            for coordinate in p.coords:
                i_value,j_value=sheet.sheet2matrixidx(coordinate[0],coordinate[1])
                for curve_label in sorted(sheet.curve_dict[p.x_axis].keys()):
                    x_values= sorted(sheet.curve_dict[p.x_axis][curve_label].keys())
                    y_values = [sheet.curve_dict[p.x_axis][curve_label][key].view()[0][i_value,j_value] for key in x_values]
                    if np.max(y_values) > max_y:
                        max_y = np.max(y_values)
                        self.peak_argmax = np.argmax(y_values)

        super(cyclic_tuning_curve,self).__call__(**p)


    # This implementation should work for quantities periodic with
    # some multiple of pi that we want to express in degrees, but it
    # will need to be reimplemented in a subclass to work with other
    # cyclic quantities.
    def _format_x_tick_label(self,x):
        return str(int(180*x/pi))


    def _curve_values(self, i_value, j_value, curve):
        """
        Return the x, y, and x ticks values for the specified curve from the curve_dict.

        With the current implementation, there may be cases (i.e.,
        when the lowest contrast curve gives a lot of zero y_values)
        in which the maximum is not in the center.  This may
        eventually be changed so that the preferred orientation is in
        the center.
        """
        if self.first_curve:
            x_values= sorted(curve.keys())
            y_values=[curve[key].view()[0][i_value,j_value] for key in x_values]

            if self.recenter:
                rotate_n = self.peak_argmax+len(x_values)/2
                y_values = self._rotate(y_values, n=rotate_n)
                self.ticks=self._rotate(x_values, n=rotate_n)
            else:
                self.ticks = list(x_values)

            self.ticks.append(self.ticks[0])
            x_values.append(x_values[0]+self.cyclic_range)
            y_values.append(y_values[0])
            self.x_values=x_values
        else:
            y_values=[curve[key].view()[0][i_value,j_value] for key in self.ticks]

        return self.x_values,y_values,self.ticks



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


# JABALERT: Untested as of Mon Nov 10 12:59:54 GMT 2008
class plot_tracked_attributes(PylabPlotCommand):
    """
    Plots parameter values associated with an AttributeTrackingTF.
    Example call:
    VT=AttributeTrackingTF(function=HE, debug_params=['a', 'b',], units=[(0,0),(1,1)], step=1)
    plot_tracked_attributes(VT,0,10000,attrib_names=['a'],units=[(0,0)], filename='V1')
    """

    # JABALERT: These parameters need to be documented.
    raw = param.Boolean(default=False)

    attrib_names = param.List(default=[])

    ylabel = param.String(default="")

    # Should be renamed to coords to match other commands
    units = param.List(default=[])

    ybounds = param.Parameter(default=(None,None))


    # JABALERT: All but the first two arguments should probably be Parameters
    def __call__(self,output_fn,init_time=0,final_time=None,**params):
        p=ParamOverrides(self,params)

        if final_time is None:
            final_time=topo.sim.time()

        attrs = p.attrib_names if len(p.attrib_names)>0 else output_fn.attrib_names
        for a in attrs:
            plt.figure(figsize=(6,4))
            isint=plt.isinteractive()
            plt.ioff()
            plt.grid(True)
            ylabel=p.ylabel
            plt.ylabel(a+" "+ylabel)
            plt.xlabel('Iteration Number')

            coords = p.units if len(p.units)>0 else output_fn.units
            for coord in coords:
                y_data=[y for (x,y) in output_fn.values[a][coord]]
                x_data=[x for (x,y) in output_fn.values[a][coord]]
                if p.raw==True:
                    plot_data=zip(x_data,y_data)
                    plt.save(normalize_path(p.filename+a+'(%.2f, %.2f)' %(coord[0], coord[1])),plot_data,fmt='%.6f', delimiter=',')


                plt.plot(x_data,y_data, label='Unit (%.2f, %.2f)' %(coord[0], coord[1]))
                (ymin,ymax)=p.ybounds
                plt.axis(xmin=init_time,xmax=final_time,ymin=ymin,ymax=ymax)

            if isint: plt.ion()
            plt.legend(loc=0)
            p.title=topo.sim.name+': '+a
            p.filename_suffix=a
            self._generate_figure(p)



# JABALERT: Should be updated to plot for a specified list of sheets,
# and then the combination of all of them, so that it will work for
# any network.  Will need to remove the simple_sheet_name and
# complex_sheet_name parameters once that works.
class plot_modulation_ratio(PylabPlotCommand):
    """
    This function computes the modulation ratios of neurons in the
    specified sheets and plots their histograms. See
    analysis.vision.complexity for more info.
    """

    # JABALERT: All but the first argument should probably be Parameters
    def __call__(self,fullmatrix,simple_sheet_name=None,complex_sheet_name=None,bins=frange(0,2.0,0.1,inclusive=True),**params):
        p=ParamOverrides(self,params)

        from topo.analysis.vision import complexity
        if (topo.sim.objects().has_key(simple_sheet_name) and topo.sim.objects().has_key(complex_sheet_name)):
            v1s = complexity(fullmatrix[topo.sim[simple_sheet_name]]).flatten()
            v1c = complexity(fullmatrix[topo.sim[complex_sheet_name]]).flatten()
            #double the number of complex cells to reflect large width of layer 2/3
            v1c = np.concatenate((np.array(v1c),np.array(v1c)),axis=1)
            plt.figure()
            n = plt.subplot(311)
            plt.hist(v1s,bins)
            plt.axis([0,2.0,0,4100])
	    n.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(3))

	    n = plt.subplot(312)
            plt.hist(v1c,bins)
            plt.axis([0,2.0,0,4100])
	    n.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(3))

	    n = plt.subplot(313)
            plt.hist(np.concatenate((np.array(v1s),np.array(v1c)),axis=1),bins)
            plt.axis([0,2.0,0,4100])
	    n.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(3))

        self._generate_figure(p)



class measure_position_pref(PositionMeasurementCommand):
    """Measure a position preference map by collating the response to patterns."""

    scale = param.Number(default=0.3)

    def _feature_list(self,p):
        width =1.0*p.x_range[1]-p.x_range[0]
        height=1.0*p.y_range[1]-p.y_range[0]
        return [Feature(name="x",range=p.x_range,step=width/p.divisions,preference_fn=self.preference_fn),
                Feature(name="y",range=p.y_range,step=height/p.divisions,preference_fn=self.preference_fn)]


from topo.misc.distribution import DSF_WeightedAverage
pg= create_plotgroup(name='Position Preference',category="Preference Maps",
           doc='Measure preference for the X and Y position of a Gaussian.',
           pre_plot_hooks=[measure_position_pref.instance(
            preference_fn=DSF_WeightedAverage( selectivity_scale=(0.,17.) ))],
           plot_hooks=[topographic_grid.instance()],
           normalize='Individually')

pg.add_plot('X Preference',[('Strength','XPreference')])
pg.add_plot('Y Preference',[('Strength','YPreference')])
pg.add_plot('Position Preference',[('Red','XPreference'),
                                   ('Green','YPreference')])



class measure_cog(ParameterizedFunction):
    """
    Calculate center of gravity (CoG) for each CF of each unit in each CFSheet.

    Unlike measure_position_pref and other measure commands, this one
    does not work by collating the responses to a set of input patterns.
    Instead, the CoG is calculated directly from each set of incoming
    weights.  The CoG value thus is an indirect estimate of what
    patterns the neuron will prefer, but is not limited by the finite
    number of test patterns as the other measure commands are.

    Measures only one projection for each sheet, as specified by the
    proj_name parameter.  The default proj_name of '' selects the
    first non-self connection, which is usually useful to examine for
    simple feedforward networks, but will not necessarily be useful in
    other cases.
    """

    proj_name = param.String(default='',doc="""
        Name of the projection to measure; the empty string means 'the first
        non-self connection available'.""")

    def __call__(self,**params):
        p=ParamOverrides(self,params)

        measured_sheets = [s for s in topo.sim.objects(CFSheet).values()
                           if hasattr(s,'measure_maps') and s.measure_maps]

        # Could easily be extended to measure CoG of all projections
        # and e.g. register them using different names (e.g. "Afferent
        # XCoG"), but then it's not clear how the PlotGroup would be
        # able to find them automatically (as it currently supports
        # only a fixed-named plot).
        requested_proj=p.proj_name
        for sheet in measured_sheets:
            for proj in sheet.in_connections:
                if (proj.name == requested_proj) or \
                   (requested_proj == '' and (proj.src != sheet)):
                    self._update_proj_cog(proj)
                    if requested_proj=='':
                        print "measure_cog: Measured %s projection %s from %s" % \
                              (proj.dest.name,proj.name,proj.src.name)
                        break


    def _update_proj_cog(self,proj):
        """Measure the CoG of the specified projection and register corresponding SheetViews."""

        sheet=proj.dest
        rows,cols=sheet.activity.shape
        xpref=np.zeros((rows,cols),np.float64)
        ypref=np.zeros((rows,cols),np.float64)

        for r in xrange(rows):
            for c in xrange(cols):
                cf=proj.cfs[r,c]
                r1,r2,c1,c2 = cf.input_sheet_slice
                row_centroid,col_centroid = centroid(cf.weights)
                xcentroid, ycentroid = proj.src.matrix2sheet(
                        r1+row_centroid+0.5,
                        c1+col_centroid+0.5)

                xpref[r][c]= xcentroid
                ypref[r][c]= ycentroid

                sheet.sheet_views['XCoG']=SheetView((xpref,sheet.bounds), sheet.name,
                                                    sheet.precedence,topo.sim.time(),sheet.row_precedence)

                sheet.sheet_views['YCoG']=SheetView((ypref,sheet.bounds), sheet.name,
                                                    sheet.precedence,topo.sim.time(),sheet.row_precedence)


pg= create_plotgroup(name='Center of Gravity',category="Preference Maps",
             doc='Measure the center of gravity of each ConnectionField in a Projection.',
             pre_plot_hooks=[measure_cog.instance()],
             plot_hooks=[topographic_grid.instance(xsheet_view_name="XCoG",ysheet_view_name="YCoG")],
             normalize='Individually')
pg.add_plot('X CoG',[('Strength','XCoG')])
pg.add_plot('Y CoG',[('Strength','YCoG')])
pg.add_plot('CoG',[('Red','XCoG'),('Green','YCoG')])


class measure_or_tuning_fullfield(FeatureCurveCommand):
    """
    Measures orientation tuning curve(s) of a particular unit using a
    full-field sine grating stimulus.

    The curve can be plotted at various different values of the
    contrast (or actually any other parameter) of the stimulus.  If
    using contrast and the network contains an LGN layer, then one
    would usually specify michelson_contrast as the
    contrast_parameter. If there is no explicit LGN, then scale
    (offset=0.0) can be used to define the contrast.  Other relevant
    contrast definitions (or other parameters) can also be used,
    provided they are defined in PatternPresenter and the units
    parameter is changed as appropriate.
    """

    coords = param.Parameter(default=None,doc="""Ignored; here just to suppress warning.""")

    pattern_presenter = param.Callable(
        default=PatternPresenter(pattern_generator=SineGrating(),
                                 contrast_parameter="michelson_contrast"))


create_plotgroup(template_plot_type="curve",name='Orientation Tuning Fullfield',category="Tuning Curves",doc="""
            Plot orientation tuning curves for a specific unit, measured using full-field sine gratings.
            Although the data takes a long time to collect, once it is ready the plots
            are available immediately for any unit.""",
        pre_plot_hooks=[measure_or_tuning_fullfield.instance()],
        plot_hooks=[cyclic_tuning_curve.instance(x_axis="orientation")])



class measure_or_tuning(UnitCurveCommand):
    """
    Measures orientation tuning curve(s) of a particular unit.

    Uses a circular sine grating patch as the stimulus on the
    retina.

    The curve can be plotted at various different values of the
    contrast (or actually any other parameter) of the stimulus.  If
    using contrast and the network contains an LGN layer, then one
    would usually specify weber_contrast as the contrast_parameter. If
    there is no explicit LGN, then scale (offset=0.0) can be used to
    define the contrast.  Other relevant contrast definitions (or
    other parameters) can also be used, provided they are defined in
    PatternPresenter and the units parameter is changed as
    appropriate.
    """

    num_orientation = param.Integer(default=12)

    static_parameters = param.List(default=["size","x","y"])

    def __call__(self,**params):
        p=ParamOverrides(self,params)
        self.params('sheet').compute_default()
        sheet=p.sheet

        for coord in p.coords:
            self.x=self._sheetview_unit(sheet,coord,'XPreference',default=coord[0])
            self.y=self._sheetview_unit(sheet,coord,'YPreference',default=coord[1])
            self._compute_curves(p,sheet)


create_plotgroup(template_plot_type="curve",name='Orientation Tuning',category="Tuning Curves",doc="""
            Measure orientation tuning for a specific unit at different contrasts,
            using a pattern chosen to match the preferences of that unit.""",
        pre_plot_hooks=[measure_or_tuning.instance()],
        plot_hooks=[cyclic_tuning_curve.instance(x_axis="orientation")],
        prerequisites=['XPreference'])



# JABALERT: Is there some reason not to call it measure_size_tuning?
class measure_size_response(UnitCurveCommand):
    """
    Measure receptive field size of one unit of a sheet.

    Uses an expanding circular sine grating stimulus at the preferred
    orientation and retinal position of the specified unit.
    Orientation and position preference must be calulated before
    measuring size response.

    The curve can be plotted at various different values of the
    contrast (or actually any other parameter) of the stimulus.  If
    using contrast and the network contains an LGN layer, then one
    would usually specify weber_contrast as the contrast_parameter. If
    there is no explicit LGN, then scale (offset=0.0) can be used to
    define the contrast.  Other relevant contrast definitions (or
    other parameters) can also be used, provided they are defined in
    PatternPresenter and the units parameter is changed as
    appropriate.
    """
    size=None # Disabled unused parameter

    static_parameters = param.List(default=["orientation","x","y"])

    num_sizes = param.Integer(default=10,bounds=(1,None),softbounds=(1,50),
                              doc="Number of different sizes to test.")

    max_size = param.Number(default=1.0,bounds=(0.1,None),softbounds=(1,50),
                              doc="Maximum extent of the grating")

    x_axis = param.String(default='size',constant=True)


    def __call__(self,**params):
        p=ParamOverrides(self,params)
        self.params('sheet').compute_default()
        sheet=p.sheet

        for coord in p.coords:
            # Orientations are stored as a normalized value beween 0
            # and 1, so we scale them by pi to get the true orientations.
            self.orientation=pi*self._sheetview_unit(sheet,coord,'OrientationPreference')
            self.x=self._sheetview_unit(sheet,coord,'XPreference',default=coord[0])
            self.y=self._sheetview_unit(sheet,coord,'YPreference',default=coord[1])
            self._compute_curves(p,sheet)


    # Why not vary frequency too?  Usually it's just one number, but it could be otherwise.
    def _feature_list(self,p):
        return [Feature(name="phase",range=(0.0,2*pi),step=2*pi/p.num_phase,cyclic=True),
                Feature(name="frequency",values=p.frequencies),
                Feature(name="size",range=(0.0,p.max_size),step=p.max_size/p.num_sizes,cyclic=False)]


create_plotgroup(template_plot_type="curve",name='Size Tuning',category="Tuning Curves",
        doc='Measure the size preference for a specific unit.',
        pre_plot_hooks=[measure_size_response.instance()],
        plot_hooks=[tuning_curve.instance(x_axis="size",unit="Diameter of stimulus")],
        prerequisites=['OrientationPreference','XPreference'])



class measure_contrast_response(UnitCurveCommand):
    """
    Measures contrast response curves for a particular unit.

    Uses a circular sine grating stimulus at the preferred
    orientation and retinal position of the specified unit.
    Orientation and position preference must be calulated before
    measuring contrast response.

    The curve can be plotted at various different values of the
    contrast (or actually any other parameter) of the stimulus.  If
    using contrast and the network contains an LGN layer, then one
    would usually specify weber_contrast as the contrast_parameter. If
    there is no explicit LGN, then scale (offset=0.0) can be used to
    define the contrast.  Other relevant contrast definitions (or
    other parameters) can also be used, provided they are defined in
    PatternPresenter and the units parameter is changed as
    appropriate.
    """

    static_parameters = param.List(default=["size","x","y"])

    contrasts = param.List(class_=int,default=[10,20,30,40,50,60,70,80,90,100])

    relative_orientations = param.List(class_=float,default=[0.0, pi/6, pi/4, pi/2])

    x_axis = param.String(default='contrast',constant=True)

    units = param.String(default=" rad")

    def __call__(self,**params):
        p=ParamOverrides(self,params)
        self.params('sheet').compute_default()
        sheet=p.sheet

        for coord in p.coords:
            orientation=pi*self._sheetview_unit(sheet,coord,'OrientationPreference')
            self.curve_parameters=[{"orientation":orientation+ro} for ro in self.relative_orientations]

            self.x=self._sheetview_unit(sheet,coord,'XPreference',default=coord[0])
            self.y=self._sheetview_unit(sheet,coord,'YPreference',default=coord[1])

            self._compute_curves(p,sheet,val_format="%.4f")

    def _feature_list(self,p):
        return [Feature(name="phase",range=(0.0,2*pi),step=2*pi/p.num_phase,cyclic=True),
                Feature(name="frequency",values=p.frequencies),
                Feature(name="contrast",values=p.contrasts,cyclic=False)]


create_plotgroup(template_plot_type="curve",name='Contrast Response',category="Tuning Curves",
        doc='Measure the contrast response function for a specific unit.',
        pre_plot_hooks=[measure_contrast_response.instance()],
        plot_hooks=[tuning_curve.instance(x_axis="contrast",unit="%")],
        prerequisites=['OrientationPreference','XPreference'])


class measure_frequency_response(UnitCurveCommand):
    """
    Measure spatial frequency preference of one unit of a sheet.

    Uses an constant circular sine grating stimulus at the preferred
    with varying spatial frequency orientation and retinal position
    of the specified unit. Orientation and position preference must
    be calulated before measuring size response.

    The curve can be plotted at various different values of the
    contrast (or actually any other parameter) of the stimulus.  If
    using contrast and the network contains an LGN layer, then one
    would usually specify weber_contrast as the contrast_parameter. If
    there is no explicit LGN, then scale (offset=0.0) can be used to
    define the contrast.  Other relevant contrast definitions (or
    other parameters) can also be used, provided they are defined in
    PatternPresenter and the units parameter is changed as
    appropriate.
    """

    x_axis = param.String(default="frequency",constant=True)

    static_parameters = param.List(default=["orientation","x","y"])

    num_freq = param.Integer(default=20,bounds=(1,None),softbounds=(1,50),
                              doc="Number of different sizes to test.")

    max_freq = param.Number(default=10.0,bounds=(0.1,None),softbounds=(1,50),
                              doc="Maximum extent of the grating")

    def __call__(self,**params):
        p=ParamOverrides(self,params)
        self.params('sheet').compute_default()
        sheet=p.sheet

        for coord in p.coords:
            # Orientations are stored as a normalized value beween 0
            # and 1, so we scale them by pi to get the true orientations.
            self.orientation=pi*self._sheetview_unit(sheet,coord,'OrientationPreference')
            self.x=self._sheetview_unit(sheet,coord,'XPreference',default=coord[0])
            self.y=self._sheetview_unit(sheet,coord,'YPreference',default=coord[1])
            self._compute_curves(p,sheet)

    def _feature_list(self,p):
        return [Feature(name="orientation",values=[self.orientation],cyclic=True),
                Feature(name="phase",range=(0.0,2*pi),step=2*pi/p.num_phase,cyclic=True),
                Feature(name="frequency",range=(0.0,p.max_freq),step=p.max_freq/p.num_freq,cyclic=False),
                Feature(name="size",values=[p.size])]


create_plotgroup(template_plot_type="curve",name='Frequency Tuning',category="Tuning Curves",
        doc='Measure the spatial frequency preference for a specific unit.',
        pre_plot_hooks=[measure_frequency_response.instance()],
                 plot_hooks=[tuning_curve.instance(x_axis="frequency",unit="cycles per unit distance")],
        prerequisites=['OrientationPreference','XPreference'])


class measure_orientation_contrast(UnitCurveCommand):
    """
    Measures the response to a center sine grating disk and a surround
    sine grating ring at different contrasts of the central disk.

    The central disk is set to the preferred orientation of the unit
    to be measured. The surround disk orientation (relative to the
    central grating) and contrast can be varied, as can the size of
    both disks.
    """

    pattern_presenter = param.Callable(
        default=PatternPresenter(pattern_generator=OrientationContrast(),
                                 contrast_parameter="weber_contrast"))

    size=None # Disabled unused parameter
    # Maybe instead of the below, use size and some relative parameter, to allow easy scaling?

    sizecenter=param.Number(default=0.5,bounds=(0,None),doc="""
        The size of the central pattern to present.""")

    sizesurround=param.Number(default=1.0,bounds=(0,None),doc="""
        The size of the surround pattern to present.""")

    thickness=param.Number(default=0.5,bounds=(0,None),softbounds=(0,1.5),doc="""Ring thickness.""")

    contrastsurround=param.Number(default=100,bounds=(0,100),doc="""Contrast of the surround.""")

    contrastcenter=param.Number(default=100,bounds=(0,100),doc="""Contrast of the center.""")

    x_axis = param.String(default='orientationsurround',constant=True)

    orientation_center = param.Number(default=0.0,softbounds=(0.0,pi),doc="""
        Orientation of the center grating patch""")

    units = param.String(default="%")

    static_parameters = param.List(default=["x","y","sizecenter","sizesurround","orientationcenter","thickness","contrastcenter"])

    curve_parameters=param.Parameter([{"contrastsurround":30},{"contrastsurround":60},{"contrastsurround":80},{"contrastsurround":90}],doc="""
        List of parameter values for which to measure a curve.""")

    or_surrounds = []

    def __call__(self,**params):
        p=ParamOverrides(self,params)
        self.params('sheet').compute_default()
        sheet=p.sheet
        for coord in p.coords:
            self.or_surrounds=[]
            orientation=pi*self._sheetview_unit(sheet,coord,'OrientationPreference',default=p.orientation_center/pi)
            self.orientationcenter=orientation

            for i in xrange(0,self.num_orientation):
                self.or_surrounds.append((-pi/2)+i*pi/(self.num_orientation))

            self.x=self._sheetview_unit(sheet,coord,'XPreference',default=coord[0])
            self.y=self._sheetview_unit(sheet,coord,'YPreference',default=coord[1])

            self._compute_curves(p,sheet)

    def _feature_list(self,p):
        return [Feature(name="phase",range=(0.0,2*pi),step=2*pi/p.num_phase,cyclic=True),
    	 	Feature(name="frequency",values=p.frequencies),
		Feature(name="orientationsurround",values=self.or_surrounds,cyclic=True)]

create_plotgroup(template_plot_type="curve",name='Orientation Contrast',category="Tuning Curves",
                 doc='Measure the response of one unit to a center and surround sine grating disk.',
                 pre_plot_hooks=[measure_orientation_contrast.instance()],
                 plot_hooks=[cyclic_tuning_curve.instance(x_axis="orientationsurround",unit="degrees",recenter=False)],
                 prerequisites=['OrientationPreference','XPreference'])



class test_measure(UnitCurveCommand):

    static_parameters = param.List(default=["size","x","y"])

    x_axis = param.String(default='contrast',constant=True)

    units = param.String(default=" rad")

    def __call__(self,**params):
        p=ParamOverrides(self,params)
        self.params('sheet').compute_default()
        sheet=p.sheet
        self.x = 0.0
	self.y = 0.0
        for coord in p.coords:
            self._compute_curves(p,sheet,val_format="%.4f")

    def _feature_list(self,p):
        return [Feature(name="orientation",values=[1.0]*22,cyclic=True),
    		Feature(name="contrast",values=[100],cyclic=False)]

import types
__all__ = list(set([k for k,v in locals().items()
                    if isinstance(v,types.FunctionType) or
                    (isinstance(v,type) and issubclass(v,ParameterizedFunction))
                    and not v.__name__.startswith('_')]))
