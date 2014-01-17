import sys, os

submodules = ['param', 'paramtk', 'imagen', 'featuremapper', 'lancet']

def sys_paths():
    cwd = os.path.abspath(os.path.split(__file__)[0])
    topo_path = os.path.abspath(os.path.join(cwd, '..'))
    return [os.path.join(cwd, s) for s in submodules] + [topo_path]

sys.path = sys_paths() + sys.path