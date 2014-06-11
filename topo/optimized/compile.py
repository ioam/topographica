import os
import numpy

(basepath, _) = os.path.split(os.path.abspath(__file__))
(rootpath, _) = os.path.split(os.path.split(basepath)[0])

try:
    from Cython.Distutils import build_ext
except:
    from nose.plugins.skip import SkipTest
    raise SkipTest('Cython could not be imported, '
                   'cannot compile sparse components.')
from distutils.core import setup
from distutils.extension import Extension


ext_module = Extension(
    "optimized", [basepath + "/optimized.pyx"],
    extra_compile_args=['-fopenmp', '-O2', '-Wno-unused-variable',
                        '-fomit-frame-pointer','-funroll-loops'],
    extra_link_args=['-fopenmp', '-lstdc++'],
    include_dirs=[numpy.get_include()]
)

setup_args = ['--quiet', 'build_ext', '--build-lib', basepath]
setup(
    name = 'Cython Optimized Functions',
    cmdclass = {'build_ext': build_ext},
    ext_modules = [ext_module],  script_args = setup_args)