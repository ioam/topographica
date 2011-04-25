"""
Code used to support old snapshots (those created from 0.9.7/r11275
onwards).

$Id$
"""
__version__='$Revision: 8021 $'

import imp
import sys


# CEB: code to support older snapshots is available in earlier
# versions of this file (e.g. r11323). I consider that version of the
# file to be a "proof of concept"; techniques from it will be used to
# support changes made from 0.9.7 onwards.


# CEBNOTE: If we were using pickle rather than cpickle, could subclass
# the unpickler to look for module Xs as module X if Xs can't be
# found, and probably simplify quite a lot of the legacy code
# installation.
#
# Maybe we could do that by trying to use cpickle initially, then
# falling back to pickle when we do a 'legacy load' of the snapshot.


# CEBNOTE: To avoid restoring parameters of classes that are changed
# from from Parameterized to something else:
# param.parameterized.PicklableClassAttributes.do_not_restore+=...


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


class SnapshotSupport(object):

    @staticmethod
    def install(svn=None):

        # CEBALERT: I think there's no reliable way to tell what
        # "version" of Topographica a snapshot comes from. When you're
        # running Topographica from svn, you can try topo.version, but
        # you'll get things like 11499:11503 or 11499M. If you use
        # git, you'll see "exported". Therefore, we can't have
        # fine-grained control over what's loaded. We can at least use
        # the release number for coarse-grained control, though. Need
        # to add that (depends on change to way snapshots are saved
        # and loaded).

        import param
        global supporters
        for f in supporters:
            param.Parameterized(name='SnapshotSupport').debug("calling %s"%f.__name__)
            f()


def install_legacy_support():
    SnapshotSupport.install()


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



class _DuplicateCheckingList(list):
    def append(self,item):
        assert item not in self, "%s already added"%item
        list.append(self,item)




######################################################################
######################################################################

# Specification of changes to support


S=supporters=_DuplicateCheckingList()


def param_add_pickle_default_value():
    # pickle_default_value attribute added to Parameter in r11321

    from topo import param
    def _param_add_pickle_default_value(instance,state):
        if 'pickle_default_value' not in state:
            state['pickle_default_value']=True
    preprocess_state(param.Parameter,_param_add_pickle_default_value)

S.append(param_add_pickle_default_value)


# CEB: deliberately no support for audio-related changes, since
# audio-related code is changing fast and isn't in general
# use. Support could be added if necessary.

# CEBALERT: the code below will only run if legacy support is
# installed for some other reason (i.e. if the snapshot contains
# stored defaults for param.normalize_path and param.resolve_path but
# has no other problems, this code won't be run). Either need to
# install legacy support according to version (rather than installing
# if snapshot fails to load), or handle this in the classes
# themselves.

# Avoid restoring search_paths,prefix for resolve_path,normalize_path
# (For snapshots before r11323, these were included.)
import param.parameterized
param.parameterized.PicklableClassAttributes.do_not_restore+=[
    'param.normalize_path',
    'param.resolve_path']
