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

import copy
import time
import sys

import numpy as np

import param
from param import ParameterizedFunction, ParamOverrides

from dataviews import SheetView, SheetStack, SheetLines, CoordinateGrid

from featuremapper.command import * # pyflakes:ignore (API import)

import topo
from topo.base.cf import CFSheet, Projection
from topo.base.sheet import Sheet
from topo.base.arrayutil import centroid
from topo.misc.attrdict import AttrDict
from topo.base.cf import CFProjection
from topo.analysis.featureresponses import pattern_present, pattern_response, update_activity  # pyflakes:ignore (API import)


class Collector(param.Parameterized):
    """
    A Collector collects the results of measurements over time,
    allowing any measurement to be easily saved as an animation. The
    output of any measurement can be recorded as well as sheet
    activities, projection CFs or projection activities:

    c = Collector()
    with r(100, steps=10):
       c.collect(topo.sim.V1)      # c.V1.Activity
       c.collect(measure_or_pref)  # c.V1.OrientationPreference etc.
       c.collect(measure_cog)      # c.V1.Afferent.CoG
       c.collect(topo.sim.V1.Afferent)  # c.V1.Afferent.CFGrid
       c.collect(topo.sim.V1.Afferent,  # c.V1.Afferent.Activity
                            activity=True)

   Once completed, the data may be easy obtained via attribute access
   as shown in the comments above. You may also pass keywords to the
   measurement via the record method or the sampling density (rows,
   cols) when recording CFs from projections.
    """


    measurements = param.List(default=[], doc="""
        A list of tuples of form (obj, kwargs) where obj may be a
        measurement class, a sheet or a projection.""")

    class group(object):
        """
        Container class for convenient attribute access.
        """
        def __repr__(self):
            return "Keys:\n   %s" % "\n   ".join(self.__dict__.keys())

    def __init__(self, **kwargs):
        super(Collector,self).__init__(**kwargs)

    def _projection_CFs(self, projection, **kwargs):
        """
        Record the CFs of a projection as a ProjectionGrid.
        """
        data = measure_projection.instance(projection=projection, **kwargs)()
        sheet = data.metadata['proj_dest_name']
        projection = data.metadata['info']
        projection_CFs = {}
        projection_CFs[sheet] = {}
        projection_CFs[sheet][projection] = {}
        projection_CFs[sheet][projection]['CFGrid'] = data
        return projection_CFs

    def _projection_activity(self, projection, **kwargs):
        """
        Record the projection activity of a projection.
        """
        sview = projection.projection_view()
        sheet = sview.metadata['src_name']
        stack = SheetStack(title=projection.name, bounds=sview.bounds,
                           initial_items=[(topo.sim.time(), sview)],
                           dimension_labels=['Time'],
                           time_type=[topo.sim.time.time_type])
        proj_name = sview.metadata['proj_name']
        projection_activity = {}
        projection_activity[sheet] = {}
        projection_activity[sheet][proj_name] = {}
        projection_activity[sheet][proj_name]['Activity'] = stack
        return projection_activity

    def _projection_measurement(self, projection, activity=False, **kwargs):
        """
        Record the CFs of a projection as a ProjectionGrid or record
        the projection activity SheetView.
        """
        if activity:
            return self._projection_activity(projection, **kwargs)
        else:
            return self._projection_CFs(projection, **kwargs)

    def _sheet_activity(self, sheet):
        """
        Given a sheet, return the data as a measurement in the
        appropriate dictionary format.
        """
        sview = sheet[:]
        stack = SheetStack(title=sview.name, bounds=sview.bounds,
                          initial_items=[(1.0,sview)], key_type=[float]) # topo.sim.time()
        activity_data = {}
        activity_data[sheet.name] = {}
        activity_data[sheet.name]['Activity'] =  stack
        return activity_data

    def _get_measurement(self, item):
        """
        Method to declare the measurements to collect views
        from. Accepts measurement classes or instances, sheet
        objects(to measure sheet activity) and projection objects (to
        measure CFs or projection activities).
        """
        if isinstance(item, tuple):
            obj, kwargs = item
        else:
            obj, kwargs = item, {}

        if isinstance(obj, CFProjection):
            return lambda :self._projection_measurement(obj, **kwargs)
        elif isinstance(obj, Sheet):
            return lambda: self._sheet_activity(obj)
        else:
            return obj.instance(**kwargs)

    def collect(self, obj, **kwargs):

        items = [self._formatter(el) for el in self.measurements]
        if kwargs:
            fmt = self._formatter((obj, kwargs))
            if fmt in items:
                raise Exception("%r already being recorded." % fmt)
            self.measurements.append((obj, kwargs))
        else:
            fmt = self._formatter(obj)
            if fmt in items:
                raise Exception("%r already being recorded." % fmt)
            self.measurements.append(obj)

    def save_entry(self, sheet_name, feature_name, data, projection=None):
        """
        Create or update entries, dynamically creating attributes for
        convenient access as necessary.
        """
        if not hasattr(self, sheet_name):
            setattr(self, sheet_name, self.group())
        group = getattr(self, sheet_name)

        if projection is not None:
            if not hasattr(group, projection):
                setattr(group, projection, self.group())
            group = getattr(group, projection)

        time_type = param.Dynamic.time_fn

        if 'Time' not in data.dimension_labels and not isinstance(data, CoordinateGrid):
            timestamped_data = data.add_dimension('Time', 0,
                                                  topo.sim.time(),
                                                  time_type)
        else:
            timestamped_data = data

        if not hasattr(group, feature_name):
            setattr(group, feature_name, timestamped_data)
        else:
            getattr(group, feature_name).update(timestamped_data)

    def _record_data(self, measurement_data):
        """
        Given measurement data in the standard dictionary format
        record the elements. The dictionary may be indexed by sheet
        name then by feature name (e.g. sheet measurements) or by
        sheet name, then projection name before the feature name
        (projection measurements).
        """
        for sheet_name in measurement_data:
            for name in measurement_data[sheet_name]:
                data = measurement_data[sheet_name][name]
                # Data may be a feature, or dictionary of projection labels
                if not isinstance(data, dict):
                    # Indexed by sheet name and feature name
                    self.save_entry(sheet_name, name, data, None)
                else:
                    # Indexed by sheet and projection name before the feature.
                    for feature_name in data:
                        self.save_entry(sheet_name, feature_name,
                                         data[feature_name], name)

    def run(self, durations, cycles=1):
        try:
            self.durations = list(durations) * cycles
        except:
            self.durations = [durations] * cycles
        return self


    def __enter__(self):
        self._old_measurements = self.measurements
        self.measurements = []
        return self

    def __exit__(self, exc, *args):
        self.advance(self.durations)
        self.measurements = self._old_measurements


    def advance(self, durations):
        measurements = [self._get_measurement(item) for item in self.measurements]
        for i,duration in enumerate(durations):
            try:
                # clear_output is needed to avoid displaying garbage
                # in static HTML notebooks.
                from IPython.core.display import clear_output
                clear_output()
            except:
                pass
            for measurement in measurements:
                measurement_data = measurement()
                self._record_data(copy.deepcopy(measurement_data))
            info = (i+1, len(durations), topo.sim.time())
            msg = "%d/%d measurement cycles complete. Simulation Time=%s" % info
            print '\r', msg
            sys.stdout.flush()
            time.sleep(0.0001)
            topo.sim.run(duration)
        print "Completed collection. Simulation Time=%s" % topo.sim.time()

    def _formatter(self, item):
        if isinstance(item, tuple):
            (obj, kwargs) = item
            return '(%s, %s)' % (obj.name, kwargs)
        else:
            return item.name

    def __repr__(self):

        if self.measurements == []:
            return 'Collector()'
        items = [self._formatter(el) for el in self.measurements]
        return 'Collector([%s])' % ', '.join(items)




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
        metadata = AttrDict(src_name=sheet.name, precedence=sheet.precedence,
                            row_precedence=sheet.row_precedence,
                            timestamp=topo.sim.time())
        for c in ['Red','Green','Blue']:
            # should this ensure all of r,g,b are present?
            if hasattr(sheet,'activity_%s'%c.lower()):
                activity_copy = getattr(sheet,'activity_%s'%c.lower()).copy()
                new_view = SheetView(activity_copy, bounds=sheet.bounds, metadata=metadata)
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

    stride = param.Integer(default=1, doc="Stride by which to skip grid lines"
                                          "in the CoG Wireframe.")

    def __call__(self, **params):
        p = ParamOverrides(self, params)

        measured_sheets = [s for s in topo.sim.objects(CFSheet).values()
                           if hasattr(s,'measure_maps') and s.measure_maps]

        results = {}

        # Could easily be extended to measure CoG of all projections
        # and e.g. register them using different names (e.g. "Afferent
        # XCoG"), but then it's not clear how the PlotGroup would be
        # able to find them automatically (as it currently supports
        # only a fixed-named plot).
        requested_proj=p.proj_name
        for sheet in measured_sheets:
            if sheet not in results:
                results[sheet.name] = {}
            for proj in sheet.in_connections:
                if (proj.name == requested_proj) or \
                   (requested_proj == '' and (proj.src != sheet)):
                   results[sheet.name][proj.name] = self._update_proj_cog(p, proj)

        return results


    def _update_proj_cog(self, p, proj):
        """Measure the CoG of the specified projection and register corresponding SheetViews."""

        sheet = proj.dest
        rows, cols = sheet.activity.shape
        xcog = np.zeros((rows, cols), np.float64)
        ycog = np.zeros((rows, cols), np.float64)

        for r in xrange(rows):
            for c in xrange(cols):
                cf = proj.cfs[r, c]
                r1, r2, c1, c2 = cf.input_sheet_slice
                row_centroid, col_centroid = centroid(cf.weights)
                xcentroid, ycentroid = proj.src.matrix2sheet(
                    r1 + row_centroid + 0.5,
                    c1 + col_centroid + 0.5)

                xcog[r][c] = xcentroid
                ycog[r][c] = ycentroid

        metadata = dict(precedence=sheet.precedence, row_precedence=sheet.row_precedence,
                        src_name=sheet.name, dimension_labels=['Time'], key_type=[topo.sim.time.time_type])

        timestamp = topo.sim.time()
        xsv = SheetView(xcog, sheet.bounds)
        ysv = SheetView(ycog, sheet.bounds)

        lines = []
        hlines, vlines = xsv.data.shape
        for hind in range(hlines)[::p.stride]:
            lines.append(np.vstack([xsv.data[hind,:].T, ysv.data[hind,:]]).T)
        for vind in range(vlines)[::p.stride]:
            lines.append(np.vstack([xsv.data[:,vind].T, ysv.data[:,vind]]).T)

        xcog_stack = SheetStack((timestamp, xsv), **metadata)
        ycog_stack = SheetStack((timestamp, ysv), **metadata)
        contour_stack = SheetStack((timestamp, SheetLines(lines, sheet.bounds)), **metadata)

        if 'XCoG' in sheet.views.maps:
            sheet.views.maps['XCoG'].update(xcog_stack)
        else:
            sheet.views.maps['XCoG'] = xcog_stack

        if 'YCoG' in sheet.views.maps:
            sheet.views.maps['YCoG'].update(ycog_stack)
        else:
            sheet.views.maps['YCoG'] = ycog_stack

        if 'CoG' in sheet.views.maps:
            sheet.views.maps['CoG'].update(contour_stack)
        else:
            sheet.views.maps['CoG'] = contour_stack

        return {'XCoG': xcog_stack, 'YCoG': ycog_stack, 'CoG': contour_stack}


import types

__all__ = list(set([k for k, v in locals().items()
                    if isinstance(v, types.FunctionType) or (isinstance(v, type)
                    and issubclass(v, ParameterizedFunction))
                    and not v.__name__.startswith('_')]))
