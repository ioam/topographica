"""
User-level analysis commands, typically for measuring or generating
SheetViews.

This file mostly consists of plotgroup declarations for existing
measurement commands defined in the FeatureMapper project. It also
implements several Topographica specific measurement commands,
including activity measurements (implemented by update_activity())
and weight matrix visualizations (e.g. update_projection).

The implementation of Activity plots for instance consists of the
update_activity() command plus the Activity PlotGroupTemplate.  The
update_activity() command reads the activity array of each Sheet and
makes a corresponding SheetView to put in the Sheet's sheet_views
dictionary, while the Activity PlotGroupTemplate specifies which
SheetViews should be plotted in which combination.  See the help for
PlotGroupTemplate for more information.
"""

import numpy as np

from imagen.views import SheetView, SheetStack

from featuremapper.command import * # pyflakes:ignore (API import)

import param
from param import ParameterizedFunction, ParamOverrides

import topo
from topo.base.cf import CFSheet, Projection
from topo.base.sheet import Sheet
from topo.base.arrayutil import centroid

from topo.analysis.featureresponses import pattern_present, pattern_response, update_activity # pyflakes:ignore (API import)


class ProjectionSheetMeasurementCommand(param.ParameterizedFunction):
    """A callable Parameterized command for measuring or plotting a specified Sheet."""

    outputs = param.List(default=[],doc="""
        List of sheets to use in measurements.""")

    __abstract = True



class UnitMeasurementCommand(ProjectionSheetMeasurementCommand):
    """A callable Parameterized command for measuring or plotting specified units from a Sheet."""

    coords = param.List(default=[(0,0)],doc="""
        List of coordinates of unit(s) to measure.""")

    projection = param.ObjectSelector(default=None,doc="""
        Name of the projection to measure; None means all projections.""")

    __abstract = True

    def __call__(self,**params):
        p=ParamOverrides(self,params)
        for output in p.outputs:
            s = getattr(topo.sim,output,None)
            if s is not None:
                for x,y in p.coords:
                    s.update_unit_view(x,y,'' if p.projection is None else p.projection.name)


def update_rgb_activities():
    """
    Make available Red, Green, and Blue activity matrices for all appropriate sheets.
    """
    for sheet in topo.sim.objects(Sheet).values():
        metadata = dict(bounds=sheet.bounds,src_name=sheet.name,
                        precedence=sheet.precedence,
                        row_precedence=sheet.row_precedence,
                        timestamp=topo.sim.time())
        for c in ['Red','Green','Blue']:
            # should this ensure all of r,g,b are present?
            if hasattr(sheet,'activity_%s'%c.lower()):
                activity_copy = getattr(sheet,'activity_%s'%c.lower()).copy()
                new_view = SheetView(activity_copy,**metadata)
                sheet.views.maps['%sActivity'%c]=new_view



class update_connectionfields(UnitMeasurementCommand):
    """A callable Parameterized command for measuring or plotting a unit from a Projection."""

    # Force plotting of all CFs, not just one Projection
    projection = param.ObjectSelector(default=None,constant=True)



class update_projection(UnitMeasurementCommand):
    """A callable Parameterized command for measuring or plotting units from a Projection."""



class measure_projection(param.ParameterizedFunction):

    rows = param.Number(default=10, doc="Number of CF rows.")

    cols = param.Number(default=10, doc="Number of CF columns.")

    projection = param.ObjectSelector(default=None, constant=True)

    def __call__(self, **params):
        p = ParamOverrides(self, params)
        return p.projection.grid(p.rows, p.cols)



class update_projectionactivity(ProjectionSheetMeasurementCommand):
    """
    Add SheetViews for all of the Projections of the ProjectionSheet
    specified by the sheet parameter, for use in template-based plots.
    """

    def __call__(self, **params):
        p = ParamOverrides(self, params)
        for sheet_name in p.outputs:
            s = getattr(topo.sim, sheet_name, None)
            if s is not None:
                for conn in s.in_connections:
                    if not isinstance(conn,Projection):
                        topo.sim.debug("Skipping non-Projection "+conn.name)
                    else:
                        v = conn.projection_view(topo.sim.time())
                        key = v.metadata.proj_name + 'ProjectionActivity'
                        topo.sim[v.metadata.src_name].views.maps[key] = v



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
        rows, cols = sheet.activity.shape
        xpref = np.zeros((rows, cols), np.float64)
        ypref = np.zeros((rows, cols), np.float64)

        for r in xrange(rows):
            for c in xrange(cols):
                cf = proj.cfs[r, c]
                r1, r2, c1, c2 = cf.input_sheet_slice
                row_centroid, col_centroid = centroid(cf.weights)
                xcentroid, ycentroid = proj.src.matrix2sheet(
                    r1 + row_centroid + 0.5,
                    c1 + col_centroid + 0.5)

                xpref[r][c]= xcentroid
                ypref[r][c]= ycentroid

        metadata = dict(precedence=sheet.precedence, row_precedence=sheet.row_precedence,
                        src_name=sheet.name)

        timestamp=topo.sim.time()

        xpref_sv = SheetView(xpref, sheet.bounds)
        ypref_sv = SheetView(ypref, sheet.bounds)

        sheet.views.maps['XCoG'] = SheetStack((timestamp, xpref_sv), **metadata)

        sheet.views.maps['YCoG'] = SheetStack((timestamp, ypref_sv), **metadata)


import types

__all__ = list(set([k for k, v in locals().items()
                    if isinstance(v, types.FunctionType) or (isinstance(v, type)
                    and issubclass(v, ParameterizedFunction))
                    and not v.__name__.startswith('_')]))
