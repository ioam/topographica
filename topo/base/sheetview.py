"""
Topographica SheetView objects and its subclasses.

For use with the Topographica plotting and data analysis mechanisms.
A Sheet object has its internal data which remains hidden, but it will
create views of this data depending on the Sheet defaults or the
information requested.  This way there can be multiple views recorded
for a single sheet, and a view can be passed around independent of the
originating source object.
"""

import param

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
        return (self.data, self.bounds)

    def __init__(self, (data, bounds), src_name=None, precedence=0.0,
                 timestamp=-1, row_precedence=0.5):
        super(SheetView,self).__init__(bounds=bounds,
                                       src_name = src_name,
                                       precedence = precedence,
                                       timestamp = timestamp,
                                       row_precedence = row_precedence)
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


def ProjectionView((data, bounds), projection, timestamp,**params):
    """
    Function for backward compatibility with earlier ProjectionView
    compoennt. Original docstring for ProjectionView:

    ProjectionViews should be stored in Sheets via a tuple
    ('Weights',Sheet,Projection).
    """
    projectionview = SheetView((data, bounds), projection.src.name,
                               projection.src.precedence, timestamp,
                               row_precedence = projection.src.row_precedence, **params)
    projectionview.projection = projection
    return projectionview
