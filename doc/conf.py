# -*- coding: utf-8 -*-

import os, sys

sys.path.append(os.path.abspath('.'))

from builder.shared_conf import * # pyflakes:ignore (API import)

paths = ['../external/imagen/', '../external/lancet/', '../external/param/',
         '../external/paramtk/', '../external/dataviews/', '../external/featuremapper/',
         '..']
add_paths(paths)

# General information about the project.
project = u'Topographica'
copyright = u'2013, IOAM'
ioam_project = 'topographica'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '0.9.8'
# The full version, including alpha/beta/rc tags.
release = '0.9.8'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build', 'test_data', 'reference_data', 'nbpublisher',
                    'builder']

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
html_title = project

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = 'images/topo-banner7.png'


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static', 'builder/_shared_static']

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = '_static/topo-favicon/topo-favicon.ico'


# Output file base name for HTML help builder.
htmlhelp_basename = project + 'doc'


# -- Options for LaTeX output --------------------------------------------------

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
  ('index', project + '.tex', project + u'Documentation',
   u'IOAM', 'manual'),
]


# -- Options for manual page output --------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('index', ioam_project, project + u' Documentation',
     [u'IOAM'], 1)
]

# If true, show URL addresses after external links.
#man_show_urls = False


# -- Options for Texinfo output ------------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
  ('index', project, project + u' Documentation',
   u'IOAM', project, 'One line description of project.',
   'Miscellaneous'),
]

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {'http://docs.python.org/': None,
                       'http://ipython.org/ipython-doc/2/': None,
                       'http://ioam.github.io/dataviews/': None,
                       'http://ioam.github.io/imagen/': None,
                       'http://ioam.github.io/featuremapper/': None,
                       'http://ioam.github.io/param/': None}

from builder.paramdoc import param_formatter
from nbpublisher import nbbuild


def setup(app):
    app.connect('autodoc-process-docstring', param_formatter)
    try:
        import runipy
        nbbuild.setup(app) # pyflakes:ignore (Warning import)
    except:
        print('RunIPy could not be imported, pages including the '
              'Notebook directive will not build correctly')

