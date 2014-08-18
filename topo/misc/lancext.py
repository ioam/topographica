"""
The Topographica Lancet extension allows Topographica simulations to
be easily integrated into a Lancet workflow (see
github.com/ioam/lancet). The TopoCommand is appropriate for simple
runs using the default analysis function, whereas the RunBatchCommand
allow for more sophisticated measurements and analysis to be executed
during a simulation run using a dataviews Collector object.
"""

import os, pickle
from collections import namedtuple, OrderedDict

import numpy.version as np_version
import topo
import param

from lancet import PrettyPrinted, vcs_metadata
from lancet import Command
from lancet import Launcher, review_and_launch
from lancet import ViewFile
from lancet import Log, FileInfo, FileType
from lancet import List, Args

try:
   from external import sys_paths
   submodule_paths = sys_paths()
   ordering = ['topographica', 'param', 'paramtk', 'imagen', 'lancet']
   submodules = [[p for p in submodule_paths if p.endswith(name)][0] for name in ordering]
except:
   submodules = []


from dataviews import NdMapping
from dataviews.collector import Collector, Collator

from topo.misc.commandline import default_output_path
review_and_launch.output_directory = default_output_path()
Launcher.output_directory = default_output_path()


class topo_metadata(param.Parameterized):
   """
   Topographica specific helper function that expands on Lancet's
   vcs_metadata function to generate suitable metadata information for
   logging with Lancet. Records Topographica version control
   information as well as information about all relevant submodules
   and the current numpy version.

   No arguments should be necessary when either contructing or calling
   this object as the default behaviour is designed to be useful. The
   summary method prints out the key information collected to assist
   with reproducibility. For instance, this may be called to print all
   the relevant git revisions in an IPython Notebook before launching
   jobs.
   """

   max_log_length = param.Integer(default=90, doc="""
      Maximum number of characters that will be shown per message in
      the printed summary.""")

   paths = param.List(default = submodules, doc="""
   List of git repositories including Topographica and relevant
   submodules. Version control information from these repositories
   will be returned as a dictionary when called. The most important
   information is pretty printed when the summary method is called.""")

   commands = param.Dict(default={'.git':(['git', 'rev-parse', 'HEAD'],
                                          ['git', 'log', '--oneline', '-n', '1'],
                                          ['git', 'diff'])},
      doc="""The git commands to pass to subprocess to extract the
      necessary version control information. Uses the same
      specification format as the lancet.vsc_metdata helper function.""")

   def __init__(self, **kwargs):
      super(topo_metadata,self).__init__(**kwargs)
      self._repos = ['Topographica', 'Param', 'Param Tk', 'Imagen', 'Lancet']
      self._summarized = ['Topographica', 'Param', 'Imagen', 'Lancet']
      self._paths = dict(zip(self._repos, self.paths))
      self._info = {}


   def __call__(self, **params_to_override):
      p = param.ParamOverrides(self, params_to_override)
      self._info = vcs_metadata(paths=p.paths,
                                commands=p.commands)

      self._info['numpy_version'] = np_version.full_version
      self._info['numpy_git_revision'] = np_version.git_revision
      return self._info

   def _modified_files(self, diff):
      "Returns the set of files mentioned in a given git diff string."
      modified_files = []
      diff_marker = 'diff --git '
      diff_lines = [line for line in diff.splitlines()
                    if line.startswith(diff_marker)]

      for diff_line in diff_lines:
         bfilepath = diff_line[len(diff_marker):].rsplit(' b/')[1]
         bfile = bfilepath.rsplit('/')[-1]
         modified_files.append(bfile)
      return set(modified_files)


   def summary(self):
      "Printed summary of the versioning information captured via git."
      np_name = 'Numpy'
      info = self._info if self._info else self()

      messages = [info['vcs_messages'][self._paths[repo]] for repo in self._summarized]
      diffs = [info['vcs_diffs'][self._paths[repo]] for repo in self._summarized]

      diff_message = "   %s  [%d files have uncommited changes as captured by git diff]"
      longest_name = max(len(name) for name in self._summarized + [np_name])

      print "Topographica version control summary:\n"
      for repo_name, message, diff in zip(self._summarized, messages, diffs):
         truncate_len = (self.max_log_length - 3)
         if len(message) > truncate_len:
            message = message[:truncate_len]+'...'

         sha_len = len(message.split()[0])
         modified_files = self._modified_files(diff)
         print '   %s: %s%s' % (repo_name,
                                ' ' * (longest_name - len(repo_name)),
                                message)
         if len(modified_files) != 0:
            print diff_message % (' ' * (sha_len+longest_name+1),
                                  len(modified_files))

      numpy_sha = self._info['numpy_git_revision'][:7]
      np_info = (np_name,   ' ' * (longest_name-len(np_name)),
                 numpy_sha, self._info['numpy_version'],
                 '' if np_version.release else 'Non-')
      print '   %s: %s%s Version %s (%srelease)' % np_info


class param_formatter(param.ParameterizedFunction):
   """
   This class is closely related to the param_formatter class in
   topo/command/__init__.py.  Like that default class, it formats
   parameters as a string for use in a directory name. Unlike that
   default class, it does not use the parameters repr methods but the
   exact, succinct commandline representation as returned by a Lancet
   Args object.

   This version has several advantages over the default:

   - It formats values exactly as they appear in a command. For
   example, a value specified as 6.00 on the commandline remains this
   way and is never represented to higher precision or with floating
   point error.

   - Parameters are sorted from slowest to fastest varying or
   (optionally) alphanumerically by default.

   - It allows for a custom separator and an optional trunctation
   length for values.

   - By default, formats a string only for the parameters that are
   varying (may be toggled).
   """

   abbreviations = param.Dict(default={}, doc='''
       A dictionary of abbreviations to use of type {<key>:<abbrev>}.
       If a specifier key has an entry in the dictionary, the
       abbreviation is used.  Useful for shortening long parameter
       names in the directory structure.''')

   alphanumeric_sort = param.Boolean(default=False, doc='''
        Whether to sort the (potentially abbreviated) keys
        alphabetically or not. By default, keys are ordered from
        slowest varying to fastest varying using thr information
        provided by Lancet's Args object.''')

   format_constant_keys = param.Boolean(default=False, doc='''
        Whether to represent parameters that are known to be constant
        across batches.''')

   truncation_limit = param.Number(default=None, allow_None=True, doc= '''
        If None, no truncation is performed, otherwise specifies the
        maximum length of any given specification value.''')

   separator = param.String(default=',', doc="""
          The separator to use between <key>=<value> pairs.""")


   def __call__(self, constant_keys, varying_keys, spec):

      ordering = (constant_keys if self.format_constant_keys else []) + varying_keys
      if self.alphanumeric_sort:  ordering = sorted(ordering)
      abbreved = [(self.abbreviations.get(k,k), spec[k]) for k in ordering]
      return self.separator.join(['%s=%s' % (k, v[:self.truncation_limit]) for (k,v) in abbreved])



class TopoCommand(Command):
   """
   TopoCommand is designed to to format Lancet Args objects into
   run_batch commands in a general way. Note that Topographica is
   always invoked with the -a flag so all of topo.command is imported.

   Some of the parameters duplicate those in run_batch to ensure
   consistency with previous run_batch usage in Topographica. As a
   consequence, this class sets all the necessary options for
   run_batch except the 'times' parameter which may vary specified
   arbitrarily by the Lancet Args object.
   """

   tyfile = param.String(doc="The Topographica model file to run.")

   analysis_fn = param.String(default="default_analysis_function", doc="""
       The name of the analysis_fn to run. If modified from the
       default, the named callable will need to be imported into the
       namespace using a '-c' command in topo_flag_options.""")

   tag = param.Boolean(default=False, doc="""
       Whether to label the run_batch generated directory with the
       batch name and batch tag.""")

   topo_switches = param.List(default=['-a'], doc = """
          Specifies the Topographica qsub switches (flags without
          arguments) as a list of strings. Note the that the -a switch
          is always used to auto import commands.""")

   topo_flag_options = param.Dict(default={}, doc="""
          Specifies Topographica flags and their corresponding options
          as a dictionary.  This parameter is suitable for setting -c
          and -p flags for Topographica. This parameter is important
          for introducing the callable named by the analysis_fn
          parameter into the namespace.

          Tuples can be used to indicate groups of options using the
          same flag:
          {'-p':'retina_density=5'} => -p retina_density=5
          {'-p':('retina_density=5', 'scale=2') => -p retina_density=5 -p scale=2

          If a plain Python dictionary is used, the keys are
          alphanumerically sorted, otherwise the dictionary is assumed
          to be an OrderedDict (Python 2.7+, Python3 or
          param.external.OrderedDict) and the key ordering will be
          preserved. Note that the '-' is prefixed to the key if
          missing (to ensure a valid flag). This allows keywords to be
          specified with the dict constructor eg.. dict(key1=value1,
          key2=value2).""")

   param_formatter = param.Callable(param_formatter.instance(),
      doc="""Used to specify run_batch formatting.""")

   max_name_length= param.Number(default=200, doc="Matches run_batch parameter of same name.")

   snapshot = param.Boolean(default=True, doc="Matches run_batch parameter of same name.")

   vc_info = param.Boolean(default=True, doc="Matches run_batch parameter of same name.")

   save_global_params = param.Boolean(default=True, doc="Matches run_batch parameter of same name.")

   progress_bar = param.String(default='disabled', doc="Matches run_batch parameter of same name.")


   def __init__(self, tyfile, executable=None, **kwargs):

      auto_executable =  os.path.realpath(
         os.path.join(topo.__file__, '..', '..', 'topographica'))

      executable = executable if executable else auto_executable
      super(TopoCommand, self).__init__(tyfile=tyfile, executable=executable, **kwargs)
      self.pprint_args(['executable', 'tyfile', 'analysis_fn'],['topo_switches', 'snapshot'])
      self._typath = os.path.abspath(self.tyfile)

      if not os.path.isfile(self.executable):
         raise Exception('Cannot find the topographica script relative to topo/__init__.py.')
      if not os.path.exists(self._typath):
         raise Exception("Tyfile doesn't exist! Cannot proceed.")

      if ((self.analysis_fn.strip() != "default_analysis_function")
          and (type(self) == TopoCommand)
          and ('-c' not in self.topo_flag_options)):
         raise Exception, 'Please use -c option to introduce the appropriate analysis into the namespace.'


   def _topo_args(self, switch_override=[]):
      """
      Method to generate Popen style argument list for Topographica
      using the topo_switches and topo_flag_options
      parameters. Switches are returned first, sorted
      alphanumerically.  The qsub_flag_options follow in the order
      given by keys() which may be controlled if an OrderedDict is
      used (eg. in Python 2.7+ or using param.external
      OrderedDict). Otherwise the keys are sorted alphanumerically.
      """
      opt_dict = type(self.topo_flag_options)()
      opt_dict.update(self.topo_flag_options)

      # Alphanumeric sort if vanilla Python dictionary
      if type(self.topo_flag_options) == dict:
            ordered_options = [(k, opt_dict[k]) for k in sorted(opt_dict)]
      else:
         ordered_options =  list(opt_dict.items())

      # Unpack tuple values so flag:(v1, v2,...)) => ..., flag:v1, flag:v2, ...
      unpacked_groups = [[(k,v) for v in val] if type(val)==tuple else [(k,val)]
                           for (k,val) in ordered_options]
      unpacked_kvs = [el for group in unpacked_groups for el in group]

      # Adds '-' if missing (eg, keywords in dict constructor) and flattens lists.
      ordered_pairs = [(k,v) if (k[0]=='-') else ('-%s' % (k), v)
                       for (k,v) in  unpacked_kvs]
      ordered_options = [[k]+([v] if type(v) == str else v)
                         for (k,v) in ordered_pairs]
      flattened_options = [el for kvs in ordered_options for el in kvs]
      switches =  [s for s in switch_override
                   if (s not in self.topo_switches)] + self.topo_switches
      return sorted(switches) + flattened_options


   def _run_batch_kwargs(self, spec, tid, info):
      """
      Defines the keywords accepted by run_batch and so specifies
      run_batch behaviour. These keywords are those consumed by
      run_batch for controlling run_batch behaviour.
      """
      # Direct options for controlling run_batch.
      options = {'name_time_format':   repr(info['timestamp_format']),
                 'max_name_length':    self.max_name_length,
                 'snapshot':           self.snapshot,
                 'vc_info':            self.vc_info,
                 'save_global_params': self.save_global_params,
                 'progress_bar':       repr(self.progress_bar),
                 'metadata_dir':       repr('metadata'),
                 'compress_metadata':  repr('zip'),
                 'save_script_repr':   repr('first')}

      # Settings inferred using information from launcher ('info')
      tag_info = (info['batch_name'], info['batch_tag'])
      tag = '[%s]_' % ':'.join(el for el in tag_info if el) if self.tag else ''

      derived_options = {'dirname_prefix':  repr(''),
                         'tag':             repr('%st%s_' % (tag, tid)),
                         'output_directory':repr(info['root_directory'])}

      # Use fixed timestamp argument to run_batch if available.
      if info['timestamp'] is not None:
         derived_options['timestamp'] = info['timestamp']

      # The analysis_fn is set my self.analysis_fn
      derived_options['analysis_fn'] = self.analysis_fn

      # Use the specified param_formatter to create the suitably named
      # lambda (returning the desired string) in run_batch.
      dir_format = self.param_formatter(info['constant_keys'],
                                        info['varying_keys'], spec)

      dir_formatter = 'lambda p: %s' % repr(dir_format)
      derived_options['dirname_params_filter'] =  dir_formatter

      return dict(options.items() + derived_options.items())


   def __call__(self, spec, tid=None, info={}):
      """
      Returns a Popen argument list to invoke Topographica and execute
      run_batch with all options appropriately set (in alphabetical
      order). Keywords that are not run_batch options are also in
      alphabetical order at the end of the keyword list.
      """

      kwarg_opts = self._run_batch_kwargs(spec, tid, info)
      # Override spec values if mistakenly included.
      allopts = dict(spec,**kwarg_opts)

      keywords = ', '.join(['%s=%s' % (k,allopts[k]) for k in
                            sorted(kwarg_opts.keys())+sorted(spec.keys())])

      run_batch_list = ["run_batch(%s,%s)" % (repr(self._typath), keywords)]
      topo_args = self._topo_args(['-a'])
      return  [self.executable] + topo_args + ['-c',  '; '.join(run_batch_list)]




class BatchCollector(PrettyPrinted, param.Parameterized):
   """
   BatchCollector is a wrapper class used to execute a Collector in a
   Topographica run_batch context, saving the dataviews to disk as
   *.view files.
   """

   metadata = param.List(default=[], doc="""
       Spec keys or collector paths to include as metadata in the
       output file along with 'time' (simulation time).

       AttrTree paths are specified by dotted paths
       e.g. 'PinwheelAnalysis.V1' would add the pinwheel analysis on
       V1 to the metadata.
       """)

   @classmethod
   def pickle_path(cls, root_directory, batch_name):
      """
      Locates the pickle file based on the given launch info
      dictionary. Used by load as a classmethod and by save as an
      instance method.
      """
      return os.path.join(root_directory, '%s.collector' % batch_name)


   @classmethod
   def load(cls, tid, specs, root_directory, batch_name, batch_tag):
      """
      Classmethod used to load the RunBatchCommand callable into a
      Topographica run_batch context. Loads the pickle file based on
      the batch_name and root directory in batch_info.
      """
      pkl_path = cls.pickle_path(root_directory, batch_name)
      with open(pkl_path,'rb') as pkl:
         collectorfn =  pickle.load(pkl)

      info = namedtuple('info',['tid', 'specs', 'batch_name', 'batch_tag'])
      collectorfn._info = info(tid, specs, batch_name, batch_tag)
      return collectorfn


   def __init__(self, collector, **kwargs):
      from topo.analysis import Collector
      self._pprint_args = ([],[],None,{})
      super(BatchCollector, self).__init__(**kwargs)
      if not isinstance(collector, Collector):
         raise TypeError("Please supply a Collector to BatchCollector")
      self.collector = collector
      # The _info attribute holds information about the batch.
      self._info = ()


   def __call__(self):
      """
      Calls the collector specified by the user in the run_batch
      context. Invoked as an analysis function by RunBatchCommand.
      """
      from dataviews.collector import AttrTree
      self.collector.interval_hook = topo.sim.run

      topo_time = topo.sim.time()
      filename = '%s%s_%s' % (self._info.batch_name,
                              ('[%s]' % self._info.batch_tag
                               if self._info.batch_tag else ''),
                              topo_time)

      viewtree = AttrTree()
      viewtree = self.collector(viewtree, times=[topo_time])

      spec_metadata = [(key, self._info.specs[key])
                       for key in self.metadata if '.' not in key]


      path_metadata = [(key, viewtree.path_items.get(tuple(key.split('.')), float('nan')))
                       for key in self.metadata if '.' in key]

      ViewFile(directory= param.normalize_path.prefix,
               hash_suffix = False).save(filename,
                                         viewtree,
                                         metadata=dict(spec_metadata
                                                     + path_metadata
                                                     + [('time',topo_time)]))

   def verify(self, specs, model_params):
      """
      Check that a times list has been supplied, call verify_times on
      the Collator and if model_params has been supplied, check that a
      valid parameter set has been used.
      """
      # Note: Parameter types could also be checked...
      unknown_params = set()
      known_params = (set(model_params if model_params else []) # Model
                      | set(['times']))                         # Extras

      for spec in specs:
         if 'times' not in spec:
            raise Exception("BatchCollector requires a times argument.")
         self.collector.verify_times(spec['times'], strict=True)

         if not model_params: continue

         unknown_params = unknown_params | (set(spec) - known_params)

         if not set(self.metadata).issubset(spec.keys()):
            raise Exception("Metadata keys not always available: %s"
                            % ', '.join(self.metadata))

      if unknown_params:
         raise KeyError("The following keys do not belong to "
                        "the model parameters or RunBatchCommand: %s"
                        % ', '.join('%r' % p for p in unknown_params))

   def summary(self):
      print "Collector definition summary:\n\n%s" % self.collector

   def _pprint(self, cycle=False, flat=False, annotate=False,
               onlychanged=True, level=1, tab = '   '):
      """Pretty print the collector in a declarative style."""
      split = '\n%s' % (tab*(level+1))
      spec_strs = []
      for path, val in self.collector.path_items.items():
         key = repr('.'.join(path)) if isinstance(path, tuple) else 'None'
         spec_strs.append('(%s,%s%s%r),' % (key, split, tab, val))

      return 'Collector([%s%s%s])' % (split, split.join(spec_strs)[:-1], split)



class BatchCollator(Collator):
    """
    BatchCollator provides a convenient interface to load the output
    of a BatchCollector run, which is spread across a number of
    files. As input it takes a Lancet FileInfo object, an NdMapping or
    a Pandas DataFrame, which contains all the filenames indexed by
    the parameter space values. The regular NdMapping slicing and
    selecting syntax can be used to narrow down the parameter space
    and load just the data that is needed.

    By supplying a log, BatchCollector can also find missing data
    files and return an Args object to relaunch them.

    Internally it uses Pandas operations, making Pandas a core
    dependency.
    """

    filekey = param.String(default='filename', doc="""
        The column key in which file paths are stored.""")

    filetype = param.ClassSelector(FileType, doc="""
       FileType object required to load data files, can be passed directly
       or via the FileInfo object.""")

    fileinfo = param.ClassSelector(FileInfo, doc="""
       FileInfo object contains the filenames and associated metadata of all
       files to be loaded.""")

    log = param.ClassSelector(Log, doc="""
        The Log object contains information about the full batch and may be
        passed optionally to find missing data files.""")

    _deep_indexable = False

    def __init__(self, data, filetype=None, filekey='filename', log=None, **params):
        if not isinstance(data, FileInfo) and filetype is None:
            raise Exception('BatchCollator requires a FileType '
                            'to be specified.')

        if isinstance(data, (OrderedDict, list)):
            dimensions = params.pop('dimensions')
        else:
            if isinstance(data, FileInfo):
                params['fileinfo'] = data
                filekey = data.key
                filetype = data.filetype
                data = data.dframe
            elif isinstance(data, NdMapping):
                data = data.dframe()
            data, dimensions = self._process_dframe(data, log, filekey)

        super(BatchCollator, self).__init__(data, dimensions=dimensions, log=log,
                                            filetype=filetype, filekey=filekey,
                                            **params)

        if self.log and self.fileinfo:
            if len(self.missing_args()):
                self.warning("Missing data files. Use .missing_args method "
                             "to view missing entries.")

    def _process_data(self, data):
        return self.filetype.data(data)[self.filetype.data_key]


    def _process_dframe(self, dframe, log, filekey):
        """
        Takes a dframe as input, merges it with the log dframe if
        supplied, and converts it to an OrderedDict.
        """

        if log:
            if 'tid' not in dframe:
                self.warning('Without a tid field, missing runs cannot be determined.')
            else:
                dframe = dframe.merge(log.dframe.drop('times', axis=1))

        data = OrderedDict()
        for filename, df in dframe.groupby(filekey):
            df = df.drop(filekey, 1)
            data[tuple(df.values[0])] = filename
            dimensions = list(df.columns)

        return data, dimensions


    def missing_args(self):
        """
        Finds any missing data by merging the FileInfo and Log,
        returning an Args object, which can be used to fill in the
        missing runs.
        """
        if not self.log or not self.fileinfo:
            raise Exception('Lancet FileInfo and Lancet log required '
                            'to determine missing args.')

        # Expand 'times' list into 'time'
        specs = self.log.specs[0]
        expanded_log = self.log * List('time', specs['times'])

        # Expand fileinfo with constant dims
        expanded_info = self.fileinfo
        constant_args = Args(**dict((d, self.dim_values(d)[0])
                                        for d in self.constant_dims
                                        if d not in expanded_info))
        if constant_args:
           expanded_info *= constant_args

        # Compute set of sorted log and file spec tuples
        sort_fn = lambda k: self.dimension_labels.index(k[0])
        log_specs = [tuple(sorted(tuple((k, v) for k, v in spec.items()
                                        if k != 'times'), key=sort_fn))
                     for spec in expanded_log.specs]
        file_specs = [tuple(sorted(tuple((k, v) for k, v in spec.items()
                                         if k != 'filename'), key=sort_fn))
                      for spec in expanded_info.specs]

        return Args([dict(spec) for spec in (set(log_specs) - set(file_specs))])


    def clone(self, items=None, **kwargs):
        settings = dict(self.get_param_values(), **kwargs)
        return self.__class__(items, **settings)




class RunBatchCommand(TopoCommand):
   """
   Runs a custom analysis function specified by a Collector using
   run_batch. This command is far more flexible for regular usage than
   TopoCommand as it allows you to build a run_batch analysis
   incrementally.
   """

   metadata = param.List(default=[], doc="""
       Keys to include as metadata in the output file along with
       'time' (Topographica simulation time).""")

   analysis = param.ClassSelector(default=None, class_=(Collector, BatchCollector),
                                  allow_None=True, doc="""
      The object used to define the analysis executed in
      RunBatch. This object may be a Topographica Collector or a
      BatchCollector which is a wrapper of a Collector.""" )

   model_params = param.Parameter(default={}, doc="""
     A list or dictionary of model parameters to be passed to the
     model via run_batch. This is used to validate the parameter names
     specified. If set to an empty container, no checking is applied
     (default).""")

   def __init__(self, tyfile, analysis, **kwargs):
      super(RunBatchCommand, self).__init__(tyfile=tyfile,
                                            analysis_fn = 'analysis_fn',
                                            analysis = analysis,
                                            do_format=False,
                                            **kwargs)
      self.pprint_args(['executable', 'tyfile', 'analysis'], [])
      if isinstance(self.analysis, Collector):
         self.analysis = BatchCollector(analysis, metadata=self.metadata)


   def __call__(self, spec=None, tid=None, info={}):
      """
      Generates the appropriate Topographica run_batch command to make
      use of the pickled RunBatchCommand object.
      """

      formatted_spec = dict((k, repr(v) if isinstance(v,str) else str(v))
                            for (k,v) in spec.items())
      kwarg_opts = self._run_batch_kwargs(formatted_spec, tid, info)
      allopts = dict(formatted_spec,**kwarg_opts) # Override spec values if
                                                  # mistakenly included.

      # Load and configure the analysis
      prelude = ['from topo.misc.lancext import BatchCollector']
      prelude += ["analysis_fn=BatchCollector.load(%r, %r, %r, %r, %r)"
                  % (tid, spec, info['root_directory'],
                     info['batch_name'], info['batch_tag']) ]

      # Create the keyword representation to pass into run_batch
      keywords = ', '.join(['%s=%s' % (k,allopts[k]) for k in
                            sorted(kwarg_opts.keys())
                            +sorted(formatted_spec.keys())])
      run_batch_list = prelude + ["run_batch(%s,%s)"
                                  % (repr(self.tyfile), keywords)]
      topo_args = self._topo_args(['-a'])
      return  [self.executable] + topo_args + ['-c',  '; '.join(run_batch_list)]


   def verify(self, args):
      """
      Check that the supplied arguments make sense given the specified
      analysis.
      """
      return self.analysis.verify(args.specs, self.model_params)


   def finalize(self, info):
      """Pickle the analysis before launch."""
      pkl_path = self.analysis.pickle_path(info['root_directory'],
                                           info['batch_name'])
      with open(pkl_path,'wb') as pkl:
         pickle.dump(self.analysis, pkl)


   def summary(self):
      print("Command executable: %s" % self.executable)
      self.analysis.summary()
