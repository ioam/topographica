# Configuration file for ipython.

c = get_config()

import sys, os
profile_dir = os.path.split(__file__)[0]
project_dir = os.path.join(profile_dir, '..', '..', '..')
sys.path = [os.path.abspath(project_dir)] + sys.path

import external

# To customize your personal settings, (e.g default settings of the
# Topographica IPython extension), add a python script file to the
# 'startup' folder. For instance, you could add a file 'settings.py'
# with the following contents:

# import dataviews
# dataviews.ipython.VIDEO_FORMAT = 'gif'
# dataviews.ipython.WARN_MISFORMATTED_DOCSTRINGS = True

# For more information, consult the README file in the 'startup'
# directory.
