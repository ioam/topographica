import os

(basepath, _) = os.path.split(os.path.abspath(__file__))

warn_for_each_unoptimized_component = False

try:
    from optimized import * # pyflakes:ignore (API import)
except ImportError:
    print "WARNING: Install distutils and Cython to build optimized component, " \
          "falling back to unoptimized components."
    from unoptimized import * # pyflakes:ignore (API import)
