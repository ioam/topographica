# Configuration file for ipython.

c = get_config()

import sys, os
profile_dir = os.path.split(__file__)[0]
project_dir = os.path.join(profile_dir, '..', '..', '..')
sys.path = [os.path.abspath(project_dir)] + sys.path

import external
import param

from topo.misc.commandline import default_output_path
param.resolve_path.search_paths.append(default_output_path())

# To customize your personal settings, (e.g default settings of the
# Topographica or Imagen IPython extensions), add a python script file
# to the 'startup' folder. For instance, you could introduce a startup
# file 'settings.py' with the following contents:

# import dataviews
# dataviews.ipython.VIDEO_FORMAT = 'gif'
# dataviews.ipython.WARN_MISFORMATTED_DOCSTRINGS = True

# For more information, please consult the README file in the
# 'startup' directory.
