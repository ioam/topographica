"""
Analysis tools for Topographica, other than plotting tools.

Configures the interface to the featuremapper and dataviews projects
and sets the appropriate Topographica-specific hooks.
"""

from topo.analysis.featureresponses import FeatureResponses, FeatureCurves,\
    FeatureMaps, ReverseCorrelation, MeasureResponseCommand, pattern_response,\
    topo_metadata_fn, StorageHook, get_feature_preference
from featuremapper.command import measure_response

import imagen.colorspaces
import topo.optimized.color

import numpy as np

from dataviews.collector import Reference
from dataviews.options import channels, ChannelOpts
from dataviews.operation import cmap2rgb, operator, chain
from dataviews.testing import IPTestCase

import topo
from featuremapper.command import Collector
from topo.base.sheet import Sheet
from topo.base.projection import Projection
from topo.misc.ipython import RunProgress

from command import measure_cog

from topo.base.sheetview import CFView, CFStack
from imagen import Animation

class TopoIPTestCase(IPTestCase):

    def __init__(self, *args, **kwargs):
        super(TopoIPTestCase, self).__init__(*args, **kwargs)
        self.addTypeEqualityFunc(CFView,   self.compare_cfviews)
        self.addTypeEqualityFunc(CFStack,   self.compare_cfstack)
        self.addTypeEqualityFunc(Animation,   self.compare_animation)

    def compare_cfviews(self, view1, view2, msg):
        self.compare_sheetviews(view1, view2, msg)

    def compare_cfstack(self, view1, view2, msg):
        self.compare_sheetstack(view1, view2, msg)

    def compare_animation(self, view1, view2, msg):
        self.compare_sheetstack(view1, view2, msg)



class SimRef(Reference):
    """
    A SimRef instance is installed on Collector to allow Topographica
    model elements to be referenced for collection.

    This is important to allow pickling and unpickling of Collectors
    that work correctly with Topographica in different execution
    environments (e.g. nodes of a cluster) and across different models
    without directly pickling the components (e.g. Sheets and
    Projections) themselves.

    More information about references can be found in the docstring of
    the dataviews.collector.Reference.
    """
    @property
    def resolved_type(self):
        if self.array_ref:
            return np.ndarray
        elif isinstance(self.obj, tuple):
            return Projection
        else:
            return Sheet

    def __init__(self, obj=None, array_ref=None):
        if [obj, array_ref] == [None,None]:
            raise Exception("Please specify an object, a path string or an array_ref.")

        self.array_ref = None
        if obj is None:
            self.obj = None
            self.array_ref = array_ref
        elif isinstance(obj, str):
            self.obj = tuple(obj.split('.')) if '.' in obj else obj
        elif isinstance(obj, Projection):
            self.obj = (obj.dest.name, obj.name)
        else:
            self.obj = obj.name

    def resolve(self):
        from topo import sim
        if isinstance(self.obj, tuple):
            (sheet, proj) = self.obj
            return sim[sheet].projections()[proj]
        elif self.obj:
            return sim[self.obj]
        else:
            return eval('topo.sim.'+self.array_ref)

    def __repr__(self):
        if isinstance(self.obj, tuple):
            return "SimRef(%r)" % '.'.join(el for el in self.obj)
        elif self.obj is None:
            return "SimRef(array_ref=%r)" % self.array_ref
        else:
            return "SimRef(%r)" % self.obj


    def __str__(self):
        if isinstance(self.obj, tuple):
            return "topo.sim."+'.'.join(el for el in self.obj)
        elif self.obj is None:
            return "topo.sim." + self.array_ref
        else:
            return "topo.sim."+ self.obj


### Collection hooks


Collector.time_fn = topo.sim.time
Collector.interval_hook = RunProgress


def sheet_hook(obj, *args, **kwargs):
    """
    Return a SheetView of the Sheet activity.
    """
    return obj[:]

def projection_hook(obj, *args, **kwargs):
    """
    Return a SheetView of the projection activity, otherwise if
    grid=True, return a CoordinateGrid of the CFs.
    """
    if kwargs.pop('grid', False):
        return obj.grid(**kwargs)
    else:
        return obj.projection_view()

def measurement_hook(obj, *args, **kwargs):
    return obj(*args, **kwargs)


# Configure Collector with appropriate hooks
Collector.sim = SimRef
Collector.for_type(Sheet, sheet_hook, referencer=SimRef)
Collector.for_type(Projection, projection_hook, referencer=SimRef)
Collector.for_type(measure_cog,  measurement_hook, mode='merge')


# Setting default channel operation for ON-OFF visualization
ON_sub_OFF = chain.instance(chain=lambda x: [cmap2rgb(operator(x, operator=np.subtract).N, cmap='jet')])
ChannelOpts.operations['ON_sub_OFF'] = ON_sub_OFF
channels['ON_sub_OFF'] = ChannelOpts('ON_sub_OFF', "CF Weights * CF Weights")


# Featuremapper hooks

def empty_storage_hook(arg):
    """Use this to unset storage hook because lambda will not work
    with snapshots.

    This function is used in notebook_setup.py of the topographica
    IPython profile.
    """
    pass


FeatureResponses.metadata_fns = [topo_metadata_fn]
FeatureResponses.pattern_response_fn = pattern_response.instance()
FeatureMaps.measurement_storage_hook = StorageHook.instance(sublabel='Maps')
FeatureCurves.measurement_storage_hook = StorageHook.instance(sublabel='Curves')
ReverseCorrelation.measurement_storage_hook = StorageHook.instance(sublabel='RFs')
measure_response.measurement_storage_hook = StorageHook.instance(sublabel=None)
measure_cog.measurement_storage_hook = StorageHook.instance(sublabel='CoG')


MeasureResponseCommand.preference_lookup_fn = get_feature_preference
MeasureResponseCommand.pattern_response_fn = pattern_response.instance()


## Set optimized versions of color conversion functions
imagen.colorspaces.rgb_to_hsv = topo.optimized.color._rgb_to_hsv_array_opt
imagen.colorspaces.hsv_to_rgb = topo.optimized.color._hsv_to_rgb_array_opt


# Automatically discover all .py files in this directory.
import os,fnmatch
__all__ = [f.split('.py')[0] for f in os.listdir(__path__[0]) if fnmatch.fnmatch(f,'[!._]*.py')]
del f,os,fnmatch

