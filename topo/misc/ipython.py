"""
Topographica IPython extension for notebook support. Automatically
loaded when importing the topo module but may also be explicitly
loaded using:

%load_ext topo.misc.ipython
"""
import topo
import imagen
import param
import os, time, difflib, uuid, sys
from matplotlib import pyplot as plt


try:
    from IPython.core.pylabtools import print_figure
    from IPython.display import HTML, Javascript, display
except:
    from nose.plugins.skip import SkipTest
    raise SkipTest("IPython extension requires IPython >= 0.12")


from imagen.views import SheetView
from topo.base.sheet import Sheet
from topo.base.projection import Projection
from topo.command import pylabplot, analysis

# Pylabplots should return a matplotlib figure when working in Notebook
# otherwise open display windows for the Topographica Tk GUI
if not isinstance(sys.stdout, file):
    pylabplot.PylabPlotCommand.display_window = False

class ProgressBar(param.Parameterized):
    """
    A simple progress bar for IPython notebook inspired by the example
    notebook "Progress Bars" available in IPython GitHub repository.
    """

    name = param.String(doc="The name given to the progress bar.")

    def __init__(self, name, **kwargs):
        super(ProgressBar,self).__init__(name = name, **kwargs)
        self._divname = "%s-%s" % (name, uuid.uuid4())
        html = ("""<b>%s progress</b><div style="border: 1px"""
                """ solid black; width:500px">"""
                """<div id="%s" style="background-color:grey;"""
                """ width:0%%">&nbsp;</div></div>""")
        display(HTML(html % (name, self._divname)))

    def update(self, percentage):
        " Update the progress bar to the given percentage value "
        display(Javascript("$('div#%s').width('%i%%')"
                           % (self._divname, percentage)))

class RunProgress(ProgressBar):
    """
    Progress bar for running Topographica models in IPython notebook.
    """
    interval = param.Number(default=20,
        doc="How often to update the progress bar in topo.sim.time units")

    def __init__(self, interval=20, name="Training"):
        super(RunProgress,self).__init__(name=name, interval=interval)

    def run(self, duration):
        """
        Run topo.sim(duration), updating every interval duration.
        """
        completed = 0.0
        while (duration - completed) >= self.interval:
            topo.sim.run(self.interval)
            completed += self.interval
            self.update(100*(completed / duration))
        topo.sim.run(duration - completed)
        self.update(100)


def export_notebook(notebook, output_path=None, ext='.ty', identifier='_export_',
                    diff=True, invert=False, stale_time=None):
    """
    Given a v3-format .ipynb notebook file (from IPython 0.13 or
    later), allows the contents of labelled code cells to be exported
    to a plaintext file.  The typical use case is for generating a
    runnable plain Python source file from selected cells of an
    IPython notebook.

    Code is selected for export by placing the given identifier on the first
    line of the chosen code cells. By default, only the labelled cells are
    exported. This behavior may be inverted to exclude labelled cells by
    setting the invert flag.

    notebook    The filename of the notebook (.ipynb).
    output_path Optional output file path. Otherwise, uses the notebook basename.
    ext         The file extension of the output.
    identifier  The identifier used to label cells.
    diff        Whether to print a diff when overwriting content.
    invert      When set, only the non-labelled cells are exported.
    stale_time  Number of seconds that may elapse since the last notebook
                save before a staleness warning is issued. Useful when
                exporting from an active IPython notebook.
    """
    lines = []
    if output_path is None:
        output_path = os.path.splitext(os.path.basename(notebook))[0] + ext

    # Assumes the v3 version of the ipynb format.
    import IPython.nbformat.current
    nbnode = IPython.nbformat.current.read(open(notebook, 'r'), 'ipynb')
    for cell in nbnode['worksheets'][0]['cells']:
        if cell['cell_type'] == 'code':
            celllines = cell['input'].rsplit("\n")
            labelled = (celllines[0].strip() == identifier)
            if labelled and not invert:
                lines.append('\n'.join(celllines[1:]))
            if invert and not labelled:
                lines.append('\n'.join(celllines[1:]))

    if stale_time:
        modified_time = time.time() - os.path.getmtime(notebook)
        if  modified_time > stale_time:
            print "Notebook last saved %.1f seconds ago." % modified_time

    new_contents = "\n".join(lines)
    overwrite = os.path.isfile(output_path)
    if overwrite:
        old_contents = open(output_path, 'r').read()
    with open(output_path, 'w') as outfile:
        outfile.write(new_contents)

    if diff and overwrite:
        deltas =difflib.unified_diff(old_contents.splitlines(), new_contents.splitlines(), lineterm='')
        print '\n'.join(list(deltas))

#===============#
# Display hooks #
#===============#

from topo.analysis.featureresponses import update_sheet_activity

def sheet_activity_display(sheet, size=256, format='svg'):
    if not isinstance(sheet, Sheet): return None
    update_sheet_activity(sheet.name, force=True)
    return sheetview_display(sheet.views.maps._activity_buffer.top,
                             size=size, format=format)


def projection_activity_display(projection, size=256, format='svg'):
    if not isinstance(projection, Projection): return None
    analysis.update_projectionactivity(outputs=[projection.dest.name])
    view = projection.dest.views.maps[projection.name+'ProjectionActivity'].top
    return sheetview_display(view, size=size, format=format)


def pattern_display(pattern, size=256, format='svg'):
    if not isinstance(pattern, imagen.PatternGenerator): return None
    view = SheetView(pattern(xdensity=size, ydensity=size), pattern.bounds)
    return sheetview_display(view, size=size, format=format)

def sheetview_display(sheetview, size=256, format='svg'):
    if not isinstance(sheetview, SheetView): return None
    cyclic = sheetview.cyclic_range is not None
    plot_type = plt.hsv if cyclic else plt.gray
    mat = sheetview.data/sheetview.cyclic_range if cyclic else sheetview.data
    extent = sheetview.bounds.aarect().lbrt()
    fig = pylabplot.matrixplot(mat,
                             extent=extent,
                             plot_type=plot_type)
    inches = size / float(fig.dpi)
    fig.set_size_inches(inches, inches)
    prefix = 'data:image/png;base64,'
    b64 = prefix + print_figure(fig, 'png').encode("base64")
    html = "<img height='%d' width='%d' src='%s' />" % (size, size, b64)
    plt.close(fig)
    return html

try:
    from lancet import ViewFrame
    ViewFrame.display_fns.append(sheetview_display)
    ViewFrame.display_fns.append(sheet_activity_display)
    ViewFrame.display_fns.append(projection_activity_display)
    ViewFrame.display_fns.append(pattern_display)
except:
    pass


_loaded = False
def load_ipython_extension(ip):
    from topo.command import runscript
    runscript.ns = ip.user_ns
    runscript.push = ip.push

    global _loaded
    if not _loaded:
        _loaded = True

        html_formatter = ip.display_formatter.formatters['text/html']
        html_formatter.for_type(Projection, projection_activity_display)
        html_formatter.for_type(Sheet, sheet_activity_display)
        html_formatter.for_type(SheetView, sheetview_display)
        html_formatter.for_type(imagen.PatternGenerator, pattern_display)
