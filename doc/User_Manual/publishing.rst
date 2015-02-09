*******************************
Publishing Topographica results
*******************************

While many people will want to use Topographica for demonstrations,
class tutorials, small projects, etc., other projects are expected
to lead to a publication eventually. This section describes how to
produce publication-quality results, rather than screen images. If
you follow these guidelines, you should end up with smaller file
sizes, faster document generation, and better quality.

Before discussing Topographica-specific tips, we first provide
background on image formats and image plotting in general. These
considerations apply to any image displayed on screen or in a paper.
Other suggestions for making good figures are available from
`Rougier et al. (2014)`_.

Image types: photos, bitmaps, and vector graphics
-------------------------------------------------

Before working with any graphical software, it is crucial to
understand the three basic types of computer graphics images, which
determine the file formats and programs that are appropriate for a
particular task. The three types and the recommended formats are:

.. _image-types:

+-------------------------+------------------------------------------------------------------+---------------------------------------------+-----------------------------------+----------------------+
| **Type**                | **Description**                                                  | **Examples**                                | **Still formats**                 | **Animated formats** |
+-------------------------+------------------------------------------------------------------+---------------------------------------------+-----------------------------------+----------------------+
|**Photographic bitmaps** |smooth, continuously-varying bitmapped images, with lots of colors|photographs, photorealistic renderings, scans| JPEG                              | MPEG                 |
+-------------------------+------------------------------------------------------------------+---------------------------------------------+-----------------------------------+----------------------+
|**Indexed-color bitmaps**|sharp-edged bitmapped images with only a few colors               | screenshots, 80's-style video games, icons  |PNG, GIF (if colors<256), TIFF, BMP| GIF89a, MNG          |
+-------------------------+------------------------------------------------------------------+---------------------------------------------+-----------------------------------+----------------------+
| **Vector/structured     |sharp-edged diagrams/text that is resolution-independent, i.e. not| text, diagrams, charts, graphs              | SVG, PDF, EPS, PostScript, FIG    | Flash                |
| graphics**              |bitmapped and intended to display well on both the screen and on a|                                             |                                   |                      |
|                         |printer.                                                          |                                             |                                   |                      |
+-------------------------+------------------------------------------------------------------+---------------------------------------------+-----------------------------------+----------------------+

Each of these three categories needs to be treated very differently,
and if you use an image from one category with a format or program
suitable for another, the result will have much lower quality and a
much larger file size than it would with the correct format. For
instance, if you are drawing a box-and-arrow diagram to be used in a
printed document and save it in type GIF, the result will have ugly
"jaggies" and will look quite unprofessional. The same simple
drawing saved in type JPEG will have little "halos" and "ringing"
around all of the sharp borders if you look closely, and solid color
areas will have "speckles" and will not look uniform, especially in
a printout. Plus the file size will be very large in JPEG and GIF
for any reasonable quality printed version. So for such a drawing, a
vector drawing program is the only acceptable choice. On the other
hand, vector drawing programs do not generally offer any benefits
for photographs, for which JPEG is a great choice. But JPEG is a
very bad choice for screenshots, as it will introduce the
above-mentioned artifacts, and PNG works well for those.

Overuse of JPEG is probably the most common mistake; see the `JPEG
FAQ`_ for more information about when **not** to use it. Note that
the most important time to consider the format is when you first
create the file. Once a file is in JPEG format, it will have
artifacts forever, even if later converted to a non-lossy format.
And once a file is in GIF format, it will have limited color
resolution, even if later converted to JPEG or PNG. Using PNG by
default works well, switching to JPEG for photo-like images and PDF
or SVG for diagrams when appropriate.

Printed versus displayed graphics (white versus black backgrounds)
------------------------------------------------------------------

Display screens like CRTs create images by combining different
colors of light, starting from a black background and adding more
red, green, and/or blue light until the image becomes white. (LCD
displays are similar, though the light that they use is often
initially white and then filtered into these three colors.) This
process is called `additive color mixing`_. The result is that
bright colors and bright white are both very visible against a black
background on a CRT; they are both very different from the default
state of the screen.

Diagrams on printed paper use `subtractive color mixing`_ -- the
paper initially reflects white light (all colors of light), and then
ink put on it removes more and more of certain colors of light until
none remain, at which case black is perceived. In this case very
bright colors (with lots of color ink) and black both show up well
against white. But each color is difficult to distinguish from
black, because both bright colors and black have large amounts of
ink, and so bright colors on a black background is a poor choice for
subtractive color.

The practical effect is that diagrams and plots displayed onscreen
should have white or colored lines or patches against a black
background, while those printed on paper should have black or
colored lines or patches against a white background. Only in those
cases will colors and fine lines be clear and visible.

Unfortunately, Topographica so far has only partial support for
black-on-white diagrams suitable for printing; in other cases
support is planned but not yet implemented. In some cases, it is
possible to swap the Saturation and Value channels of plots using
`the Gimp`_, but in others programming support will be necessary.

Topographica plots
------------------

These sections describe how to generate publication-quality figures
from each of the various Topographica plots and display windows.
Note that in most cases, it is best to automate these commands by
doing them in `batch mode`_, so that you have a permanent record of
all of the commands and options used to generate your results, and
so that they will be stored in a uniquely identifiable directory
that you can access reliably later.

Model architecture
^^^^^^^^^^^^^^^^^^

The Model Editor window of Topographica is helpful for generating
architecture diagrams for modeling papers. Just arrange the Sheets
as clearly as possible, make sure everything is named appropriately,
and then export this diagram to a file for use in your paper by
right-clicking and selecting ``Export PostScript image``. You will
probably want to select ``Printing`` mode first, to plot each sheet
in white instead of black.

Of course, it is possible to grab a screenshot of the Model Editor
window as well, but this is not recommended because the result will
have jagged lines, jagged text, and will usually be a much larger
file than necessary. 

Once you have an Encapsulated PostScript image, you can convert it to
PDF for use in a document using ``epstopdf`` (free) or Adobe Acrobat
Distiller (expensive).  You can also load it into a vector drawing
program like Inkscape (free) to edit it, e.g. to add extra labels or
to change the fonts.

Preference Map plots
^^^^^^^^^^^^^^^^^^^^

In the Tk GUI, plots in one of these windows can be saved by right
clicking on one and selecting ``Save as PNG``. A unique filename is
generated automatically. You can also save these images from a
script, e.g. in batch mode, using `save\_plotgroup`_.

Color keys
^^^^^^^^^^

PlotGroups that include color-based plots, such as preference maps,
typically include a color key when displayed in a Topographica
window. A low-resolution bitmap version of the key is saved with the
plots by save\_plotgroup, but for publication it is usually better
to use the original vector-format PDF files from which the bitmaps
were generated. The PDF files will usually be located near the
bitmap used in the PlotGroup. For instance, the 'Orientation
Preference' PlotGroup defined in topo/command/analysis.py specifies
that the key is 'topo/static/or\_key\_white\_vert\_small.png', and
the corresponding PDF file is
'topo/static/or\_key\_white\_vert.pdf'.

Activity and ConnectionField plots
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Plots in these Tk GUI windows can be saved just as for Preference Map
plots, using `save\_plotgroup`_.

Note that if you plan to show plots from different Sheets in your
paper (e.g. multiple ConnectionFields side by side, or Activity in
each Sheet), you will usually want to ensure that each plot is
plotted at the same size scale, so that their sizes will faithfully
reflect their Sheet coordinate sizes. To do this, you would turn
``Sheet Coordinates`` on and ``Integer Scaling`` off. This way, the
relative sizes of the sheets will be preserved, at the expense of
individual units being slightly different sizes and the overall
image size being larger. You will still need to ensure that the
relative sizes are preserved when presenting the images in a paper,
of course. Otherwise, the reader is likely to be confused about what
part of each plot corresponds to the others.

Projection plots
^^^^^^^^^^^^^^^^

The Tk GUI does not yet support saving Projection plots from the
right-click menu. However, they can be saved in PNG format from the
command line using `save\_plotgroup`_.

Alternatively, they can be selected by taking a screenshot using
your favorite such utility. First, be sure to make the CFs as small
as possible on screen; there is no need to store many bytes of data
for each weight value (unless you want very thin outlines around the
weights). Also, be sure that each pixel represents one unit, by
turning on ``Integer Scaling``. That way each unit will be plotted
as either 1x1, 2x2, 3x3, etc., rather than some being 1x2, some 2x3,
etc., as needed to reach a certain fixed overall plot size. Be sure
to hit ``Reduce`` as many times as you can, to get down to 1 pixel
per unit. It does not matter that the plot will be too small on
screen at that point; it will be fine in the final document if it is
scaled appropriately. Be sure to save in PNG or another `appropriate
bitmap format`_, rather than GIF or JPG.

Citations
---------

If you use this software in work leading to an academic publication,
please cite the following paper so that readers will know how to
replicate your results and build upon them. 

    James A. Bednar.
    `Topographica: Building and Analyzing Map-Level Simulations from
    Python, C/C++, MATLAB, NEST, or NEURON Components. 
    <http://dx.doi.org/10.3389/neuro.11.008.2009>`_
    Frontiers in Neuroinformatics, 3:8, 2009.

or in BibTeX format:

::

    @Article{bednar:fin09,
      author  = "James A. Bednar",
      title   = "{Topographica}: {B}uilding and Analyzing Map-Level
                 Simulations from {Python}, {C/C++}, {MATLAB}, {NEST},
                 or {NEURON} Components",
      journal = "Frontiers in Neuroinformatics",
      year    = 2009,
      volume  = 3,
      pages   = 8,
      url     = "http://dx.doi.org/10.3389/neuro.11.008.2009",
    }



.. _JPEG FAQ: http://www.faqs.org/faqs/jpeg-faq/part1/section-3.html
.. _additive color mixing: http://en.wikipedia.org/wiki/Additive_color
.. _subtractive color mixing: http://en.wikipedia.org/wiki/Subtractive_color
.. _the Gimp: http://www.gimp.org
.. _batch mode: batch.html
.. _save\_plotgroup: commandline.html#saving-bitmaps
.. _appropriate bitmap format: #image-types
.. _Rougier et al. (2014): http://dx.doi.org/10.1371/journal.pcbi.1003833
