<H1>Publishing Topographica results</H1>

<P>While many people will want to use Topographica for demonstrations,
class tutorials, small projects, etc., other projects are expected to
lead to a publication eventually.  This section describes how to
produce publication-quality results, rather than screen images.  If
you follow these guidelines, you should end up with smaller file
sizes, faster document generation, and better quality.

<P>Before discussing Topographica-specific tips, we first provide
background on image formats and image plotting in general.  These
considerations apply to any image displayed on screen or in a paper.


<H2><A NAME="image-types">Image types: photos, bitmaps, and vector graphics</A></H2>

<P>Before working with any graphical software, it is crucial to
understand the three basic types of computer graphics images, which
determine the file formats and programs that are appropriate for a
particular task.  The three types and the recommended formats are:

<P>
<TABLE>
<TR>
<TH><b>Type</b></TH>
<TH><b>Description</b></TH>
<TH><b>Examples</b></TH>
<TH><b>Still formats</b></TH>
<TH><b>Animated formats</b></TH>

<TR><TD><B>Photographic bitmaps</B></TD>
<TD>smooth, continuously-varying bitmapped images, with lots of colors</TD>
<TD>photographs, photorealistic renderings, scans</TD>
<TD>JPEG</TD>
<TD>MPEG</TD>

<TR><TD><B>Indexed-color bitmaps</B></TD>

<TD>sharp-edged bitmapped images with only a few colors</TD> 
<TD>screenshots, 80's-style video games, icons</TD>
<TD>PNG, GIF (if colors<256), TIFF, BMP</TD>
<TD>GIF89a, MNG</TD>

<TR><TD><B>Vector/structured graphics</B></TD>
<TD>sharp-edged diagrams/text that is resolution-independent,
   i.e. not bitmapped and intended to display well on both the
   screen and on a printer.</TD>
<TD>text, diagrams, charts, graphs</TD>
<TD>SVG, PDF, EPS, PostScript, FIG</TD>
<TD>Flash</TD>
</TABLE>

<P>Each of these three categories needs to be treated very
differently, and if you use an image from one category with a format
or program suitable for another, the result will have much lower
quality and a much larger file size than it would with the correct
format.  For instance, if you are drawing a box-and-arrow diagram to
be used in a printed document and save it in type GIF, the result will
have ugly "jaggies" and will look quite unprofessional.  The same
simple drawing saved in type JPEG will have little "halos" and
"ringing" around all of the sharp borders if you look closely, and
solid color areas will have "speckles" and will not look uniform,
especially in a printout. Plus the file size will be very large in
JPEG and GIF for any reasonable quality printed version.  So for such
a drawing, a vector drawing program is the only acceptable choice.  On
the other hand, vector drawing programs do not generally offer any
benefits for photographs, for which JPEG is a great choice.  But JPEG
is a very bad choice for screenshots, as it will introduce the
above-mentioned artifacts, and PNG works well for those.

<P>Overuse of JPEG is probably the most common mistake; see the
<a target="_top" href="http://www.faqs.org/faqs/jpeg-faq/part1/section-3.html">JPEG
FAQ</a> for more information about when <strong>not</strong> to use
it.  Note that the most important time to consider the format is when
you first create the file.  Once a file is in JPEG format, it will
have artifacts forever, even if later converted to a non-lossy format.
And once a file is in GIF format, it will have limited color
resolution, even if later converted to JPEG or PNG.  Using PNG by
default works well, switching to JPEG for photo-like images and PDF or
SVG for diagrams when appropriate.


<H2>Printed versus displayed graphics (white versus black backgrounds)</H2>

<P>Display screens like CRTs create images by combining different
colors of light, starting from a black background and adding more red,
green, and/or blue light until the image becomes white.  (LCD displays
are similar, though the light that they use is often initially white
and then filtered into these three colors.)  This process is called
<A HREF="http://en.wikipedia.org/wiki/Additive_color"> additive color
mixing</A>.  The result is that bright colors and bright white are
both very visible against a black background on a CRT; they are both
very different from the default state of the screen.

<P>Diagrams on printed paper use
<A HREF="http://en.wikipedia.org/wiki/Subtractive_color"> subtractive
color mixing</A> -- the paper initially reflects white light (all
colors of light), and then ink put on it removes more and more of
certain colors of light until none remain, at which case black is
perceived.  In this case very bright colors (with lots of color ink)
and black both show up well against white.  But each color is
difficult to distinguish from black, because both bright colors and
black have large amounts of ink, and so bright colors on a black
background is a poor choice for subtractive color.

<P>The practical effect is that diagrams and plots displayed onscreen
should have white or colored lines or patches against a black
background, while those printed on paper should have black or colored
lines or patches against a white background.  Only in those cases will
colors and fine lines be clear and visible.

<P>Unfortunately, Topographica so far has only partial support for
black-on-white diagrams suitable for printing; in other cases support
is planned but not yet implemented.  In some cases, it is possible
to swap the Saturation and Value channels of plots using
<A HREF="http://www.gimp.org">the Gimp</A>, but in others programming
support will be necessary.



<H2>Topographica plots</H2>

<P>These sections describe how to generate publication-quality figures
from each of the various Topographica plots and display windows.  Note
that in most cases, it is best to automate these commands by doing
them in <a target="_top" href="batch.html">batch mode</a>, so that you have a permanent
record of all of the commands and options used to generate your
results, and so that they will be stored in a uniquely identifiable
directory that you can access reliably later.


<H4>Model architecture</H4>

<P>The Model Editor window of Topographica is helpful for generating
architecture diagrams for modeling papers.  Just arrange the Sheets as
clearly as possible, make sure everything is named appropriately, and
then export this diagram to a file for use in your paper by
right-clicking and selecting <code>Export PostScript image</code>.
You will probably want to select <code>Printing</code> mode first, to
plot each sheet in white instead of black.

<P>Of course, it is possible to grab a screenshot of the Model Editor
window as well, but this is not recommended because the result will
have jagged lines, jagged text, and will usually be a much larger file
than necessary.  Once you have an Encapsulated PostScript image, you
can convert it to PDF for use in a document using
<code>epstopdf</code> (free) or Adobe Acrobat Distiller (expensive).


<H4>Preference Map plots</H4>

<P>In the GUI, plots in one of these windows can be saved by right
clicking on one and selecting <code>Save as PNG</code>.  A unique
filename is generated automatically.  You can also save these images
from a script, e.g. in batch mode, using
<a target="_top" href="commandline.html#saving-bitmaps">save_plotgroup</a>.

<H4>Color keys</H4>

PlotGroups that include color-based plots, such as preference maps,
typically include a color key when displayed in a Topographica window.
A low-resolution bitmap version of the key is saved with the plots by
save_plotgroup, but for publication it is usually better to use the
original vector-format PDF files from which the bitmaps were
generated.  The PDF files will usually be located near the bitmap used
in the PlotGroup.  For instance, the 'Orientation Preference'
PlotGroup defined in topo/command/analysis.py specifies that the key
is 'topo/command/or_key_white_vert_small.png', and the corresponding
PDF file is 'topo/command/or_key_white_vert.pdf'.

<H4>Activity and ConnectionField plots</H4>

<P>Plots in these windows can be saved just as for Preference Map
plots, using
<a target="_top" href="commandline.html#saving-bitmaps">save_plotgroup</a>.

<p> Note that if you plan to show plots from different Sheets in your
paper (e.g. multiple ConnectionFields side by side, or Activity in
each Sheet), you will usually want to ensure that each plot is plotted
at the same size scale, so that their sizes will faithfully reflect
their Sheet coordinate sizes.  To do this, you would turn <code>Sheet
Coordinates</code> on and <code>Integer Scaling</code> off.  This way,
the relative sizes of the sheets will be preserved, at the expense of
individual units being slightly different sizes and the overall image
size being larger.  You will still need to ensure that the relative
sizes are preserved when presenting the images in a paper, of course.
Otherwise, the reader is likely to be confused about what part of each
plot corresponds to the others.

<H4>Projection plots</H4>

<P>The GUI does not yet support saving Projection plots from the
right-click menu.  However, they can be saved in PNG format from the
command line using <a target="_top" href="commandline.html#saving-bitmaps">save_plotgroup</a>.

<P>Alternatively, they can be selected by taking a screenshot using
your favorite such utility.
First, be sure to make the CFs as small as possible on screen;
there is no need to store many bytes of data for each weight value
(unless you want very thin outlines around the weights).  Also, be
sure that each pixel represents one unit, by turning on <code>Integer
Scaling</code>.  That way each unit will be plotted as either 1x1,
2x2, 3x3, etc., rather than some being 1x2, some 2x3, etc., as needed
to reach a certain fixed overall plot size.  Be sure to hit
<code>Reduce</code> as many times as you can, to get down to 1 pixel
per unit.  It does not matter that the
plot will be too small on screen at that point; it will be fine in
the final document if it is scaled appropriately.  Be sure to save in
PNG or another <A HREF="#image-types">appropriate bitmap format</A>,
rather than GIF or JPG.


<H2>Citations</H2>

<P><A NAME="citing">If</A> you use this software in work leading to an
academic publication, please cite the following paper so that readers
will know how to replicate your results and build upon them.  (Plus,
it is only polite to cite work done by others that you rely on!)

<BLOCKQUOTE>
James&nbsp;A. Bednar.
<A HREF="http://www.brains-minds-media.org/archive/1402">Understanding
Neural Maps with Topographica</A>.
<CITE>Brains, Minds, and Media</CITE>, 3:bmm1402, 2008.
</BLOCKQUOTE>

or in BibTeX format:

<pre>
@Article{bednar:bmm08,
  author       = "James A. Bednar",
  title	       = "Understanding Neural Maps with {Topographica}",
  journal      = "Brains, Minds, and Media",
  year	       = 2008,
  volume       = 3,
  pages	       = "bmm1402",
  url          = "http://www.brains-minds-media.org/archive/1402",
}
</pre>
