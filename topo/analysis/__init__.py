"""
Analysis tools for Topographica, other than plotting tools.

Configures the interface to the featuremapper and holoviews projects
and sets the appropriate Topographica-specific hooks.
"""

import numpy as np

from holoviews.interface.collector import Reference
from holoviews import HSV, Image
from holoviews.core.options import Compositor
from holoviews.ipython import IPTestCase
from holoviews.operation import chain, operation, factory, image_overlay
import imagen.colorspaces
from featuremapper.command import Collector, measure_response

import topo
from topo.analysis.featureresponses import FeatureResponses, FeatureCurves,\
    FeatureMaps, ReverseCorrelation, MeasureResponseCommand, pattern_response,\
    topo_metadata_fn, StorageHook, get_feature_preference
from topo.base.projection import Projection
from topo.base.sheet import Sheet
from topo.base.sheetview import CFView
from topo.misc.ipython import RunProgress
from topo.misc import color

from command import measure_cog



CoG_spec = "Image.X CoG * Image.Y CoG * Image.BlueChannel"
XYCoG = chain.instance(group='XYCoG', name='XYCoG',
                       operations = [image_overlay.instance(spec=CoG_spec), factory.instance()])
Compositor.register(Compositor("Image.X CoG * Image.Y CoG", XYCoG, 'XYCoG', 'display'))


import param
from holoviews import RGB, ElementOperation
from holoviews.operation.normalization import raster_normalization


class colorizeHSV(ElementOperation):
    """
    Given an Overlay consisting of two Image elements, colorize the
    data in the bottom Image with the data in the top Image using
    the HSV color space.
    """

    group = param.String(default='ColorizedHSV', doc="""
        The group string for the colorized output (an RGB element)""")

    output_type = RGB

    def _process(self, overlay, key=None):
        if len(overlay) != 2:
            raise Exception("colorizeHSV required an overlay of two Image elements as input.")
        if (len(overlay.get(0).value_dimensions), len(overlay.get(1).value_dimensions)) != (1,1):
            raise Exception("Each Image element must have single value dimension.")
        if overlay.get(0).shape != overlay.get(1).shape:
            raise Exception("Mismatch in the shapes of the data in the Image elements.")


        hue = overlay.get(1)
        Hdim = hue.value_dimensions[0]
        H = hue.clone(hue.data.copy(),
                      value_dimensions=[Hdim(cyclic=True, range=hue.range(Hdim.name))])

        normfn = raster_normalization.instance()
        if self.p.input_ranges:
            S = normfn.process_element(overlay.get(0), key, *self.p.input_ranges)
        else:
            S = normfn.process_element(overlay.get(0), key)

        C = Image(np.ones(hue.data.shape),
                  bounds=self.get_overlay_bounds(overlay), group='F', label='G')

        C.value_dimensions[0].range = (0,1)
        S.value_dimensions[0].range = (0,1)
        return HSV(H * C * S).relabel(group=self.p.group)


Compositor.register(
    Compositor('CFView.CF Weight * Image.Orientation_Preference',
               colorizeHSV, 'ColorizedWeights', mode='display'))


class TopoIPTestCase(IPTestCase):

    def __init__(self, *args, **kwargs):
        super(TopoIPTestCase, self).__init__(*args, **kwargs)

    @classmethod
    def register(cls):
        super(TopoIPTestCase, cls).register()
        cls.equality_type_funcs[CFView] = cls.compare_cfview
        return cls.equality_type_funcs

    @classmethod
    def compare_cfview(cls, el1, el2, msg='CFView data'):
        cls.compare_image(el1, el2, msg=msg)


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
    the holoviews.collector.Reference.
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

        if topo.sim.model is not None:
            print "DEPRECATION WARNING: use topo.submodel.specifications instead of SimRef."

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
    Return a Image of the Sheet activity.
    """
    return obj[:]

def projection_hook(obj, *args, **kwargs):
    """
    Return a Image of the projection activity, otherwise if
    grid=True, return a Grid of the CFs.
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
op_subtract = operation.instance(output_type=CFView, op=lambda x, k: x.collapse(np.subtract))
Compositor.register(Compositor('CFView.CF_Weight * CFView.CF_Weight',
                               op_subtract, 'OnOff CFs', mode='data'))

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
imagen.colorspaces.rgb_to_hsv = color._rgb_to_hsv_array_opt
imagen.colorspaces.hsv_to_rgb = color._hsv_to_rgb_array_opt


# Automatically discover all .py files in this directory.
import os,fnmatch
__all__ = [f.split('.py')[0] for f in os.listdir(__path__[0]) if fnmatch.fnmatch(f,'[!._]*.py')]
del f,os,fnmatch

