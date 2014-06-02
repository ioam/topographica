"""
Topographica SheetView objects and its subclasses.

For use with the Topographica plotting and data analysis mechanisms.
A Sheet object has its internal data which remains hidden, but it will
create views of this data depending on the Sheet defaults or the
information requested.  This way there can be multiple views recorded
for a single sheet, and a view can be passed around independent of the
originating source object.
"""

import numpy as np

import param

from dataviews import SheetView as ImagenSheetView
from dataviews.sheetviews import BoundingRegion, SheetCoordinateSystem, SheetStack
from dataviews.options import options, StyleOpts


class SheetView(param.Parameterized):
    """
    Class provided for backward compatibility with earlier SheetView
    component.
    """

    timestamp = param.Number(default=None, doc=
        """ The initial timestamp. If None, the DataView will not all slicing of
            a time interval and record method will be disabled.""")

    bounds = param.Parameter(default=None, doc=
        """ The bounds of the two dimensional coordinate system in which the data resides.""")

    src_name = param.String(default = None, allow_None=True)

    precedence = param.Number(default=0.0)

    row_precedence = param.Number(default=0.5)

    cyclic = param.Boolean(False, doc="""If cyclic is True, this value is the cyclic range.""")

    cyclic_range = param.Parameter(None)


    def view(self):
        """
        Return the requested view as a (data, bbox) tuple.  Provided
        for backward compatibility with the original Topographica
        SheetView model. It is now easier to access the data and
        bounds attributes directly.
        """
        if hasattr(self, 'data'):
            return (self.data, self.bounds)
        else: # Necessary for backward compatibility with older snapshots.
            return self._view_list[0]

    def __init__(self, (data, bounds), src_name=None, precedence=0.0,
                 timestamp=-1, row_precedence=0.5,**params):
        self.warning('Initializing old SheetView class')
        super(SheetView,self).__init__(bounds=bounds,
                                       src_name = src_name,
                                       precedence = precedence,
                                       timestamp = timestamp,
                                       row_precedence = row_precedence, **params)
        self._view_list = []
        self.data = data


def UnitView((data, bounds), x, y, projection, timestamp, **params):
    """
    Function for backward compatibility with earlier UnitView
    component. Original docstring for UnitView:

    Consists of an X,Y position for the unit that this View is
    created for.  Subclasses SheetView.

    UnitViews should be stored in Sheets via a tuple
    ('Weights',Sheet,Projection,X,Y).  The dictionary in Sheets can be
    accessed by any valid key.
    """
    unitview = SheetView((data, bounds), projection.src.name,
                         projection.src.precedence, timestamp = timestamp,
                         row_precedence = projection.src.row_precedence, **params)

    unitview.x = x
    unitview.y = y
    unitview.projection = projection
    return unitview


class CFView(ImagenSheetView):

    situated_bounds = param.ClassSelector(class_=BoundingRegion, default=None, doc="""
        The situated bounds can be set to embed the SheetLayer in a larger
        bounded region.""")

    input_sheet_slice = param.NumericTuple(default=(0, 0, 0, 0), doc="""
        Slice indices of the embedded view into the situated matrix.""")

    @property
    def stack_type(self):
        return CFStack

    @property
    def situated(self):
        if self.bounds.lbrt() == self.situated_bounds.lbrt():
            return self
        l, b, r, t = self.bounds.lbrt()
        xd = int(np.round(self.data.shape[1] / (r-l)))
        yd = int(np.round(self.data.shape[0] / (t-b)))

        scs = SheetCoordinateSystem(self.situated_bounds, xd, yd)

        data = np.zeros(scs.shape, dtype=np.float64)
        r1, r2, c1, c2 = self.input_sheet_slice
        data[r1:r2, c1:c2] = self.data

        return ImagenSheetView(data, self.situated_bounds, roi_bounds=self.roi_bounds,
                               situated_bounds=self.situated_bounds,
                               label=self.label, value=self.value)


class CFStack(SheetStack):

    @property
    def situated(self):
        return self.map(lambda x, _: x.situated)


options.CFView = StyleOpts(interpolation='nearest')
