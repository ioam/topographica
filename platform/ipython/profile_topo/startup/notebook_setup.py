# Settings that apply to IPython Notebook only
import logging
import param
import sys

# Pylabplots should return a matplotlib figure when working in Notebook
# otherwise open display windows for the Topographica Tk GUI
from topo.command import pylabplot
pylabplot.PylabPlotCommand.display_window = False

from topo.analysis import empty_storage_hook
from topo.analysis.command import measure_cog
from topo.analysis.featureresponses import FeatureCurves, FeatureMaps, ReverseCorrelation
from featuremapper.command import measure_response

FeatureMaps.measurement_storage_hook = empty_storage_hook
FeatureCurves.measurement_storage_hook = empty_storage_hook
ReverseCorrelation.measurement_storage_hook = empty_storage_hook
measure_response.measurement_storage_hook = empty_storage_hook
measure_cog.measurement_storage_hook = empty_storage_hook


# Create new logger to ensure param logging shows in notebooks
iplogger = logging.getLogger('ip-param')
iplogger.addHandler(logging.StreamHandler(stream=sys.stderr))
iplogger.propagate = False
param.parameterized.logger = iplogger

