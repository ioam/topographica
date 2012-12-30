"""
Support for optional Cython .pyx files.
"""

# CEBENHANCEMENT: If we begin using Cython components, consider adding
# more features of inlinec.py (ie: test of Cython compilation, control
# over warnings).

# CEBALERT: currently, need to do something like
# "export C_INCLUDE_PATH=lib/python2.6/site-packages/numpy/core/include/"
# for cython to find numpy headers. Might need to fix pyximport to look
# in the right place (it's possible to ask numpy for the location).

import __main__
import_pyx = __main__.__dict__.get('import_pyx',False)

pyximported = False

if import_pyx:
    try:
        import pyximport
        pyximport.install()
        pyximported = True
    except:
        pass


# JABALERT: As for the version in inlinec, I can't see any reason why
# this function accepts names rather than the more pythonic option of
# accepting objects, from which names can be extracted if necessary.
def provide_unoptimized_equivalent_cy(optimized_name, unoptimized_name, local_dict):
    """
    Replace the optimized Cython component with its unoptimized
    equivalent if pyximport is not available.

    If import_pyx is True, warns about the unavailable component.
    """
    if not pyximported:
        local_dict[optimized_name] = local_dict[unoptimized_name]
        if import_pyx:
            print '%s: Cython components not available; using %s instead of %s.' \
                  % (local_dict['__name__'], unoptimized_name, optimized_name)
