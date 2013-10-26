import os

(basepath, _) = os.path.split(os.path.abspath(__file__))

try:
    from distutils.core import run_setup

    # Run the setup script in the sandbox, so that it doesn't complain about unknown args when launched through nose
    run_setup(basepath + "/compile.py")

    from topo.sparse import sparse # pyflakes:ignore (try/except import)
except ImportError:
    print "WARNING: Install distutils and Cython to build sparse extension."
