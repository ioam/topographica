"""
Functions for measuring memory usage, to allow usage to be optimized.

Examples::

  bin/python -c 'execfile("topo/misc/memuse.py") ; print topsize_mb()'

  ./topographica -c 'from topo.misc import memuse' -c 'print memuse.topsize_mb()'

  ./topographica -c 'from topo.misc import memuse, asizeof' -c 'print memuse.topsize_mb()'

  ./topographica -a -c 'from topo.misc import memuse, asizeof' -c 'print memuse.topsize_mb()'

  ./topographica -a -c 'from topo.misc import memuse, asizeof' examples/tiny.ty -c 'print memuse.allsizes_mb()'

  ./topographica -a -c 'from topo.misc import memuse, asizeof' -c 'memuse.memuse_batch("examples/tiny.ty",cortex_density=20)'

  ./topographica -a -c 'from topo.misc import memuse, asizeof' -c 'memuse.memuse_batch("examples/tiny.ty",times=[0,100],analysis_fn=memuse.plotting_and_saving_analysis_fn,cortex_density=20)'
"""

# If functions in this file need anything other than the very basic
# imports declared here at the top, they must do so using import
# statements *within* the function definition to avoid polluting
# memory.  Otherwise, the simplest functions in this file would end up
# measuring memory taken by unused and irrelevant imports like 'topo',
# which doesn't ever need to be loaded for the 'execfile' example
# shown above.

import subprocess


def cmd_to_string(cmd):
    """Run a system command as in os.system(), but capture the stdout and return it as a string."""
    return subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE).communicate()[0]



def topsize():
    """Return the RES size of this process as reported by the top(1) command."""
    import os
    top_line=cmd_to_string("top -n 1 -b -p %d | grep '^[ ]*%d '" % (os.getpid(),os.getpid()))
    return top_line.split()[5]



def simsize():
    """
    Return the size of topo.sim reported by asizeof.asizeof().
    This estimate does not currently include any numpy arrays, and
    may also be missing other important items.

    Python 2.6 supports getsizeof() and a __sizeof__ attribute that user
    code can implement, which should provide a more accurate estimate.
    """
    import asizeof,topo
    return asizeof.asizeof(topo.sim)



###############################################################################
# String-formatted versions of the above

def mb(bytes):
    """Format the given value in bytes as a string in megabytes"""
    return "%dMB" % (bytes/1024.0/1024.0)

def topsize_mb():
    """String-formatted version of the RES size of this process reported by top(1)."""
    return "topsize:%s" % topsize()

def simsize_mb():
    """String-formatted version of the value reported by asizeof(topo.sim)."""
    return "simsize:%s" % (mb(simsize()))

def wtsize_mb():
    """String-formatted version of the memory taken by the weights, from print_sizes()."""
    from topo.command import n_bytes
    return "wtsize:%s" % (mb(n_bytes()))

def allsizes_mb():
    """
    Collates results from topsize, simsize, and wtsize.

    Formatted to suggest that the topsize is made up of code (not
    currently estimated), topo.sim (apart from weights), and weights.
    """
    from topo.command import n_bytes
    return "%s =? code + %s + %s (%s tot)" % (topsize_mb(),simsize_mb(),wtsize_mb(),mb(simsize()+n_bytes()))


###############################################################################
# Batch commands


def default_memuse_analysis_fn(prefix=""):
    """Basic memuse function for use with memuse_batch()"""
    import topo
    print "%st%s: %s" % (prefix,topo.sim.timestr(),allsizes_mb())



def plotting_and_saving_analysis_fn(prefix=""):
    """For use with memuse_batch() to test snapshot and plotting memory usage."""
    import topo
    from topo.command import save_snapshot
    from topo.command.analysis import measure_sine_pref,save_plotgroup

    print "%sMemuse at time %s: %s" % (prefix,topo.sim.timestr(),allsizes_mb())
    measure_sine_pref()
    print "%sAfter measure_sine_pref:  %s" % (prefix,allsizes_mb())
    save_plotgroup("Orientation Preference")
    print "%sAfter save_plotgroup:     %s" % (prefix,allsizes_mb())
    save_snapshot("/tmp/tmp.typ")
    print "%sAfter save_snapshot:      %s" % (prefix,allsizes_mb())



def memuse_batch(script_file,times=[0],analysis_fn=default_memuse_analysis_fn,**params):
    """
    Similar to run_batch, but analyzes the memory requirement of a simulation at different times.

    First, the specified script file will be run using the specified parameters.
    Then at each of the specified times, the given analysis_fn (which
    calls allsizes_mb() by default) is run.  The output is labeled
    with the script file, time, and parameters so that results from
    different runs can be compared.
    """
    import os,re,__main__,topo
    from topo.misc.commandline import global_params

    # Construct simulation name, etc.
    scriptbase= re.sub('.ty$','',os.path.basename(script_file))
    prefix = ""
    #prefix += time.strftime("%Y%m%d%H%M") + "_"
    prefix += scriptbase
    simname = prefix

    # Construct parameter-value portion of filename; should do more filtering
    for a,val in params.iteritems():
        # Special case to give reasonable filenames for lists
        valstr= ("_".join([str(i) for i in val]) if isinstance(val,list)
                 else str(val))
        prefix += "," + a + "=" + valstr

    # Set provided parameter values in main namespace
    global_params.set_in_context(**params)

    # Run script in main
    try:
        execfile(script_file,__main__.__dict__) #global_params.context
        global_params.check_for_unused_names()
        topo.sim.name=simname

        # Run each segment, doing the analysis and saving the script state each time
        for run_to in times:
            topo.sim.run(run_to - topo.sim.time())
            analysis_fn(prefix=prefix+": ")

    except:
        import traceback,sys
        traceback.print_exc(file=sys.stdout)
        sys.stderr.write("Warning -- Error detected: execution halted.\n")
