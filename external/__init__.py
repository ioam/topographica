import sys, os

submodules = ['param', 'paramtk', 'imagen', 'featuremapper', 'lancet', 'dataviews']

def sys_paths():
    cwd = os.path.abspath(os.path.split(__file__)[0])
    topo_path = os.path.abspath(os.path.join(cwd, '..'))
    module_dirs = [os.path.join(cwd, s) for s in submodules]
    for submodule, module_dir in zip(submodules, module_dirs):
        if not os.path.isdir(module_dir) or not os.listdir(module_dir):
            raise ImportError('{submodule} submodule files not found in {module_dir}. '
                              'Please run `git submodule update --init` before '
                              'launching Topographica.'.format(submodule=submodule,
                                                               module_dir=module_dir))

    return module_dirs + [topo_path]

sys.path = sys_paths() + sys.path