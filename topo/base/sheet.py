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

from functionfamily import TransferFn

from dataviews import AttrDict
from dataviews.collector import AttrTree
from dataviews.sheetviews import BoundingBox, BoundingRegionParameter,\
    SheetCoordinateSystem, SheetView

activity_type = float64


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

    precedence = param.Number(default=0.1, softbounds=(0.0,1.0),doc="""
            Allows a sorting order for Sheets, e.g. in the GUI.""")

    row_precedence = param.Number(default=0.5, softbounds=(0.0,1.0),doc="""
            Allows grouping of Sheets before sorting precedence is
            applied, e.g. for two-dimensional plots in the GUI.""")

    layout_location = param.NumericTuple(default=(-1,-1),precedence=-1,doc="""
            Location for this Sheet in an arbitrary pixel-based space
            in which Sheets can be laid out for visualization.""")

    output_fns = param.HookList(default=[],class_=TransferFn,
        doc="Output function(s) to apply (if apply_output_fns is true) to this Sheet's activity.")

    apply_output_fns=param.Boolean(default=True,
        doc="Whether to apply the output_fn after computing an Activity matrix.")

    properties = param.Dict(default={}, doc="""
       A dictionary of property values associated with the Sheet
       object.  For instance, the dictionary:

       {'polarity':'ON', 'eye':'Left'}

       could be used to indicate a left, LGN Sheet with ON-surround
       receptive fields.""")


    def _get_density(self):
        return self.xdensity

    density = property(_get_density,doc="""The sheet's true density (i.e. the
        xdensity, which is equal to the ydensity for a Sheet.)""")

    def __init__(self,**params):
        """
        Initialize this object as an EventProcessor, then also as
        a SheetCoordinateSystem with equal xdensity and ydensity.

        views is an AttrTree, which stores associated measurements,
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

        self.views = AttrTree()
        self.views.Maps = AttrTree()
        self.views.Curves = AttrTree()


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
        if view_name in self.views.Maps:
            del self.views.Maps[view_name]


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


    def __getitem__(self, coords):
        metadata = AttrDict(precedence=self.precedence,
                            row_precedence=self.row_precedence,
                            timestamp=self.simulation.time())

        sv = SheetView(self.activity.copy(), self.bounds,
                       label=self.name+' Activity', value='Activity')[coords]
        sv.metadata=metadata
        return sv


