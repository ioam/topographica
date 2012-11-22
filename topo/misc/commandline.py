"""
Support functions for parsing command-line arguments and providing
the Topographica command prompt.  Typically called from the
'./topographica' script, but can be called directly if using
Topographica files within a separate Python.

$Id$
"""


from optparse import OptionParser

import sys, __main__, math, os, re

import topo
import param
from param.parameterized import Parameterized
from topo.base.simulation import OptionalSingleton


try:
    # By default, use a non-GUI backend for matplotlib.
    from matplotlib import rcParams
    rcParams['backend']='Agg'
    matplotlib_imported=True
except ImportError:
    matplotlib_imported=False


ipython_shell_interface = None
ipython_prompt_interface = None
try:
    from IPython.frontend.terminal.embed import InteractiveShellEmbed as IPShell
    from IPython.config.loader import Config
    ipython_shell_interface = "InteractiveShellEmbed"
    try:
        from IPython.core.prompts import PromptManager  # pyflakes:ignore (try/except import)
        ipython_prompt_interface = "PromptManager"
    except ImportError:
        pass
except ImportError:
    try:
        # older version?
        from IPython.Shell import IPShell  # pyflakes:ignore (try/except import)
        ipython_shell_interface = "IPython.Shell"
    except ImportError:
        print "Note: IPython is not available; using basic interactive Python prompt instead."



# Startup banner
BANNER = """
Welcome to Topographica!

Type help() for interactive help with python, help(topo) for general
information about Topographica, help(commandname) for info on a
specific command, or topo.about() for info on this release, including
licensing information.
"""


class GlobalParams(Parameterized,OptionalSingleton):
    """
    A Parameterized class providing script-level parameters.
    
    Script-level parameters can be set from the commandline by passing
    via -p, e.g. ./topographica -p retina_density=10

    Within scripts, parameters can be declared by using the add()
    method.


    Example usage in a script:

    from topo.misc.commandline import global_params as p
    p.add(
        retina_density=param.Number(default=24.0,bounds=(0,None),
        inclusive_bounds=(False,True),doc=\"""
        The nominal_density to use for the retina.\"""))
    ...
    topo.sim['Retina']=sheet.GeneratorSheet(
        nominal_density=p.retina_density)


    Further information:

    'context' is usually set to __main__.__dict__ and is used to find
    the value of a parameter as it is add()ed to this object
    (i.e. add() has access to values set via the commandline or in
    scripts).

    Values set via set_in_context() or exec_in_context() (used by -p)
    are tracked: warnings are issued for overwritten values, and
    unused values can be warned about via check_for_unused_names().

    The context is not saved in snapshots, but parameter values are
    saved.
    """
    context = None

    def __new__(cls,*args,**kw):
        return OptionalSingleton.__new__(cls,True)

    def __init__(self,context=None,**params):
        self.context = context or {}
        self.unused_names = set()
        params['name']="global_params"
        super(GlobalParams,self).__init__(**params)

    def __getstate__(self):
        # context is neither saved nor restored
        # (in our current usage, the context of the GlobalParams
        # instance will be set to __main__.__dict__ on startup).
        state = super(GlobalParams,self).__getstate__()
        del state['context']
        return state

    def set_in_context(self,**params):
        """
        Set in self.context all name=val pairs specified in **params,
        tracking new names and warning of any replacements.
        """
        for name,val in params.items():
            if name in self.context:
                self.warning("Replacing previous value of '%s' with '%s'"%(name,val))
            self.context[name]=val
            self.unused_names.add(name)
            
    def exec_in_context(self,arg):
        """
        exec arg in self.context, tracking new names and
        warning of any replacements.
        """
        ## contains elaborate scheme to detect what is specified by
        ## -s, and to warn about any replacement
        current_ids = dict([(k,id(v)) for k,v in self.context.items()])

        exec arg in self.context

        for k,v in self.context.items():
            if k in self.unused_names and id(v)!=current_ids[k]:
                self.warning("Replacing previous value of '%s' with '%s'"%(k,v))

        new_names = set(self.context.keys()).difference(set(current_ids.keys()))
        for k in new_names:
            self.unused_names.add(k)
        
    def check_for_unused_names(self):
        """Warn about any unused names."""
        for s in self.unused_names:
            self.warning("'%s' is unused."%s)

# warns for param that specified with -c (but also if name gets defined in __main__,
# e.g. by default_density=global_params.default_density in a script file
##         for name in self.params():
##             if name in self.context:
##                 self.warning("'%s' still exists in global_params.context"%name)

        # detect duplicate param value that wasn't used (e.g. specified with after script)
        for name,val in self.params().items():
            if name in self.context:
                if self.context[name]!=self.inspect_value(name):
                    self.warning("'%s=%s' is unused."%(name,self.context[name]))
            
    
    def add(self,**kw):
        """
        For each parameter_name=parameter_object specified in kw:
        * adds the parameter_object to this object's class
        * if there is an entry in context that has the same name as the parameter,
          sets the value of the parameter in this object to that value, and then removes
          the name from context
        """        
        for p_name,p_obj in kw.items():
            self._add_parameter(p_name,p_obj)
            if p_name in self.context:
                setattr(self,p_name,self.context[p_name])
                if p_name in self.unused_names:
                    # i.e. remove from __main__ if it was a -p option (but not if -c)
                    del self.context[p_name]  
                    self.unused_names.remove(p_name)
                

global_params=GlobalParams(context=__main__.__dict__)



##### Command-prompt formatting
#    
class IPCommandPromptHandler(object):
    """
    Allows control over IPython's dynamic command prompts.
    """
    _format = ''
    _prompt = ''

    @classmethod
    def set_format(cls,format):
        """
        Set IPython's prompt template to format.
        """
        import __main__
        IP = __main__.__dict__['__IP']
        prompt = getattr(IP.outputcache,cls._prompt)
        prompt.p_template = format
        prompt.set_p_str()        
        cls._format = format

    @classmethod
    def get_format(cls):
        """
        Return the current template.
        """
        return cls._format

    
class CommandPrompt(IPCommandPromptHandler):
    """
    Control over input prompt.

    Several predefined formats are provided, and any of these (or any
    arbitrary string) can be used by calling set_format() with their
    values.

    See the IPython manual for details:
    http://ipython.scipy.org/doc/manual/html/config/index.html

    Examples:
      # Use one of the predefined formats:
      CommandPrompt.set_format(CommandPrompt.basic_format)
      # Just print the command number:
      CommandPrompt.set_format('\# ')
      # Print the command number but don't use color:
      CommandPrompt.set_format('\N ')
      # Print the value of my_var at each prompt:
      CommandPrompt.set_format('{my_var}>>> ')
    """
    _prompt = 'prompt1'
    
    # Predefined alternatives
    basic_format   = 'Topographica>>> '
    if ipython_prompt_interface == "PromptManager":
        simtime_format = 'topo_t{topo.sim.timestr_prop}>>> '
        simtimecmd_format = 'topo_t{topo.sim.timestr_prop}_c\\#>>> '
    else:
        simtime_format = 'topo_t${topo.sim.timestr()}>>> '
        simtimecmd_format = 'topo_t${topo.sim.timestr()}_c\\#>>> '
    
    _format = simtimecmd_format


class CommandPrompt2(IPCommandPromptHandler):
    """
    Control over continuation prompt.

    (See CommandPrompt.)
    """
    _prompt = 'prompt2'
    basic_format = '   .\\D.: '
    _format = basic_format


class OutputPrompt(IPCommandPromptHandler):
    """
    Control over output prompt.

    (See CommandPrompt.)
    """
    _prompt = 'prompt_out'
    basic_format = 'Out[\#]:'
    _format = basic_format

#####



# Use to define global constants
global_constants = {'pi':math.pi}

# Create the topographica parser.
usage = "usage: topographica ([<option>]:[<filename>])*\n\
where any combination of options and Python script filenames will be\n\
processed in order left to right."
topo_parser = OptionParser(usage=usage)


def sim_name_from_filename(filename):
    """
    Set the simulation title from the given filename, if none has been
    set already.
    """
    if topo.sim.name is None:
        topo.sim.name=re.sub('.ty$','',os.path.basename(filename))


def boolean_option_action(option,opt_str,value,parser):
    """Callback function for boolean-valued options that apply to the entire run.""" 
    #print "Processing %s" % (opt_str)
    setattr(parser.values,option.dest,True)


def interactive():
    os.environ['PYTHONINSPECT']='1'

# CB: note that topographica should stay open if an error occurs
# anywhere after a -i (i.e. in a -c command or script)
def i_action(option,opt_str,value,parser):
    """Callback function for the -i option."""
    boolean_option_action(option,opt_str,value,parser)
    interactive()
    
topo_parser.add_option("-i","--interactive",action="callback",callback=i_action,
                       dest="interactive",default=False,
                       help="provide an interactive prompt even if stdin does not appear to be a terminal.")


def v_action(option,opt_str,value,parser):
    """Callback function for the -v option."""
    import param.parameterized
    param.parameterized.min_print_level=param.parameterized.VERBOSE
    print "Enabling verbose message output."
    
topo_parser.add_option("-v","--verbose",action="callback",callback=v_action,dest="verbose",default=False,help="""\
enable verbose messaging output.""")


def d_action(option,opt_str,value,parser):
    """Callback function for the -d option."""
    import param.parameterized
    param.parameterized.min_print_level=param.parameterized.DEBUG
    print "Enabling debugging message output."
    
topo_parser.add_option("-d","--debug",action="callback",callback=d_action,dest="debug",default=False,help="""\
enable debugging message output (implies --verbose).""")



def l_action(option,opt_str,value,parser):
    """Callback function for the -l option."""
    boolean_option_action(option,opt_str,value,parser)
    from topo.misc.legacy import install_legacy_support
    print "Enabling legacy support."
    install_legacy_support()
    
topo_parser.add_option("-l","--legacy",action="callback",callback=l_action,dest="legacy",default=False,help="""\
launch Topographica with legacy support enabled.""")


def gui(start=True):
    """Start the GUI as if -g were supplied in the command used to launch Topographica."""
    if matplotlib_imported: 
        rcParams['backend']='TkAgg'
    auto_import_commands()
    if start:
        import topo.tkgui
        topo.tkgui.start()


# Topographica stays open if an error occurs after -g
# (see comment by i_action)
def g_action(option,opt_str,value,parser):
    """Callback function for the -g option."""
    boolean_option_action(option,opt_str,value,parser)
    interactive()
    gui()


topo_parser.add_option("-g","--gui",action="callback",callback=g_action,dest="gui",default=False,help="""\
launch an interactive graphical user interface; \
equivalent to -c 'from topo.misc.commandline import gui ; gui()'. \
Implies -a.""")

topo_parser.add_option("--pdb",action="store_true",dest="pdb",help="""\
Automatically call the pdb debugger after every uncaught \
exception. See IPython documentation for further details.""")

# Keeps track of whether something has been performed, when deciding whether to assume -i
something_executed=False

def c_action(option,opt_str,value,parser):
    """Callback function for the -c option."""
    #print "Processing %s '%s'" % (opt_str,value)
    exec value in __main__.__dict__
    global something_executed
    something_executed=True
    openmp_settings_names = ['openmp_threads', 'openmp_min_threads', 'openmp_max_threads']
    openmp_present = [(k in __main__.__dict__) for k in openmp_settings_names]
    if openmp_present and parser.values.gui: 
        print "\nWARNING: For OpenMP settings to be used properly they need to be specified after the -g flag."
    
topo_parser.add_option("-c","--command",action = "callback",callback=c_action,type="string",
		       default=[],dest="commands",metavar="\"<command>\"",
		       help="string of arbitrary Python code to be executed in the main namespace.")



def p_action(option,opt_str,value,parser):
    """Callback function for the -p option."""
    global_params.exec_in_context(value)
    global something_executed
    something_executed=True
            
topo_parser.add_option("-p","--set-parameter",action = "callback",callback=p_action,type="string",
		       default=[],dest="commands",metavar="\"<command>\"",
		       help="command specifying value(s) of script-level (global) Parameter(s).")


def auto_import_commands():
    """Import the contents of all files in the topo/command/ directory."""
    import re,os
    import topo
    import __main__

    # CEBALERT: this kind of thing (topo.__file__) won't work with
    # py2exe and similar tools
    topo_path = os.path.join(os.path.split(topo.__file__)[0],"command")
    for f in os.listdir(topo_path):
        if re.match('^[^_.].*\.py$',f):
            modulename = re.sub('\.py$','',f)
            exec "from topo.command."+modulename+" import *" in __main__.__dict__
    exec "from topo.command import *" in __main__.__dict__
    
def a_action(option,opt_str,value,parser):
    """Callback function for the -a option."""
    auto_import_commands()
    
topo_parser.add_option("-a","--auto-import-commands",action="callback",callback=a_action,help="""\
import everything from commands/*.py into the main namespace, for convenience; \
equivalent to -c 'from topo.misc.commandline import auto_import_commands ; auto_import_commands()'.""")



def exec_startup_files():
    """
    Execute startup files.

    Linux/UNIX/OS X: ~/.topographicarc
    Windows: %USERPROFILE%\topographica.ini
    """
    # From Bilal: On OS X, ~/Library/Preferences/ is the standard path
    # for user-defined params. The filename format (corresponding to
    # .ini on windows) is org.topographica.plist, where a plist is an
    # XML file. But, many shell-based programs follow the Unix
    # convention, so we should be fine doing that.

    # Linux/UNIX/OS X:
    rcpath = os.path.join(os.path.expanduser("~"),'.topographicarc')
    # Windows (ini is convention, and can be double clicked to edit):
    inipath = os.path.join(os.path.expandvars("$USERPROFILE"),'topographica.ini')

    for startup_file in (rcpath,inipath):
        if os.path.exists(startup_file):
            print "Executing user startup file %s" % (startup_file)
            execfile(startup_file,__main__.__dict__)
    
    #####
    # CEBALERT: locations we used to use on Windows and OS X. Should
    # remove after 0.9.8.
    # application data on windows
    inipath = os.path.join(os.path.expandvars("$APPDATA"),'Topographica','topographica.ini')
    # application support on OS X  
    configpath = os.path.join(os.path.expanduser("~"),"Library","Application Support",'Topographica','topographica.config')
    for startup_file in (configpath,inipath):
        if os.path.exists(startup_file):
            param.Parameterized().warning("Ignoring %s; location for startup file is %s (UNIX/Linux/Mac OS X) or %s (Windows)."%(startup_file,rcpath,inipath)) 
    #####


def get_omp_num_threads(openmp_threads, openmp_min_threads, openmp_max_threads):
    """ Helper function to implement sensible OpenMP behaviour where
        possible.  Returns a integer tuple (OpenMP threads, CPUs detected).

        CPUs detected may be None if multiprocessing is not available (ie
        Python 2.5) and consequently OpenMP threads may be None if the user
        gave a relative thread specification (ie openmp_threads <= 0). When
        OpenMP threads is None, the default OpenMP behaviour of using all
        available cores is used.
        """

    if 'OMP_NUM_THREADS' in os.environ: return (None, None)

    if 'NSLOTS' in os.environ: return ('NSLOTS', None)

    try:
        import multiprocessing
        total_cores = multiprocessing.cpu_count()
        if total_cores == 1: return (1, 1)
        if total_cores == 2: return (2, 2)
    except:
        print "Cannot import multiprocessing to determine number of cores."
        total_cores = None

    if total_cores and (-openmp_threads >= (total_cores-1)):
        print "OpenMP: Topographica needs a positive number of threads to execute!"
        return (1, total_cores)

    if (openmp_threads <= 0) and total_cores:      openmp_threads = total_cores + openmp_threads
    if (openmp_threads <= 0) and not total_cores:  return (None, total_cores)

    if (total_cores is not None) and (openmp_threads > total_cores):
        print "OpenMP: More threads specified than cores detected."; return (total_cores, total_cores)

    if openmp_threads < openmp_min_threads:
        print "OpenMP: Using minimum number of allowed threads."
        openmp_threads = openmp_min_threads

    if (openmp_max_threads is None): return (openmp_threads, total_cores)

    elif (openmp_max_threads < openmp_min_threads):
        print"OpenMP: Maximum allowed threads lower than minimum allowed threads. Ignoring maximum limit."
        return (openmp_threads, total_cores)
    elif (openmp_threads > openmp_max_threads):
        print "OpenMP: Using maximum number of allowed threads."
        return (openmp_max_threads, total_cores)
    else:
        return (openmp_threads, total_cores)


### Execute what is specified by the options.

def process_argv(argv):
    """
    Process command-line arguments (minus argv[0]!), rearrange and execute.
    """
    # Initial preparation
    import __main__
    for (k,v) in global_constants.items():
        exec '%s = %s' % (k,v) in __main__.__dict__

    exec_startup_files()

    # Repeatedly process options, if any, followed by filenames, if any, until nothing is left
    topo_parser.disable_interspersed_args()
    args=argv
    option=None
    global something_executed
    while True:
        # Process options up until the first filename
        (option,args) = topo_parser.parse_args(args,option)

        # Handle filename
        if args:
            filename=args.pop(0)
            #print "Executing %s" % (filename)
            filedir = os.path.dirname(os.path.abspath(filename))
            sys.path.insert(0,filedir) # Allow imports relative to this file's path
            sim_name_from_filename(filename) # Default value of topo.sim.name

            execfile(filename,__main__.__dict__)
            something_executed=True

        if not args:
            break

    global_params.check_for_unused_names()

    # OpenMP settings and defaults
    openmp_threads = __main__.__dict__.get('openmp_threads')
    if (openmp_threads is None): openmp_threads=-1

    openmp_min_threads = __main__.__dict__.get('openmp_min_threads')
    if (openmp_min_threads is None): openmp_min_threads=2

    openmp_max_threads = __main__.__dict__.get('openmp_max_threads')

    if (openmp_threads != 1): # OpenMP is disabled if openmp_threads == 1

        (num_threads, total_cores) = get_omp_num_threads(openmp_threads,
                                                         openmp_min_threads,
                                                         openmp_max_threads)

        if num_threads is None:
            print "OpenMP: Using OMP_NUM_THREADS environment variable if set. Otherwise, all cores in use."
        elif num_threads == 'NSLOTS':
            os.environ['OMP_NUM_THREADS'] =  os.environ['NSLOTS']
            print "NSLOTS environment variable found; overriding any other thread settings and using N=%s threads" % os.environ['NSLOTS']

        elif total_cores is None:
            print "OpenMP: Using %d threads" % num_threads
            os.environ['OMP_NUM_THREADS'] =  str(num_threads)
        else:
            print "OpenMP: Using %d threads on a machine with %d detected CPUs" % (num_threads, total_cores)
            os.environ['OMP_NUM_THREADS'] =  str(num_threads)

    # If no scripts and no commands were given, pretend -i was given.
    if not something_executed: interactive()

    if option.gui: topo.guimain.title(topo.sim.name)

    ## INTERACTIVE SESSION BEGINS HERE (i.e. can't have anything but
    ## some kind of cleanup code afterwards)
    if os.environ.get('PYTHONINSPECT'):
        print "Output path: %s" % param.normalize_path.prefix
        print BANNER    
        # CBALERT: should probably allow a way for users to pass
        # things to IPython? Or at least set up some kind of
        # topographica ipython config file. Right now, a topo_parser
        # option has to be added for every ipython option we want to
        # support (e.g. see --pdb)

        if ipython_shell_interface == "IPython.Shell":
            # IPython 0.10 and earlier

            # Stop IPython namespace hack?
            # http://www.nabble.com/__main__-vs-__main__-td14606612.html
            __main__.__name__="__mynamespace__"

            ipython_args = ['-noconfirm_exit','-nobanner',
                            '-pi1',CommandPrompt.get_format(),
                            '-pi2',CommandPrompt2.get_format(),
                            '-po',OutputPrompt.get_format()]
            if option.pdb:
                ipython_args.append('-pdb')

            ipshell = IPShell(ipython_args,user_ns=__main__.__dict__)
            ipshell.mainloop(sys_exit=1)

        elif ipython_shell_interface == "InteractiveShellEmbed":
            # IPython 0.11 and later

            config = Config()

            if ipython_prompt_interface == "PromptManager":
                config.PromptManager.in_template = CommandPrompt.get_format()
                config.PromptManager.in2_template = CommandPrompt2.get_format()
                config.PromptManager.out_template = OutputPrompt.get_format()
            else:
                config.InteractiveShell.prompt_in1 = CommandPrompt.get_format()
                config.InteractiveShell.prompt_in2 = CommandPrompt2.get_format()
                config.InteractiveShell.prompt_out = OutputPrompt.get_format()
            config.InteractiveShell.confirm_exit = False
            ipshell = IPShell(config=config,user_ns=__main__.__dict__,
                              banner1="",exit_msg="")
            if option.pdb:
                ipshell.call_pdb = True
            ipshell()
            sys.exit()
