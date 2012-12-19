"""
Object classes for recording and plotting time-series data.

This module defines a set of DataRecorder object types for recording
time-series data, a set of Trace object types for
specifying ways of generating 1D-vs-time traces from recorded data,
and a TraceGroup object that will plot a set of traces on stacked,
aligned axes.
"""

import os
import bisect
from itertools import izip

from numpy import asarray
import ImageDraw

import param
from param import normalize_path

from topo.base.simulation import EventProcessor
from topo.plotting.bitmap import RGBBitmap, MontageBitmap, TITLE_FONT
from topo.misc.util import Struct



class DataRecorder(EventProcessor):
    """
    Record time-series data from a simulation.

    A DataRecorder instance stores a set of named time-series
    variables, consisting of a sequence of recorded data items of any
    type, along with the times at which they were recorded.

    DataRecorder is an abstract class for which different
    implementations may exist for different means of storing recorded
    data.  For example, the subclass InMemoryRecorder stores all the
    data in memory.

    A DataRecorder instance can operate either as an event processor, or in a
    stand-alone mode.  Both usage modes can be used on the same
    instance in the same simulation.

    STAND-ALONE USAGE:

    A DataRecorder instance is used as follows:

      - Method .add_variable adds a named time series variable.
      - Method .record_data records a new data item and timestamp.
      - Method .get_data gets a time-delimited sequence of data from a variable

    EVENTPROCESSOR USAGE:

    A DataRecorder can also be connected to a simulation as an event
    processor, forming a kind of virtual recording equipment.  An
    output port from any event processor in a simulation can be
    connected to a DataRecorder; the recorder will automaticall create
    a variable with the same name as the connection, and record any
    incoming data on that variable with the time it was received.  For
    example::

      topo.sim['Recorder'] =  InMemoryRecorder()
      topo.sim.connect('V1','Recorder',name='V1 Activity')

    This script snippet will create a new DataRecorder and
    automatically record all activity sent from the sheet 'V1'.
    """

    __abstract = True


    def __init__(self,**params):
        super(DataRecorder,self).__init__(**params)
        self._trace_groups = {}


    def _src_connect(self,conn):
        raise NotImplementedError


    def _dest_connect(self,conn):
        super(DataRecorder,self)._dest_connect(conn)
        self.add_variable(conn.name)


    def input_event(self,conn,data):
        self.record_data(conn.name,self.simulation.time(),data)


    def add_variable(self,name):
        """
        Create a new time-series variable with the given name.
        """
        raise NotImplementedError


    def record_data(self,varname,time,data):
        """
        Record the given data item with the given timestamp in the
        named timeseries.
        """
        raise NotImplementedError


    def get_data(self,varname,times=(None,None),fill_range=False):
        """
        Get the named timeseries between the given times
        (inclusive). If fill_range is true, the returned data will
        have timepoints exactly at the start and end of
        the given timerange.  The data values at these timepoints will
        be those of the next-earlier datapoint in the series.

        (NOTE: fill_range can fail to create a beginning timepoint if
        the start of the time range is earlier than the first recorded datapoint.]
        """
        raise NotImplementedError


    def get_times(self,var):
        """
        Get all the timestamps for a given variable.
        """
        raise NotImplementedError


    def get_time_indices(self,varname,start_time,end_time):
        """
        For the named variable, get the start and end indices suitable
        for slicing the data to include all times t::

          start_time <= t <= end_time.

        A start_ or end_time of None is interpreted to mean the
        earliest or latest available time, respectively.
        """

        times = self.get_times(varname)
        if start_time is None:
            start = 0
        else:
            start = bisect.bisect_left(times,start_time)
            if start >= len(times):
                start = len(times)-1
            elif times[start] > start_time:
                start -= 1

        if end_time is None:
            end = None
        else:
            end = bisect.bisect_right(times,end_time)

        return start,end




class InMemoryRecorder(DataRecorder):
    """
    A data recorder that stores all recorded data in memory.
    """

    def __init__(self,**params):
        super(InMemoryRecorder,self).__init__(**params)
        self._vars = {}


    def add_variable(self,name):
        self._vars[name] = Struct(time=[],data=[])


    def record_data(self,varname,time,data):
        var = self._vars[varname]

        # add the data, maintaining it sorted by time
        if not var.time or var.time[-1] <= time:
            var.time.append(time)
            var.data.append(data)
        elif time < var.time[0]:
            var.time.insert(0,time)
            var.data.insert(0,data)
        else:
            idx = bisect.bisect_right(var.time,time)
            var.time.insert(idx,time)
            var.data.insert(idx,data)

    def get_datum(self,name,time):
        idx,dummy = self.get_time_indices(name,time,time)
        data = self._vars[name].data
        if idx >= len(data):
            idx -= 1
        return data[idx]

    def get_data(self,name,times=(None,None),fill_range=False):
        tstart,tend = times
        start,end = self.get_time_indices(name,tstart,tend)
        var = self._vars[name]

        if start >= len(var.data):
            # if the start index is out of bounds
            if fill_range:
                time = times
                data = [var.data[-1]]*2
            else:
                time,data = [],[]
        else:
            time,data = var.time[start:end],var.data[start:end]
            if fill_range:
                if time[0] > tstart and start > 0:
                    time.insert(0,tstart)
                    data.insert(0,var.data[start-1])
                if time[-1] < tend:
                    time.append(tend)
                    data.append(data[-1])

        return time,data


    def get_times(self,varname):
        return self._vars[varname].time




class Trace(param.Parameterized):
    """
    A specification for generating 1D traces of data from recorded
    timeseries.

    A Trace object is a callable object that encapsulates
    a method for generating a 1-dimensional trace from possibly
    multidimensional timeseries data, along with a specification for
    how to plot that data, including Y-axis boundaries and plotting arguments.

    Trace is an abstract class.  Subclasses implement
    the __call__ method to define how to extract a 1D trace from a
    sequence of data.
    """

    __abstract = True

    data_name = param.String(default=None,doc="""
        Name of the timeseries from which the trace is generated.
        E.g. the connection name into a DataRecorder object.""")

    # JPALERT: This should really be something like a NumericTuple,
    # except that NumericTuple won't allow the use of None to indicate
    # 'no default'.  (Nor will Number.)
    # JB: We could have that as an option, or as another Parameter
    # type, but in many cases knowing that the parameter cannot be set
    # to a non-numeric value is crucial, as it means we don't have to
    # do special checks every time the value is used.  So we should
    # leave the default behavior as it is, but yes, it would be good
    # to handle None for numeric types (and also for Boolean, to make
    # it tri-state).  Note that Bounds is a specific type that we
    # should probably support in any case, because it not only needs
    # to support None, it needs to specify whether the bounds are
    # inclusive or exclusive.
    ybounds = param.Parameter(default=(None,None),doc="""
        The (min,max) boundaries for y axis.  If either is None, then
        the bound min or max of the data given, respectively.""")

    ymargin = param.Number(default=0.1,doc="""
        The fraction of the difference ymax-ymin to add to the
        top of the plot as padding.""")

    plotkw = param.Dict(default=dict(linestyle='steps'),doc="""
        Contains the keyword arguments to pass to the plot command
        when plotting the trace.""")


    def __call__(self,data):
        raise NotImplementedError


    # JB: Needs docstring.  Should this be a property instead?
    def get_ybounds(self,ydata):
        ymin,ymax = self.ybounds
        if ymax is None:
            ymax = max(ydata)

        if ymin is None:
            ymin = min(ydata)

        ymax += (ymax-ymin)*self.ymargin

        return ymin,ymax


class IdentityTrace(Trace):
    """
    A Trace that returns the data, unmodified.
    """
    def __call__(self,data):
        return data



class IndexTrace(Trace):
    """
    A Trace that assumes that each data item is a sequence that can be
    indexed with a single integer, and traces the value of one indexed element.
    """

    index = param.Integer(default=0,doc="""
        The index into the data to be traced.""")

    def __call__(self,data):
        return [x[self.index] for x in data]



class SheetPositionTrace(Trace):
    """
    A trace that assumes that the data are sheet activity matrices,
    and traces the value of a given (x,y) position on the sheet.
    """

    x = param.Number(default=0.0,doc="""
        The x sheet-coordinate of the position to be traced.""")

    y = param.Number(default=0.0,doc="""
        The y sheet-coordinate of the position to be traced.""")

    position = param.Composite(attribs=['x','y'],doc="""
        The sheet coordinates of the position to be traced.""")

    # JPALERT:  Would be nice to some way to set up the coordinate system
    # automatically.  The DataRecorder object already knows what Sheet
    # the data came from.
    coordframe = param.Parameter(default=None,doc="""
        The SheetCoordinateSystem to use to convert the position
        into matrix coordinates.""")

    def __call__(self,data):
        r,c = self.coordframe.sheet2matrixidx(self.x,self.y)
        return [d[r,c] for d in data]



class TraceGroup(param.Parameterized):
    """
    A group of data traces to be plotted together.

    A TraceGroup defines a set of associated data traces and allows
    them to be plotted on stacked, aligned axes.  The constructor
    takes a DataRecorder object as a data source, and a list of
    Trace objects that indicate the traces to plot.  The
    trace specifications are stored in the attribute self.traces,
    which can be modified at any time.
    """


    hspace = param.Number(default=0.6,doc="""
       Height spacing adjustment between plots.  Larger values
       produce more space.""")

    time_axis_relative = param.Boolean(default=False,doc="""
       Whether to plot the time-axis tic values relative to the start
       of the plotted time range, or in absolute values.""")


    def __init__(self,recorder,traces=[],**params):
        super(TraceGroup,self).__init__(**params)
        self.traces = traces
        self.recorder = recorder


    def plot(self,times=(None,None)):
        """
        Plot the traces.

        Requires MatPlotLib (aka pylab).

        Plots the traces specified in self.traces, over the timespan
        specified by times.  times = (start_time,end_time); if either
        start_time or end_time is None, it is assumed to extend to the
        beginning or end of the timeseries, respectively.
        """

        import pylab
        rows = len(self.traces)
        tstart,tend = times

        pylab.subplots_adjust(hspace=self.hspace)
        for i,trace in enumerate(self.traces):
            # JPALERT: The TraceGroup object should really create its
            # own matplotlib.Figure object and always plot there
            # (instead of in the frontmost plot), but I haven't
            # figured out how to do that yet.
            pylab.subplot(rows,1,i+1)
            pylab.title(trace.name)
            time,data = self.recorder.get_data(trace.data_name,times=times,fill_range=True)
            y = trace(data)
            if self.time_axis_relative:
                time = asarray(time) - time[0]
            pylab.plot(time,y,**trace.plotkw)
            ymin,ymax = trace.get_ybounds(y)
            pylab.axis(xmin=time[0],xmax=time[-1],ymin=ymin,ymax=ymax)





def get_images(name,times,recorder,overlays=(0,0,0)):
    """
    Get a time-sequence of matrix data from a DataRecorder variable
    and convert it to a sequence of images stored in Bitmap objects.

    Parameters: name is the name of the variable to be queried. times
    is a sequence of timepoints at which to query the
    variable. recorder is the data recorder. overlays is a tuple of
    matrices or scalars to be added to the red, green, and blue
    channels of the bitmaps respectively.
    """
    result = []

    for t in times:
        d = recorder.get_datum(name,t)
        im = RGBBitmap(d+overlays[0],d+overlays[1],d+overlays[2])
        result.append(im)
    return result


# JABALERT: Is there some reason it is called ActivityMovie in
# particular, if it can plot things other than Activity?
# Maybe DataRecorderMovie?
class ActivityMovie(param.Parameterized):
    """
    An object encapsulating a series of movie frames displaying the
    value of one or more matrix-valued time-series contained in a
    DataRecorder object.

    An ActivityMovie takes a DataRecorder object, a list of names of
    variables in that recorder and a sequence of timepoints at which
    to sample those variables.  It uses that information to compose a
    sequence of MontageBitmap objects displaying the stored values of
    each variable at each timepoint.  These bitmaps can then be saved
    to sequentially-named files that can be composited into a movie by
    external software.

    Parameters are available to control the layout of the montage,
    adding timecodes to the frames, and the names of the frame files.
    """


    variables = param.List(class_=str, doc="""
        A list of variable names in a DataRecorder object containing
        matrix-valued time series data.""")

    overlays = param.Dict(default={}, doc="""
        A dictionary indicating overlays for the variable bitmaps.  The
        for each key in the dict matching the name of a variable, there
        should be associated a triple of matrices to be overlayed on
        the red, green, and blue channels of the corresponding bitmap
        in each frame.""")

    frame_times = param.List(default=[0,1], doc="""
        A list of the times of the frames in the movie.""")

    montage_params = param.Dict(default={},doc="""
        A dictionary containing parameters to be used when
        instantiating the MontageBitmap objects representing each frame.""",
        instantiate=False)

    recorder = param.ClassSelector(class_=DataRecorder, doc="""
        The DataRecorder storing the timeseries.""")

    filename_fmt = param.String(default='%n_%t.%T',doc="""
        The format for the filenames used to store the frames.  The following
        substitutions are possible:

        %n: The name of this ActivityMovie object.
        %t: The frame time, as formatted by the filename_time_fmt parameter
        %T: The filetype given by the filetype parameter. """)

    filename_time_fmt = param.String(default='%05.0f', doc="""
        The format of the frame time, using Python string substitution for
        a floating-point number.""")

    filetype = param.String(default='tif',doc="""
        The filetype to use when writing frames. Can be any filetype understood
        by the Python Imaging Library.""")

    filename_prefix = param.String(default='', doc="""
        A prefix to prepend to the filename of each frame when saving;
        can include directories.  If the filename contains a path, any
        non-existent directories in the path will be created when the
        movie is saved.""")

    add_timecode = param.Boolean(default=False, doc="""
        Whether to add a visible timecode indicator to each frame.""")

    timecode_options = param.Dict(default={},instantiate=False,doc="""
        A dictionary of keyword options to be passed to the PIL ImageDraw.text method
        when drawing the timecode on the frame. Valid options include font,
        an ImageFont object indicating the text font, and fill a PIL color
        specification indicating the text color.  If unspecified, color defaults to
        the PIL default of black.  Font defaults to topo.plotting.bitmap.TITLE_FONT.""")

    timecode_fmt = param.String(default='%05.0f',doc="""
        The format of the timecode displayed in the movie frames, using
        Python string substitution for a floating-point number.""")

    timecode_offset = param.Number(default=0,doc="""
        A value to be added to each timecode before formatting for display.""")


    def __init__(self,**params):
        super(ActivityMovie,self).__init__(**params)

        bitmaps = [get_images(var,self.frame_times,self.recorder,
                              overlays=self.overlays.get(var,(0,0,0)))
                   for var in self.variables]

        self.frames = [MontageBitmap(bitmaps=list(bms),**self.montage_params)
                       for bms in izip(*bitmaps)]
        if self.add_timecode:
            for t,f in izip(self.frame_times,self.frames):
                draw = ImageDraw.Draw(f.image)
                timecode = self.timecode_fmt % (t+self.timecode_offset)
                tw,th = draw.textsize(timecode,font=self.timecode_options.setdefault('font',TITLE_FONT))
                w,h = f.image.size

                draw.text((w-tw-f.margin-1,h-th-1),timecode,**self.timecode_options)


    def save(self):
        """Save the movie frames."""

        filename_pat = self.name.join(self.filename_fmt.split('%n'))
        filename_pat = self.filename_time_fmt.join(filename_pat.split('%t'))
        filename_pat = self.filetype.join(filename_pat.split('%T'))

        filename_pat = normalize_path(filename_pat,prefix=self.filename_prefix)
        dirname = os.path.dirname(filename_pat)
        if not os.access(dirname,os.F_OK):
            os.makedirs(dirname)

        self.verbose('Writing',len(self.frames),'to files like "%s"'%filename_pat)
        for t,f in zip(self.frame_times,self.frames):
            filename = filename_pat% t
            self.debug("Writing frame",repr(filename))
            f.image.save(filename)
