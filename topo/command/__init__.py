"""
A family of high-level user commands acting on the entire simulation.

Any new commands added to this directory will automatically become
available for any program.

Commands here should be 'bullet-proof' and work 'from scratch'.
That is, they should print warnings if required but should not raise
errors that would interrupt e.g. a long batch run of simulation work,
no matter what the context from which they are called.
"""

import cPickle as pickle
import sys
import os
import re
import string
import time
import platform
import tarfile, zipfile

import __main__

# gzip module might not have been built (if zlib could not be found when building)
try:
    import gzip
except ImportError:
    pass

import param
from param.parameterized import ParameterizedFunction, ParamOverrides
from param import normalize_path

import imagen, numbergen
from collections import OrderedDict

import topo
from topo.base.sheet import Sheet
from topo.base.projection import ProjectionSheet
from topo.sheet import GeneratorSheet
from topo.misc.util import MultiFile
from topo.misc.picklemain import PickleMain
from topo.misc.snapshots import PicklableClassAttributes
from topo.misc.genexamples import generate as _generate

from featuremapper import PatternDrivenAnalysis



def generate_example(target):
    """
    Generate the saved network target, as defined in
    topo.misc.genexamples.
    """
    _generate(targets=[target])


# Not sure where to put CommandMetaclass, since it doesn't need to be
# seen or used by anyone. Probably also the import error classes
# shouldn't be so visible.
from param.parameterized import ParameterizedMetaclass
class CommandMetaclass(ParameterizedMetaclass):
    """
    A class having this as a metaclass will have its __call__() method
    automatically wrapped so that any exception occurring inside
    __call__() will be passed to the class's _except() method.
    """
    def __new__(mcs,classname,bases,classdict):
        if '__call__' in classdict:
            classdict['__call__'] = mcs._safecall(classdict['__call__'])
            #assert '_except' in classdic
        # else it is probably abstract, or something
        return ParameterizedMetaclass.__new__(mcs,classname,bases,classdict)

    @classmethod
    def _safecall(mcs,fn):
        """
        Wrap fn with caller, which catches any exception raised inside
        fn() and passes it to _except().
        """
        def caller(self,*args,**kw):
            try:
                return fn(self,*args,**kw)
            except Exception, e:
                # Mis-invoked call should raise error as normal.
                if isinstance(e,TypeError):
                    import inspect
                    # Is this a hack to detect mis-calling?
                    if len(inspect.getargspec(fn)[0])!=len(args):
                        raise
                try:
                    return self._except(e)
                except:
                    # the _except() method raises an error (or doesn't
                    # exist). what should happen? programming error,
                    # so I guess just re-raise
                    raise
        return caller



class Command(ParameterizedFunction):
    """
    Parameterized command: any error when the command is run (called)
    will not raise an exception, but will instead generate a warning.
    """
    __metaclass__ = CommandMetaclass
    __abstract = True

    def _except(self,e):
        # import traceback
        # print traceback.print_exc()
        self.warning("%s failed: %s"%(self,e)) # or traceback.format_exc()))

    def __call__(self,*args,**params):
        return super(Command,self).__call__(*args,**params)


class ImportErrorObject(object):
    """
    Raises an ImportError on any attempt to access an attribute, call,
    or get an item.

    Useful to delay an ImportError until the point of use, thus
    allowing e.g. a class attribute to contain something from a
    non-core external module (e.g. pylab).

    Delaying an ImportError until the point of use allows users to be
    informed of the possibility of having various extra functions on
    installation of a missing package.
    """
    __dict__ = {}
    def __init__(self,module_name):
        self.__dict__['_ImportErrorObject__module_name'] = module_name
    def _raise(self):
        #param.Parameterized().warning("err:%s"%self.module_name)
        raise ImportError, "No module named %s. Install %s to get this functionality."%(self.__module_name,self.__module_name)
        return None
    def __call__(self,*args,**kw):
        self._raise()
    # Might be better to override __getattribute__, special casing the
    # module_name attribute. Then everything is guaranteed to raise an
    # error (rather than covering call, getitem, getattr, and maybe
    # other things I've forgotten about).
    def __getattr__(self,name):
        if name in self.__dict__:
            return self.__dict__[name]
        return self._raise()
    def __getitem__(self,i):
        self._raise()



class ImportErrorRaisingFakeModule(object):
    """
    Returns an ImportErrorObject for any attribute request.

    Instances of this class can be used in place of a module to delay
    an import error until the point of use of an attribute of that
    module.

    See ImportErrorObject for more details.
    """
    def __init__(self,module_name):
        self.__module_name = module_name
    def __getattr__(self,name):
        return ImportErrorObject(self.__module_name)


# CEBALERT: commands in here should inherit from Command, and make use
# of _except() to ensure all necessary state is reverted.

def save_input_generators():
    """Save a copy of the active_sim's current input_generators for all GeneratorSheets."""
    # ensure EPs get started (if save_input_generators is called before the simulation is run())
    topo.sim.run(0.0)

    generator_sheets = topo.sim.objects(GeneratorSheet).values()
    for sheet in generator_sheets:
        sheet.push_input_generator()


def restore_input_generators():
    """Restore previously saved input_generators for all of topo.sim's GeneratorSheets."""
    generator_sheets = topo.sim.objects(GeneratorSheet).values()
    for sheet in generator_sheets:
        sheet.pop_input_generator()


def clear_event_queue():
    """Remove pending events from the simulator's event queue."""
    topo.sim.event_clear()


class runscript(param.ParameterizedFunction):
    """
    Runs a script that has been parameterized with script parameters.
    For example, runscript('tiny.ty', cortex_density=10) will execute
    the 'tiny.ty' script in the currently active namespace.
    """

    ns = param.Parameter(default={}, pickle_default_value=False, doc="""
        The namespace in which the script is to be executed.""")

    push = param.Callable(pickle_default_value=False, doc="""
        Hook to push the updated namespace for handling more
        complicated namespaces, such as IPython Notebook.""")

    load = param.Boolean(default=True, doc="""
       Whether to automatically load class based models when called.
       Useful for compatibility with older ty script definition files.""")

    def __call__(self, source_file, ns={}, **kwargs):

        from topo.misc.commandline import global_params
        ns = ns if ns else self.ns
        for (key, val) in kwargs.items():
            global_params.exec_in_context('%s=%s' % (key,val))

        source_path = param.resolve_path(source_file)
        code = compile(open(source_path, 'r').read(), "<execution>", "exec")
        exec code in ns #globals and locals
        self.push(ns)
        if self.load:
            topo.sim(verbose=kwargs.get('verbose', False))

# This class is left around to support older snapshots: All snapshots
# since 0.9.7 up until r11545 (addition of UnpickleEnvironmentCreator)
# have a pickled instance of this class. We maintain the same behavior
# as before for them: install all legacy support.
class _VersionPrinter(object):
    def __setstate__(self,state):
        import topo.misc.legacy as L
        L.SnapshotSupport.install("0.9.7")


class UnpickleEnvironmentCreator(object):
    """When unpickled, installs any necessary legacy support."""
    def __init__(self,release,version):
        self.release = release
        self.version = version
    def __getstate__(self):
        return {'release':self.release,
                'version':self.version}
    def __setstate__(self,state):
        self.release = state['release']
        self.version = state['version']
        import topo.misc.legacy as L
        L.SnapshotSupport.install(self.release,self.version)


def save_snapshot(snapshot_name=None):
    """
    Save a snapshot of the network's current state.

    The snapshot is saved as a gzip-compressed Python binary pickle.

    As this function uses Python's 'pickle' module, it is subject to
    the same limitations (see the pickle module's documentation) -
    with the notable exception of class attributes. Python does not
    pickle class attributes, but this function stores class attributes
    of any Parameterized class that is declared within the topo
    package. See the param.parameterized.PicklableClassAttributes
    class for more information.
    """
    if not snapshot_name:
        snapshot_name = topo.sim.basename() + ".typ"

    # For now we just search topo, but could do same for other packages.

    # CEBALERT: shouldn't it be topo and param? I guess we already get
    # many classes defined in param because they are imported into
    # topo at some point anyway.
    topoPOclassattrs = PicklableClassAttributes(topo,exclusions=('plotting','tests','tkgui'),
                                                startup_commands=topo.sim.startup_commands)

    paramPOclassattrs = PicklableClassAttributes(param)
    imagenPOclassattrs = PicklableClassAttributes(imagen)
    numbergenPOclassattrs = PicklableClassAttributes(numbergen)


    from topo.misc.commandline import global_params

    topo.sim.RELEASE=topo.release
    topo.sim.VERSION=topo.version

    to_save = (UnpickleEnvironmentCreator(topo.release,topo.version),
               PickleMain(),
               global_params,
               topoPOclassattrs,
               paramPOclassattrs,
               imagenPOclassattrs,
               numbergenPOclassattrs,
               topo.sim)

    try:
        snapshot_file=gzip.open(normalize_path(snapshot_name),'wb',compresslevel=5)
    except NameError:
        snapshot_file=open(normalize_path(snapshot_name),'wb')

    pickle.dump(to_save,snapshot_file,2)


    snapshot_file.close()


def load_snapshot(snapshot_name):
    """
    Load the simulation stored in snapshot_name.
    """
    # unpickling the PicklableClassAttributes() executes startup_commands and
    # sets PO class parameters.

    snapshot_name = param.resolve_path(snapshot_name)

    # If it's not gzipped, open as a normal file.
    try:
        snapshot = gzip.open(snapshot_name,'r')
        snapshot.read(1)
        snapshot.seek(0)
    except (IOError,NameError):
        snapshot = open(snapshot_name,'r')

    try:
        pickle.load(snapshot)
    except ImportError:
        # CEBALERT: Support snapshots where the unpickling support
        # (UnpickleEnvironmentCreator) cannot be found because the
        # support itself was moved from topo.command.basic to
        # topo.command.__init__! Was it a bad idea to have the support
        # code loaded via an object?
        sys.modules['topo.command.basic'] = topo.command
        # Could instead set find_global on cPickle.Unpickler (could
        # support all import changes that way, as alternative to what
        # we currently do), but I'm reluctant to mess with cPickle's
        # default way of finding things. (Also it would be specific to
        # cPickle; would be different for pickle.)

        snapshot.seek(0)
        try:
            pickle.load(snapshot)
        except:
            import traceback

            m = """
            Snapshot could not be loaded.

            Please file a support request via topographica.org.

Loading error:
%s
            """%traceback.format_exc()

            param.Parameterized(name="load_snapshot").warning(m)


    snapshot.close()

    # Restore subplotting prefs without worrying if there is a
    # problem (e.g. if topo/analysis/ is not present)
    try:
        from topo.plotting.plotgroup import Subplotting
        Subplotting.restore_subplots()
    except:
        p = param.Parameterized(name="load_snapshot")
        p.message("Unable to restore Subplotting settings")

    # Temporary -- broadcast topo.sim.time to all subpackages
    param.Dynamic.time_fn = topo.sim.time
    numbergen.TimeAware.time_fn = topo.sim.time
    imagen.Translator.time_fn = topo.sim.time
    imagen.Sweeper.time_fn = topo.sim.time
    imagen.Animation.time_fn = topo.sim.time
    # Another hack - this attribute should be unpickling correctly!
    topo.sim._instantiated_model = True




def save_script_repr(script_name=None):
    """
    Save the current simulation as a Topographica script.

    Generates a script that, if run, would generate a simulation with
    the same architecture as the one currently in memory.  This can be
    useful when defining networks in place, so that the same general
    configuration can be recreated later.  It also helps when
    comparing two similar networks generated with different scripts,
    so that the corresponding items can be matched rigorously.

    Note that the result of this operation is usually just a starting
    point for further editing, because it will not usually be runnable
    as-is (for instance, some parameters may not have runnable
    representations).  Even so, this is usually a good start.
    """
    if not script_name:
        script_name = topo.sim.basename() + "_script_repr.ty"

    header = ("# Generated by Topographica %s on %s\n\n" %
              (topo.release,time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())))
    script = header+topo.sim.script_repr()

    script_file = open(normalize_path(script_name),'w')
    script_file.write(script)


# Location of the version-controlled topographica directory (i.e. path
# of topo/ but up a level). Could be None. Nothing should assume that
# there is a version control system available.
try:
    vc_topographica_dir = os.path.split(os.path.split(topo.__file__)[0])[0]
except:
    vc_topographica_dir = None


# decorator that changes to vc_topographica_dir for duration of fn,
# if there is such a directory. Otherwise, doesn't change directory.
def in_vc_topographica_dir(fn):
    import os
    def temporarily_change_to_vc_topographica_dir(*args,**kw):
        orig_path = os.getcwd()
        if vc_topographica_dir is not None:
            os.chdir(vc_topographica_dir)
        try:
            result = fn(*args,**kw)
        finally:
            # ensure dir put back even if there's an error calling fn
            if os.getcwd()!=orig_path:
                os.chdir(orig_path)
        return result
    return temporarily_change_to_vc_topographica_dir


@in_vc_topographica_dir
def _get_vc_commands():
    # return name of version control system (None if no vc could be
    # detected)
    import os.path
    vc_types = {'git':["status","diff",["log","-n1"],["svn","log","--limit=1"]],
                'svn':["info","status","diff"],
                'bzr':['info','status','diff']}
    for vc_type,commands in vc_types.items():
        if os.path.exists(".%s"%vc_type):
            return vc_type,commands

@in_vc_topographica_dir
def _print_vc_info(filename):
    """Save the version control status of the current code to the specified file."""
    try:
        import subprocess
        f = open(normalize_path(filename),'w')
        f.write("Information about working copy used for batch run\n\n")
        f.write("topo.version=%s\n"% topo.version)
        f.flush()
        vctype,commands = _get_vc_commands()
        for cmd in commands:
            fullcmd = [vctype,cmd] if isinstance(cmd,str) else [vctype]+cmd

            # Note that we do not wait for the process below to finish
            # (by calling e.g. wait() on the Popen object). Although
            # this was probably done unintentionally, for a slow svn
            # connection, it's an advantage. But it does mean the
            # output of each command can appear in the file at any
            # time (i.e. the command outputs appear in the order of
            # finishing, rather than in the order of starting, making
            # it impossible to label the commands).
            subprocess.Popen(fullcmd,stdout=f,stderr=subprocess.STDOUT)
    except:
        print "Unable to retrieve version control information."
    finally:
        f.close()


def _save_parameters(p,filename):
    from topo.misc.commandline import global_params

    g = {'global_params_specified':p,
         'global_params_all':dict(global_params.get_param_values())}

    for d in g.values():
        if 'name' in d:
            del d['name']
        if 'print_level' in d:
            del d['print_level']

    pickle.dump(g,open(normalize_path(filename),'w'))

# I'd expect your personal name_replacements to be set in some file
# you use to create batch runs, but it can alsp be set on the
# commandline. Before calling run_batch(), include something like the
# following:
# run_batch.dirname_params_filter.map=OrderedDict(("cortex_density","cd"))

class param_formatter(ParameterizedFunction):

    # CEBALERT: should I have made this a parameter at the run_batch
    # level? And I don't know what to call it.
    map = param.Dict(default=OrderedDict(),doc="""
        Optional ordered dictionary of alternative names to use for
        parameters, parameter_name:alternative_name

        Use to shorten common parameter names (directory names are
        limited in length on most file systems), and to specify an
        order.

        Names not specified here will be sorted alphabetically.""")

    def __call__(self,params):
        result = ""
        # present in params but not in map
        unspecified_in_map = sorted(set(params).difference(set(self.map)))
        # present in params and in map, preserving order of map
        specified_in_map = [n for n in self.map.keys() if n in params]

        for pname in specified_in_map+unspecified_in_map:
            val = params[pname]
            # Special case to give reasonable filenames for lists
            valstr= ("_".join([str(i) for i in val]) if isinstance(val,list)
                     else str(val))
            result += "," + self.map.get(pname,pname) + "=" + valstr
        return result


# Used only by default_analysis_function
# Should be in order they are needed; e.g. Activity after map measurement,
# in case Activity plot includes map subplots
default_analysis_plotgroups=["Orientation Preference","Activity"]

def default_analysis_function():
    """
    Basic example of an analysis command for run_batch; users are
    likely to need something similar but highly customized.
    """
    # CEBALERT: why are these imports here rather than at the top?
    import topo
    from topo.plotting.plotgroup import save_plotgroup

    # Save all plotgroups listed in default_analysis_plotgroups
    for pg in default_analysis_plotgroups:
        save_plotgroup(pg,use_cached_results=True)

    # Plot projections from each measured map
    measured_sheets = [s for s in topo.sim.objects(ProjectionSheet).values()
                       if hasattr(s,'measure_maps') and s.measure_maps]
    for s in measured_sheets:
        for p in s.in_connections:
            save_plotgroup("Projection",projection=p)

    # Test response to a standardized pattern
    from topo.pattern import Gaussian
    from analysis import pattern_present
    from math import pi
    pattern_present(inputs=Gaussian(orientation=pi/4,aspect_ratio=4.7))
    save_plotgroup("Activity",saver_params={"filename_suffix":"_45d"})


def load_kwargs(fname, glob, loc, fail_exception=False):
    """
    Helper function to allow keyword arguments (dictionary format)
    to be  loaded from a file 'fname'. The intended use is to allow a callable
    (specifically run_batch) to obtain its settings and parameters from file.

    This is useful when dispatching jobs on a cluster as you can then queue
    run_batch jobs (eg. using qsub) before all the settings are known. This
    type of scenario is typical in parameter search (eg hillclimbing) where
    the settings file for future run_batch instances are conditional on data
    from previous simulations.

    Variable glob should be provided as globals() and loc should be provided
    as locals(). Either a dictionary is returned or an exception is raised
    (conditioned on fail_exception). If fail_exception=False and eval does
    not evaluateas expected, an empty dictionary is returned. Eval is used
    as it allows classes, objects and other complex datastructures to load.
    """
    with open(fname,'r') as f: lines = f.readlines()
    expression = "".join([l.strip() for l in lines])
    kwargs = eval(expression, glob, loc)
    if not isinstance(kwargs,dict):
        if fail_exception: raise Exception('Invalid settings file.')
        else:              return {}
    else:                        return kwargs


# ALERT: Need to move docs into params.
class run_batch(ParameterizedFunction):
    """
    Run a Topographica simulation in batch mode.

    Features:

      - Generates a unique, well-defined name for each 'experiment'
        (i.e. simulation run) based on the date, script file, and
        parameter settings. Note that very long names may be truncated
        (see the max_name_length parameter).

      - Allows parameters to be varied on the command-line,
        to allow comparing various settings

      - Saves a script capturing the simulation state periodically,
        to preserve parameter values from old experiments and to allow
        them to be reproduced exactly later

      - Can perform user-specified analysis routines periodically,
        to monitor the simulation as it progresses.

      - Stores commandline output (stdout) in the output directory

    A typical use of this function is for remote execution of a large
    number of simulations with different parameters, often on remote
    machines (such as clusters).

    The script_file parameter defines the .ty script we want to run in
    batch mode. The output_directory defines the root directory in
    which a unique individual directory will be created for this
    particular run.  The optional analysis_fn can be any python
    function to be called at each of the simulation iterations defined
    in the analysis times list.  The analysis_fn should perform
    whatever analysis of the simulation you want to perform, such as
    plotting or calculating some statistics.  The analysis_fn should
    avoid using any GUI functions (i.e., should not import anything
    from topo.tkgui), and it should save all of its results into
    files.

    As a special case, a number can be passed for the times list, in
    which case it is used to scale a default list of times up to
    10000; e.g. times=2 will select a default list of times up to
    20000.  Alternatively, an explicit list of times can be supplied.

    Any other optional parameters supplied will be set in the main
    namespace before any scripts are run.  They will also be used to
    construct a unique topo.sim.name for the file, and they will be
    encoded into the simulation directory name, to make it clear how
    each simulation differs from the others.

    If requested by setting snapshot=True, saves a snapshot at the
    end of the simulation.

    If available and requested by setting vc_info=True, prints
    the revision number and any outstanding diffs from the version
    control system.

    Note that this function alters param.normalize_path.prefix so that
    all output goes into the same location. The original value of
    param.normalize_path.prefix is deliberately not restored at the
    end of the function so that the output of any subsequent commands
    will go into the same place.
    """
    output_directory=param.String("Output")

    analysis_fn = param.Callable(default_analysis_function)

    times = param.Parameter(1.0)

    snapshot=param.Boolean(True)

    vc_info=param.Boolean(True)

    dirname_prefix = param.String(default="",doc="""
        Optional prefix for the directory name (allowing e.g. easy
        grouping).""")

    tag = param.String(default="",doc="""
        Optional tag to embed in directory prefix to allow unique
        directory naming across multiple independent batches that
        share a common timestamp.""")

    # CB: do any platforms also have a maximum total path length?
    max_name_length = param.Number(default=200,doc="""
        The experiment's directory name will be truncated at this
        number of characters (since most filesystems have a
        limit).""")

    name_time_format = param.String(default="%Y%m%d%H%M",doc="""
        String format for the time included in the output directory
        and file names.  See the Python time module library
        documentation for codes.

        E.g. Adding '%S' to the default would include seconds.""")

    timestamp = param.NumericTuple(default=(0,0), doc="""
        Optional override of timestamp in Python struct_time 8-tuple format.
        Useful when running many run_batch commands as part of a group with
        a shared timestamp. By default, the timestamp used is the time when
        run_batch is started.""")

    save_global_params = param.Boolean(default=True,doc="""
        Whether to save the script's global_parameters to a pickle in
        the output_directory after the script has been loaded (for
        e.g. future inspection of the experiment).""")

    dirname_params_filter = param.Callable(param_formatter.instance(),doc="""
        Function to control how the parameter names will appear in the
        output_directory's name.""")

    metadata_dir = param.String(doc="""Specifies the name of a
        subdirectory used to output metadata from run_batch (if set).""")


    compress_metadata = param.ObjectSelector(default=None,
                              objects=[None, 'tar.gz', 'zip'], doc="""
         If not None and a metadata directory is specified, the
         metadata directory will be replaced by either a tar.gz file
         or a .zip file.""")

    save_script_repr = param.ObjectSelector(default='first',
                    objects=[None, 'first', 'last', 'all'], doc="""
       Whether to save a script_repr and if so, how often. If set to
       'first', the script_repr is saved on the first time value, if
       set to 'last' then it will be saved on the last time value. If
       set to 'all' then a script repr is saved for all time values.
       Saving is disabled entirely if set to None.""")

    def _truncate(self,p,s):
        """
        If s is greater than the max_name_length parameter, truncate it
        (and indicate that it has been truncated).
        """
        # '___' at the end is supposed to represent '...'
        return s if len(s)<=p.max_name_length else s[0:p.max_name_length-3]+'___'

    def __call__(self,script_file,**params_to_override):
        p=ParamOverrides(self,params_to_override,allow_extra_keywords=True)
        import os
        import shutil

        # Construct simulation name, etc.
        scriptbase= re.sub('.ty$','',os.path.basename(script_file))
        prefix = ""
        if p.timestamp==(0,0): prefix += time.strftime(p.name_time_format)
        else:                  prefix += time.strftime(p.name_time_format, p.timestamp)

        prefix += "_" + scriptbase + "_" + p.tag
        simname = prefix

        # Construct parameter-value portion of filename; should do more filtering
        # CBENHANCEMENT: should provide chance for user to specify a
        # function (i.e. make this a function, and have a parameter to
        # allow the function to be overridden).
        # And sort by name by default? Skip ones that aren't different
        # from default, or at least put them at the end?
        prefix += p.dirname_params_filter(p.extra_keywords())

        # Set provided parameter values in main namespace
        from topo.misc.commandline import global_params
        global_params.set_in_context(**p.extra_keywords())

        # Create output directories
        if not os.path.isdir(normalize_path(p.output_directory)):
            try: os.mkdir(normalize_path(p.output_directory))
            except OSError: pass   # Catches potential race condition (simultaneous run_batch runs)

        dirname = self._truncate(p,p.dirname_prefix+prefix)
        dirpath = normalize_path(os.path.join(p.output_directory,dirname))
        normalize_path.prefix = dirpath
        metadata_dir = os.path.join(normalize_path.prefix, p.metadata_dir)
        simpath = os.path.join(metadata_dir, simname)

        if os.path.isdir(normalize_path.prefix):
            print "Batch run: Warning -- directory already exists!"
            print "Run aborted; wait one minute before trying again, or else rename existing directory: \n" + \
                  normalize_path.prefix

            sys.exit(-1)
        else:
            os.makedirs(metadata_dir)
            print "Batch run output will be in " + normalize_path.prefix


        if p.vc_info:
            _print_vc_info(simpath + ".diffs")

        hostinfo = "Host: " + " ".join(platform.uname())
        topographicalocation = "Topographica: " + os.path.abspath(sys.argv[0])
        topolocation = "topo package: " + os.path.abspath(topo.__file__)
        scriptlocation = "script: " + os.path.abspath(script_file)

        starttime=time.time()
        startnote = "Batch run started at %s." % time.strftime("%a %d %b %Y %H:%M:%S +0000",
                                                               time.gmtime())

        # store a re-runnable copy of the command used to start this batch run
        try:
            # pipes.quote is undocumented, so I'm not sure which
            # versions of python include it (I checked python 2.6 and
            # 2.7 on linux; they both have it).
            import pipes
            quotefn = pipes.quote
        except (ImportError,AttributeError):
            # command will need a human to insert quotes before it can be re-used
            quotefn = lambda x: x

        command_used_to_start = string.join([quotefn(arg) for arg in sys.argv])

        # CBENHANCEMENT: would be nice to separately write out a
        # runnable script that does everything necessary to
        # re-generate results (applies diffs etc).

        # Shadow stdout to a .out file in the output directory, so that
        # print statements will go to both the file and to stdout.
        batch_output = open(normalize_path(simpath+".out"),'w')
        batch_output.write(command_used_to_start+"\n")
        sys.stdout = MultiFile(batch_output,sys.stdout)

        print
        print hostinfo
        print topographicalocation
        print topolocation
        print scriptlocation
        print
        print startnote

        from topo.misc.commandline import auto_import_commands
        auto_import_commands()

        # Ensure that saved state includes all parameter values
        from topo.command import save_script_repr
        param.parameterized.script_repr_suppress_defaults=False

        # Save a copy of the script file for reference
        shutil.copy2(script_file, normalize_path.prefix)
        shutil.move(normalize_path(scriptbase+".ty"),
                    normalize_path(simpath+".ty"))


        # Default case: times is just a number that scales a standard list of times
        times=p.times
        if not isinstance(times,list):
            times=[t*times for t in [0,50,100,500,1000,2000,3000,4000,5000,10000]]

        # Run script in main
        error_count = 0
        initial_warning_count = param.parameterized.warning_count
        try:
            execfile(script_file,__main__.__dict__) #global_params.context
            global_params.check_for_unused_names()
            if p.save_global_params:
                _save_parameters(p.extra_keywords(), simpath+".global_params.pickle")
            print_sizes()
            topo.sim.name=simname

            # Run each segment, doing the analysis and saving the script state each time
            for run_to in times:
                topo.sim.run(run_to - topo.sim.time())
                p.analysis_fn()
                normalize_path.prefix = metadata_dir
                if p.save_script_repr == 'first'  and run_to == times[0]:
                    save_script_repr()
                elif p.save_script_repr == 'last'  and (run_to == times[-1]):
                    save_script_repr()
                elif p.save_script_repr == 'all':
                    save_script_repr()
                normalize_path.prefix = dirpath
                elapsedtime=time.time()-starttime
                param.Parameterized(name="run_batch").message(
                    "Elapsed real time %02d:%02d." % (int(elapsedtime/60),int(elapsedtime%60)))

            if p.snapshot:
               save_snapshot()

        except:
            error_count+=1
            import traceback
            traceback.print_exc(file=sys.stdout)
            sys.stderr.write("Warning -- Error detected: execution halted.\n")

        if p.metadata_dir != '' and p.compress_metadata == 'tar.gz':
            _, name = os.path.split(metadata_dir)
            tar = tarfile.open(normalize_path("%s.tar.gz" % name), "w:gz")
            tar.add(metadata_dir, arcname=name)
            tar.close()
            shutil.rmtree(metadata_dir)
        elif p.metadata_dir != '' and p.compress_metadata == 'zip':
            _, name = os.path.split(metadata_dir)
            zipf = zipfile.ZipFile(normalize_path("%s.zip" % name), 'w')
            zipf.write(metadata_dir, arcname=name)
            for f in os.listdir(metadata_dir):
                zipf.write(os.path.join(metadata_dir, f),
                           os.path.join(p.metadata_dir,f))
            zipf.close()
            shutil.rmtree(metadata_dir)



        print "\nBatch run completed at %s." % time.strftime("%a %d %b %Y %H:%M:%S +0000",
                                                             time.gmtime())
        print "There were %d error(s) and %d warning(s)%s." % \
              (error_count,(param.parameterized.warning_count-initial_warning_count),
               ((" (plus %d warning(s) prior to entering run_batch)"%initial_warning_count
                 if initial_warning_count>0 else "")))

        # restore stdout
        sys.stdout = sys.__stdout__
        batch_output.close()



def wipe_out_activity():
    """
    Resets activity of all Sheets and their connections to zero.
    """
    # ALERT: this works for now, but it may need to be implemented
    # recursively using methods implemented separately on each class,
    # if there are often new types of objects created that store an
    # activity value.
    for s in topo.sim.objects(Sheet).values():
        s.activity*=0.0
        for c in s.in_connections:
            if hasattr(c,'activity'):
                c.activity*=0.0



def n_bytes():
    """
    Estimate the minimum memory needed for the Sheets in this Simulation, in bytes.

    This estimate is a lower bound only, based primarily on memory for
    the matrices used for activity and connections.
    """
    return sum([s.n_bytes() for s in topo.sim.objects(Sheet).values()])



def n_conns():
    """
    Count the number of connections in all ProjectionSheets in the current Simulation.
    """
    return sum([s.n_conns() for s in topo.sim.objects(ProjectionSheet).values()])


def print_sizes():
    """Format the results from n_conns() and n_bytes() for use in batch output."""
    print "Defined %d-connection network; %0.0fMB required for weight storage." % \
    (n_conns(),max(n_bytes()/1024.0/1024.0,1.0))

# added these two function to the PatternDrivenAnalysis hooks
PatternDrivenAnalysis.pre_presentation_hooks.append(topo.sim.state_push)
PatternDrivenAnalysis.pre_presentation_hooks.append(wipe_out_activity)
PatternDrivenAnalysis.pre_presentation_hooks.append(clear_event_queue)
PatternDrivenAnalysis.post_presentation_hooks.append(topo.sim.state_pop)

# maybe an explicit list would be better?
import types
_public = list(set([_k for _k,_v in locals().items()
                    if isinstance(_v,types.FunctionType) or
                    (isinstance(_v,type) and issubclass(_v,ParameterizedFunction))
                    and not _v.__name__.startswith('_')]))
_public += [
    "_VersionPrinter",
    "UnpickleEnvironmentCreator",
    "ImportErrorRaisingFakeModule",
    "ImportErrorObject",
]

# Automatically discover all .py files in this directory.
import os,fnmatch
__all__ = _public + [f.split('.py')[0] for f in os.listdir(__path__[0]) if fnmatch.fnmatch(f,'[!._]*.py')]
del f,os,fnmatch
