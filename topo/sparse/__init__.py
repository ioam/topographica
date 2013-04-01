import numpy
import os

(basepath, _) = os.path.split(os.path.abspath(__file__))
(rootpath, _) = os.path.split(os.path.split(basepath)[0])

try:
    from Cython.Distutils import build_ext
    from distutils.core import setup
    from distutils.extension import Extension

    ext_modules = [Extension("sparse", [basepath + "/sparse.pyx"],
                             language="c++", extra_compile_args = ["-w","-O2","-fopenmp","-DNDEBUG","-msse2"],
                             extra_link_args=['-lgomp'])]

    setup_args = ['--quiet','build_ext','--build-lib',basepath]
    setup(name = "Sparse CF Matrix",  ext_modules = ext_modules,
          include_dirs=[rootpath+'/external/',numpy.get_include()],
          cmdclass = {'build_ext':build_ext}, script_args = setup_args)

    from topo.sparse import sparse #pyflakes:ignore (this import is intentional)
except ImportError:
    print "WARNING: Install distutils and Cython to build sparse extension."
