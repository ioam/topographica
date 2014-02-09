"""
Topographica IPython extension for notebook support. Automatically
loaded when importing the topo module but may also be explicitly
loaded using:

%load_ext topo.misc.ipython
"""
import os
import math
import time
import difflib
import uuid
import sys

import topo
import param


try:
    from IPython.display import HTML, Javascript, display
    from IPython.core.display import clear_output
except:
    clear_output = None
    from nose.plugins.skip import SkipTest
    raise SkipTest("IPython extension requires IPython >= 0.12")

# Pylabplots should return a matplotlib figure when working in Notebook
# otherwise open display windows for the Topographica Tk GUI
if not isinstance(sys.stdout, file):
    from topo.command import pylabplot
    pylabplot.PylabPlotCommand.display_window = False

class ProgressBar(param.Parameterized):
    """
    A simple text progress bar suitable for the IPython notebook.
    """

    width = param.Integer(default=70, doc="""
        The width of the progress bar in multiples of 'char'.""")

    fill_char = param.String(default='#', doc="""
        The character used to fill the progress bar.""")

    def __init__(self, **kwargs):
        super(ProgressBar,self).__init__(**kwargs)

    def update(self, percentage):
        " Update the progress bar to the given percentage value "
        if clear_output: clear_output()
        percent_per_char = 100.0 / self.width
        char_count = int(math.floor(percentage/percent_per_char) if percentage<100.0 else self.width)
        blank_count = self.width - char_count
        print '\r', "[%s%s] %0.1f%%" % (self.fill_char * char_count,
                              ' '*len(self.fill_char)*blank_count,
                              percentage)
        sys.stdout.flush()
        time.sleep(0.0001)


class RunProgress(ProgressBar):
    """
    Progress bar for running Topographica simulations in a Notebook.
    """

    interval = param.Number(default=20,
        doc="How often to update the progress bar in topo.sim.time units")

    def __init__(self, **kwargs):
        super(RunProgress,self).__init__(**kwargs)

    def run(self, duration):
        """
        Run topo.sim(duration), updating every interval duration.
        """
        completed = 0.0
        while (duration - completed) >= self.interval:
            topo.sim.run(self.interval)
            completed += self.interval
            self.update(100*(completed / duration))
        remaining = duration - completed
        if remaining != 0:
            topo.sim.run(remaining)
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

from dataviews.ipython import load_ipython_extension as load_imagen_extension
from dataviews.ipython import stack_display, view_display

try:
    from lancet import ViewFrame
    ViewFrame.display_fns.append(stack_display)
    ViewFrame.display_fns.append(view_display)
except:
    pass


_loaded = False
def load_ipython_extension(ip):
    load_imagen_extension(ip, verbose=False)

    global _loaded
    if not _loaded:
        _loaded = True
        from topo.command import runscript
        runscript.ns = ip.user_ns
        runscript.push = ip.push
