"""
FeatureResponses and associated functions and classes.

These classes implement map and tuning curve measurement based
on measuring responses while varying features of an input pattern.
"""

import copy

from collections import defaultdict

import numpy as np

import param
from param.parameterized import ParamOverrides

from dataviews import SheetView, SheetStack
from dataviews.ipython.widgets import ProgressBar
from dataviews.ndmapping import AttrDict

import topo
import topo.base.sheetcoords
from topo.base.sheet import Sheet
from topo.command import restore_input_generators, save_input_generators
from topo import pattern
from topo.sheet import GeneratorSheet

from featuremapper.command import PatternPresentingCommand, MeasureResponseCommand,\
    SingleInputResponseCommand, SinusoidalMeasureResponseCommand, PositionMeasurementCommand,\
    FeatureCurveCommand, UnitCurveCommand
from featuremapper import MeasurementInterrupt, DistributionMatrix, FullMatrix, FeatureResponses,\
    ReverseCorrelation, FeatureMaps, FeatureCurves, Feature
from featuremapper.metaparams import *  # pyflakes:ignore (API import)
from featuremapper.features import Time

activity_dtype = np.float64


def update_sheet_activity(sheet_name, force=False):
    """
    Update the '_activity_buffer' SheetStack for a given sheet by name.

    If force is False and the existing Activity SheetView isn't stale,
    the existing view is returned.
    """
    name = 'ActivityBuffer'
    sheet = topo.sim.objects(Sheet)[sheet_name]
    view = sheet.views.Maps.get(name, False)
    time = topo.sim.time()
    metadata = AttrDict(precedence=sheet.precedence,
                        row_precedence=sheet.row_precedence,
                        src_name=sheet.name, shape=sheet.activity.shape,
                        timestamp=time)
    if not view:
        sv = SheetView(np.array(sheet.activity), sheet.bounds)
        sv.metadata=metadata
        view = SheetStack((time, sv), dimensions=[Time])
        view.metadata = metadata
        sheet.views.Maps[name] = view
    else:
        if force or view.dim_range('Time')[1] < time:
            sv = SheetView(np.array(sheet.activity), sheet.bounds)
            sv.metadata=metadata
            view[time] = sv
    return view


def update_activity(force=False):
    """
    Make a map of neural activity available for each sheet, for use in
    template-based plots.

    This command simply asks each sheet for a copy of its activity
    matrix, and then makes it available for plotting.  Of course, for
    some sheets providing this information may be non-trivial, e.g. if
    they need to average over recent spiking activity.
    """
    for sheet_name in topo.sim.objects(Sheet).keys():
        update_sheet_activity(sheet_name, force)


class pattern_present(PatternPresentingCommand):
    """
    Given a set of input patterns, installs them into the specified
    GeneratorSheets, runs the simulation for the specified length of
    time, then restores the original patterns and the original
    simulation time.  Thus this input is not considered part of the
    regular simulation, and is usually for testing purposes.

    May also be used to measure the response to a pattern by calling
    it with restore_events disabled and restore_state and
    install_sheetview enabled, which will push and pop the simulation
    state and install the response in the sheets views dictionary. The
    update_activity command implements this functionality.

    As a special case, if 'inputs' is just a single pattern, and not
    a dictionary, it is presented to all GeneratorSheets.

    If this process is interrupted by the user, the temporary patterns
    may still be installed on the retina.

    If overwrite_previous is true, the given inputs overwrite those
    previously defined.

    If plastic is False, overwrites the existing values of Sheet.plastic
    to disable plasticity, then re-enables plasticity.

    If this process is interrupted by the user, the temporary patterns
    may still be installed on the retina.

    In order to to see the sequence of values presented, you may use
    the back arrow history mechanism in the GUI. Note that the GUI's Activity
    window must be open. Alternatively or access the activities through the
    Activity entry in the views.Maps dictionary on the specified sheets.
    """

    apply_output_fns = param.Boolean(default=True, doc="""
        Determines whether sheet output functions will be applied.
        """)

    inputs = param.Dict(default={}, doc="""
        A dictionary of GeneratorSheetName:PatternGenerator pairs to be
        installed into the specified GeneratorSheets""")

    install_sheetview = param.Boolean(default=False, doc="""Determines
        whether to install a sheet view in the global storage dictionary.""")

    plastic = param.Boolean(default=False, doc="""
        If plastic is False, overwrites the existing values of
        Sheet.plastic to disable plasticity, then reenables plasticity.""")

    overwrite_previous = param.Boolean(default=False, doc="""
        If overwrite_previous is true, the given inputs overwrite those
        previously defined.""")

    restore_events = param.Boolean(default=True, doc="""
        If True, restore simulation events after the response has been
        measured, so that no simulation time will have elapsed.
        Implied by restore_state=True.""")

    restore_state = param.Boolean(default=False, doc="""
        If True, restore the state of both sheet activities and simulation
        events
        after the response has been measured. Implies restore_events.""")

    return_responses = param.Boolean(default=False, doc="""
        If True, return a dictionary of the responses.""")

    __abstract = True

    def __call__(self, inputs={}, outputs=[], **params_to_override):
        p = ParamOverrides(self, dict(params_to_override, inputs=inputs))
        # ensure EPs get started (if pattern_response is called before the
        # simulation is run())
        topo.sim.run(0.0)

        if p.restore_state:
            topo.sim.state_push()

        if not p.overwrite_previous:
            save_input_generators()

        if not p.plastic:
            # turn off plasticity everywhere
            for sheet in topo.sim.objects(Sheet).values():
                sheet.override_plasticity_state(new_plasticity_state=False)

        if not p.apply_output_fns:
            for each in topo.sim.objects(Sheet).values():
                if hasattr(each, 'measure_maps'):
                    if each.measure_maps:
                        each.apply_output_fns = False

        # Register the inputs on each input sheet
        generatorsheets = topo.sim.objects(GeneratorSheet)

        if not isinstance(p.inputs, dict):
            for g in generatorsheets.values():
                g.set_input_generator(p.inputs)
        else:
            for each in p.inputs.keys():
                if generatorsheets.has_key(each):
                    generatorsheets[each].set_input_generator(p.inputs[each])
                else:
                    param.Parameterized().warning(
                        '%s not a valid Sheet name for pattern_present.' % each)

        if p.restore_events:
            topo.sim.event_push()

        durations = np.diff([0] + p.durations)
        projection_dict = dict((conn.name, conn) for conn in topo.sim.connections())
        outputs = outputs if len(outputs) > 0 else topo.sim.objects(Sheet).keys() + projection_dict.keys()

        responses = defaultdict(dict)
        for i, d in enumerate(durations):
            topo.sim.run(d)
            time = p.durations[i]
            if hasattr(topo, 'guimain'):
                update_activity(p.install_sheetview)
                topo.guimain.refresh_activity_windows()
            if p.return_responses:

                for output in outputs:
                    if output in topo.sim.objects(Sheet).keys():
                        responses[(output, time)] = topo.sim[output].activity.copy()
                    elif output in projection_dict:
                        responses[(output, time)] = projection_dict[output].activity.copy()

        if p.restore_events:
            topo.sim.event_pop()

        # turn sheets' plasticity and output_fn plasticity back on if we
        # turned it off before
        if not p.plastic:
            for sheet in topo.sim.objects(Sheet).values():
                sheet.restore_plasticity_state()

        if not p.apply_output_fns:
            for each in topo.sim.objects(Sheet).values():
                each.apply_output_fns = True

        if not p.overwrite_previous:
            restore_input_generators()

        if p.restore_state:
            topo.sim.state_pop()

        return responses



class pattern_response(pattern_present):
    """
    This command is used to perform measurements, which require a
    number of permutations to complete. The inputs and outputs are
    defined as dictionaries corresponding to the generator sheets they
    are to be presented on and the measurement sheets to record from
    respectively. The update_activity_fn then accumulates the updated
    activity into the appropriate entry in the outputs dictionary.

    The command also makes sure that time, events and state are reset
    after each presentation. If a GUI is found a timer will be opened
    to display a progress bar and sheet_views will be made available
    to the sheet to display activities.
    """

    restore_state = param.Boolean(default=True, doc="""
        If True, restore the state of both sheet activities and
        simulation events after the response has been measured.
        Implies restore_events.""")

    return_responses = param.Boolean(default=True, doc="""
        If True, return a dictionary of the measured sheet activities.""")

    def __call__(self, inputs={}, outputs=[], current=0, total=1, **params):
        all_input_names = topo.sim.objects(GeneratorSheet).keys()

        if 'default' in inputs:
            for input_name in all_input_names:
                inputs[input_name] = inputs['default']
            del inputs['default']

        for input_name in set(all_input_names).difference(set(inputs.keys())):
            inputs[input_name] = pattern.Constant(scale=0)

        if current == 0:
            self.timer = copy.copy(topo.sim.timer)
            self.timer.stop = False
            self._progress = current
            if hasattr(topo, 'guimain'):
                topo.guimain.open_progress_window(self.timer)
                self.install_sheetview = True
                self.progressbar = None
            else:
                self.progressbar = ProgressBar(label='Measurement Progress')
        if self.timer.stop:
            raise MeasurementInterrupt(current, total)
        self.timer.update_timer('Measurement Timer', current, total)
        progress = float(current)/total*100 if total else 100
        if self.progressbar and (progress > self._progress or progress == 100):
            self._progress = progress + 1 # +1 reduces fast updates/flicker
            self.progressbar(progress)

        responses = super(pattern_response, self).__call__(inputs=inputs,
                                                           outputs=outputs,
                                                           **params)

        if hasattr(topo, 'guimain') and current == total:
            topo.guimain.refresh_activity_windows()

        return responses



def topo_metadata_fn(input_names=[], output_names=[]):
    """
    Return the shapes of the specified GeneratorSheets and measurement
    sheets, or if none are specified return all that can be found in
    the simulation.
    """
    metadata = AttrDict()
    metadata['timestamp'] = topo.sim.time()

    generator_sheets = topo.sim.objects(GeneratorSheet)
    all_sheets = dict((n, s) for n, s in topo.sim.objects(Sheet).items())
    measurement_sheets = dict((n, s) for n, s in topo.sim.objects(Sheet).items()
                              if hasattr(s, 'measure_maps') and s.measure_maps)
    projections = dict((conn.name, conn) for conn in topo.sim.connections())

    if input_names == []:
        input_names = generator_sheets.keys()

    metadata['inputs'] = {}
    for i in input_names:
        if i in generator_sheets:
            gs = generator_sheets[i]
            metadata['inputs'][i] = {'bounds': gs.bounds, 'precedence': gs.precedence,
                                     'row_precedence': gs.row_precedence,
                                     'shape': gs.shape, 'src_name': gs.name}
        else:
            topo.sim.warning('Input sheet {0} not found.'.format(i))

    if output_names == []:
        output_names = measurement_sheets.keys()

    metadata['outputs'] = {}
    for o in output_names:
        if o in all_sheets:
            s = all_sheets[o]
            metadata['outputs'][o] = {'bounds': s.bounds, 'precedence': s.precedence,
                                      'row_precedence': s.row_precedence,
                                      'shape': s.shape, 'src_name': s.name}
        elif o in projections:
            p = projections[o]
            metadata['outputs'][o] = {'bounds': p.dest.bounds, 'precedence': p.dest.precedence,
                                      'row_precedence': p.dest.row_precedence,
                                      'shape': p.dest.shape, 'dest_name': p.dest.name,
                                      'src_name': p.src.name}
        else:
            topo.sim.warning('Output sheet {0} not found.'.format(o))

    return metadata


class StorageHook(param.ParameterizedFunction):

    sublabel = param.String(default=None, allow_None=True, doc="""
        Storage location on the sheet specific view object. If None simply
        inserts results into top level views object.""")

    only_latest = param.Boolean(default=True, doc="""
        Whether to replace any existing results in the global AttrTree.""")

    def __call__(self, viewcontainer, **params):
        p = ParamOverrides(self, params)
        objects = dict(topo.sim.objects(), **dict([(proj.name, proj) for proj in topo.sim.connections()]))
        for path, container in viewcontainer.path_items.items():
            label, src_name = path
            source = objects[src_name]
            if isinstance(source, Sheet):
                storage = source.views[p.sublabel] if p.sublabel else source.views
            else:
                proj_store = source.dest.views[source.name] = {}
                proj_store[p.sublabel] = {}
                storage = proj_store[p.sublabel]
            if label not in storage or p.only_latest:
                storage[label] = container
            else:
                storage[label].update(container)


def get_feature_preference(feature, sheet_name, coords, default=0.0):
    """Return the feature preference for a particular unit."""
    try:
        sheet = topo.sim[sheet_name]
        map_name = feature.capitalize() + "Preference"
        x, y = coords
        return sheet.views.Maps[map_name].last[x, y]
    except:
        topo.sim.warning(
            ("%s should be measured before plotting this tuning curve -- "
             "using default value of %s for %s unit (%d,%d).") %
            (map_name, default, sheet.name, x, y))
        return default


__all__ = [
    "DistributionMatrix",
    "FullMatrix",
    "FeatureResponses",
    "ReverseCorrelation",
    "FeatureMaps",
    "FeatureCurves",
    "Feature",
    "MeasureResponseCommand",
    "SinusoidalMeasureResponseCommand",
    "PositionMeasurementCommand",
    "SingleInputResponseCommand",
    "FeatureCurveCommand",
    "UnitCurveCommand",
    "pattern_present",
    "pattern_response",
    "update_activity",
    "update_sheet_activity"
]
