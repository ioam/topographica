<H1>Running Topographica simulations in batch mode</H1>

<P>Topographica is designed so that full functionality is available
from the command line and batch mode, without any GUI required.  This
support is essential for running large numbers of similar simulations,
e.g. to compare parameter settings or other options, usually using
clusters or networks of workstations.

<P>To make this process simpler, Topographica provides a command
topo.command.run_batch, which puts all results into a uniquely
identifiable directory that records the options used for the run.
Example:

<pre>
  topographica -a -c "run_batch('~/Documents/Topographica/examples/tiny.ty')"
</pre>
(see <A HREF="../User_Manual/scripts.html#copy_examples">how to get a copy of the
  example files</A> if you do not have them already).

<P>Here the <A href="commandline.html#option-a">"-a" option</a> is
used so that run_batch can be called without importing it explicitly,
and also so that all commands will be available to the various
plotting and analysis routines called by run_batch (as described
below). The result will be a directory with a name like
<code>200710112056_tiny</code> in the <code>Output</code> subdirectory
of your <code>Topographica</code> folder in your
<code>Documents</code> directory (this can be customized, and
is <code>~/topographica</code> in release 0.9.7 and earlier; see the
note about the <A HREF="scripts.html#outputpath">default output
path</A> for more information).  The name encodes the date of the run
(in year/month/day/hour/minute format) plus the name of the script
file.

<P>If you want to override any of the options accepted by tiny.ty, you
can do that when you call run_batch:

<pre>
  topographica -a -c "run_batch('~/Documents/Topographica/examples/tiny.ty',cortex_density=3)"
</pre>

<p>To help you keep the options straight, they will be encoded into
the directory name (as
<code>200710112056_tiny,cortex_density=3</code> in this case).

<p>run_batch also accepts a parameter <code>analysis_fn</code>, which
can be any callable Python object (e.g. the name of a function).  The
analysis_fn will be called periodically during the run, at times
specified by a parameter <code>times</code> (e.g.
<code>[0.5,2.8,100,500,1000,5000]</code>).  The simulation will
complete after the last analysis time.

<p>The default analysis_fn creates a few plots each time and saves the
current script_repr() of the simulation to record the parameter
settings from that time.  In practice you will want to supply your own
function, defined either in your .ty file or in a separate script or
module executed before you call run_batch.  In this case you can start
from the default_analysis_function in topo/command/basic.py as an
example.  Your analysis_fn should avoid using any GUI functions (i.e.,
should not import anything from topo.tkgui), and it should save all of
its results into files.  For more information about commands that can
go into the analysis_fn, see the <A HREF="commandline.html">command
line/script language</A> section.

<P>As you might expect, you can provide any other options before or
after the run_batch call, as usual.  These will be processed before or
after the batch run, respectively:

<pre>
  topographica -a -c "save_script_repr()" -p cortex_density=3\
  -c "run_batch('~/Documents/Topographica/examples/tiny.ty')" \
  -c "save_snapshot()"
</pre>

Note that the output directory is not created or changed until the
run_batch command is executed, so the output from the
save_script_repr() command will go into the default output directory.
Also note that when a parameter is set before run_batch (as
cortex_density is in this example), it will not be encoded into the
directory filename, because run_batch will not be aware that it has
changed.  Similarly, any errors in the commands provided before or
after run_batch will not show up in the .out file stored in the
simulation directory, because that is closed when run_batch completes.
Thus it's usually best to use run_batch's options rather than
the separate commands shown in this example.


<!-- CB: draft

<H2>Parameter searches</H2>

<P>Often you will want to investigate the behavior of a simulation
when changing certain aspects of it, such as the input or internal
parameters. Doing this may require a large number of simulation runs,
so to make this easy, we provide the script
<code>parameter_search</code> for launching multiple batch runs
(e.g. for submission to a cluster), and the script
<code>parameter_analysis</code> for organizing and analysing the
results.

<H3>Parameterize your simulation</H3>

<P>Ensure that your script file uses parameters (as shown in our
example scripts) for any quantities that you want to vary.  For
instance, you might include a section like this near the beginning of
your script:

<pre>

from topo.misc.commandline import global_params as p
p.add(
    dataset=param.Enumeration(default='Gaussian',available=
        ['Gaussian','Nature','FoliageA','FoliageB']),

    dims=param.List(default=['or','od','dr','dy'],class_=str),

    retina_density=param.Number(default=24.0,bounds=(0,None),
        inclusive_bounds=(False,True)),

    cortex_density=param.Number(default=48.0,bounds=(0,None),
        inclusive_bounds=(False,True)),

    afferent_strength=param.Number(default=1.0,bounds=(0,10),
    
    lateral_strength=param.Number(default=1.0,bounds=(0,100))
)

</pre>

(where the docstrings of the parameters have been ommitted for brevity
in this case).


<H3>Set up the experiments</H3>

<P>Create a text file describing combinations parameters to use as
experiments. For instance, if we want to see the effects of changing
<code>afferent_strength</code> from <code>2.0</code> to
<code>8.0</code> on simulations that use either the
<code>FoliageB</code> or <code>Gaussian</code> datasets, and contain
either the dimensions <code>or,cr</code> or <code>or,cr,od</code>, we
might define the following experiments:
 
<pre>
dataset      dims               afferent_strength
"FoliageB"   ["or","cr"]        2.0
"FoliageB"   ["or","cr"]        8.0
"Gaussian"   ["or","cr"]        2.0
"Gaussian"   ["or","cr"]        8.0
"FoliageB"   ["or","cr","od"]   2.0
"FoliageB"   ["or","cr","od"]   8.0
"Gaussian"   ["or","cr","od"]   2.0
"Gaussian"   ["or","cr","od"]   8.0
</pre>

CEBALERT: could be improved!
(Formatting rules: there must be a header row, spaces are used as
separators, strings must be enclosed in double quotes, no newline at
the end of the file.) In this case, call the file something like
<code>aff_strength_investigation</code>.


<H3>Launch the experiments</H3>

<P>Before you can use the file above to create a script that will
launch multiple, simultaneous simulations, you need to specify how
each simulation should be launched. For a normal desktop machine,
there is usually nothing special to do, but a cluster will usually
have its own job submission system. <code>parameter_search</code>
reads a configuration file where this and other options can be set:

<pre>
[Options]
# Where is the topographica script? Note that some job submission
# systems require an absolute path
# e.g. "/home/user/topographica/topographica". 
topographica_script = './topographica'

# The results (i.e. directories created by) all calls to run_batch()
# will be in one overall directory: results_path + name of
# combinations file.  results_path must already exist. Note that you
# should usually supply a local path (rather than one on a network) if
# you are going to be saving many or large files.
# e.g. "/disk/scratch/"
results_path = './Output/' 

# run_batch()'s dirname_prefix; ${combonumber} will be replaced with
# the combination number
topographica_dirname_prefix_template = '${combonumber}'

# The appropriate command template for your system; ${job} will be
# replaced with the actual job. Additionally, you can use
# ${combonumber} to get the combination number and ${comboname} to get
# the name of the combination file.
#
# E.g. on eddie: 
#  'qsub -cwd -P ecdf_baseline -pe "memory" 1 -l s_rt=40:00:0 -R y ${job}'
job_submit_template = 'nohup nice ${job} > ${comboname}-${combonumber}.out &'

# Arguments passed to Topographica before any others.
topographica_args = ['-a']
</pre>

<P>If your configuration file is <code>ps.cfg</code>, and your
simulation is defined in <code>myscript.ty</code>, you would call
<code>parameter_search</code> like this:

<pre>
parameter_search ps.cfg myscript.ty aff_strength_investigation 'retina_density=48.0,lateral_strength=10.0,analysis_function=mymodule.myanalysisfn(),times=[0,100,1000]'
</pre>

<P>The final arguments, enclosed in single quotes, are any parameters
that you want to pass to <code>run_batch</code> in all of the
experiments. Here, we are overriding the script's default
<code>retina_density</code> and <code>lateral_strength</code>, and
requesting that a custom analysis function be called at times 0, 100,
and 1000. Since we are calling a custom analysis function defined in
<code>mymodule</code>, we need to ensure that <code>mymodule</code> is
imported. To do this, <code>ps.cfg</code>'s
<code>topographica_args</code> should have contained the appropriate
code before running the command above:

<pre>
topographica_args = ['-a','import mymodule']
</pre>

<P><code>parameter_search</code> creates a script file that, when run,
will submit all your experiments using the job submission command you
defined in the <code>ps.cfg</code> file.

<H3>Analysis</H3> 

<P>Once your jobs have completed, you will need to explore the
results.  An easy way of doing this, especially once you have lots of
experiments, is to use the analysis script we provide, which puts
selected plots into a pdf file (via latex).

<P>The basic idea of the script is that you specify a directory to
analyse, optionally along with any criteria for which experiments to
include (e.g. only <code>dims=['or','cr']</code>) and what output to
include for each experiment. This specification is done via a
configuration file:

<pre>
[Outputs]
interests = ["Hue_PreferenceAndSelectivity",
             "Orientation_PreferenceAndSelectivity"]

times = ["000000.00",
         "000100.00",
         "001000.00"]


[Conditions]
dims = ['cr','or']
retina_density=48.0

[Condition-matching functions]
dims = 'sets_equal'
</pre>

Here we are saying that for each experiment, any plots containing the
string <code>Hue_PreferenceAndSelectivity</code> or
<code>Orientation_PreferenceAndSelectivity</code> should be included,
at times 0, 100, and 1000. We are only interested in experiments that
have <code>dims=['cr','or']</code> (<code>sets_equal</code> means
<code>dims=['or','cr']</code> would also match) and
retina_density=48.0.

<P>Running the script as: <code>parameter_analysis
/path/to/experiments/ config-file</code>, the output will be a pdf
showing the specified plots at each of the specified times for all
experiments in subdirectories of </code>/path/to/experiments/</code>
that used parameters matching any specifications made in the
<code>Conditions</code> section of config-file.

-->

<H3>Lancet</H3>

Once you get used to run_batch, you'll often want to run a large
number of coordinated run_batch runs, e.g. to do a parameter search.
Topographica works well with
<a target="_top" href="https://github.com/ioam/lancet/">Lancet</a>, which provides
these features and many more.  Lancet allows you to specify parameter
spaces to cover, launch multiple jobs (on single machines or computing
clusters), collate the results, generate figures and analyses from the
results, and archive these for posterity.  See the Lancet site for
more details.
