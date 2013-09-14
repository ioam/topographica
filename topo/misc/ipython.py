"""
Topographica IPython extension for notebook support. Load with:

%load_ext topo.misc.ipython
"""
import os, time, difflib
from matplotlib import pyplot as plt
from IPython.core.pylabtools import print_figure

import imagen.ipython
from topo.command import pylabplot, analysis

# Pylabplots should simply return a matplotlib figure when working with IPython
pylabplot.PylabPlotCommand.display_window = False

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



def sheetview_display(sheetview):
    f = pylabplot.activityplot(sheetview, sheetview.view()[0])
    prefix = 'data:image/png;base64,'
    b64 = prefix+ print_figure(f, 'png').encode("base64")
    html = '<img src="%s" />' % b64
    plt.close(f)
    return html

def sheet_activity_display(sheet):
    analysis.update_sheet_activity(sheet.name, force=True)
    return sheetview_display(sheet.views['Activity'])

def projection_activity_display(projection):
    analysis.update_projectionactivity(sheet=projection.dest)
    view = projection.dest.views[('ProjectionActivity', projection.dest.name, projection.name)]
    #arr = view.view()[0]
    #arr *= 10
    return sheetview_display(view)


_loaded = False
def load_ipython_extension(ip):
    from topo.command import runscript
    # Load Imagen's IPython extension
    imagen.ipython.load_ipython_extension(ip)

    runscript.ns = ip.user_ns
    runscript.push = ip.push

    global _loaded
    if not _loaded:
        _loaded = True

        html_formatter = ip.display_formatter.formatters['text/html']
        html_formatter.for_type_by_name('topo.base.projection', 'Projection', projection_activity_display)
        html_formatter.for_type_by_name('topo.base.sheet', 'Sheet', sheet_activity_display)
        html_formatter.for_type_by_name('topo.base.sheetview', 'SheetView', sheetview_display)
