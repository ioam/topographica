"""
Code used to support old snapshots (those created from 0.9.7/r11275
onwards).
"""
import collections as odict

import sys
import decimal # CEBALERT: when did decimal appear? too late to use?

import param

from snapshots import PicklableClassAttributes

from topo import version_int
from topo.misc.util import unit_value

# CEBALERT: remove the extraneous "import param"s

# CEB: Add note that snapshot can be re-saved, making updates
# permanent. All functions in here should be written to support that.

# CEB: code to support older snapshots is available in earlier
# versions of this file (e.g. r11323). I consider that version of the
# file to be a "proof of concept"; techniques from it will be used to
# support changes made from 0.9.7 onwards.

# CEBNOTE: could also support running old scripts without modifying
# them.
#
# E.g. we changed output_fn to output_fns for several classes. To
# support that in a snapshot requires intercepting the saved data and
# detecting 'output_fn=x' and replacing it with 'output_fns=[x]',
# etc. To support it in a script requires installing something in the
# class that will take .output_fn=x and actually do
# .output_fns=[x]. Here's one way we could support CFProjection's
# weights_shape changing to cf_shape:
#
#    import topo.base.cf
#    cfp = topo.base.cf.CFProjection
#    type.__setattr__(cfp,'weights_shape',cfp.__dict__['cf_shape'])


# CEBALERT: should probably restructure this file so that as little as
# possible happens on import. Should be easy to do.

releases = {"0.9.7": 11275}


def _get_version(snapshot_release,snapshot_version):
    """
    Try to determine a single numerical version for use in looking up
    patches in the support dictionary, given a snapshot's declared
    release and version.

    Because of the variety of different version formats that have been
    in use over the different version-control systems over the years,
    it's not always possible to make such a mapping.  E.g. versions
    controlled by SVN would normally return topo.version like 11499,
    which is clear, but also sometimes 11499:11503 or 11499M.
    Versions from git checkouts of svn source would just say
    "exported", while native git versions will have a four-tuple.  If
    nothing else works, the numerical version associated with the
    stated release is used.
    """

    found_version = False

    if snapshot_version is not None:
        try: # to detect the passed version
            snapshot_version = snapshot_version.split(":")[0]
            snapshot_version = snapshot_version.split("M")[0]
        except AttributeError: # the version is a tuple, thus it's from git
            snapshot_version = version_int(snapshot_version)

        # Convert to integer if snapshot_version contains only digits
        if snapshot_version:
            try:
                snapshot_version = int(snapshot_version)
                found_version = True
            except ValueError:
                pass

    if not found_version:
        snapshot_version = releases[snapshot_release]
        param.Parameterized().debug("No version could be detected for this snapshot; assuming version of release %s (i.e. %s)."%(snapshot_release,snapshot_version))

    return snapshot_version



class SnapshotSupport(object):

    @staticmethod
    def install(snapshot_release,snapshot_version=None):
        snapshot_version = _get_version(snapshot_release,snapshot_version)

        param.Parameterized().debug("Snapshot is from release %s (r%s)"%(snapshot_release,snapshot_version))

        SnapshotSupport.apply_external_patches()
        SnapshotSupport.apply_support(snapshot_version)


    @staticmethod
    def apply_external_patches():
        global external_patches

        # not ordered
        for message in external_patches.keys():
            #param.Parameterized().message(message)
            external_patches[message]()


    @staticmethod
    def apply_support(version_to_support):
        global support

        # apply oldest to newest
        for version in sorted(support.keys())[::-1]:
            if version_to_support < version:
                param.Parameterized().message("Applying legacy support for change r%s"%version)
                support[version]()



######################################################################
######################################################################

# Supporting code

def _version_greater_or_equal(module,than):
    # CB: I forgot Python: how do I do "if module version >= than"?!
    major,minor = module.__version__.split(".")[0:2]
    version = decimal.Decimal(major+"."+minor)
    return version>=than

def _setstate(inst,state):
    for k,v in state.items():
        setattr(inst,k,v)

def preprocess_state(class_,state_mod_fn):
    """
    Allow processing of state with state_mod_fn before
    class_.__setstate__(instance,state) is called.

    state_mod_fn must accept two arguments: instance and state.
    """
    if not hasattr(class_,'__setstate__'):
        # e.g. class_ used to be Parameterized, but now isn't
        class_.__setstate__ = _setstate

    old_setstate = class_.__setstate__
    def new_setstate(instance,state):
        state_mod_fn(instance,state)
        old_setstate(instance,state)
    class_.__setstate__ = new_setstate

def postprocess_state(class_,state_mod_fn):
    """
    Allow processing of instance and state after state has been applied.

    state_mod_fn must accept two arguments: instance and state.
    """
    if not hasattr(class_,'__setstate__'):
        # e.g. class_ used to be Parameterized, but now isn't
        class_.__setstate__ = _setstate

    old_setstate = class_.__setstate__
    def new_setstate(instance,state):
        old_setstate(instance,state)
        state_mod_fn(instance,state)
    class_.__setstate__ = new_setstate

# CEBNOTE: eventually, might have to support multiple redirections for
# one module (see version in r11323).
def module_redirect(name,parent,actual_module):
    """
    For use when module parent.name is now actual_module.
    """
    sys.modules[parent.__name__+'.'+name]=actual_module
    setattr(sys.modules[parent.__name__],name,actual_module)

# CEBALERT: adapted from topo.misc.util's version; need to merge and
# clean up. Also, needs a better name: used only for allow_import().
class _ModuleFaker(object):
    def __init__(self,module):
        self.module = module

    def load_module(self,name):
        if name not in sys.modules:
            self.module.__file__ = self.path
            sys.modules[name] = self.module
            if '.' in name:
                parent_name, child_name = name.rsplit('.', 1)
                setattr(sys.modules[parent_name], child_name, self.module)
        return sys.modules[name]

class _ModuleImporter(object):
    def __init__(self,module,fullname):
        self.fullname = fullname
        self.module = module

    def find_module(self, fullname, path=None):
        if fullname == self.fullname:
            param.Parameterized().message("%s imported as %s"%(self.module.__name__,self.fullname))
            faker = _ModuleFaker(self.module)
            faker.path = path
            return faker
        return None

def allow_import(module,location):
    """Allow module to be imported from location."""
    sys.meta_path.append(_ModuleImporter(module,location))


######################################################################
######################################################################

# Functions to update old snapshots

# support[v]=fn : for snapshots saved before v, call fn

# only ONE entry per svn revision
support = {}

def do_not_restore_paths():
    # For snapshots saved before 11323
    # Avoid restoring search_paths,prefix for resolve_path,normalize_path
    # (For snapshots before r11323, these were included.)
    PicklableClassAttributes.do_not_restore+=[
        'param.normalize_path',
        'param.resolve_path']

support[11323] = do_not_restore_paths


def param_add_pickle_default_value():
    # For snapshots saved before 11321
    # pickle_default_value attribute added to Parameter in r11321

    from topo import param
    def _param_add_pickle_default_value(instance,state):
        if 'pickle_default_value' not in state:
            state['pickle_default_value']=True
    preprocess_state(param.Parameter,_param_add_pickle_default_value)

support[11321] = param_add_pickle_default_value


######################################################################
# CEB: deliberately no support for audio-related changes, since
# audio-related code is changing fast and isn't in general
# use. Support could be added if necessary.

def pattern_basic_rectangular_removed():
    # 11558 pattern.basic.rectangular() was removed
    # CB: I'm assuming nobody cares about this, but if
    # they do, replace the lambda with 11557's rectangular()
    def rectangular(*args,**kw): raise NotImplementedError
    import topo.pattern as B
    B.rectangular = rectangular

support[11558] = pattern_basic_rectangular_removed


def pattern_Null_removed():
    import imagen
    from imagen import Constant
    imagen.Null=Constant

support[90800407] = pattern_Null_removed

# CEBALERT: should be renamed (it's not only about pattern.basic). And
# did all these happen in one commit?  I added topo.ep recently; did
# that happen in the same commit as the others or not?
def pattern_basic_removed():
    import topo
    import topo.pattern
    import topo.command
    import topo.base.ep
    import topo.coordmapper
    import topo.learningfn
    import topo.numbergen
    import topo.pattern
    import topo.projection
    import topo.responsefn
    import topo.sheet
    import topo.transferfn
    module_redirect('basic',topo.command,topo.command)
    module_redirect('basic',topo.coordmapper,topo.coordmapper)
    module_redirect('basic',topo.learningfn,topo.learningfn)
    module_redirect('basic',topo.numbergen,topo.numbergen)
    module_redirect('basic',topo.pattern,topo.pattern)
    module_redirect('basic',topo.projection,topo.projection)
    module_redirect('basic',topo.responsefn,topo.responsefn)
    module_redirect('basic',topo.sheet,topo.sheet)
    module_redirect('basic',topo.transferfn,topo.transferfn)
    sys.modules['topo.ep.basic']=topo.base.ep

support[11871] = pattern_basic_removed


def param_external_removed():
    # CB: From param/external.py, only odict should be relevant to snapshots.
    import collections
    allow_import(collections,'param.external')

support[12024] = param_external_removed


# CEBALERT: slot removal/addition support could be extracted to its
# own function, then there'd be less duplication and it'd be easier to
# add new slot support.
def Number_and_BoundingRegion_add_set_hook():
    import param
    import topo.base.boundingregion as R
    def _add_set_hook(instance,state):
        if 'set_hook' not in state and hasattr(instance.__class__,'set_hook'):
            # have to add to state or else slot won't exist on instance, but will
            # exist on class (consequence of using __slots__)
            state['set_hook']=param.identity_hook
    preprocess_state(param.Number,_add_set_hook)
    preprocess_state(R.BoundingRegionParameter,_add_set_hook)

support[12028] = Number_and_BoundingRegion_add_set_hook


def renamed_sheetview_norm_factor():
    # CEBALERT: stuff to avoid overwriting existing dict could be extracted and made reusable to avoid
    # repeating it in all param_name_changes, param_moves
    sv_name_changes = PicklableClassAttributes.param_name_changes.get(
        'topo.base.sheetview.SheetView',{})
    sv_name_changes.update(
        {'norm_factor':'cyclic_range'})
    PicklableClassAttributes.param_name_changes['topo.base.sheetview.SheetView']=sv_name_changes

def moved_featuremaps_selectivity_multiplier():
    fm_moves = PicklableClassAttributes.param_moves.get(
        'topo.analysis.featureresponses.FeatureMaps',{})
    fm_moves.update(
        {'selectivity_multiplier':('topo.misc.distribution.DSF_WeightedAverage','selectivity_scale')})
    PicklableClassAttributes.param_moves['topo.analysis.featureresponses.FeatureMaps'] = fm_moves

def reorganized_analysis():
    renamed_sheetview_norm_factor()
    moved_featuremaps_selectivity_multiplier()

support[11904] = reorganized_analysis

def moved_picklableclassattributes():
    param.parameterized.PicklableClassAttributes = PicklableClassAttributes

support[12089] = moved_picklableclassattributes


def LISSOM_moved_to_SettlingCFSheet():
    import topo.sheet.lissom
    import topo.sheet.optimized
    def _LISSOM_move_private_params_to_SettlingCFSheet(instance,state):
        if '_SettlingCFSheet__counter_stack' not in state and '_LISSOM__counter_stack' in state:
            state['_SettlingCFSheet__counter_stack']=state['_LISSOM__counter_stack']
            del state['_LISSOM__counter_stack']

    preprocess_state(topo.sheet.lissom.LISSOM,_LISSOM_move_private_params_to_SettlingCFSheet)
    preprocess_state(topo.sheet.optimized.LISSOM_Opt,_LISSOM_move_private_params_to_SettlingCFSheet)

support[90800126] = LISSOM_moved_to_SettlingCFSheet


def sim_time_moved_to_Dynamic_time_fn():
    def _sim_time_moved_to_Dynamic_time_fn(instance,state):
        if '_time' in state and '_time_type_param_value' in state:
            param.Dynamic.time_fn(state['_time'],time_type=state['_time_type_param_value'])
            del state['_time']
            del state['_time_type_param_value']
            del state['_time_type_args_param_value']
        else:
            print "skipped"

    import topo.base.simulation
    preprocess_state(topo.base.simulation.Simulation,_sim_time_moved_to_Dynamic_time_fn)

support[90800408] = sim_time_moved_to_Dynamic_time_fn


def removed_JointScaling():
    from numpy import zeros,ones
    import copy
    from topo.base.sheet import activity_type
    from topo.sheet import SettlingCFSheet
    class JointScaling(SettlingCFSheet):
        """SettlingCFSheet sheet extended to allow joint auto-scaling of Afferent input projections."""
        target = param.Number(default=0.045, doc="""
            Target average activity for jointly scaled projections.""")
        target_lr = param.Number(default=0.045, doc="""
            Target learning rate for jointly scaled projections.
            Used for calculating a learning rate scaling factor.""")
        smoothing = param.Number(default=0.999, doc="""
            Influence of previous activity, relative to current, for computing the average.""")
        apply_scaling = param.Boolean(default=True, doc="""Whether to apply the scaling factors.""")
        precedence = param.Number(0.65)
    
        def __init__(self,**params):
            super(JointScaling,self).__init__(**params)
            self.x_avg=None
            self.sf=None
            self.lr_sf=None
            self.scaled_x_avg=None
            self.__current_state_stack=[]
    
        def calculate_joint_sf(self, joint_total):
            if self.plastic:
                self.sf *=0.0
                self.lr_sf *=0.0
                self.sf += self.target/self.x_avg
                self.lr_sf += self.target_lr/self.x_avg
                self.x_avg = (1.0-self.smoothing)*joint_total + self.smoothing*self.x_avg
                self.scaled_x_avg = (1.0-self.smoothing)*joint_total*self.sf + self.smoothing*self.scaled_x_avg
    
        def do_joint_scaling(self):
            joint_total = zeros(self.shape, activity_type)
            for key,projlist in self._grouped_in_projections('JointNormalize').items():
                if key is not None:
                    if key =='Afferent':
                        for proj in projlist:
                            joint_total += proj.activity
                        self.calculate_joint_sf(joint_total)
                        if self.apply_scaling:
                            for proj in projlist:
                                proj.activity *= self.sf
                                if hasattr(proj.learning_fn,'learning_rate_scaling_factor'):
                                    proj.learning_fn.update_scaling_factor(self.lr_sf)
                                else:
                                    raise ValueError("Projections to be joint scaled must have a learning_fn that supports scaling, such as CFPLF_PluginScaled")
    
                    else:
                        raise ValueError("Only Afferent scaling currently supported")
    
        def activate(self):
            self.activity *= 0.0
            if self.x_avg is None: self.x_avg=self.target*ones(self.shape, activity_type)
            if self.scaled_x_avg is None: self.scaled_x_avg=self.target*ones(self.shape, activity_type)
            if self.sf is None: self.sf=ones(self.shape, activity_type)
            if self.lr_sf is None: self.lr_sf=ones(self.shape, activity_type)
            if self.activation_count == 0: self.do_joint_scaling()
            for proj in self.in_connections: self.activity += proj.activity
            if self.apply_output_fns:
                for of in self.output_fns:
                    of(self.activity)
            self.send_output(src_port='Activity',data=self.activity)

        def state_push(self,**args):
            super(JointScaling,self).state_push(**args)
            self.__current_state_stack.append((copy.copy(self.x_avg),copy.copy(self.scaled_x_avg),
                                               copy.copy(self.sf), copy.copy(self.lr_sf)))
        def state_pop(self,**args):
            super(JointScaling,self).state_pop(**args)
            self.x_avg,self.scaled_x_avg, self.sf, self.lr_sf=self.__current_state_stack.pop()

    import topo.sheet.lissom
    topo.sheet.lissom.JointScaling = JointScaling

support[90800129] = removed_JointScaling


def featuremapper_legacy():
    # For snapshots saved before 90800300

    # Replace PatternPresenter objects with stub
    import topo.analysis.featureresponses
    import param
    class PatternPresenter(param.Parameterized):
        def __init__(self):
            pass
    topo.analysis.featureresponses.PatternPresenter = PatternPresenter

    # Move parameters and change them if necessary
    duration_lambda = lambda x: param.List(default=[x.default], doc="""
        If non-None, pattern_response_fn.duration will be set to this value.""")
    apply_output_fns_lambda = lambda x: {'apply_output_fns': x.default}

    name_changes = PicklableClassAttributes.param_name_changes

    mrc_name_changes = name_changes.get(
        'topo.analysis.featureresponses.MeasureResponseCommand',{})
    mrc_name_changes.update(
        {'duration': ('durations', duration_lambda)})
    name_changes['topo.analysis.featureresponses.MeasureResponseCommand']=mrc_name_changes

    mrc_moves = PicklableClassAttributes.param_moves.get(
        'topo.analysis.featureresponses.MeasureResponseCommand',{})
    mrc_moves.update({'apply_output_fns':
                          ('topo.analysis.featureresponses.FeatureResponses','cmd_overrides',apply_output_fns_lambda)})
    PicklableClassAttributes.param_moves['topo.analysis.featureresponses.MeasureResponseCommand'] = mrc_moves

    fcc_name_changes = name_changes.get(
        'topo.analysis.featureresponses.FeatureCurveCommand',{})
    fcc_name_changes.update(
        {'duration': ('durations', duration_lambda)})
    name_changes['topo.analysis.featureresponses.FeatureCurveCommand']=fcc_name_changes

    fcc_moves = PicklableClassAttributes.param_moves.get(
        'topo.analysis.featureresponses.FeatureCurveCommand',{})
    fcc_moves.update({'apply_output_fns':
                          ('topo.analysis.featureresponses.FeatureCurves','cmd_overrides',apply_output_fns_lambda)})
    PicklableClassAttributes.param_moves['topo.analysis.featureresponses.FeatureCurveCommand'] = fcc_moves

    ppc_name_changes = name_changes.get(
        'topo.analysis.featureresponses.PatternPresentingCommand',{})
    ppc_name_changes.update(
        {'duration': ('durations', duration_lambda),
         'sheet_views_prefix': 'measurement_prefix'})
    name_changes['topo.analysis.featureresponses.PatternPresentingCommand']=ppc_name_changes

    # Move enable_fullmatrix parameter
    fr_name_changes = name_changes.get(
        'topo.analysis.featureresponses.FeatureResponses',{})
    fr_name_changes.update(
        {'enable_fullmatrix':'store_fullmatrix'})
    name_changes['topo.analysis.featureresponses.FeatureResponses']=fr_name_changes

    # Measurement Prefix
    fr_name_changes = name_changes.get(
        'topo.analysis.featureresponses.FeatureResponses',{})
    fr_name_changes.update(
        {'enable_fullmatrix':'store_fullmatrix'})
    name_changes['topo.analysis.featureresponses.FeatureResponses']=fr_name_changes


    # Delete old parameters
    old_cmd_params = ('display', 'pattern_presenter', 'generator_sheets',
                      'input_sheet', 'sheet')
    param_no_restore = {'MeasureResponseCommand': old_cmd_params,
                        'FeatureCurveCommand': old_cmd_params,
                        'ProjectionSheetMeasurementCommand' : old_cmd_params,
                        'SingleInputResponseCommand': old_cmd_params,
                        'measure_rfs': ('sampling_interval', 'sampling_area'),
                        'unit_tuning_curve': ('x_axis', 'sheet'),
                        'ReverseCorrelation': old_cmd_params,
                        'FeatureCurves': ('post_collect_responses_hook'),
                        'FeatureMaps': ('sheet_views_prefix'),
                        'measure_latency_preference': old_cmd_params,
                        'PositionMeasurementCommand': old_cmd_params,
                        'measure_corner_or_pref': old_cmd_params,
                        'measure_orientation_contrast': old_cmd_params,
                        'PatternPresenter': ('contrast_parameter', 'divisions',
                                             'generator_sheets', 'apply_output_fns',
                                             'duration'),
                        'measure_or_tuning_fullfield': old_cmd_params,
                        'UnitCurveCommand': old_cmd_params,
                        'measure_frequency_preference': old_cmd_params,
                        'SinusoidalMeasureResponseCommand': old_cmd_params,
                        'measure_log_frequency_preference': old_cmd_params}
    PicklableClassAttributes.deleted_params.update(param_no_restore)

    # Convert old sheet_views and curve_dict
    from topo.misc.attrdict import AttrDict
    from topo.base.sheet import Sheet
    from dataviews import SheetView, NdMapping
    def _set_sheet_views(instance, state):
        if state['simulation'] is None:
            return None
        name = state['_name_param_value']
        if not hasattr(state['simulation'], 'views'):
            state['simulation'].views = AttrDict()
        if name not in state['simulation'].views:
            if hasattr(instance, 'views'):
                state['views'] = instance.views
            else:
                state['views'] = AttrDict()
            state['simulation'].views[name] = state['views']
        views = state['views']
        views['maps'] = AttrDict()
        views['cfs'] = AttrDict()
        views['rfs'] = AttrDict()
        views['curves'] = AttrDict()
        if 'sheet_views' in state:
            svs = state['sheet_views']
            for key, sv in svs.items():
                data, bounds = sv.view()
                new_sv = SheetView(data, bounds)
                metadata = dict(dimension_labels=['Time'])
                metadata_names = ['cyclic_range', 'precedence',
                                  'row_precedence', 'src_name']
                for p in metadata_names:
                    if hasattr(sv, p):
                        metadata[p] = getattr(sv, p)
                state['views'].maps[key] = NdMapping((sv.timestamp, new_sv),
                                                  **metadata)
        if 'curve_dict' in state:
            old_curves = state['curve_dict']
            curves = views['curves']
            for key, value in old_curves.items():
                key = key.capitalize()
                for label, item in value.items():
                    labels = unit_value(label)
                    label_name = labels[0].split(' ')[0]
                    l_val = labels[-1]
                    if key not in views['curves']:
                        curves[key] = NdMapping(dimension_labels=['Time'])
                    for f_val, old_sv in item.items():
                        timestamp = old_sv.timestamp
                        curves[key][timestamp] = NdMapping(dimension_labels=[label_name])
                        if l_val not in curves[key][timestamp].keys():
                            curves[key][timestamp] [l_val] = NdMapping(dimension_labels=[key],
                                                                       label=label,
                                                                       timestamp=old_sv.timestamp)
                        data, bounds = old_sv.view()
                        sv = SheetView(data, bounds)
                        curves[key][timestamp][l_val][f_val] = sv
        state.pop('curve_dict', None)
        state.pop('sheet_views', None)

    preprocess_state(Sheet, _set_sheet_views)

    param.Parameterized().warning('Legacy code does not guarantee all '
        'measurement parameters have been restored. Make sure measurements are '
        'still set up correctly.')

support[90800300] = featuremapper_legacy


def topo_misc_odict_removed():
    import collections
    allow_import(collections, 'topo.misc.odict')

support[90800361] = topo_misc_odict_removed


def ndmapping_ndim_remove():
    import dataviews
    def remove_ndmapping(instance,state):
        if 'ndim' in state:
            del state['ndim']
    preprocess_state(dataviews.NdMapping, remove_ndmapping)

support[90800401] = ndmapping_ndim_remove


def moved_Subplotting():
    import topo.analysis.featureresponses
    import topo.command.analysis
    from topo.plotting.plotgroup import Subplotting, _equivalent_for_plotgroup_update, save_plotgroup
    topo.analysis.featureresponses.Subplotting = Subplotting
    topo.command.analysis._equivalent_for_plotgroup_update = _equivalent_for_plotgroup_update
    topo.command.analysis.save_plotgroup = save_plotgroup
    
support[90800454] = moved_Subplotting


def moved_distribution():
    from featuremapper import distribution
    allow_import(distribution, 'topo.misc.distribution')

support[90800481] = moved_distribution


def moved_ep():
    from topo.base import ep
    sys.modules['topo.ep']=ep
    setattr(sys.modules['topo'],'ep',ep)

support[90800486] = moved_ep


def moved_generatorsheet():
    from topo.base import generatorsheet
    allow_import(generatorsheet, 'topo.misc.generatorsheet')

support[90800490] = moved_generatorsheet


def replace_keyedlist():
    class KeyedList(list):
        def __getitem__(self, key):
            for value in [v for k,v in self if k == key]: return value
            if isinstance(key,int):
                for v in [v for i,k,v in enumerate(self) if i==key]: return v
            raise KeyError(key)
        def get(self, key, default=None):
            if key in self.keys(): return self[key]
            return default
        def set(self, key, value):
            if key in self.keys(): self[self.index((key,self[key]))] = (key,value)
            else: self.append((key,value))
            return True
        def has_key(self, key): return key in self.keys()
        def __setitem__(self,k,v): return self.set(k,v)
        def append(self, (key, value)): super(KeyedList,self).append(tuple((key,value)))
        def items(self): return list(self)
        def keys(self): return [k for (k, v) in self.items()]
        def values(self): return [v for (k, v) in self.items()]
        def update(self,b): [self.set(k, v) for (k, v) in b.items()]
    odict.KeyedList = KeyedList
    sys.modules['topo.misc.keyedlist'] = odict
    setattr(sys.modules['topo.misc'], 'keyedlist', odict)

support[90800491] = replace_keyedlist

def fmapper_rename():
    import featuremapper
    allow_import(featuremapper, 'fmapper')

    param_no_restore = {'SheetView': ('bounds',),
                        'ProjectionGrid': ('bounds',)}
    PicklableClassAttributes.deleted_params.update(param_no_restore)

    import dataviews
    def remove_shape(instance,state):
        if 'shape' in state:
            x, y = state.pop('shape')
        elif '_shape_param_value' in state:
            x, y = state.pop('_shape_param_value')
        if '_bounds_param_value' in state:
            bounds = state.pop('_bounds_param_value')
        elif 'scs' in state:
            bounds = state.pop('scs').bounds
        l, b, r, t = bounds.lbrt()

        cl_name = 'SheetCoordinateSystem'
        xdensity = x/(r-l)
        ydensity = y/(t-b)
        state['_{cl}__xdensity'.format(cl=cl_name)] = xdensity
        state['_{cl}__xstep'.format(cl=cl_name)] = 1.0/xdensity
        state['_{cl}__ydensity'.format(cl=cl_name)] = ydensity
        state['_{cl}__ystep'.format(cl=cl_name)] = 1.0/ydensity
        state['_{cl}__shape'.format(cl=cl_name)] = (x, y)
        state['lbrt'] = (l, b, r, t)
        state['bounds'] = bounds

    preprocess_state(dataviews.SheetView, remove_shape)
    preprocess_state(dataviews.CoordinateGrid, remove_shape)

support[90800536] = fmapper_rename

######################################################################
######################################################################

# patches for external dependencies

# pickle stores path to modules; if path to module changes, module
# can't be imported, so snapshot can't be opened.

external_patches = {}

def numpy_core_defmatrix():
    import numpy.matrixlib.defmatrix
    allow_import(numpy.matrixlib.defmatrix,'numpy.core.defmatrix')


import numpy
if _version_greater_or_equal(numpy,decimal.Decimal("1.4")):
    external_patches['Support numpy.core.defmatrix for numpy>=1.4'] = numpy_core_defmatrix

# CB: About support for things like the numpy defmatrix change
# (above). When someone asks to load a snapshot, and they have
# numpy>=1.4, we register an import hook so that if the snapshot tries
# to import numpy.core.defmatrix, numpy.matrixlib.defmatrix will be
# provided. This happens without testing that the snapshot will
# actually try to import numpy.core.defmatrix (i.e. "import
# numpy.core.defmatrix" will work (with a warning) after loading *any*
# snapshot if version of numpy>=1.4). As far as I can see, the only
# way of improving this would be either (a) to set
# cPickle.Unpickler.find_global and make it handle all the various
# import changes (plus normal imports; there's no default because
# that's hidden in C) or (b) store version numbers of imported modules
# in the snapshot and use those to figure out what to do.



######################################################################
######################################################################

# CEBALERT: not sure whether to keep the "-l" option to Topographica.
# The idea is that we could start old scripts by loading legacy
# support, and then save a script_repr, thus allowing the script to be
# updated automatically. Not sure script_repr works well enough
# yet. (Should alter the -l option to take an optional release and svn
# version number.)
def install_legacy_support(release="0.9.7",version=None):
    if version is None:
        version = releases[release]

    assert version>=releases[release], "Release/version mismatch."

    SnapshotSupport.apply_external_patches()
    SnapshotSupport.apply_support(version)
