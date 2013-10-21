"""
FeatureResponses and associated functions and classes.

These classes implement map and tuning curve measurement based
on measuring responses while varying features of an input pattern.
"""

import copy

from math import pi
from colorsys import hsv_to_rgb

import numpy as np

import param
from param.parameterized import ParameterizedFunction, ParamOverrides, \
    bothmethod

from imagen.dataview import SheetView, ProjectionGrid, FeatureRangeMap
from imagen.sheetcoords import SheetCoordinateSystem

import topo
import topo.base.sheetcoords
from topo.base.arrayutil import wrap
from topo.base.functionfamily import PatternDrivenAnalysis
from topo.base.sheet import Sheet, activity_type
from topo.command import restore_input_generators, save_input_generators
from topo.misc.distribution import Distribution, DistributionStatisticFn, \
    DSF_MaxValue, DSF_WeightedAverage
from topo.misc.util import cross_product, frange
from topo.misc.attrdict import AttrDict
from topo import pattern
from topo.pattern import SineGrating, Gaussian, RawRectangle, Disk
from topo.plotting.plotgroup import plotgroups
from topo.sheet import GeneratorSheet


activity_dtype = np.float64

# CB: having a class called DistributionMatrix with an attribute
# distribution_matrix to hold the distribution matrix seems silly.
# Either rename distribution_matrix or make DistributionMatrix into
# a matrix.
class DistributionMatrix(param.Parameterized):
    """
    Maintains a matrix of Distributions (each of which is a dictionary
    of (feature value: activity) pairs).

    The matrix contains one Distribution for each unit in a
    rectangular matrix (given by the matrix_shape constructor
    argument).  The contents of each Distribution can be updated for a
    given bin value all at once by providing a matrix of new values to
    update().

    The results can then be accessed as a matrix of weighted averages
    (which can be used as a preference map) and/or a selectivity map
    (which measures the peakedness of each distribution).
    """

    def __init__(self, matrix_shape, axis_range=(0.0, 1.0), cyclic=False,
                 keep_peak=True):
        """Initialize the internal data structure: a matrix of Distribution
        objects."""
        self.axis_range = axis_range
        new_distribution = np.vectorize(
            lambda x: Distribution(axis_range, cyclic, keep_peak),
            doc="Return a Distribution instance for each element of x.")
        self.distribution_matrix = new_distribution(np.empty(matrix_shape))


    def update(self, new_values, bin):
        """Add a new matrix of histogram values for a given bin value."""
        ### JABHACKALERT!  The Distribution class should override +=,
        ### rather than + as used here, because this operation
        ### actually modifies the distribution_matrix, but that has
        ### not yet been done.  Alternatively, it could use a different
        ### function name altogether (e.g. update(x,y)).
        self.distribution_matrix + np.fromfunction(
            np.vectorize(lambda i, j: {bin: new_values[i, j]}),
            new_values.shape)

    def apply_DSF(self, dsf):
        """
        Apply the given dsf DistributionStatisticFn on each element of
        the distribution_matrix

        Return a dictionary of dictionaries, with the same structure
        of the called DistributionStatisticFn, but with matrices as
        values, instead of scalars
        """

        shape = self.distribution_matrix.shape
        result = {}

        # this is an extra call to the dsf() DistributionStatisticFn,
        # in order to retrieve
        # the dictionaries structure, and allocate the necessary matrices
        r0 = dsf(self.distribution_matrix[0, 0])
        for k, maps in r0.items():
            result[k] = {}
            for m in maps.keys():
                result[k][m] = np.zeros(shape, np.float64)

        for i in range(shape[0]):
            for j in range(shape[1]):
                response = dsf(self.distribution_matrix[i, j])
                for k, d in response.items():
                    for item, item_value in d.items():
                        result[k][item][i, j] = item_value

        return result


class FullMatrix(param.Parameterized):
    """
    Records the output of every unit in a sheet, for every combination
    of feature values.  Useful for collecting data for later analysis
    while presenting many input patterns.
    """

    def __init__(self, matrix_shape, features):
        self.matrix_shape = matrix_shape
        self.features = features
        self.dimensions = ()
        for f in features:
            self.dimensions = self.dimensions + (np.size(f.values),)
        self.full_matrix = np.empty(self.dimensions, np.object_)


    def update(self, new_values, feature_value_permutation):
        """Add a new matrix of histogram values for a given bin value."""
        index = ()
        for f in self.features:
            for ff, value in feature_value_permutation:
                if (ff == f.name):
                    index = index + (f.values.index(value),)
        self.full_matrix[index] = new_values


class FeatureResponses(PatternDrivenAnalysis):
    """
    Systematically vary input pattern feature values and collate the
    responses.

    A DistributionMatrix for each measurement source and feature is
    created.  The DistributionMatrix stores the distribution of
    activity values for that feature.  For instance, if the features
    to be tested are orientation and phase, we will create a
    DistributionMatrix for orientation and a DistributionMatrix for
    phase for each measurement source.  The orientation and phase of
    the input are then systematically varied (when measure_responses
    is called), and the responses of all units from a measurement
    source to each pattern are collected into the DistributionMatrix.

    The resulting data can then be used to plot feature maps and
    tuning curves, or for similar types of feature-based analyses.
    """

    cmd_overrides = param.Dict(default={}, doc="""
        Dictionary used to overwrite default values of the
        pattern_response_fn.""")

    inputs = param.String(default=[], doc="""Names of the input supplied to
        the metadata_fns to filter out desired inputs.""")

    metadata_fns = param.HookList(default=[], instantiate=False, doc="""
        Interface functions for metadata. Should return a dictionary
        that at a minimum must contain the name and dimensions of the
        inputs and outputs for pattern presentation and response
        measurement.""")

    metafeature_fns = param.HookList(default=[], doc="""
        Metafeature functions can be used to coordinate lower level
        features across input devices or depending on a metafeature
        set on the function itself.""")

    measurement_prefix = param.String(default="", doc="""
        Prefix to add to the name under which results are stored.""")

    measurement_storage_hook = param.Callable(default=None, instantiate=True,
                                              doc="""
        Interface to store measurements after they have been completed.""")

    outputs = param.String(default=[], doc="""
        Names of the output source supplied to metadata_fns to filter out
        desired outputs.""")

    param_dict = param.Dict(default={}, doc="""
        Dictionary containing name value pairs of a feature, which is to
        be varied across measurements.""")

    pattern_generator = param.Callable(instantiate=True, default=None, doc="""
        Defines the input pattern to be presented.""")

    pattern_response_fn = param.Callable(default=None, instantiate=True, doc="""
        Presenter command responsible for presenting the input
        patterns provided to it, returning measurement labels and
        collecting and storing the measurement results in the
        appropriate place.""")

    repetitions = param.Integer(default=1, bounds=(1, None), doc="""
        How many times each stimulus will be presented.

        Each stimulus is specified by a particular feature
        combination, and need only be presented once if the network
        has no other source of variability.  If results differ for
        each presentation of an identical stimulus (e.g. due to
        intrinsic noise), then this parameter can be increased
        so that results will be an average over the specified
        number of repetitions.""")

    store_fullmatrix = param.Boolean(default=False, doc="""
        Determines whether or not store the full matrix of feature
        responses as a class attribute.""")

    metadata = {}

    _fullmatrix = {}

    __abstract = True

    def _initialize_featureresponses(self, p):
        """
        Create an empty DistributionMatrix for each feature and each
        measurement source, in addition to activity buffers and if
        requested, the full matrix.
        """
        self._apply_cmd_overrides(p)
        for fn in p.metadata_fns:
            self.metadata = AttrDict(p.metadata, **fn(p.inputs, p.outputs))

        self._featureresponses = {}
        self._activities = {}

        for output_label, output_metadata in self.metadata.outputs.items():
            self._featureresponses[output_label] = {}
            self._activities[output_label] = np.zeros(output_metadata['shape'])
            for f in self.features:
                self._featureresponses[output_label][f.name] = \
                    DistributionMatrix(output_metadata['shape'],
                                       axis_range=f.range,
                                       cyclic=f.cyclic)
            if p.store_fullmatrix:
                self._fullmatrix[output_label] = FullMatrix(output_metadata['shape'],
                                                            self.features)


    def _measure_responses(self, p):
        """
        Generate feature permutations and present each in sequence.
        """

        # Run hooks before the analysis session
        for f in p.pre_analysis_session_hooks: f()

        features_to_permute = [f for f in self.features if f.compute_fn is None]
        self.features_to_compute = [f for f in self.features
                                    if f.compute_fn is not None]

        self.feature_names = [f.name for f in features_to_permute]
        values_lists = [f.values for f in features_to_permute]

        self.permutations = cross_product(values_lists)

        self.total_steps = len(self.permutations) * p.repetitions - 1
        for permutation_num, permutation in enumerate(self.permutations):
            try:
                self._present_permutation(p, permutation, permutation_num)
            except MeasurementInterrupt as MI:
                self.warning(
                    "Measurement was stopped after {current} out of {total} "
                    "presentations. " \
                    "Results may be incomplete.".format(current=MI.current,
                                                        total=MI.total))
                break

        # Run hooks after the analysis session
        for f in p.post_analysis_session_hooks: f()


    def _present_permutation(self, p, permutation, permutation_num):
        """Present a pattern with the specified set of feature values."""
        for output_label in self.metadata.outputs:
            self._activities[output_label] *= 0

        # Calculate complete set of settings
        permuted_settings = zip(self.feature_names, permutation)
        complete_settings = permuted_settings + \
                            [(f.name, f.compute_fn(permuted_settings))
                             for f in self.features_to_compute]

        for i in xrange(0, p.repetitions):
            for f in p.pre_presentation_hooks:
                f()

            inputs = self._coordinate_inputs(p, dict(permuted_settings))
            responses = p.pattern_response_fn(inputs,
                                              self.metadata['outputs'].keys(),
                                              p.repetitions * permutation_num+i,
                                              self.total_steps)

            for f in p.post_presentation_hooks:
                f()

            for response_label, response in responses.items():
                self._activities[response_label] += response

        for response_label in responses:
            self._activities[response_label] = self._activities[response_label] / p.repetitions

        self._update(p, complete_settings)


    def _coordinate_inputs(self, p, feature_values):
        """
        Generates pattern generators for all the requested inputs,
        applies the correct feature values and iterates through
        metafeature_fns, coordinating complex features.
        """

        input_names = self.metadata.inputs.keys()

        feature_values = dict(feature_values, **p.param_dict)

        for feature, value in feature_values.iteritems():
            setattr(p.pattern_generator, feature, value)

        if len(input_names) == 0:
            input_names = ['default']

        # Copy the given generator once for every input
        inputs = dict.fromkeys(input_names)
        for k in inputs.keys():
            inputs[k] = copy.deepcopy(p.pattern_generator)

        # Apply metafeature_fns
        for fn in p.metafeature_fns:
            fn(inputs, feature_values)

        return inputs


    def _update(self, p, current_values):
        """
        Update each DistributionMatrix with (activity,bin) and
        populate the full matrix, if enabled.
        """
        for output_label in self.metadata.outputs:
            for feature, value in current_values:
                self._featureresponses[output_label][feature].update(
                    self._activities[output_label],
                    value)
            if p.store_fullmatrix:
                self._fullmatrix[output_label].update(
                    self._activities[output_label],
                    current_values)


    def _apply_cmd_overrides(self, p):
        """
        Applies the cmd_overrides to the pattern_response_fn and
        the pattern_coordinator before launching a measurement.
        """

        for override, value in p.cmd_overrides.items():
            if override in p.pattern_response_fn.params():
                p.pattern_response_fn.set_param(override, value)


    @bothmethod
    def set_cmd_overrides(self_or_cls, **overrides):
        """
        Allows setting of cmd_overrides at the class and instance
        level. Important for setting overrides on the
        pattern_response_fn.
        """
        self_or_cls.cmd_overrides = dict(self_or_cls.cmd_overrides,
                                         **overrides)


class FeatureMaps(FeatureResponses):
    """
    Measure and collect the responses to a set of features, for
    calculating feature maps.

    For each feature and each measurement source, the results are
    stored as a preference matrix and selectivity matrix in the
    sheet's sheet_views; these can then be plotted as preference or
    selectivity maps.
    """

    preference_fn = param.ClassSelector(DistributionStatisticFn,
                                        default=DSF_WeightedAverage(), doc="""
        Function for computing a scalar-valued preference, selectivity,
        etc. from the distribution of responses. Note that this default
        is overridden by specific functions for individual features, if
        specified in the Feature objects.""")

    selectivity_multiplier = param.Number(default=17.0, doc="""
        Scaling of the feature selectivity values, applied in all
        feature dimensions.  The multiplier sets the output scaling.
        The precise value is arbitrary, and set to match historical
        usage.""")


    def __call__(self, features, **params):
        """
        Present the given input patterns and collate the responses.

        Responses are statistics on the distributions of measure for
        every unit, extracted by functions that are subclasses of
        DistributionStatisticFn, and could be specified in each
        feature with the preference_fn parameter, otherwise the
        default in self.preference_fn is used.
        """
        p = ParamOverrides(self, params, allow_extra_keywords=True)
        self.features = features

        self._initialize_featureresponses(p)
        self._measure_responses(p)

        results = self._collate_results(p)

        if p.measurement_storage_hook:
            p.measurement_storage_hook(results)

        return results


    def _collate_results(self, p):
        results = {'fullmatrix': self._fullmatrix if self.store_fullmatrix else None}

        for output_label, output_metadata in self.metadata.outputs.items():
            results[output_label] = {}
            for feature in self._featureresponses[output_label]:
                fp = filter(lambda f: f.name == feature, self.features)[0]
                ar = self._featureresponses[output_label][
                    feature].distribution_matrix[0, 0].axis_range
                cyclic_range = ar if fp.cyclic else 1.0
                pref_fn = fp.preference_fn if fp.preference_fn is not None\
                    else self.preference_fn
                if p.selectivity_multiplier is not None:
                    pref_fn.selectivity_scale = (pref_fn.selectivity_scale[0],
                                                 self.selectivity_multiplier)
                fr = self._featureresponses[output_label][feature]
                response = fr.apply_DSF(pref_fn)
                base_name = self.measurement_prefix + feature.capitalize()
                for k, maps in response.items():
                    for map_name, map_view in maps.items():
                        sv = SheetView(map_view, output_metadata['bounds'])
                        cr = None if map_name == 'selectivity' else cyclic_range
                        metadata = dict(timestamp=self.metadata.timestamp,
                                        cyclic_range=cr, **output_metadata)
                        name = base_name + k + map_name.capitalize()
                        results[output_label][name] = FeatureRangeMap(sv, **metadata)

        return results


class FeatureCurves(FeatureResponses):
    """
    Measures and collects the responses to a set of features, for
    calculating tuning and similar curves.

    These curves represent the response of a measurement source to
    patterns that are controlled by a set of features.  This class can
    collect data for multiple curves, each with the same x axis.  The
    x axis represents the main feature value that is being varied,
    such as orientation.  Other feature values can also be varied,
    such as contrast, which will result in multiple curves (one per
    unique combination of other feature values).

    The measured responses used to construct the curves will be passed
    to the pattern_presenting_fn to be stored.  A particular set of
    patterns is then constructed using a user-specified
    PatternPresenter by adding the parameters determining the curve
    (curve_param_dict) to a static list of parameters (param_dict),
    and then varying the specified set of features.  The results can
    be accessed in the curve_dict passed to the presenter_cmd, indexed
    by the curve_label and feature value.
    """

    x_axis = param.String(default=None, doc="""
        Parameter to use for the x axis of tuning curves.""")

    curve_params = param.String(default=None, doc="""
        Curve label, specifying the value along some feature dimension.""")

    label = param.String(default='', doc="""
        Units for labeling the curve_parameters in figure legends.
        The default is %, for use with contrast, but could be any
        units (or the empty string).""")


    def __call__(self, features, **params):
        p = ParamOverrides(self, params, allow_extra_keywords=True)
        self.features = features
        self._initialize_featureresponses(p)
        self._measure_responses(p)

        results = self._collate_results(p)

        if p.measurement_storage_hook:
            p.measurement_storage_hook(results)

        return results


    def _collate_results(self, p):
        results = {'fullmatrix': self._fullmatrix if self.store_fullmatrix else None}

        for output_label, output_metadata in self.metadata.outputs.items():
            results[output_label] = {}
            metadata = dict(timestamp=self.metadata.timestamp,
                            dimension_labels=[p.x_axis.capitalize()],
                            label=p.label, prefix=p.measurement_prefix,
                            curve_params=p.curve_params, **output_metadata)
            view = FeatureRangeMap(**metadata)
            rows, cols = output_metadata['shape']
            curve_responses = self._featureresponses[output_label][p.x_axis].distribution_matrix
            for x in curve_responses[0, 0]._data.iterkeys():
                y_axis_values = np.zeros(output_metadata['shape'],
                                         activity_type)
                for i in range(rows):
                    for j in range(cols):
                        y_axis_values[i, j] = curve_responses[i, j].get_value(x)
                sv = SheetView(y_axis_values, output_metadata['bounds'])
                view.add_item(x, sv)
            results[output_label] = view

        return results



class ReverseCorrelation(FeatureResponses):
    """
    Calculate the receptive fields for all neurons using reverse correlation.
    """

    continue_measurement = param.Boolean(default=True)

    def _initialize_featureresponses(self, p):
        self._apply_cmd_overrides(p)
        for fn in p.metadata_fns:
            self.metadata = AttrDict(p.metadata, **fn(p.inputs, p.outputs))

        self._activities = {}
        self._featureresponses = {}

        for input_label, input_metadata in self.metadata.inputs.items():
            self._featureresponses[input_label] = {}
            for output_label, output_metadata in self.metadata.outputs.items():
                rows, cols = output_metadata['shape']
                rc_array = np.array([[np.zeros(input_metadata['shape'],
                                               dtype=activity_dtype)
                                      for r in range(rows)] for c in
                                     range(cols)])
                self._featureresponses[input_label][output_label] = rc_array


    def __call__(self, features, **params):
        p = ParamOverrides(self, params, allow_extra_keywords=True)
        self.features = features

        self._initialize_featureresponses(p)
        self._measure_responses(p)

        results = self._collate_results(p)

        if p.measurement_storage_hook:
            p.measurement_storage_hook(results)

        return results


    def _collate_results(self, p):
        results = {'fullmatrix': self._fullmatrix if self.store_fullmatrix else None}

        for input_label, input_metadata in self.metadata.inputs.items():
            results[input_label] = {}
            for output_label, output_metadata in self.metadata.outputs.items():
                rows, cols = output_metadata['shape']
                view = ProjectionGrid(label=p.measurement_prefix + 'RFs',
                                      timestamp=self.metadata['timestamp'],
                                      bounds=output_metadata['bounds'],
                                      shape=output_metadata['shape'])
                metadata = dict(timestamp=self.metadata['timestamp'],
                                measurement_src=output_metadata['src_name'],
                                **input_metadata)
                rc_response = self._featureresponses[input_label][output_label]
                for ii in range(rows):
                    for jj in range(cols):
                        coord = view.matrixidx2coord(ii, jj)
                        sv = SheetView(rc_response[ii, jj],
                                       input_metadata['bounds'])
                        rf_metadata = dict(coord=coord, **metadata)
                        frm = FeatureRangeMap(sv, **rf_metadata)
                        view.add_item(coord, frm)
                results[input_label][output_label] = view
        return results



    def _present_permutation(self, p, permutation, permutation_num):
        """Present a pattern with the specified set of feature values."""

        # Calculate complete set of settings
        permuted_settings = zip(self.feature_names, permutation)
        complete_settings = permuted_settings + \
                            [(f.name, f.compute_fn(permuted_settings)) for f in
                             self.features_to_compute]

        # Run hooks before and after pattern presentation.
        for f in p.pre_presentation_hooks:
            f()

        inputs = self._coordinate_inputs(p, dict(permuted_settings))
        measurement_sources = self.metadata.outputs.keys() + self.metadata\
            .inputs.keys()
        responses = p.pattern_response_fn(inputs, measurement_sources,
                                          permutation_num, self.total_steps)

        for f in p.post_presentation_hooks:
            f()

        self._update(p, responses)


    def _update(self, p, responses):
        """
        Updates featureresponses object with latest reverse correlation data.
        """
        for input_label in self.metadata.inputs:
            for output_label, output_metadata in self.metadata.outputs.items():
                rows, cols = output_metadata['shape']
                feature_responses = self._featureresponses[input_label][
                    output_label]
                for ii in range(rows):
                    for jj in range(cols):
                        delta_rf = responses[output_label][ii, jj] * responses[
                            input_label]
                        feature_responses[ii, jj] += delta_rf


###############################################################################
###############################################################################

# Define user-level commands and helper classes for calling the above


class Feature(param.Parameterized):
    """
    Specifies several parameters required for generating a map of one input
    feature.
    """

    name = param.String(default="", doc="Name of the feature to test")

    cyclic = param.Boolean(default=False, doc="""
        Whether the range of this feature is cyclic (wraps around at the high
        end).""")

    compute_fn = param.Callable(default=None, doc="""
        If non-None, a function that when given a list of other parameter
        values, computes and returns the value for this feature.""")

    preference_fn = param.ClassSelector(DistributionStatisticFn,
                                        default=DSF_WeightedAverage(), doc="""
        Function that will be used to analyze the distributions of unit response
        to this feature.""")

    range = param.NumericTuple(default=(0, 0), doc="""
        Lower and upper values for a feature,used to build a list of values,
        together with the step parameter.""")

    step = param.Number(default=0.0, doc="""
        Increment used to build a list of values for this feature, together with
        the range parameter.""")

    offset = param.Number(default=0.0, doc="""
        Offset to add to the values for this feature""")

    values = param.List(default=[], doc="""
        Explicit list of values for this feature, used in alternative to the
        range and step parameters""")


    def __init__(self, **params):
        """
        Users can provide either a range and a step size, or a list of
        values.  If a list of values is supplied, the range can be
        omitted unless the default of the min and max in the list of
        values is not appropriate.

        If non-None, the compute_fn should be a function that when
        given a list of other parameter values, computes and returns
        the value for this feature.

        If supplied, the offset is added to the given or computed
        values to allow the starting value to be specified.

        """

        super(Feature, self).__init__(**params)

        if len(self.values):
            self.values = self.values if self.offset == 0 \
                else [v + self.offset for v in self.values]
            if self.range == (0, 0):
                self.range = (min(self.values), max(self.values))
        else:
            if self.range == (0, 0):
                raise ValueError('The range or values must be specified.')
            low_bound, up_bound = self.range
            self.values = frange(low_bound, up_bound,
                                 self.step, not self.cyclic)
            self.values = self.values if self.offset == 0 else \
                [(v + self.offset) % (up_bound - low_bound) if self.cyclic
                 else (v + self.offset) for v in self.values]


class contrast2centersurroundscale(param.ParameterizedFunction):
    contrast_parameter = param.String(default='weber_contrast')

    def __call__(self, inputs, feature_values):
        if "contrastcenter" in feature_values:
            if self.contrast_parameter == 'michelson_contrast':
                for g in inputs.itervalues():
                    g.offsetcenter = 0.5
                    g.scalecenter = 2*g.offsetcenter * g.contrastcenter/100.0

            elif self.contrast_parameter == 'weber_contrast':
                # Weber_contrast is currently only well defined for
                # the special case where the background offset is equal
                # to the target offset in the pattern type
                # SineGrating(mask_shape=Disk())
                for g in inputs.itervalues():
                    g.offsetcenter = 0.5   #In this case this is the offset of
                    # both the background and the sine grating
                    g.scalecenter = 2*g.offsetcenter * g.contrastcenter/100.0

            elif self.contrast_parameter == 'scale':
                for g in inputs.itervalues():
                    g.offsetcenter = 0.0
                    g.scalecenter = g.contrastcenter

        if "contrastsurround" in feature_values:
            if self.contrast_parameter == 'michelson_contrast':
                for g in inputs.itervalues():
                    g.offsetsurround = 0.5
                    g.scalesurround = 2 * g.offsetsurround * g\
                        .contrastsurround / 100.0

            elif self.contrast_parameter == 'weber_contrast':
                # Weber_contrast is currently only well defined for
                # the special case where the background offset is equal
                # to the target offset in the pattern type
                # SineGrating(mask_shape=Disk())
                for g in inputs.itervalues():
                    g.offsetsurround = 0.5   #In this case this is the offset
                    # of both the background and the sine grating
                    g.scalesurround = 2 * g.offsetsurround * g\
                        .contrastsurround / 100.0

            elif self.contrast_parameter == 'scale':
                for g in inputs.itervalues():
                    g.offsetsurround = 0.0
                    g.scalesurround = g.contrastsurround


class contrast2scale(param.ParameterizedFunction):
    """
    Coordinates complex contrast values in single and compound
    patterns.  Requires the contrast entry in the meta_params
    dictionary to be set to one of three values: michelson_contrast,
    weber_contrast or simply scale.
    """

    contrast_parameter = param.String(default='michelson_contrast')

    def __call__(self, inputs, feature_values):

        if "contrast" in feature_values:
            if self.contrast_parameter == 'michelson_contrast':
                for g in inputs.itervalues():
                    g.offset = 0.5
                    g.scale = 2 * g.offset * g.contrast / 100.0

            elif self.contrast_parameter == 'weber_contrast':
                # Weber_contrast is currently only well defined for
                # the special case where the background offset is equal
                # to the target offset in the pattern type
                # SineGrating(mask_shape=Disk())
                for g in inputs.itervalues():
                    g.offset = 0.5   #In this case this is the offset of both
                    # the background and the sine grating
                    g.scale = 2 * g.offset * g.contrast / 100.0

            elif self.contrast_parameter == 'scale':
                for g in inputs.itervalues():
                    g.offset = 0.0
                    g.scale = g.contrast


class direction2translation(param.ParameterizedFunction):
    """
    Coordinates the presentation of moving patterns. Currently
    supports an old and new motion model.
    """

    def __call__(self, inputs, feature_values):
        if 'direction' in feature_values:
            import __main__ as main

            if '_new_motion_model' in main.__dict__ and main.__dict__[
                '_new_motion_model']:
            #### new motion model ####
                from topo.pattern import Translator

                for name in inputs:
                    inputs[name] = Translator(generator=inputs[name],
                                              direction=feature_values[
                                                  'direction'],
                                              speed=feature_values['speed'],
                                              reset_period=self.duration)
            else:
            #### old motion model ####
                orientation = feature_values['direction'] + pi / 2
                from topo.pattern import Sweeper

                for name in inputs.keys():
                    speed = feature_values['speed']
                    try:
                        step = int(name[-1])
                    except:
                        if not hasattr(self, 'direction_warned'):
                            self.warning('Assuming step is zero; no input lag'
                                         ' number specified at the end of the'
                                         ' input sheet name.')
                            self.direction_warned = True
                        step = 0
                    speed = feature_values['speed']
                    inputs[name] = Sweeper(generator=inputs[name],
                                           step=step, speed=speed)
                    setattr(inputs[name], 'orientation', orientation)


class phasedisparity2leftrightphase(param.ParameterizedFunction):
    """
    Coordinates phase disparity between two eyes, by looking for
    the keywords Left and Right in the input names.
    """

    def __call__(self, inputs, feature_values):
        if "contrast" in feature_values:
            temp_phase1 = feature_values['phase'] - feature_values[
                'phasedisparity'] / 2.0
            temp_phase2 = feature_values['phase'] + feature_values[
                'phasedisparity'] / 2.0
            for name in inputs.keys():
                if (name.count('Right')):
                    inputs[name].phase = wrap(0, 2 * pi, temp_phase1)
                elif (name.count('Left')):
                    inputs[name].phase = wrap(0, 2 * pi, temp_phase2)
                else:
                    if not hasattr(self, 'disparity_warned'):
                        self.warning('Unable to measure disparity preference,'
                                     ' because disparity is defined only when'
                                     ' there are inputs for Right and Left'
                                     ' retinas.')
                        self.disparity_warned = True


class hue2rgbscale(param.ParameterizedFunction):
    """
    Coordinates hue between inputs with Red, Green or Blue in their
    name.
    """

    def __call__(self, inputs, feature_values):
        if 'hue' in feature_values:

            # could be three retinas (R, G, and B) or a single RGB
            # retina for the color dimension; if every retina has
            # 'Red' or 'Green' or 'Blue' in its name, then three
            # retinas for color are assumed

            rgb_retina = False
            for name in inputs:
                if not ('Red' in name or 'Green' in name or 'Blue' in name):
                    rgb_retina = True

            if not rgb_retina:
                for name in inputs.keys():
                    r, g, b = hsv_to_rgb(feature_values['hue'], 1.0, 1.0)
                    if (name.count('Red')):
                        inputs[name].scale = r
                    elif (name.count('Green')):
                        inputs[name].scale = g
                    elif (name.count('Blue')):
                        inputs[name].scale = b
                    else:
                        if not hasattr(self, 'hue_warned'):
                            self.warning('Unable to measure hue preference,'
                                         ' because hue is defined only when'
                                         ' there are different input sheets'
                                         ' with names with Red, Green or Blue'
                                         ' substrings.')
                            self.hue_warned = True
            else:
                from contrib import rgbimages

                r, g, b = hsv_to_rgb(feature_values['hue'], 1.0, 1.0)
                for name in inputs.keys():
                    inputs[name] = rgbimages.ExtendToRGB(generator=inputs[name],
                                                         relative_channel_strengths=[
                                                             r, g, b])
                    # CEBALERT: should warn as above if not a color network


class ocular2leftrightscale(param.ParameterizedFunction):
    """
    Coordinates patterns between two eyes, by looking for the
    keywords Left and Right in the input names.
    """

    def __call__(self, inputs, feature_values):
        if "ocular" in feature_values:
            for name in inputs.keys():
                if (name.count('Right')):
                    inputs[name].scale = 2 * feature_values['ocular']
                elif (name.count('Left')):
                    inputs[name].scale = 2.0 - 2 * feature_values['ocular']
                else:
                    self.warning('Skipping input region %s; Ocularity is'
                                 ' defined only for Left and Right retinas.' %
                                 name)


class Subplotting(param.Parameterized):
    """
    Convenience functions for handling subplots (such as colorized
    Activity plots).  Only needed for avoiding typing, as plots can be
    declared with their own specific subplots without using these
    functions.
    """

    plotgroups_to_subplot = param.List(default=
                                       ["Activity", "Connection Fields",
                                        "Projection", "Projection Activity"],
                                       doc="List of plotgroups for which to "
                                           "set subplots.")

    subplotting_declared = param.Boolean(default=False,
                                         doc="Whether set_subplots has "
                                             "previously been called")

    _last_args = param.Parameter(default=())

    @staticmethod
    def set_subplots(prefix=None, hue="", confidence="", force=True):
        """
        Define Hue and Confidence subplots for each of the
        plotgroups_to_subplot.
        Typically used to make activity or weight plots show a
        preference value as the hue, and a selectivity as the
        confidence.

        The specified hue, if any, should be the name of a SheetView,
        such as OrientationPreference.  The specified confidence, if
        any, should be the name of a (usually) different SheetView,
        such as OrientationSelectivity.

        The prefix option is a shortcut making the usual case easier
        to type; it sets hue to prefix+"Preference" and confidence to
        prefix+"Selectivity".

        If force=False, subplots are changed only if no subplot is
        currently defined.  Force=False is useful for setting up
        subplots automatically when maps are measured, without
        overwriting any subplots set up specifically by the user.

        Currently works only for plotgroups that have a plot
        with the same name as the plotgroup, though this could
        be changed easily.

        Examples::

           Subplotting.set_subplots("Orientation")
             - Set the default subplots to OrientationPreference and
             OrientationSelectivity

           Subplotting.set_subplots(hue="OrientationPreference")
             - Set the default hue subplot to OrientationPreference with no
             selectivity

           Subplotting.set_subplots()
             - Remove subplots from all the plotgroups_to_subplot.
        """

        Subplotting._last_args = (prefix, hue, confidence, force)

        if Subplotting.subplotting_declared and not force:
            return

        if prefix:
            hue = prefix + "Preference"
            confidence = prefix + "Selectivity"

        for name in Subplotting.plotgroups_to_subplot:
            if name in plotgroups.keys():
                pg = plotgroups[name]
                if name in pg.plot_templates.keys():
                    pt = pg.plot_templates[name]
                    pt["Hue"] = hue
                    pt["Confidence"] = confidence
                else:
                    Subplotting().warning("No template %s defined for plotgroup"
                                          " %s" % (name, name))
            else:
                Subplotting().warning("No plotgroup %s defined" % name)

        Subplotting.subplotting_declared = True


    @staticmethod
    def restore_subplots():
        args = Subplotting._last_args
        if args != ():
            Subplotting.set_subplots(*(Subplotting._last_args))


class MeasureResponseCommand(ParameterizedFunction):
    """Parameterized command for presenting input patterns and measuring
    responses."""

    duration = param.Number(default=None, doc="""
        If non-None, pattern_response_fn.duration will be
        set to this value.""")

    inputs = param.List(default=[], doc="""Name of input supplied to
        the metadata_fns to filter out desired input.""")

    measurement_prefix = param.String(default="", doc="""
        Optional prefix to add to the name under which results are
        stored as part of a measurement response.""")

    metafeature_fns = param.HookList(default=[contrast2scale])

    offset = param.Number(default=0.0, softbounds=(-1.0, 1.0), doc="""
        Additive offset to input pattern.""")

    outputs = param.List(default=[], doc="""Name of output sources supplied
        to metadata_fns to filter out desired output.""")

    pattern_generator = param.Callable(default=None, instantiate=True, doc="""
        Callable object that will generate input patterns coordinated
        using a list of meta parameters.""")

    pattern_response_fn = param.Callable(default=None, instantiate=False,
                                         doc="""
        Callable object that will present a parameter-controlled pattern to a
        set of Sheets.  Needs to be supplied by a subclass or in the call.
        The attributes duration and apply_output_fns (if non-None) will
        be set on this object, and it should respect those if possible.""")

    preference_fn = param.ClassSelector(DistributionStatisticFn,
                                        default=DSF_MaxValue(), doc="""
        Function that will be used to analyze the distributions of unit
        responses.""")

    preference_lookup_fn = param.Callable(default=None, instantiate=True,
                                          doc="""
        Callable object that will look up a preferred feature values.""")

    scale = param.Number(default=1.0, softbounds=(0.0, 2.0), doc="""
        Multiplicative strength of input pattern.""")

    static_parameters = param.List(class_=str, default=["scale", "offset"],
                                   doc="""
        List of names of parameters of this class to pass to the
        pattern_presenter as static parameters, i.e. values that
        will be fixed to a single value during measurement.""")

    subplot = param.String(default='', doc="""
        Name of map to register as a subplot, if any.""")

    weighted_average = param.Boolean(default=True, doc="""
        Whether to compute results using a weighted average, or just discrete
        values. A weighted average can give more precise results, without being
        limited to a set of discrete values, but the results can have systematic
        biases due to the averaging, especially for non-cyclic parameters.""")

    __abstract = True

    def __call__(self, **params):
        """Measure the response to the specified pattern and store the data
        in each sheet."""
        p = ParamOverrides(self, params, allow_extra_keywords=True)
        self._set_presenter_overrides(p)
        static_params = dict([(s, p[s]) for s in p.static_parameters])
        if p.subplot != "":
            Subplotting.set_subplots(p.subplot, force=True)

        return FeatureMaps(self._feature_list(p), duration=p.duration,
                           inputs=p.inputs,
                           metafeature_fns=p.metafeature_fns,
                           measurement_prefix=p.measurement_prefix,
                           outputs=p.outputs, param_dict=static_params,
                           pattern_generator=p.pattern_generator,
                           pattern_response_fn=p.pattern_response_fn)


    def _feature_list(self, p):
        """Return the list of features to vary; must be implemented by each
        subclass."""
        raise NotImplementedError


    def _set_presenter_overrides(self, p):
        """
        Overrides parameters of the pattern_response_fn and
        pattern_coordinator, using extra_keywords passed into the
        MeasurementResponseCommand.
        """
        for override, value in p.extra_keywords().items():
            if override in p.pattern_response_fn.params():
                p.pattern_response_fn.set_param(override, value)


class SinusoidalMeasureResponseCommand(MeasureResponseCommand):
    """
    Parameterized command for presenting sine gratings and measuring
    responses.
    """

    pattern_generator = param.Callable(instantiate=True,
                                       default=SineGrating(), doc="""
        Callable object that will present a parameter-controlled pattern to a
        set of Sheets.  By default, uses a SineGrating presented for a short
        duration. By convention, most Topographica example files are designed
        to have a suitable activity pattern computed by that time, but the
        duration will need to be changed for other models that do not follow
        that convention.""")

    frequencies = param.List(class_=float, default=[2.4], doc="""
        Sine grating frequencies to test.""")

    num_phase = param.Integer(default=18, bounds=(1, None), softbounds=(1, 48),
                              doc="""Number of phases to test.""")

    num_orientation = param.Integer(default=4, bounds=(1, None),
                                    softbounds=(1, 24),
                                    doc="Number of orientations to test.")

    scale = param.Number(default=0.3)

    preference_fn = param.ClassSelector(DistributionStatisticFn,
                                        default=DSF_WeightedAverage(),
                                        doc="""Function that will be used to
                                        analyze the distributions of unit
                                        responses.""")

    __abstract = True


class PositionMeasurementCommand(MeasureResponseCommand):
    """
    Parameterized command for measuring topographic position.
    """

    divisions = param.Integer(default=6, bounds=(1, None), doc="""
        The number of different positions to measure in X and in Y.""")

    x_range = param.NumericTuple((-0.5, 0.5), doc="""
        The range of X values to test.""")

    y_range = param.NumericTuple((-0.5, 0.5), doc="""
        The range of Y values to test.""")

    size = param.Number(default=0.5, bounds=(0, None), doc="""
        The size of the pattern to present.""")

    pattern_generator = param.Callable(
        default=Gaussian(aspect_ratio=1.0), doc="""
        Callable object that will present a parameter-controlled
        pattern to a set of Sheets.  For measuring position, the
        pattern_presenter should be spatially localized, yet also able
        to activate the appropriate neurons reliably.""")

    static_parameters = param.List(default=["scale", "offset", "size"])

    __abstract = True


class SingleInputResponseCommand(MeasureResponseCommand):
    """
    A callable Parameterized command for measuring the response to
    input on a specified Sheet.

    Note that at present the input is actually presented to all input
    sheets; the specified Sheet is simply used to determine various
    parameters.  In the future, it may be modified to draw the pattern
    on one input sheet only.
    """

    scale = param.Number(default=30.0)

    offset = param.Number(default=0.5)

    # JABALERT: Presumably the size is overridden in the call, right?
    pattern_generator = param.Callable(default=RawRectangle(size=0.1,
                                                            aspect_ratio=1.0))

    static_parameters = param.List(default=["scale", "offset", "size"])

    weighted_average = None # Disabled unused parameter

    __abstract = True


class FeatureCurveCommand(SinusoidalMeasureResponseCommand):
    """A callable Parameterized command for measuring tuning curves."""

    num_orientation = param.Integer(default=12)

    units = param.String(default='%', doc="""
        Units for labeling the curve_parameters in figure legends.
        The default is %, for use with contrast, but could be any
        units (or the empty string).""")

    # Make constant in subclasses?
    x_axis = param.String(default='orientation', doc="""
        Parameter to use for the x axis of tuning curves.""")

    static_parameters = param.List(default=[])

    # JABALERT: Might want to accept a list of values for a given
    # parameter to make the simple case easier; then maybe could do
    # the crossproduct of them?
    curve_parameters = param.Parameter([{"contrast": 30}, {"contrast": 60},
                                        {"contrast": 80}, {"contrast": 90}],
        doc="""List of parameter values for which to measure a curve.""")

    __abstract = True


    def __call__(self, **params):
        """Measure the response to the specified pattern and store the data
        in each sheet."""
        p = ParamOverrides(self, params, allow_extra_keywords=True)
        self._set_presenter_overrides(p)
        return self._compute_curves(p)


    def _compute_curves(self, p, val_format='%s'):
        """
        Compute a set of curves for the specified sheet, using the
        specified val_format to print a label for each value of a
        curve_parameter.
        """
        curve_measurements = {}
        for curve in p.curve_parameters:
            static_params = dict([(s, p[s]) for s in p.static_parameters])
            static_params.update(curve)
            curve_label = "; ".join(
                [('%s = ' + val_format + '%s') % (n.capitalize(), v, p.units)
                 for n, v in curve.items()])
            curve_measurements[curve_label] = FeatureCurves(
                self._feature_list(p), curve_params=curve, duration=p.duration,
                param_dict=static_params, pattern_generator=p.pattern_generator,
                label=curve_label, pattern_response_fn=p.pattern_response_fn,
                x_axis=p.x_axis, measurement_prefix=p.measurement_prefix,
                metafeature_fns=p.metafeature_fns, inputs=p.inputs,
                outputs=p.outputs)
        return curve_measurements


    def _feature_list(self, p):
        return [Feature(name="phase", range=(0.0, 2 * pi),
                        step=2 * pi / p.num_phase, cyclic=True),
                Feature(name="orientation", range=(0, pi),
                        step=pi / p.num_orientation, cyclic=True),
                Feature(name="frequency", values=p.frequencies)]


class UnitCurveCommand(FeatureCurveCommand):
    """
    Measures tuning curve(s) of particular unit(s).
    """

    pattern_generator = param.Callable(
        default=SineGrating(mask_shape=Disk(smoothing=0.0, size=1.0)))

    metafeature_fns = param.HookList(
        default=[contrast2scale.instance(contrast_parameter='weber_contrast')])

    size = param.Number(default=0.5, bounds=(0, None), doc="""
        The size of the pattern to present.""")

    coords = param.List(default=[(0, 0)], doc="""
        List of coordinates of units to measure.""")

    __abstract = True


###############################################################################
###############################################################################
###############################################################################
#
# 20081017 JABNOTE: This implementation could be improved.
#
# It currently requires every subclass to implement the feature_list
# method, which constructs a list of features using various parameters
# to determine how many and which values each feature should have.  It
# would be good to replace the feature_list method with a Parameter or
# set of Parameters, since it is simply a special data structure, and
# this would make more detailed control feasible for users. For
# instance, instead of something like num_orientations being used to
# construct the orientation Feature, the user could specify the
# appropriate Feature directly, so that they could e.g. supply a
# specific list of orientations instead of being limited to a fixed
# spacing.
#
# However, when we implemented this, we ran into two problems:
#
# 1. It's difficult for users to modify an open-ended list of
#     Features.  E.g., if features is a List:
#
#      features=param.List(doc="List of Features to vary""",default=[
#          Feature(name="frequency",values=[2.4]),
#          Feature(name="orientation",range=(0.0,pi),step=pi/4,cyclic=True),
#          Feature(name="phase",range=(0.0,2*pi),step=2*pi/18,cyclic=True)])
#
#    then it it's easy to replace the entire list, but tough to
#    change just one Feature.  Of course, features could be a
#    dictionary, but that doesn't help, because when the user
#    actually calls the function, they want the arguments to
#    affect only that call, whereas looking up the item in a
#    dictionary would only make permanent changes easy, not
#    single-call changes.
#
#    Alternatively, one could make each feature into a separate
#    parameter, and then collect them using a naming convention like:
#
#     def feature_list(self,p):
#         fs=[]
#         for n,v in self.get_param_values():
#             if n in p: v=p[n]
#             if re.match('^[^_].*_feature$',n):
#                 fs+=[v]
#         return fs
#
#    But that's quite hacky, and doesn't solve problem 2.
#
# 2. Even if the users can somehow access each Feature, the same
#    problem occurs for the individual parts of each Feature.  E.g.
#    using the separate feature parameters above, Spatial Frequency
#    map measurement would require:
#
#      from topo.command.analysis import Feature
#      from math import pi
#      pre_plot_hooks=[measure_or_pref.instance(\
#         frequency_feature=Feature(name="frequency",values=frange(1.0,6.0,
# 0.2)), \
#         phase_feature=Feature(name="phase",range=(0.0,2*pi),step=2*pi/15,
# cyclic=True), \
#         orientation_feature=Feature(name="orientation",range=(0.0,pi),
# step=pi/4,cyclic=True)])
#
#    rather than the current, much more easily controllable implementation:
#
#      pre_plot_hooks=[measure_or_pref.instance(frequencies=frange(1.0,6.0,
# 0.2),\
#         num_phase=15,num_orientation=4)]
#
#    I.e., to change anything about a Feature, one has to supply an
#    entirely new Feature, because otherwise the original Feature
#    would be changed for all future calls.  Perhaps there's some way
#    around this by copying objects automatically at the right time,
#    but if so it's not obvious.  Meanwhile, the current
#    implementation is reasonably clean and easy to use, if not as
#    flexible as it could be.

### PJFRALERT: Functions and classes below will stay in Topographica


def update_sheet_activity(sheet_name, sheet_views_prefix='', force=False):
    """
    Update the 'Activity' SheetView for a given sheet by name.

    If force is False and the existing Activity SheetView isn't stale,
    the existing view is returned.
    """
    name = sheet_views_prefix + 'Activity'
    sheet = topo.sim.objects(Sheet)[sheet_name]
    view = sheet.views.maps.get(name, False)
    if not view:
        metadata = dict(bounds=sheet.bounds, timestamp=topo.sim.time(),
                        src_name=sheet.name, precedence=sheet.precedence,
                        row_precedence=sheet.row_precedence, depth=1,
                        shape=sheet.activity.shape)
        sv = SheetView(np.array(sheet.activity), sheet.bounds)
        view = FeatureRangeMap(sv, **metadata)
        sheet.views.maps[name] = view
    else:
        if force or topo.sim.time() > view.timestamp:
            sv = SheetView(np.array(sheet.activity), sheet.bounds)
            view.add_item(topo.sim.time(), sv)

    return view


def update_activity(sheet_views_prefix='', force=False):
    """
    Make a map of neural activity available for each sheet, for use in
    template-based plots.

    This command simply asks each sheet for a copy of its activity
    matrix, and then makes it available for plotting.  Of course, for
    some sheets providing this information may be non-trivial, e.g. if
    they need to average over recent spiking activity.
    """
    for sheet_name in topo.sim.objects(Sheet).keys():
        update_sheet_activity(sheet_name, sheet_views_prefix, force)


class pattern_present(ParameterizedFunction):
    """
    Presents a pattern on the input sheet(s) and returns the
    response. Does not affect the state but can overwrite the previous
    pattern if overwrite_previous is set to True.

    May also be used to measure the response to a pattern by calling
    it with restore_events disabled and restore_state and
    force_sheetview enabled, which will push and pop the simulation
    state and install the response in the sheet_view dictionary. The
    measure_activity command in topo.command implements this
    functionality.

    Given a set of input patterns, installs them into the specified
    GeneratorSheets, runs the simulation for the specified length of
    time, then restores the original patterns and the original
    simulation time.  Thus this input is not considered part of the
    regular simulation, and is usually for testing purposes.

    As a special case, if 'inputs' is just a single pattern, and not
    a dictionary, it is presented to all GeneratorSheets.

    If a simulation is not provided, the active simulation, if one
    exists, is requested.

    If this process is interrupted by the user, the temporary patterns
    may still be installed on the retina.

    In order to to see the sequence of values presented, you may use
    the back arrow history mechanism in the GUI. Note that the GUI's
    Activity window must be open.
    """

    apply_output_fns = param.Boolean(default=True, doc="""
        Determines whether sheet output functions will be applied.
        """)

    duration = param.Number(default=None, doc="""
        If non-None, pattern_presenter.duration will be
        set to this value.  Provides a simple way to set
        this commonly changed option of CoordinatedPatternGenerator.""")

    inputs = param.Dict(default={}, doc="""
        A dictionary of GeneratorSheetName:PatternGenerator pairs to be
        installed into the specified GeneratorSheets""")

    install_sheetview = param.Boolean(default=False, doc="""Determines
        whether to install a sheet view in the appropriate sheet_views
        dict even when there is an existing sheetview.""")

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

    sheet_views_prefix = param.String(default="", doc="""
        Optional prefix to add to the name under which results are
        stored in sheet_views. Can be used e.g. to distinguish maps as
        originating from a particular GeneratorSheet.""")

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

        duration = p.duration if (p.duration is not None) else 1.0
        topo.sim.run(duration)

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

        update_activity(p.sheet_views_prefix, p.install_sheetview)

        responses = {}
        outputs = outputs if len(outputs) > 0 else topo.sim.objects(Sheet).keys()
        if p.return_responses:
                for output in outputs:
                    responses[output] = topo.sim[output].activity.copy()

        if hasattr(topo, 'guimain'):
            topo.guimain.refresh_activity_windows()

        if p.restore_state:
            topo.sim.state_pop()

        return responses


class MeasurementInterrupt(Exception):
    """
    Exception raised when a measurement is stopped before
    completion. Stores the number of executed presentations and
    total presentations.
    """

    def __init__(self, current, total):
        self.current = current
        self.total = total + 1


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

    def __call__(self, inputs={}, outputs=[], current=0, total=1,
                 **params_to_override):
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
            if hasattr(topo, 'guimain'):
                topo.guimain.open_progress_window(self.timer)
                self.install_sheetview = True
        if self.timer.stop:
            raise MeasurementInterrupt(current, total)
        self.timer.update_timer('Measurement Timer', current, total)

        p = ParamOverrides(self, dict(params_to_override, inputs=inputs))

        return super(pattern_response, self).__call__(outputs=outputs, **p)


def topo_metadata_fn(input_names=[], output_names=[]):
    """
    Return the shapes of the specified GeneratorSheets and measurement
    sheets, or if none are specified return all that can be found in
    the simulation.
    """
    metadata = AttrDict()
    metadata['timestamp'] = topo.sim.time()

    sheets = {}
    sheets['inputs'] = [getattr(topo.sim, input_name, input_name)
                        for input_name in input_names]

    for input_name in input_names:
        if input_name in sheets['inputs']:
            topo.sim.warning('Input sheet {0} not found.'.format(input_name))
            sheets['inputs'].pop(input_name)
    if not sheets['inputs']:
        if input_names:
            topo.sim.warning(
                "Warning specified input sheets do not exist, using all "
                "generator sheets instead.")
        sheets['inputs'] = topo.sim.objects(GeneratorSheet).values()

    sheets['outputs'] = [getattr(topo.sim, output_name, output_name) for
                         output_name in output_names]
    for input_name in input_names:
        if output_name in sheets['outputs']:
            topo.sim.warning('Output sheet {0} not found.'.format(output_name))
            sheets['outputs'].pop(output_name)
    if not sheets['outputs']:
        if output_names:
            topo.sim.warning(
                "Warning specified output sheets do not exist, using all "
                "sheets with measure_maps enabled.")
        sheets['outputs'] = [s for s in topo.sim.objects(Sheet).values() if
                             hasattr(s, 'measure_maps') and s.measure_maps]

    for sheet_type, sheet_list in sheets.items():
        metadata[sheet_type] = dict(
            [(s.name, {'bounds': s.bounds, 'precedence': s.precedence,
                       'row_precedence': s.row_precedence,
                       'shape': s.shape, 'src_name': s.name})
             for s in sheet_list])

    return metadata # Consider (inputs, outputs, metadata) as return


def store_measurement(measurement_dict):
    """
    Interface function to install measurement results the appropriate
    sheet_views, curves or rfs dictionary.
    """
    measurement_dict.pop('fullmatrix')
    for sheet_name, sheet_data in measurement_dict.items():
        sheet = topo.sim[sheet_name]
        if isinstance(sheet_data, FeatureRangeMap):
            measurement_label = sheet_data.metadata.prefix + \
                                sheet_data.dimension_labels[0]
            indexed_features, feature_vals = zip(*sheet_data.metadata.curve_params.items())
            metadata = dict(bounds=sheet_data.metadata.bounds,
                            timestamp=sheet_data.timestamp,
                            dimension_labels=list(indexed_features))
            curve_storage = sheet.views.curves
            if measurement_label not in curve_storage:
                curve_storage[measurement_label] = FeatureRangeMap(**metadata)
            else:
                new_timestamp = sheet_data.timestamp > curve_storage[measurement_label].timestamp
                new_measurement = any([True for c in curve_storage[measurement_label][...].values()
                                       if sheet_data.metadata.label == c.metadata.label])
                if new_timestamp or new_measurement:
                    curve_storage[measurement_label] = FeatureRangeMap(**metadata)
            curve_storage[measurement_label].add_item(feature_vals, sheet_data)
        else:
            for data_name, data in sheet_data.items():
                if isinstance(data, FeatureRangeMap):
                    if data_name not in sheet.views.maps:
                        sheet.views.maps[data_name] = data
                    else:
                        sheet.views.maps[data_name].update(data)
                if isinstance(data, ProjectionGrid):
                    data_sheet = topo.sim[data_name]
                    label = "{sheet}_{key}".format(sheet=sheet_name,
                                                   key=data.metadata.label)
                    if label not in data_sheet.views.rfs:
                        data_sheet.views.rfs[label] = data
                    else:
                        data_sheet.views.rfs[label].update(data)


def get_feature_preference(feature, sheet_name, coords, default=0.0):
    """Return the feature preference for a particular unit."""
    try:
        sheet = topo.sim[sheet_name]
        matrix_coords = sheet.sheet2matrixidx(*coords)
        map_name = feature.capitalize() + "Preference"
        return sheet.views.maps[map_name].top[matrix_coords]
    except:
        topo.sim.warning(
            ("%s should be measured before plotting this tuning curve -- " +
             "using default value of %s for %s unit (%d,%d).") %
            (map_name, default, sheet.name, coords[0], coords[1]))
        return default


__all__ = [
    "DistributionMatrix",
    "FullMatrix",
    "FeatureResponses",
    "ReverseCorrelation",
    "FeatureMaps",
    "FeatureCurves",
    "Feature",
    "CoordinatedPatternGenerator",
    "Subplotting",
    "MeasureResponseCommand",
    "SinusoidalMeasureResponseCommand",
    "PositionMeasurementCommand",
    "SingleInputResponseCommand",
    "FeatureCurveCommand",
    "UnitCurveCommand",
]
