"""
Topographica-specific changes to the standard pydoc command.

Moves generated pydoc HTML files to the docs directory after they are
created by pydoc.  Intended for use with MAKE, from within the base
topographica/ directory.

The generated index.html file is for the topo/__init__.py file, which
does not necessarily catalog every .py file in topo/.  To see all
files, select the 'index' link at the top of one of the html docs.

To generate documentation, enter 'make docs' from the base
topographica/ directory, which will call this file on the Topographica
sources.

From the Makefile (Tabs have been stripped)::

    cleandocs:
        - rm -r docs

    docs: topo/*.py
        mkdir -p docs
        ./topographica topo/gendocs.py
        mv docs/topo.__init__.html docs/index.html
"""


import pydoc, glob, os
from os.path import isdir
from re import search, sub
from copy import copy


TOPO = 'topo'   # Subdirectory with Topographica source
DOCS = 'doc/Reference_Manual'   # Subdirectory to place Docs
pydoc.writing = 1


def _file_list(base_name):
    """
    Recursively generate a list of files and directories to document.

    base_name is the relative path to add to directories and files.
    Files that match CVS or __init__.py are ignored.
    """
    filelist = [f for f in glob.glob(base_name + '/*')
                if (isdir(f) or search('.py$',f))
                and not search('CVS',f) and not search('__init__.py',f)]
    for f in copy(filelist):
        if isdir(f):
            filelist = filelist + _file_list(f)
    return filelist


def filename_to_docname(f):
    """
    Convert a path name into the PyDoc filename it will turn into.

    If the path name ends in a .py, then it is cut off.  If there is no
    extension, the name is assumed to be a directory.
    """
    f = sub('/','.',f)
    if search('.py$',f):
        f = sub('.py$','.html',f)
    else:
        f = f + '.html'
    return f


def filename_to_packagename(f):
    """
    Convert a path name into the Python dotted-notation package name.

    If the name ends in a .py, then cut it off.  If there is no
    extension, the name is assumed to be a directory, and nothing is done
    other than to replace the '/' with '.'
    """
    f = sub('/','.',f)
    if search('.py$',f):
        f = sub('.py$','',f)
    return f


def generate_docs():
    """
    Generate all pydoc documentation files within a docs directory under
    ./topographica according to the constant DOCS.  After generation,
    there is an index.html that displays all the modules.  Note that
    if the documentation is being changed, it may be necessary to call
    'make cleandocs' to force a regeneration of documentation.  (We
    don't want to regenerate all the documentation each time a source
    file is changed.)
    """
    # os.system('rm -rf ' + DOCS + '/*') # Force regeneration
    filelist =  _file_list(TOPO) + [TOPO]
    for i in filelist:
        f = filename_to_docname(i)
        if not glob.glob(DOCS + '/' + f):
            pydoc.writedoc(filename_to_packagename(i))
        if glob.glob(f):
            cline = 'mv -f ' + f + ' ' + DOCS + '/'
            os.system(cline)
        else:
            filelist.remove(i)


if __name__ == '__main__':
    generate_docs()
