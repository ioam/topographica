"""
Code used to support old snapshots (those created from 0.9.7/r11275
onwards).
"""
__version__='$Revision: 8021 $'

import sys
import decimal # CEBALERT: when did decimal appear? too late to use?

import param

from snapshots import PicklableClassAttributes

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

    found_version = False

    if snapshot_version is not None:
        snapshot_version = snapshot_version.split(":")[0]
        snapshot_version = snapshot_version.split("M")[0]

        if len(snapshot_version)>0:
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

        # CEB: I think there's no simple way to tell what "version" of
        # Topographica a snapshot comes from. When you're running
        # Topographica from svn, you can try topo.version, but you'll
        # get things like 11499:11503 or 11499M. If you use git,
        # you'll see "exported". Therefore, we can't always have
        # fine-grained control over what's loaded. We can at least use
        # the release number for coarse-grained control, though.

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

# CEBALERT: should be renamed (it's not only about pattern.basic). And
# did all these happen in one commit?  I added topo.ep recently; did
# that happen in the same commit as the others or not?
def pattern_basic_removed():
   import topo.pattern
   import topo.command
   import topo.coordmapper
   import topo.ep
   import topo.learningfn
   import topo.numbergen
   import topo.pattern
   import topo.projection
   import topo.responsefn
   import topo.sheet
   import topo.transferfn
   module_redirect('basic',topo.command,topo.command)
   module_redirect('basic',topo.coordmapper,topo.coordmapper)
   module_redirect('basic',topo.ep,topo.ep)
   module_redirect('basic',topo.learningfn,topo.learningfn)
   module_redirect('basic',topo.numbergen,topo.numbergen)
   module_redirect('basic',topo.pattern,topo.pattern)
   module_redirect('basic',topo.projection,topo.projection)
   module_redirect('basic',topo.responsefn,topo.responsefn)
   module_redirect('basic',topo.sheet,topo.sheet)
   module_redirect('basic',topo.transferfn,topo.transferfn)

support[11871] = pattern_basic_removed


def param_external_removed():
    # CB: From param/external.py, only odict should be relevant to snapshots.
    import topo.misc.odict
    allow_import(topo.misc.odict,'param.external')

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
