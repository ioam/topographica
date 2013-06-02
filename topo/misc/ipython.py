"""
Topographica IPython extension for notebook support. Load with:

%load_ext topo.misc.ipython
"""
import imagen.ipython
import numpy as np

import matplotlib.pyplot as plt

from tempfile import NamedTemporaryFile
from matplotlib import animation

from IPython.core.pylabtools import print_figure

from topo.command import analysis
from topo.command import plots

VIDEO_TAG = """<video controls>
 <source src="data:video/x-m4v;base64,{0}" type="video/mp4">
 Your browser does not support the video tag.
</video>"""

def animation_to_HTML(anim):
    if not hasattr(anim, '_encoded_video'):
        with NamedTemporaryFile(suffix='.mp4') as f:
            anim.save(f.name, extra_args=['-vcodec', 'libx264']) # fps=20
            video = open(f.name, "rb").read()
        anim._encoded_video = video.encode("base64")
    return VIDEO_TAG.format(anim._encoded_video)


def sheetview_display(sheetview, figure_format='png'):
    svplot = plots.matrixplot(sheetview)

    if svplot.max_frames > 1:
        return animation_to_HTML(svplot.anim())
    else:
        f = svplot.fig()
        if figure_format == 'svg':
            html = print_figure(f, 'svg')
        elif figure_format == 'png':
            prefix = 'data:image/png;base64,'
            b64 = prefix+ print_figure(f, 'png').encode("base64")
            html = '<img src="%s" />' % b64
        plt.close(f)
        return html

def sheet_display(sheet):
    analysis.update_sheet_activity(sheet.name, force=True)
    return sheetview_display(sheet.views['Activity'])

def projection_activity_display(projection):
    analysis.update_projectionactivity(sheet=projection.dest)
    view = projection.dest.views[('ProjectionActivity', projection.dest.name, projection.name)]
    arr = view.view()[0]
    arr *= 10
    return sheetview_display(view)


_loaded = False
def load_ipython_extension(ip):
    # Load Imagen's IPython extension
    imagen.ipython.load_ipython_extension(ip)

    from topo.command import runscript
    runscript.ns = ip.user_ns
    runscript.push = ip.push

    global _loaded
    if not _loaded:
        _loaded = True
        html_formatter = ip.display_formatter.formatters['text/html']

        html_formatter.for_type_by_name('topo.base.projection', 'Projection', projection_activity_display)
        html_formatter.for_type_by_name('topo.base.sheet', 'Sheet', sheet_display)
        html_formatter.for_type_by_name('topo.base.sheetview', 'SheetView', sheetview_display)
        html_formatter.for_type_by_name('matplotlib.animation', 'FuncAnimation', animation_to_HTML)
