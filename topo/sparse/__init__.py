import os

(basepath, _) = os.path.split(os.path.abspath(__file__))

try:
    from topo.sparse import sparse, sparsecf # pyflakes:ignore (try/except import)
except ImportError:
    print "WARNING: Sparse extension could not be imported, ensure Cython and"
          "distutils are available and the extension has been compiled using"
          "python setup.py build_ext."
