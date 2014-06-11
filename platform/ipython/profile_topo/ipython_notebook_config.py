# Stripped down configuration file for ipython-notebook in Topographica.

c = get_config()

#------------------------------------------------------------------------------
# NotebookApp configuration
#------------------------------------------------------------------------------

# NotebookApp will inherit config from: BaseIPythonApplication, Application

# The IP address the notebook server will listen on.
# c.NotebookApp.ip = '127.0.0.1'

# The base URL for the notebook server
# c.NotebookApp.base_project_url = '/'

# The port the notebook server will listen on.
# c.NotebookApp.port = 8888

# Whether to prevent editing/execution of notebooks.
# c.NotebookApp.read_only = False

# Whether to open in a browser after starting. The specific browser used is
# platform dependent and determined by the python standard library `webbrowser`
# module, unless it is overridden using the --browser (NotebookApp.browser)
# configuration option.
c.NotebookApp.open_browser = False

# The full path to an SSL/TLS certificate file.
# c.NotebookApp.certfile = u''

# Hashed password to use for web authentication.
# 
# To generate, type in a python/IPython shell:
# 
#   from IPython.lib import passwd; passwd()
# 
# The string should be of the form type:salt:hashed-password.
# c.NotebookApp.password = u''

# The full path to a private key file for usage with SSL/TLS.
# c.NotebookApp.keyfile = u''


#------------------------------------------------------------------------------
# IPKernelApp configuration
#------------------------------------------------------------------------------

# IPython: an enhanced interactive Python shell.

# IPKernelApp will inherit config from: KernelApp, BaseIPythonApplication,
# Application, InteractiveShellApp

# Execute the given command string.
# c.IPKernelApp.code_to_run = ''

# lines of code to run at IPython startup.
# c.IPKernelApp.exec_lines = []

# A file to be run
# c.IPKernelApp.file_to_run = ''

# List of files to run at IPython startup.
# c.IPKernelApp.exec_files = []

# dotted module name of an IPython extension to load.
c.IPKernelApp.extra_extension = 'topo.misc.ipython'

#------------------------------------------------------------------------------
# InlineBackend configuration
#------------------------------------------------------------------------------

# An object to store configuration of the inline backend.

# The image format for figures with the inline backend.
# c.InlineBackend.figure_format = 'png'

# Close all figures at the end of each cell.
# 
# When True, ensures that each cell starts with no active figures, but it also
# means that one must keep track of references in order to edit or redraw
# figures in subsequent cells. This mode is ideal for the notebook, where
# residual plots from other cells might be surprising.
# 
# When False, one must call figure() to create new figures. This means that
# gcf() and getfigs() can reference figures created in other cells, and the
# active figure can continue to be edited with pylab/pyplot methods that
# reference the current active figure. This mode facilitates iterative editing
# of figures, and behaves most consistently with other matplotlib backends, but
# figure barriers between cells must be explicit.
# c.InlineBackend.close_figures = True

# Subset of matplotlib rcParams that should be different for the inline backend.
# c.InlineBackend.rc = {'font.size': 10, 'savefig.dpi': 72, 'figure.figsize': (6.0, 4.0), 'figure.subplot.bottom': 0.125}

#------------------------------------------------------------------------------
# MappingKernelManager configuration
#------------------------------------------------------------------------------

# A KernelManager that handles notebok mapping and HTTP error handling

# MappingKernelManager will inherit config from: MultiKernelManager

# The max raw message size accepted from the browser over a WebSocket
# connection.
# c.MappingKernelManager.max_msg_size = 65536

# Kernel heartbeat interval in seconds.
# c.MappingKernelManager.time_to_dead = 3.0

# Delay (in seconds) before sending first heartbeat.
# c.MappingKernelManager.first_beat = 5.0

#------------------------------------------------------------------------------
# NotebookManager configuration
#------------------------------------------------------------------------------

# Automatically create a Python script when saving the notebook.
# 
# For easier use of import, %run and %load across notebooks, a <notebook-
# name>.py script will be created next to any <notebook-name>.ipynb on each
# save.  This can also be set with the short `--script` flag.
# c.NotebookManager.save_script = False
