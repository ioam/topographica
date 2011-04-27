"""
Code used to support old snapshots (those created from 0.9.7/r11275
onwards).

$Id$
"""
__version__='$Revision: 8021 $'

import imp
import sys

import param

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


def get_version(snapshot_release,snapshot_version):

    found_version = False
    
    try:
        snapshot_version = snapshot_version.split(":")[0]
        snapshot_version = snapshot_version.split("M")[0]
        
        if len(snapshot_version)>0:
            try:
                snapshot_version = int(snapshot_version)
                found_version = True
            except ValueError:
                pass
        
    except AttributeError:
        pass

    if not found_version:
        snapshot_version = releases[snapshot_release]

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

        snapshot_version = get_version(snapshot_release,snapshot_version)

        msgr = param.Parameterized()

        msgr.debug("Snapshot is from release %s (r%s)"%(snapshot_release,snapshot_version))

        global support

        # apply oldest to newest
        for version in sorted(support.keys())[::-1]:
            if snapshot_version < version:
                msgr.debug("Applying legacy support for change r%s"%version)
                support[version]()


######################################################################
######################################################################

# Supporting code


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


######################################################################
######################################################################

# Functions to update old snapshots

# support[v]=fn : for snapshots saved before v, call fn

support = {}

def do_not_restore_paths():
    # For snapshots saved before 11323
    # Avoid restoring search_paths,prefix for resolve_path,normalize_path
    # (For snapshots before r11323, these were included.)
    import param.parameterized
    param.parameterized.PicklableClassAttributes.do_not_restore+=[
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


# CEB: deliberately no support for audio-related changes, since
# audio-related code is changing fast and isn't in general
# use. Support could be added if necessary.

