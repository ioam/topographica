===============================
SVG Templates and PNG snapshots
===============================

This directory contains the SVG templates used for dynamic figure
generation as well as the PNG snapshots which allow for quicker
loading of the ``stevens_jn13`` notebook. The code that uses the 
templates to dynamically generate figures  can be found in
``./jn13_figures/lib/compose.py``.

- ``snapshots`` directory: Raster PNG snapshots generated at the end
  of the ``stevens_jn13`` notebook. Requires `ImageMagick
  <http://www.imagemagick.org>`_ and uses the following two commands::

   !mogrify -format png ./jn13_figures/figures/*.svg
   !mv ./jn13_figures/figures/*.png ./jn13_figures/templates/snapshots/

  These rasters then act as placeholders until the dynamic SVG figures
  are generated. The notebook with all the SVGs loaded can become
  sluggish due to the large number of SVG assets to be rendered.

- SVG templates: These SVG templates were generated with `Inkscape
  <http://inkscape.org/>`_. They are standard SVGs that have three
  types of placeholder where dynamic assets may be inserted: raster
  links, SVG links and text replacement:

  - Raster links are standard non-embedded raster images using
    relative file path. For instance, an image with a URL link to
    ``./L_pref.png`` will have that file embedded once the file is
    available and the template is applied.
  - SVG links indicate relative paths to SVG subfigures which will be
    embedded once the template is applied. This is achieved by
    setting the Inkscape label on empty SVG rectangles (Right click
    => Object Properties => Label). For instance, a rectangle with
    ``./L/L.svg`` as a label will have that SVG embedded within the
    rectangle bounds when the template is applied.
  - Text replacement allows SVG text to be set dynamically. For
    instance, in the ``fig06_09.svg`` template, the label
    ``[Model-Name]`` is replaced with the appropriate model name
    dynamically. Note that the text replacement algorithm is very
    simple - unique identifiers must be used for replacement.
