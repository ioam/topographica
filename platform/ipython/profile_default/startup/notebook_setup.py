# Settings that apply to IPython Notebook only
import logging
import param
import sys

# Pylabplots should return a matplotlib figure when working in Notebook
# otherwise open display windows for the Topographica Tk GUI
from topo.command import pylabplot
pylabplot.PylabPlotCommand.display_window = False

# Create new logger to ensure param logging shows in notebooks
iplogger = logging.getLogger('ip-param')
iplogger.addHandler(logging.StreamHandler(stream=sys.stderr))
iplogger.propagate = False
param.parameterized.logger = iplogger

