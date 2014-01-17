# Configuration file for ipython.

c = get_config()

import sys, os
cwd = os.path.split(__file__)[0]
basepath = os.path.abspath(os.path.join(cwd, '..', '..','..'))

sys.path = [os.path.join(basepath, 'external', 'param')] + sys.path
sys.path = [os.path.join(basepath, 'external', 'paramtk')] + sys.path
sys.path = [os.path.join(basepath, 'external', 'imagen')] + sys.path
sys.path = [os.path.join(basepath, 'external', 'lancet')] + sys.path
sys.path = [os.path.join(basepath, 'external', 'featuremapper')] + sys.path
sys.path = [basepath] + sys.path

