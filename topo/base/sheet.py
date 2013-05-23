"""
Neural sheet objects and associated functions.

The Sheet class is the base class for EventProcessors that simulate
topographically mapped sheets of units (neurons or columns).  A Sheet
is an EventProcessor that maintains a rectangular array of activity
values, and sends the contents of this array as the data element in
events.

The Sheet itself is a SheetCoordinateSystem, so that units may be
accessed by sheet or matrix coordinates. In general, however, sheets
should be thought of as having arbitrary density and sheet coordinates
should be used wherever possible, except when the code needs direct
access to a specific unit.  By adhering to this convention, one should
be able to write and debug a simulation at a low density, and then
scale it up to run at higher densities (or down for lower densities)
simply by changing e.g. Sheet.nominal_density.
"""



from numpy import zeros,array,arange,meshgrid
from numpy import float64

import param

from simulation import EventProcessor
from sheetcoords import SheetCoordinateSystem
from boundingregion import BoundingBox, BoundingRegionParameter
from functionfamily import TransferFn


activity_type = float64



import bisect
try:
    from collections import OrderedDict, defaultdict
except:
    OrderedDict = None


class AttrDict(defaultdict,param.Parameterized):
    """
    A dictionary type object that supports attribute access (e.g. for
    IPython tab completion).
    """

    time_fn = param.Callable(default=lambda: None)

    timestamp = param.Number(default=None)
    
    def __init__(self, *args, **kwargs):
        self.timestamp = self.time_fn()
        super(AttrDict, self).__init__(*args, **kwargs)

    def __dir__(self):
        """
        Extend dir() to include the latest SheetViews.
        """
        default_dir = dir(type(self)) + list(self.__dict__)
        keys = [key.replace(' ','___').replace('%','pct').replace('=','eq') for key in self.keys() if isinstance(key,str)]
        keys += [str(key).replace('.','_') for key in self.keys() if isinstance(key,float)]
        return sorted(set(default_dir + keys))

    def __getattr__(self, name):
        """
        Provide a simpler attribute-like syntax for accesing the
        latest SheetViews.
        """
        if '___' in name:
            name = name.replace('___','_')
            name = name.replace('pct','%')        
            name = name.replace('eq','=')
            name = name.replace('_',' ')
        if isinstance(name,str) and name[0].isdigit():
            name = name.replace('_','.')
            name = float(name)
        if name in self.keys():
            return self[name]
        else:
            raise AttributeError

def attrtree():
       ' Simple yet flexible tree datastructure '
       return AttrDict(attrtree)

class MultiDict(dict):

    depth = param.Integer(default=5)

    time_fn = param.Callable(default=lambda: None)

    def __init__(self):
        self._buffer = [] # List of tuples (timestamp, attrdict)
        self._latest_items = attrtree()
        self.initialized=True
        
    def get(self,key,default=None):
        if key in self.keys():
            return self._latest_items[key]
        else:
            return default

    def keys(self):
        return self._latest_items.keys()

    def items(self):
        return self._latest_items.items()

    def __dir__(self):
        """
        Extend dir() to include the latest SheetViews.
        """
        default_dir = dir(type(self)) + list(self.__dict__)
        keys = [key for key in self.keys() if not isinstance(key,tuple)] 
        keys += ['__'.join(str(el) for el in key).replace('.','_').replace('-','m')
                 for key in self.keys() if isinstance(key,tuple) and len(key)==4]

        return sorted(set(default_dir + keys))

    def __getattr__(self, name):
        """
        Provide a simpler attribute-like syntax for accesing the
        latest SheetViews.
        """
        if name.count('__') == 3:
            name = name.replace('__m','__-')
            name = name.split('__')
            name[2] = float(name[2].replace('_','.'))
            name[3] = float(name[3].replace('_','.'))
            name = tuple(name)
        if name in self.__dict__.keys():
            return self.__dict__[name]
        return self._latest_items[name]
        

    def __contains__(self,key):
        return key in self._latest_items.keys()

    def _update_latest_items(self):
        # for idx,_buffer in enumerate(self._buffer): # OPTIMIZE to avoid overwriting of stale SheetViews
        #     _buffer.keys() # IDENTIFY latest timestamp for each measurement (always overwrite AttrDict items as SheetViews and timestamp are too deeply recursive) maybe give attrdicts timestamps
        for _buffer in self._buffer:
            for key, item in _buffer[1].items():
                self._latest_items[key] = item    

    def _lookup_latest(self,val):
        adict = self._get_latest_dict(self.time_fn())
        if val not in adict.keys():
            adict[val]
        self._update_latest_items()
        return self._latest_items[val]
        
    def __getitem__(self, val):
        """
        If indexed by string, return corresponding value from latest
        timeslice (backward compatible behavior).

        If indexed by an integer return the attribute dictionary. Index

        If indexed by (start, stop) tuple, where start and stop are
        timestamps (or None) then return the attribute dictionaries
        from the specified time interval as a list. When start or stop
        are None the usual Python slicing semantics apply.

        Usual slicing semantics supported.
        """
        if isinstance(val,str):
            return self._lookup_latest(val)
        if isinstance(val, int):
            return self._buffer[val][1]
        if isinstance(val,tuple):
            if len(val) == 2:
                (start, stop) = val
                return [el[1] for el in self._buffer[self.timeslice(start, stop)]]
            else:
                return self._lookup_latest(val) # RFs keys use tuples
        if isinstance(val, slice):
            return [el[1] for el in self._buffer[val]]

    def __setitem__(self, key, value):
        adict = self._get_latest_dict(self.time_fn())
        adict[key] = value
        self._latest_items[key] = adict[key]
        
    def _get_latest_dict(self, timestamp):
        """
        Returns the attribute dictionary corresponding to the
        specified timestamp.
        """
        if len(self._buffer)==0 or self._buffer[-1][0] != timestamp:
            if len(self._buffer) == self.depth:
                self._buffer.pop(0)
            
            new_adict = attrtree()
            timestamps = [el[0] for el in self._buffer]
            insert_index = bisect.bisect_left(timestamps, timestamp)
            self._buffer.insert(insert_index, (timestamp, new_adict))
            return new_adict
        else:
            (time, last_adict) = self._buffer[-1]
            return last_adict

    def timeslice(self, start=None, stop=None):
        """
        Returns the corresponding integer timeslice, given a time interval.
        """
        timestamps = [el[0] for el in self._buffer]
        start_ind = None if (start is None) else bisect.bisect_left(timestamps, start)
        stop_ind = None if (stop is None) else bisect.bisect_left(timestamps, stop)
        return slice(start_ind, stop_ind)


# (disable W0223 because input_event is deliberately still not implemented)
class Sheet(EventProcessor,SheetCoordinateSystem):  # pylint: disable-msg=W0223
    """
    The generic base class for neural sheets.

    See SheetCoordinateSystem for how Sheet represents space, and
    EventProcessor for how Sheet handles time.

    output_fns are functions that take an activity matrix and produce
    an identically shaped output matrix. The default is having no
    output_fns.
    """
    __abstract = True

    nominal_bounds = BoundingRegionParameter(BoundingBox(radius=0.5),constant=True,doc="""
            User-specified BoundingBox of the Sheet coordinate area
            covered by this Sheet.  The left and right bounds--if
            specified--will always be observed, but the top and bottom
            bounds may be adjusted to ensure the density in the y
            direction is the same as the density in the x direction.
            In such a case, the top and bottom bounds are adjusted
            so that the center y point remains the same, and each
            bound is as close as possible to its specified value. The
            actual value of this Parameter is not adjusted, but the
            true bounds may be found from the 'bounds' attribute
            of this object.
            """)

    nominal_density = param.Number(default=10,constant=True,doc="""
            User-specified number of processing units per 1.0 distance
            horizontally or vertically in Sheet coordinates. The actual
            number may be different because of discretization; the matrix
            needs to tile the plane exactly, and for that to work the
            density might need to be adjusted.  For instance, an area of 3x2
            cannot have a density of 2 in each direction. The true density
            may be obtained from either the xdensity or ydensity attribute
            (since these are identical for a Sheet).
            """)

    plastic = param.Boolean(True,doc="""
            Setting this to False tells the Sheet not to change its
            permanent state (e.g. any connection weights) based on
            incoming events.
            """)

    precedence = param.Number(default = 0.1, softbounds=(0.0,1.0),doc="""
            Allows a sorting order for Sheets, e.g. in the GUI.""")

    row_precedence = param.Number(default = 0.5, softbounds=(0.0,1.0),doc="""
            Allows grouping of Sheets before sorting precedence is
            applied, e.g. for two-dimensional plots in the GUI.""")

    layout_location = param.NumericTuple(default = (-1,-1),precedence=-1,doc="""
            Location for this Sheet in an arbitrary pixel-based space
            in which Sheets can be laid out for visualization.""")

    output_fns = param.HookList(default=[],class_=TransferFn,
        doc="Output function(s) to apply (if apply_output_fns is true) to this Sheet's activity.")

    apply_output_fns=param.Boolean(default=True,
        doc="Whether to apply the output_fn after computing an Activity matrix.")


    def _get_density(self):
        return self.xdensity

    density = property(_get_density,doc="""The sheet's true density (i.e. the xdensity, which is equal to the ydensity for a Sheet.)""")

    def __init__(self,**params):
        """
        Initialize this object as an EventProcessor, then also as
        a SheetCoordinateSystem with equal xdensity and ydensity.

        sheet_views is a dictionary that stores SheetViews,
        i.e. representations of the sheet for use by analysis or plotting
        code.
        """
        EventProcessor.__init__(self,**params)

        # Initialize this object as a SheetCoordinateSystem, with
        # the same density along y as along x.
        SheetCoordinateSystem.__init__(self,self.nominal_bounds,self.nominal_density)

        n_units = round((self.lbrt[2]-self.lbrt[0])*self.xdensity,0)
        if n_units<1: raise ValueError(
           "Sheet bounds and density must be specified such that the "+ \
           "sheet has at least one unit in each direction; " \
           +self.name+ " does not.")

        # setup the activity matrix
        self.activity = zeros(self.shape,activity_type)

        # For non-plastic inputs
        self.__saved_activity = []
        self._plasticity_setting_stack = []
        self.sheet_views = MultiDict()
        self.views = self.sheet_views


    ### JABALERT: This should be deleted now that sheet_views is public
    ### JC: shouldn't we keep that, or at least write a function in
    ### utils that deletes a value in a dictinnary without returning an
    ### error if the key is not in the dict?  I leave for the moment,
    ### and have to ask Jim to advise.
    def release_sheet_view(self,view_name):
        """
        Delete the dictionary entry with key entry 'view_name' to save
        memory.
        """
        if self.sheet_views.has_key(view_name):
            del self.sheet_views[view_name]


    # CB: what to call this? sheetcoords()? sheetcoords_of_grid()? idxsheetcoords()?
    def sheetcoords_of_idx_grid(self):
        """
        Return an array of x-coordinates and an array of y-coordinates
        corresponding to the activity matrix of the sheet.
        """
        nrows,ncols=self.activity.shape

        C,R = meshgrid(arange(ncols),
                       arange(nrows))

        X,Y = self.matrixidx2sheet(R,C)
        return X,Y


    # CB: check whether we need this function any more.
    def row_col_sheetcoords(self):
        """
        Return an array of Y-coordinates corresponding to the rows of
        the activity matrix of the sheet, and an array of
        X-coordinates corresponding to the columns.
        """
        # The row and column centers are returned in matrix (not
        # sheet) order (hence the reversals below).
        nrows,ncols = self.activity.shape
        return self.matrixidx2sheet(arange(nrows-1,-1,-1),arange(ncols))[::-1]


    # CBALERT: to be removed once other code uses
    # row_col_sheetcoords() or sheetcoords_of_idx_grid().
    def sheet_rows(self):
        return self.row_col_sheetcoords()[0]
    def sheet_cols(self):
        return self.row_col_sheetcoords()[1]


    # CEBALERT: haven't really thought about what to put in this. The
    # way it is now, subclasses could make a super.activate() call to
    # avoid repeating some stuff.
    def activate(self):
        """
        Collect activity from each projection, combine it to calculate
        the activity for this sheet, and send the result out.

        Subclasses will need to override this method to whatever it
        means to calculate activity in that subclass.
        """
        if self.apply_output_fns:
            for of in self.output_fns:
                of(self.activity)

        self.send_output(src_port='Activity',data=self.activity)


    def state_push(self):
        """
        Save the current state of this sheet to an internal stack.

        This method is used by operations that need to test the
        response of the sheet without permanently altering its state,
        e.g. for measuring maps or probing the current behavior
        non-invasively.  By default, only the activity pattern of this
        sheet is saved, but subclasses should add saving for any
        additional state that they maintain, or strange bugs are
        likely to occur.  The state can be restored using state_pop().

        Note that Sheets that do learning need not save the
        values of all connection weights, if any, because
        plasticity can be turned off explicitly.  Thus this method
        is intended only for shorter-term state.
        """
        self.__saved_activity.append(array(self.activity))
        EventProcessor.state_push(self)
        for of in self.output_fns:
            if hasattr(of,'state_push'):
                of.state_push()


    def state_pop(self):
        """
        Pop the most recently saved state off the stack.

        See state_push() for more details.
        """
        self.activity = self.__saved_activity.pop()
        EventProcessor.state_pop(self)
        for of in self.output_fns:
            if hasattr(of,'state_pop'):
                of.state_pop()


    def activity_len(self):
        """Return the number of items that have been saved by state_push()."""
        return len(self.__saved_activity)


    def override_plasticity_state(self, new_plasticity_state):
        """
        Temporarily override plasticity of medium and long term internal state.

        This function should be implemented by all subclasses so that
        it preserves the ability of the Sheet to compute activity,
        i.e. to operate over a short time scale, while preventing any
        lasting changes to the state (if new_plasticity_state=False).

        Any operation that does not have any lasting state, such as
        those affecting only the current activity level, should not
        be affected by this call.

        By default, simply saves a copy of the plastic flag to an
        internal stack (so that it can be restored by
        restore_plasticity_state()), and then sets plastic to
        new_plasticity_state.
        """
        self._plasticity_setting_stack.append(self.plastic)
        self.plastic=new_plasticity_state


    def restore_plasticity_state(self):
        """
        Restores plasticity of medium and long term internal state after
        a override_plasticity_state call.

        This function should be implemented by all subclasses to
        remove the effect of the most recent override_plasticity_state call,
        i.e. to restore plasticity of any type that was overridden.
        """
        self.plastic = self._plasticity_setting_stack.pop()


    def n_bytes(self):
        """
        Return a lower bound for the memory taken by this sheet, in bytes.

        Typically, this number will include the activity array and any
        similar arrays, plus any other significant data owned (in some
        sense) by this Sheet.  It will not usually include memory
        taken by the Python dictionary or various "housekeeping"
        attributes, which usually contribute only a small amount to
        the memory requirements.

        Subclasses should reimplement this method if they store a
        significant amount of data other than in the activity array.
        """
        return self.activity.nbytes

