"""
Basic files needed by all Topographica programs.

This package should be self-contained, i.e., should not refer to any
other part of Topographica.  For instance, no file may include an
import statement like 'from topo.package.module import' or 'import
topo.package.module'.  This policy ensures that all of the
Topographica packages outside of this one are optional.

However, this package does depend on two related non-Topographica
packages, i.e. param and imagen, and will not work without those being
available in the Python path.
"""

# For backwards compatibility; these files used to be in base/
from imagen import boundingregion,sheetcoords,patterngenerator # pyflakes:ignore (API import)

__all__ = ['arrayutil','boundingregion','cf','functionfamily','patterngenerator','projection','sheet','sheetcoords','sheetview','simulation']



