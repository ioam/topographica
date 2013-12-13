"""
Analysis tools for Topographica, other than plotting tools.
"""

from topo.analysis.featureresponses import FeatureResponses, FeatureCurves,\
    FeatureMaps, ReverseCorrelation, MeasureResponseCommand, pattern_response,\
    topo_metadata_fn, store_rfs, store_maps, store_curves, store_activity, \
    get_feature_preference
from fmapper.command import measure_activity

FeatureResponses.metadata_fns = [topo_metadata_fn]
FeatureResponses.pattern_response_fn = pattern_response.instance()
FeatureMaps.measurement_storage_hook = store_maps
FeatureCurves.measurement_storage_hook = store_curves
ReverseCorrelation.measurement_storage_hook = store_rfs
measure_activity.measurement_storage_hook = store_activity

MeasureResponseCommand.preference_lookup_fn = get_feature_preference
MeasureResponseCommand.pattern_response_fn = pattern_response.instance()


# Automatically discover all .py files in this directory.
import os,fnmatch
__all__ = [f.split('.py')[0] for f in os.listdir(__path__[0]) if fnmatch.fnmatch(f,'[!._]*.py')]
del f,os,fnmatch

