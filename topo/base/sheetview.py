"""
Topographica SheetView objects and its subclasses.

For use with the Topographica plotting and data analysis mechanisms.
A Sheet object has its internal data which remains hidden, but it will
create views of this data depending on the Sheet defaults or the
information requested.  This way there can be multiple views recorded
for a single sheet, and a view can be passed around independent of the
originating source object.
"""

try:      from imagen.dataviews import Cartesian2Dx
except:   raise Exception("Imagen submodule needs to be updated - please run `git submodule update' and try again.")

try:
    from collections import OrderedDict
except ImportError:
    from topo.misc.odict import OrderedDict
except ImportError:
    OrderedDict = None

import param

class SheetView(Cartesian2Dx):
    """
    Class provided for backward compatibility with earlier SheetView
    component.
    """

    src_name = param.String(default = None, allow_None=True)

    precedence = param.Number(default=0.0)

    row_precedence = param.Number(default=0.5)

    cyclic = param.Boolean(False, doc="""If cyclic is True, this value is the cyclic range.""")

    cyclic_range = param.Parameter(None)


    def __init__(self, (data, bounds), src_name=None, precedence=0.0,
                 timestamp=-1, row_precedence=0.5, **kwargs):

        self.map_type = OrderedDict
        super(SheetView,self).__init__(bounds, src_name=src_name,
                                       precedence=precedence,
                                       timestamp = timestamp,
                                       row_precedence = row_precedence,
                                       **kwargs)
        self.record(data.copy(), timestamp)


    def view(self):
        """
        Return the requested view as a (data, bbox) tuple.  Provided
        for backward compatibility with the original Topographica
        SheetView model. It is now easier to access the data and
        bounds attributes directly.
        """
        if hasattr(self, '_data'):
            return (self._data[-1], self.bounds)
        else: # Necessary for backward compatibility with older snapshots.
            return self._view_list[0]


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
