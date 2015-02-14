"""
Topographica IPython extension for notebook support. Automatically
loaded when importing the topo module but may also be explicitly
loaded using:

%load_ext topo.misc.ipython
"""
import os
import time
import difflib

import topo


try:
    import IPython # pyflakes:ignore (Required import)
    from IPython.core.magic import Magics, magics_class, line_magic
except:
    from unittest import SkipTest
    raise SkipTest("IPython extension requires IPython >= 0.12")


def prompt(message, default, options, skip=False):
    """
    Helper function to repeatedly prompt the user with a list of
    options. If no input is given, the default value is returned. If
    wither the skip flag is True or the prompt is in a batch mode
    environment (e.g. for automated testing), the default value is
    immediately returned.
    """
    options = list(set(opt.lower() for opt in options))
    show_options = options[:]
    assert default.lower() in options, "Default value must be in options list."
    if skip or ('SKIP_IPYTHON_PROMPTS' in os.environ):
        return default
    default_index = show_options.index(default.lower())
    show_options[default_index] = show_options[default_index].upper()
    choices ="/".join(show_options)
    prompt_msg = "%s (%s): " % (message, choices)
    response = raw_input(prompt_msg)
    if response =="":
        return default.lower()
    while response.lower() not in options:
        msg = ("Response '%s' not in available options (%s). Please try again: "
               % (response, choices))
        response = raw_input(msg)
    return response.lower()


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
    print("Deprecation Warning: Please use the %define_exporter magic instead")
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


@magics_class
class ExportMagic(Magics):
    """
    Line magic that defines a cell magic to export the cell contents
    to a specific file. For instance, running

    %define_exporter OUT ./output.txt

    will define an %%OUT cell magic that writes to the file
    output.txt. This cell magic takes a optional arguments 'clear' and
    'run'. If 'clear' should be specified for the first cell to be
    exported. If 'run' is specified, the cell is executed in the
    active notebook as well as exported.
    """
    @line_magic
    def define_exporter(self, line):
        split = line.split()
        if len(split) != 2:
            raise Exception("Please supply the export magic name and target filename")
        [name, filename] = split

        def exporter(line, cell):
            mode = 'w' if 'clear' in line.split() else 'a'
            with open(os.path.abspath(filename), mode) as f:
                    f.write(cell+'\n')

            if 'run' in line.split():
                self.shell.run_cell(cell)

        self.shell.register_magic_function(exporter, magic_kind='cell',
                                           magic_name=name)
        self.shell.set_hook('complete_command', lambda k,v: ['clear'],
                            str_key = '%%{name}'.format(name=name))

@magics_class
class TimerMagic(Magics):

    start_time = None

    @staticmethod
    def elapsed_time():
        elapsed = time.time() -  TimerMagic.start_time
        minutes = elapsed // 60
        hours = minutes // 60
        seconds = elapsed % 60
        return "Timer elapsed: %02d:%02d:%02d" % (hours, minutes, seconds)


    @classmethod
    def option_completer(cls, k,v):
        return ['start']

    @line_magic
    def timer(self, line=''):
        """
        Timer magic to print initial date/time information and
        subsequent elapsed time intervals.

        To start the timer, run:

        %timer start

        This will print the start date and time.

        Subsequent calls to %timer will print the elapsed time
        relative to the time when %timer start was called. Subsequent
        calls to %timer start may also be used to reset the timer.
        """

        if line.strip() not in ['', 'start']:
            print("Invalid argument to %timer. For more information consult %timer?")
            return
        elif line.strip() == 'start':
            TimerMagic.start_time = time.time()
            timestamp = time.strftime("%Y/%m/%d %H:%M:%S")
            print("Timer start: %s" % timestamp)
            return
        elif self.start_time is None:
            print("Please start timer with %timer start. For more information consult %timer?")
        else:
            print(self.elapsed_time())



#===============#
# Display hooks #
#===============#

from topo.base.sheetview import CFView

from holoviews.core.options import Store
from holoviews.ipython import load_ipython_extension as load_imagen_extension
from holoviews.ipython.display_hooks import map_display, view_display
from holoviews.plotting import MatrixPlot

from holoviews.ipython.widgets import RunProgress
RunProgress.run_hook = topo.sim.run

Store.defaults.update({CFView: MatrixPlot})

try:
    from lancet import ViewFrame
    ViewFrame.display_fns.append(map_display)
    ViewFrame.display_fns.append(view_display)
except:
    pass




_loaded = False
def load_ipython_extension(ip):
    load_imagen_extension(ip, verbose=False)

    global _loaded
    if not _loaded:
        _loaded = True
        ip.register_magics(ExportMagic)
        ip.register_magics(TimerMagic)
        ip.set_hook('complete_command', TimerMagic.option_completer, str_key = '%timer')


        try:
            from lancet import load_ipython_extension as load_lancet_extension
            load_lancet_extension(ip)
        except:
            pass
        from topo.command import runscript
        runscript.ns = ip.user_ns
        runscript.push = ip.push

        from topo.misc.commandline import exec_startup_files
        exec_startup_files()
