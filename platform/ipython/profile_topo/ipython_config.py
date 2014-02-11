# Configuration file for ipython.

c = get_config()

import sys, os
profile_dir = os.path.split(__file__)[0]
project_dir = os.path.join(profile_dir, '..', '..', '..')
sys.path = [os.path.abspath(project_dir)] + sys.path

import external

# Example of how to change the default imagen video format via profile

# from imagen import ipython
# ipython.VIDEO_FORMAT = 'gif'
