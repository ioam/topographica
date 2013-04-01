import os, sys, re, pickle, imp, time, inspect, json
from collections import defaultdict
import topo
import param
from lancet.launch import CommandTemplate
from lancet.launch import review_and_launch

def topo_param_string(p, exclude=['print_level', 'name'], sep=", "):
   """
   Formats global parameters nicely for use in version control (for example).
   """
   strings = ['%s=%s' % (name,val) for (name,val) in p.get_param_values()
              if name not in exclude]
   return sep.join(strings)


class param_formatter(param.ParameterizedFunction):
   ''' This class is closely related to the param_formatter class in
       topo/command/__init__.py.  Like that default class, it formats parameters
       as a string for use in a directory name.  Unlike that default, it does
       not use the parameters repr directly but instead their commandline
       representation as returned by the TaskSpecifier.

   Unlike the default param_formatter, this version has several important
   advantages:
   - It allows for a custom separator and an optional trunctation
     length for values.
   - It removes the need to import param.misc.OrderedDict in
     the command string to specify map.
   - Parameters are sorted from slowest to fastest varying or
     (optionally) alphanumerically.
   - Does not support custom ordering but does still support abbreviations.
   - It formats a string for the parameters that vary by default (can be toggled)
   - Most importantly, it formats values *exactly* as they appear in a command.  For example, a value
     specified as 6.00 on the commandline remains this way and is never represented to higher
     precision or with floating point error.
   '''

   abbreviations = param.Dict(default={}, doc='''
       A dictionary of abbreviations to use of type {<key>:<abbrev>}.
       If a specifier key has an entry in the dictionary, the abbreviation is used.
       Useful for shortening long parameter names in the directory structure.''')

   alphanumeric_sort = param.Boolean(default=False, doc='''
        Whether to sort the (possibly abbreviated) keys alphabetically or not.
        By default, keys are ordered from slowest varying to fastest varying
        provided this information is available from the TaskSpecifier.''')

   format_constant_keys = param.Boolean(default=False, doc='''
        Whether or not to format the parameters that are known to be constant across batches.''')

   truncation_limit = param.Number(default=None, allow_None=True, doc= '''
        If None, no truncation is performed, otherwise specifies the maximum
        length of any given specification value. ''')

   separator = param.String(default=',', doc="""
          The separator to use between <key>=<value> pairs.""")


   def __call__(self, constant_keys, varying_keys, spec):

      if self.format_constant_keys: ordering = constant_keys + varying_keys
      else:                         ordering = varying_keys

      if self.alphanumeric_sort: ordering = sorted(ordering)
      abbreved = [ (self.abbreviations.get(k,k), spec[k]) for k in ordering]
      return self.separator.join(['%s=%s' % (k, v[:self.truncation_limit]) for (k,v) in abbreved])


class RunBatchCommand(CommandTemplate):
   """ RunBatchCommand is designed to to format task specifications into
       Topographica run_batch tasks in a way that should be flexible enough to
       be used generally. Note that Topographica is invoked with the -a flag so
       all of topo.command is imported.

       Though some of the parameters required appear to duplicate those in
       run_batch, they are necessary to ensure some basic consistency in the use
       of run_batch between tasks. This CommandTemplate class constrains -all- the
       options for run_batch with the exception of 'times' which is free to vary
       as part of the task specification. This is allowed as you may wish to
       change the times at which the analysis function is invoked across
       batches.

       This command is queuable with both the queue and specify methods
       implemented. As necessary, specifications are generated in the
       'specifications' subdirectory of the root directory.
       """

   topo_switches = param.List(default=['-a'], doc = """
          Specifies the Topographica qsub switches (flags without arguments) as a
          list of strings. By default the -a switch is always used to auto import
          commands.""")

   topo_flag_options = param.Dict(default={}, doc="""
          Specifies Topographica flags and their corresponding options as a
          dictionary.  This parameter is suitable for setting -c and -p flags for
          Topographica (eg. to customize OpenMP settings). This parameter is also
          important to introduce an analysis callable into the namespace if the
          analysis function is set to 'custom'.

          Tuples can be used to indicate groups of options using the same flag:
          {'-p':'retina_density=5'} => -p retina_density=5
          {'-p':('retina_density=5', 'scale=2') => -p retina_density=5 -p scale=2
          {'-p':'

          If a plain Python dictionary is used, the keys are alphanumerically sorted,
          otherwise the dictionary is assumed to be an OrderedDict (Python 2.7+,
          Python3 or param.external.OrderedDict) and the key ordering will be
          preserved. Finally note that the '-' is added to the key if missing (to
          make into a valid flag) to allow you to specify keywords in a dict
          constructor ie. dict(key1=value1, key2=value2,....)""")

   analysis = param.ObjectSelector(default='default',
                                   objects=['default', 'RunBatchAnalysis', 'custom'],
                                   constant=True, doc="""
              The type of analysis to use with run_batch. The options are 'default'
              which runs the default run_batch analysis function,
              'RunBatchAnalysis' which use the more sophisticated picklable
              analysis function and custom which requires the analysis callable to be
              created in the run_batch namespace via a -c option with
              topo_flag_options""")

   analysis_arguments = param.List(default=[], doc='''
         The specifier keys to be consumed as analysis function arguments''')

   name_time_format = param.String(default='%Y%m%d%H%M', doc="""
         The timestamp format for directories created by run_batch in python
         datetime format.""")

   max_name_length= param.Number(default=200, doc="Equivalent to the run_batch parameter of same name.")

   snapshot = param.Boolean(default=True, doc="Equivalent to the run_batch parameter of same name.")

   vc_info = param.Boolean(default=True, doc="Equivalent to the run_batch parameter of same name.")

   save_global_params = param.Boolean(default=True, doc="Equivalent to the run_batch parameter of same name.")

   param_formatter = param.Callable(param_formatter.instance(),doc="""
        If None, defaults to normal run_batch formatting.""")

   def __init__(self, tyfile, analysis='default', **kwargs):

      if (analysis == 'custom') and ('-c' not in self.topo_flag_options):
         raise Exception, 'Please use -c option to introduce custom analysis to namespace!'

      executable =  os.path.abspath(sys.argv[0])
      super(RunBatchCommand, self).__init__(analysis=analysis,
                                                executable=executable,
                                                **kwargs)

      self.tyfile = os.path.abspath(tyfile)
      assert os.path.exists(self.tyfile), "Tyfile doesn't exist! Cannot proceed."

      self._prelude = []
      if self.analysis=='RunBatchAnalysis':
         self._prelude = ['from lancet.topographica import RunBatchAnalysis']
      if self.analysis=='default':
         self._prelude = ["analysis = default_analysis_function"]


   def topo_args(self, switch_override=[]):
      """ Method to generate Popen style argument list for Topographica using the
      topo_switches and topo_flag_options parameters. Switches are returned first,
      sorted alphanumerically.  The qsub_flag_options follow in keys() ordered if
      not a vanilla Python dictionary (ie. a Python 2.7+ or param.external
      OrderedDict). Otherwise the keys are sorted alphanumerically."""

      opt_dict = type(self.topo_flag_options)()
      opt_dict.update(self.topo_flag_options)

      if type(self.topo_flag_options) == dict:   # Alphanumeric sort if vanilla Python dictionary
            ordered_options = [(k, opt_dict[k]) for k in sorted(opt_dict)]
      else:
         ordered_options =  list(opt_dict.items())

      # Unpack tuple values so flag:(v1, v2,...)) => ..., flag:v1, flag:v2, ...
      unpacked_groups = [[(k,v) for v in val] if type(val)==tuple else [(k,val)]
                           for (k,val) in ordered_options]
      unpacked_kvs = [el for group in unpacked_groups for el in group]

      # Adds '-' if missing (eg, keywords in dict constructor) and flattens lists.
      ordered_pairs = [(k,v) if (k[0]=='-') else ('-%s' % (k), v) for (k,v) in  unpacked_kvs]
      ordered_options = [[k]+([v] if type(v) == str else v) for (k,v) in ordered_pairs]
      flattened_options = [el for kvs in ordered_options for el in kvs]
      switches =  [s for s in switch_override if (s not in self.topo_switches)] + self.topo_switches
      return sorted(switches) + flattened_options


   def queue(self,tid, info):
      ''' Uses load_kwargs helper function in topo.command.misc to get the
      run_batch settings from the specifications directory. '''
      spec_path = os.path.join(info['root_directory'], 'specifications')
      spec_file_path = os.path.join(spec_path, 't%s.spec' % tid)
      prelude = self._prelude[:]
      prelude += ["kwargs = load_kwargs('%s',globals(),locals())" % spec_file_path]
      if self.analysis=='RunBatchAnalysis':
         prelude += ["analysis=RunBatchAnalysis.load(%s)" % repr(info['root_directory'])]
         prelude += ["analysis.current_tid = %s" % tid]
         prelude += ["analysis.analysis_kwargs = dict(kwargs)"]

      run_batch_cmd = "run_batch('%s',**kwargs)" % self.tyfile
      topo_args = self.topo_args(['-a'])
      return  [self.executable] + topo_args + ['-c', ';'.join(prelude+[run_batch_cmd])]

   def specify(self, spec, tid, info):
      ''' Writes the specification as a Python dictionary to file (to the
          specifications subdirectory of root directory) as required by the
          load_kwargs helper method in topo.misc.command.'''

      spec_path = os.path.join(info['root_directory'], 'specifications')
      spec_file_path = os.path.join(spec_path, 't%d.spec' % tid)
      if not os.path.exists(spec_path): os.mkdir(spec_path)

      spec_file = open(spec_file_path,'w')
      kwarg_opts = self._run_batch_kwargs(spec, tid, info)
      allopts = dict(spec,**kwarg_opts) # Override run_batch keys if (mistakenly) provided.

      keywords = ',\n'.join(['%s=%s' % (k, allopts[k]) for k in
                             sorted(kwarg_opts.keys()) + sorted(spec.keys())])
      spec_file.write('dict(\n%s\n)' % keywords); spec_file.close()

   def _run_batch_kwargs(self, spec, tid, info):
      ''' Defines the keywords accepted by run_batch and so specifies run_batch behaviour. '''
      options = {'name_time_format':   repr(self.name_time_format),
                 'max_name_length':    self.max_name_length,
                 'snapshot':           self.snapshot,
                 'vc_info':            self.vc_info,
                 'save_global_params': self.save_global_params}

      if info['batch_tag']=='': dirname_prefix = info['batch_name']
      else:                     dirname_prefix = info['batch_name'] + ('[%s]' % info['batch_tag'])

      # Settings using information from launcher
      derived_options = {'output_directory':repr(info['root_directory']),
                         'dirname_prefix':  repr(dirname_prefix),
                         'tag':             repr('t%s_' % tid)}

      # Use fixed timestamp argument to run_batch if available.
      if info['timestamp'] is not None: derived_options['timestamp'] = info['timestamp']
      derived_options['analysis_fn'] = 'analysis'

      # Use the specified param_formatter (if desired) to create lambda in run_batch
      if self.param_formatter is not None:
         dir_format = self.param_formatter(info['constant_keys'], info['varying_keys'], spec)
         derived_options['dirname_params_filter'] =  'lambda p: %s' % repr(dir_format)

      return dict(options.items() + derived_options.items())

   def __call__(self, spec, tid=None, info={}):
      """ Returns a Popen argument list to invoke Topographica and execute
      run_batch with all options appropriately set (in alphabetical
      order). Keywords that are not run_batch options are also in alphabetical
      order at the end of the keyword list"""

      kwarg_opts= self._run_batch_kwargs(spec, tid, info)
      allopts = dict(spec,**kwarg_opts) # Override spec values if mistakenly included.

      prelude = self._prelude[:]
      if self.analysis=='RunBatchAnalysis':
         prelude += ["analysis=RunBatchAnalysis.load(%s)" % repr(info['root_directory'])]
         prelude += ["analysis.current_tid = %s" % tid]
         analysis_kwargs = ["'%s':%s" % (k,v) for (k,v) in allopts.items()
                            if k in self.analysis_arguments]
         prelude += ["analysis.analysis_kwargs = {%s}" % ', '.join(analysis_kwargs)]


      keywords = ', '.join(['%s=%s' % (k,allopts[k]) for k in  # Was %s
                            sorted(kwarg_opts.keys())+sorted(spec.keys())])
      run_batch_list = prelude + ["run_batch(%s,%s)" % (repr(self.tyfile), keywords)]
      topo_args = self.topo_args(['-a'])
      return  [self.executable] + topo_args + ['-c',  '; '.join(run_batch_list)]


class RunBatchAnalysis(param.Parameterized):
   """ This analysis class is a generalization of the normal analysis functions
   use in Topographica's run_batch command. It allows you to factor out and
   document steps in your analysis, offers a standard mechanism to collate data
   returned from map functions across multiple simulations and allows you to
   define a metric function for use with dynamic TaskSpecifiers
   (eg. Hillclimbing). Here are the types of operation you can define:

   Map functions
   -------------
   Functions called for their side-effects. Eg. saving plotgroups, orientation
   maps etc.

   Map-reduce operations
   ---------------------
   Allows you to collect and process dataacross simulations. The map
   component generates the data per simulation while the reduce function
   collapse this data (eg. plotting a variable acrosssimulations).

   Metric function
   ---------------
   Provides the TaskSpecifier feedback (eg. for automated parameter
   search). There can only be one metric function.

   It works by restoring the analysis object from a pickle file *within* the
   run_batch context, dynamically importing the user-defined functions from the
   launch script and then executing them as specified.  Dynamic import is
   necessary as pickles do not store code and the referenced user-functions need
   to exist before execution. To create the initial pickle file, you need to
   call the save() method once all map, map-reduce and metric functions are
   defined. Note that this class is a callable (no arguments) as it is designed
   to interface with run_batch like a normal analysis function.
   """

   @classmethod
   def analysis_dir(cls):
      """ A helper method pointing to where the analysis function (map functions
      specifically) is executing. For use in analysis functions written by the
      user. Typically used to output custom files (ie. non-plotgroup) to the appropriate
      directory."""
      return param.normalize_path.prefix

   current_tid = param.Integer(default=None, allow_None=True, doc='''
         The task identifier for the current task. This needs to be set in the
         run_batch context in order to ensure the correct naming convention for
         pickles generated by the map functions (for later reduction).''')

   analysis_kwargs = param.Dict(default={}, doc='''
         The keyword arguments to be passed to the analysis functions. The analysis
         functions can capture any desired variables by setting the appropriate
         keyword arguments.''')

   analysis_arguments = param.Parameter(default=set([]), doc='''
        The names of all the arguments required by the analysis functions. Used to
        make sure that the specifiers supply all the required keys.''')

   @classmethod
   def load(cls, root_directory):
      ''' Classmethod used to load the analysis callable in a Topographica
          run_batch context.  Loads the analysisfn.pickle file from the
          specified root directory.'''
      path = os.path.join(root_directory, 'analysisfn.pickle')
      with open(path,'rb') as p:  analysisfn =  pickle.load(p)
      analysisfn.setup(); return analysisfn

   @classmethod
   def reduce_batch(cls, root_directory):
      '''
      Classmethod used to load the analysis object then apply all reductions.
      Loads the analysisfn.pickle file from the specified root directory.
      '''
      path = os.path.join(root_directory, 'analysisfn.pickle')
      with open(path,'rb') as p:
         analysis_obj = pickle.load(p)
         return analysis_obj.reduce

   def __init__(self, script_path):
      self.script_path = script_path
      self.root_directory = None
      self.maps = []; self.map_reduces = []
      self.metric = None
      self.analysis_arguments = set([])

   def save(self):
      ''' The method to save the initial pickle file once the map, reduce and
      metric functions are defined. Must be called before launch and saves
      the object as analysisfn.pickle file from the specified root
      directory.'''
      if None in [self.script_path, self.root_directory]:
         print "Please set the script_path and the root_directory before saving"
      if not os.path.isdir(self.root_directory): os.makedirs(self.root_directory)
      path = os.path.join(self.root_directory, 'analysisfn.pickle')
      with open(path,'wb') as p: pickle.dump(self, p)

   def _verify_mapfn(self, func):
      ''' Helper function to establish map function name and enforce
      correct argument signature.'''
      fn_name = func.__name__
      (args, varargs, keywords, defaults) = inspect.getargspec(func)
      assert varargs is None, "Function '%s' cannot accept arglist ie. *args" % fn_name
      assert keywords is not None, "Function '%s' must accept keywords ie. **kwargs" % fn_name
      if len(args) == 0: return (fn_name, ())
      assert (defaults is not None) and (len(defaults) == len(args)), \
          "Arguments of '%s' must all be keywords" % fn_name
      self.analysis_arguments =  self.analysis_arguments | set(args)
      return (fn_name, tuple(args))

   def set_metric(self, metric_fn, description):
      ''' Used to supply a metric function (eg. for hillclimbing) along with
      appropriate description.'''
      self.metric = {'metric_fn':metric_fn.__name__, 'description':description}

   def add_map_fn(self, map_fn, description):
      ''' Used to supply an additional map function (called for its side-effects
      only) along with appropriate description.'''
      (map_name, map_args) =  self._verify_mapfn(map_fn)
      self.maps.append({'map_fn':map_name, 'map_args':map_args, 'description':description})

   def add_map_reduce_fn(self, map_fn, reduce_fn, description):
      ''' Used to specify a map-reduce operation whereby the map_fn returns data
      from a given simulation which the reduce_fn collates across all
      simulations once the batch is complete. An appropriate description also
      needs to be supplied.'''
      (map_name, map_args) =  self._verify_mapfn(map_fn)
      reduce_name = reduce_fn.__name__
      (reduce_args, _, _, _) = inspect.getargspec(reduce_fn)
      checkmsg ="Reduction '%s' must accept three arguments of form (<info>, <data>, <accumulator>)"
      assert len(reduce_args) == 3, checkmsg % reduce_name

      self.map_reduces.append({'map_fn':map_name,
                               'map_args':map_args,
                               'reduce_fn':reduce_name,
                               'reduce_args':tuple(reduce_args),
                               'description':description})

   def set_map_reduce_fns(self, map_fns, reduce_fns, descriptions):
      ''' '''
      if len(map_fns) != len(reduce_fns) != len(descriptions):
         print "All input lists must be of the same length!"; return
      self.map_reduces = []
      for (map_fn, reduce_fn, description) in  zip(map_fns, reduce_fns, descriptions):
         self.add_map_reduce_fn(map_fn, reduce_fn, description)

   def pickle_data(self, subdir, fname, data):
      ''' Helper method to pickle the given data to a file of the given name in
          the given subdirectory on the appropriate path'''
      pickle_dir = os.path.join(self.root_directory, subdir)
      if not os.path.isdir(pickle_dir): os.makedirs(pickle_dir)
      with open(os.path.join(self.root_directory, subdir, fname),'wb') as p: pickle.dump(data, p)

   def setup(self):
      " This method is called at the start of a run_batch simulation "
      module = imp.load_source('', self.script_path)
      self.mapfns = [getattr(module, mapdict['map_fn']) for mapdict in self.maps]
      self.rmapfns = [getattr(module, map_reduce['map_fn']) for map_reduce in self.map_reduces]
      if self.metric is not None:
         self.metricfn = getattr(module, self.metric['metric_fn'])

   def __call__(self):
      '''
      The call that occurs in run_batch. Calls all the defined map functions, pickles
      the data returned from the map component of map-reductions and computes and
      pickles the metric. The pickled data is a tuple that includes the topographica
      simulation time at which the data was generated as run_batch typically applies
      the analysis functions at multiple simulation times.

      The pickles for map-reductions are stored in the root_directory under a
      subdirectory of the supplied map function name. The metric pickles are stored
      in the metrics folder of the root directory as required by all Launchers.
      '''
      if self.script_path is None:
         print "Source path was not set! Running default analysis function instead."
         topo.command.default_analysis_function(); return

      if (self.maps == []) and (self.map_reduces ==[]):
         topo.command.default_analysis_function()
         return

      topo_time = topo.sim.time()

      for mapfn in self.mapfns: mapfn(**self.analysis_kwargs) # Applying map functions in order

      for (rmapfn, info) in zip(self.rmapfns,self.map_reduces):
         rmap_result = rmapfn(**self.analysis_kwargs)
         if rmap_result is not None:
            fname = '%s@time=%s[%d]' % (info['map_fn'], str(topo_time), self.current_tid)
            self.pickle_data(info['map_fn'], fname, (topo_time, rmap_result)) # Pickle maps of map-reduces

      if self.metric is not None:
         fname = 'metric-%d-time=%s' % (self.current_tid, str(topo_time))
         self.pickle_data('metrics', fname, (self.current_tid, topo_time, self.metricfn())) # Pickle metric


   def reduce(self, spec_log, root_directory):
      '''
      Method to apply all defined map-reduces. For each map function, locates all
      the pickles in the corresponding subfolder and matches the stored data to the
      tid in the filename. The data, Topographica simulation times and corresponding
      tids are extracted and passed on to the appropriate reduce function.
      '''
      # FIXME: root_directory argument redundant!
      prefix = param.normalize_path.prefix
      param.normalize_path.prefix = root_directory
      reduces = [map_red['reduce_fn'] for map_red in self.map_reduces]
      reduce_maps = [map_red['map_fn'] for map_red in self.map_reduces]

      if self.script_path:  module = imp.load_source('', self.script_path)
      else:                 return

      reduce_fns = [getattr(module, rname) for rname in reduces]
      reduce_mapping = [(map_name, rfn) for (map_name, rfn) in zip(reduce_maps, reduce_fns)]

      previous_reduction = None
      for (map_name, reducefn) in reduce_mapping:
         ddict = defaultdict(list)
         path = os.path.join(root_directory, map_name)
         if not os.path.isdir(path):
            previous_reduction = reducefn([root_directory, spec_log], None, previous_reduction)
            continue
         tid_pattern = map_name + '.*\[(?P<tid>\d+)\]'
         regexp_matches = [(cf, re.match(tid_pattern,cf)) for cf in os.listdir(path)]
         tid_matches = [(int(m.groupdict()['tid']),  cf) for (cf,m) in regexp_matches if (m is not None)]
         for (tid, match) in tid_matches: ddict[tid].append(match)
         specDict = dict(spec_log)
         specs=[]; map_data =[]
         for tid in sorted(ddict.keys()):
            matches = ddict[tid]
            pickle_paths = [os.path.join(root_directory, map_name, f) for f in matches]
            unpickled = [pickle.load(open(p,'rb')) for p in pickle_paths]
            for (topo_time, datum) in sorted(unpickled, key=lambda tp: tp[0]):
               specs.append(dict(specDict[tid], tid=tid, time=float(topo_time)))
               map_data.append(datum)

         previous_reduction = reducefn(specs, map_data, previous_reduction)
         # Must be restored for multiple launches (global state)
      param.normalize_path.prefix = prefix

   def __str__(self):
      ''' The printed representation of the analysis object. '''
      strList = []
      for info in self.maps:
         map_str = '(%s)' % ' ,'.join(info['map_args']+('**kwargs',))
         strList += ["%(map_fn)s%(map_str)s\n\t%(description)s" % dict(info, map_str=map_str)]
      for info in self.map_reduces:
         map_str = '(%s)' % ' ,'.join(info['map_args']+('**kwargs',))
         red_str='(%s)'% ' ,'.join(info['reduce_args'])
         strList += ["%(map_fn)s%(map_str)s => %(reduce_fn)s%(red_str)s\n\t%(description)s"
                     % dict(info, map_str=map_str, red_str=red_str)]
      if strList == []: strList = ['Default RunBatchAnalysis']
      if self.metric is not None: strList += ['Metric function %(metric_fn)s' % self.metric]
      if len(self.map_reduces) > 1:
         reduction_chain = "(..) -> ".join([map_red['reduce_fn'] for map_red in self.map_reduces])
         strList += ["Reduction Chain: %s(..)" % reduction_chain]
      return "\n".join(strList)

####################
# Launch Decorator #
####################

class batch_analysis(review_and_launch):

   @classmethod
   def get_timestamp(cls, timestamp_string, timestamp_format):
      return tuple(time.strptime(timestamp_string, timestamp_format))

   def __init__(self, launcher_class, reduce_timestamp=None, skip_reduce=False, **kwargs):
      super(batch_analysis, self).__init__(launcher_class=launcher_class, **kwargs)
      self.reduce_timestamp = reduce_timestamp
      self.skip_reduce = skip_reduce
      self._get_launcher = lambda dval: dval[0]
      self._cross_checks = [(lambda dval: dval, self.cross_check_analysis),
                            (self._get_launcher, self.cross_check_launchers)]
      self._reviewers = [(self._get_launcher, self.review_launcher ),
                         (self._get_launcher, self.review_args),
                         (self._get_launcher, self.review_command_template),
                         (lambda dval: dval[1], self.review_analysis)]

      if self.reduce_timestamp is not None:
         self._reviewers = [(lambda dval: dval[1], self.review_analysis)]

   def cross_check_analysis(self, dvalues):
        """
        Performs consistency checks across all the analysis objects before launch.
        """
        if not all(len(dval)==2 and type(dval)==tuple for dval in dvalues):
           raise Exception("Launch function must return a tuple of type (Launcher, batch_analysis)")

        (launchers, analyses) = zip(*dvalues)

        if not all(isinstance(analysis, RunBatchAnalysis) for analysis in analyses):
           raise Exception("Second element of returned tuple must be a RunBatchAnalysis object")

        if not all(isinstance(launcher.command_template, RunBatchCommand) for launcher in launchers):
           raise Exception("CommandTemplate specified in launcher is not a RunBatchCommand object")

        if not all(launcher.command_template.analysis =='RunBatchAnalysis' for launcher in launchers):
           raise Exception("RunBatchCommand must use 'RunBatchAnalysis' analysis type")


   def reduce_directory(self, task_launcher):

      task_launcher.timestamp = self.reduce_timestamp
      root_directory = param.normalize_path(task_launcher.root_directory_name())
      print "Running reduce in directory %s" % os.path.basename(root_directory)
      log_name = "%s.log" % task_launcher.batch_name
      log_path = os.path.join(root_directory, log_name)
      assert os.path.exists(log_path), 'Cannot find log file %s' % log_name
      with open(log_path,'r') as log:
         splits = (line.split() for line in log)
         spec_log = [(int(split[0]), json.loads(" ".join(split[1:]))) for split in splits]

      task_launcher.reduction_fn(spec_log, root_directory)
      return False

   def configure_launch(self, dval):
      """
      Determine the root directory from the launcher to configure the analysis
      object appropriately, save the final state and set up the launcher's exit
      callable.
      """
      (task_launcher, batch_analysis) = dval
      command_template = task_launcher.command_template

      if self.reduce_timestamp is not None:
         return self.reduce_directory(task_launcher)

      arg_specifier = task_launcher.arg_specifier
      analysis_arguments = batch_analysis.analysis_arguments
      specifier_keys = set(arg_specifier.varying_keys() + arg_specifier.constant_keys())
      if not (analysis_arguments <= specifier_keys):
         clashes = analysis_arguments - specifier_keys
         raise Exception("Analysis keys %s not set in the specifier" % list(clashes))
      command_template.analysis_arguments = list(analysis_arguments)

      root_directory = param.normalize_path(task_launcher.root_directory_name())
      batch_analysis.root_directory = root_directory
      task_launcher.script_path =  batch_analysis.script_path
      batch_analysis.save()
      if self.skip_reduce or batch_analysis.map_reduces != []:
         task_launcher.reduction_fn = RunBatchAnalysis.reduce_batch(root_directory)
      return True


   def review_analysis(self, batch_analysis):
      print "\n" + self.section('Batch Analysis')
      print "Source path: %s" % batch_analysis.script_path
      print "Analysis Info:\n%s\n" %  str(batch_analysis)
      return True

   def __repr__(self):
      raise NotImplementedError

   def __str__(self):
      raise NotImplementedError

   def _repr_pretty_(self, p, cycle):
      super(batch_analysis, self)._repr_pretty_(p, cycle)
