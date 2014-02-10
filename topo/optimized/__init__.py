import os

(basepath, _) = os.path.split(os.path.abspath(__file__))

warn_for_each_unoptimized_component = False

try:
    from distutils.core import run_setup

    # Run the setup script in the sandbox, so that it doesn't complain about unknown args when launched through nose
    run_setup(basepath + "/compile.py")

    from optimized import * # pyflakes:ignore (API import)
except ImportError:
    print "WARNING: Install distutils and Cython to build optimized component, " \
          "falling back to unoptimized components."
    from unoptimized import * # pyflakes:ignore (API import)