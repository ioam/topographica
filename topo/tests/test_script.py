"""
Contains tests to check a particular script's results or speed have
not changed.

See the Makefile for examples of usage.

$Id$
"""
__version__='$Revision$'

# CEBALERT: this file needs to be cleaned up! In particular,
# could start by cleaning up the paths. 

import pickle, copy, __main__, timeit
import os

from numpy.testing import assert_array_equal, assert_array_almost_equal

from param import resolve_path, normalize_path

import topo

### train-tests

def generate_data(script="examples/lissom_oo_or.ty",data_filename=None,
                  look_at='V1',run_for=[1,99,150],**args):
    """
    Run the specified script, saving activity from look_at at times
    specified in run_for.

    args are set in __main__ before the script is executed (allowing
    one to specify e.g. cortex_density).
    
    For the default data_filename of None, saves the resulting data to
    the pickle script_DATA.
    """
    if data_filename==None:
        data_filename=script+"_DATA"
    
    # we must execute in main because e.g. scheduled events are run in __main__
    for arg,val in args.items():
        __main__.__dict__[arg]=val

    execfile(script,__main__.__dict__)
    
    data = {}

    for time in run_for:
        topo.sim.run(time)
        data[topo.sim.time()] = copy.deepcopy(topo.sim[look_at].activity)

    data['args']=args
    data['run_for']=run_for
    data['look_at']=look_at

    locn = normalize_path(data_filename)
    print "Saving data to %s"%locn
    pickle.dump(data,open(locn,'wb'),2)

# old name
GenerateData=generate_data


def _support_old_args(args):
    # support old data files which contain 'default_density', etc
    if 'default_density' in args:
        args['cortex_density']=args['default_density']
        #del args['default_density']
    if 'default_retina_density' in args:
        args['retina_density']=args['default_retina_density']
        #del args['default_retina_density']
    if 'default_lgn_density' in args:
        args['lgn_density']=args['default_lgn_density']
        #del args['default_lgn_density']
    # (left the dels commented out for now in case scripts still use old names)

def test_script(script="examples/lissom_oo_or.ty",data_filename=None,decimal=None):
    """
    Run script with the parameters specified when its DATA file was
    generated, and check for changes.

    data_filename allows the location of the DATA file to be specified
    (for the default of None, the location is assumed to be
    script_DATA).
    
    The decimal parameter defines to how many decimal points will the
    equality with the DATA file be measured. Setting it to the default
    of None will cause exact matching.
    """
    if data_filename==None:
        data_filename=script+"_DATA"
    
    locn = resolve_path(data_filename)
    try:
        data = pickle.load(open(locn,"rb"))
    except IOError:
        print "\nData file '"+data_filename+"' could not be opened; run GenerateData() to create a data file before making changes to the script you wish to check."
        raise

    print "Reading data from %s"%locn


    # retrieve parameters used when script was run
    run_for=data['run_for']
    look_at = data['look_at']

    # support very old data files that contain 'density' instead of args['cortex_density']
    if 'args' not in data:
        data['args']={'cortex_density' : data['density']}

    args = data['args']
    _support_old_args(args)

    for arg,val in args.items():
        __main__.__dict__[arg]=val

    print "Running '%s' with the following arguments: %s"%(script,args)
    execfile(script,__main__.__dict__)        

    for time in run_for:
        topo.sim.run(time)
        if decimal is None:
            assert_array_equal(data[topo.sim.time()],topo.sim[look_at].activity,
                           err_msg="\nAt topo.sim.time()=%d, with decimal=%s"%(topo.sim.time(),decimal))
        else:
            assert_array_almost_equal(data[topo.sim.time()],topo.sim[look_at].activity,
                           decimal,err_msg="\nAt topo.sim.time()=%d, with decimal=%s"%(topo.sim.time(),decimal))

    result = "Results from " + script + " have not changed."
    if decimal is not None: result+= " (%d dp)" % (decimal)
    print result+"\n"


# old name
TestScript = test_script


### speed-tests

# except variation in these results! see python's timeit module documentation
def time_sim_run(script="examples/lissom_oo_or.ty",iterations=10):
    """
    Execute the script in __main__, then time topo.sim.run(iterations).

    Uses the timeit module.
    """
    execfile(script,__main__.__dict__)

    # CB: we enable garbage collection
    # (http://docs.python.org/lib/module-timeit.html)
    return timeit.Timer('topo.sim.run('+`iterations`+')','gc.enable(); import topo').timeit(number=1)

     
def generate_speed_data(script="examples/lissom_oo_or.ty",iterations=100,data_filename=None,
                        **args):
    """
    Calls time_sim_run(script,iterations) and saves 'iterations=time'
    to script_SPEEDDATA.
    """
    if data_filename==None:
        data_filename=script+"_SPEEDDATA"

    for arg,val in args.items():
        __main__.__dict__[arg]=val
                
    how_long = time_sim_run(script,iterations)

    speed_data = {'args':args,
                  'iterations':iterations,
                  'how_long':how_long}


    locn = normalize_path(data_filename)
    print "Saving data to %s"%locn
    pickle.dump(speed_data,open(locn,'wb'),2)



def compare_speed_data(script="examples/lissom_oo_or.ty",data_filename=None):
    """
    Using previously generated script_SPEEDDATA, compares current
    time_sim_run(script) with the previous.
    """
    if data_filename==None:
        data_filename=script+"_SPEEDDATA"

    locn = resolve_path(data_filename)
    print "Reading data from %s"%locn

    speed_data_file = open(locn,'r')

    try:
        speed_data = pickle.load(speed_data_file)
    except:
        ## support old data files (used to be string in the file
        ## rather than pickle)
        speed_data_file.seek(0)
        speed_data = speed_data_file.readline()

        iterations,old_time = speed_data.split('=')
        iterations = float(iterations); old_time=float(old_time)
        speed_data = {'iterations':iterations,
                      'how_long':old_time,
                      'args':{}}

    speed_data_file.close()
        
    old_time = speed_data['how_long']
    iterations = speed_data['iterations']
    args = speed_data['args']    

    _support_old_args(args)

    for arg,val in args.items():
        __main__.__dict__[arg]=val

    print "Running '%s' with the following arguments: %s"%(script,args)
    new_time = time_sim_run(script,iterations)

    percent_change = 100.0*(new_time-old_time)/old_time

    print "["+script+"]"+ '  Before: %2.1f s  Now: %2.1f s  (change=%2.1f s, %2.1f percent)'\
          %(old_time,new_time,new_time-old_time,percent_change)

    # CEBALERT: whatever compensations the python timing functions are supposed to make for CPU
    # activity, do they work well enough? If the processor is being used, these times jump all
    # over the place (i.e. vary by more than 10%).
    #assert percent_change<=5, "\nTime increase was greater than 5%"





### startup timing

# CEBALERT: was almost copy+paste of the speed functions above, but
# now these ones need updating. Can I first share more of the code?

# except variation in these results! see python's timeit module documentation
def time_sim_startup(script="examples/lissom_oo_or.ty",density=24):
    return timeit.Timer("execfile('%s',__main__.__dict__)"%script,'import __main__;gc.enable()').timeit(number=1)

     
def generate_startup_speed_data(script="examples/lissom_oo_or.ty",density=24,data_filename=None):
    if data_filename==None:
        data_filename=script+"_STARTUPSPEEDDATA"

    how_long = time_sim_startup(script,density)

    locn = normalize_path(data_filename)
    print "Saving to %s"%locn
    speed_data_file = open(locn,'w')
    speed_data_file.write("%s=%s"%(density,how_long))
    speed_data_file.close()


def compare_startup_speed_data(script="examples/lissom_oo_or.ty",data_filename=None):
    if data_filename==None:
        data_filename=script+"_STARTUPSPEEDDATA"

    speed_data_file = open(resolve_path(data_filename),'r')
        
    info = speed_data_file.readline()
    speed_data_file.close()

    density,old_time = info.split('=')
    density = float(density); old_time=float(old_time)
    
    new_time = time_sim_startup(script,density)

    percent_change = 100.0*(new_time-old_time)/old_time

    print "["+script+ ' startup]  Before: %2.1f s  Now: %2.1f s  (change=%2.1f s, %2.1f percent)'\
          %(old_time,new_time,new_time-old_time,percent_change)

### end startup timing








######### Snapshot tests: see the Makefile

# This is clumsy. We could control topographica subprocesses, but I
# can't remember how to do it

def compare_with_and_without_snapshot_NoSnapshot(script="examples/lissom.ty",look_at='V1',cortex_density=8,lgn_density=4,retina_density=4,dims=['or','od','dr','cr','dy','sf'],dataset="Nature",run_for=10,break_at=5):

    data_filename=os.path.split(script)[1]+"_PICKLETEST"
    
    # we must execute in main because e.g. scheduled events are run in __main__
    # CEBALERT: should set global params
    __main__.__dict__['cortex_density']=cortex_density
    __main__.__dict__['lgn_density']=lgn_density
    __main__.__dict__['retina_density']=retina_density
    __main__.__dict__['dims']=dims
    __main__.__dict__['dataset']=dataset
    
    execfile(script,__main__.__dict__)
    
    data = {}
    topo.sim.run(break_at)
    data[topo.sim.time()]= copy.deepcopy(topo.sim[look_at].activity)
    topo.sim.run(run_for-break_at)
    data[topo.sim.time()]= copy.deepcopy(topo.sim[look_at].activity)
        
    data['run_for']=run_for
    data['break_at']=break_at
    data['look_at']=look_at

    data['cortex_density']=cortex_density
    data['lgn_density']=lgn_density
    data['retina_density']=retina_density
    data['dims']=dims
    data['dataset']=dataset
    
    locn = normalize_path(os.path.join("tests",data_filename))
    print "Writing pickle to %s"%locn
    pickle.dump(data,open(locn,'wb'),2)


def compare_with_and_without_snapshot_CreateSnapshot(script="examples/lissom.ty"):
    data_filename=os.path.split(script)[1]+"_PICKLETEST"

    locn = resolve_path(os.path.join('tests',data_filename))
    print "Loading pickle at %s"%locn
        
    try:
        data = pickle.load(open(locn,"rb"))
    except IOError:
        print "\nData file '"+data_filename+"' could not be opened; run _A() first."
        raise

    # retrieve parameters used when script was run
    run_for=data['run_for']
    break_at=data['break_at']
    look_at=data['look_at']

    # CEBALERT: shouldn't need to re-list - should be able to read from data!
    cortex_density=data['cortex_density']
    lgn_density=data['lgn_density']
    retina_density=data['retina_density']
    dims=data['dims']
    dataset=data['dataset']

    __main__.__dict__['cortex_density']=cortex_density
    __main__.__dict__['lgn_density']=lgn_density
    __main__.__dict__['retina_density']=retina_density
    __main__.__dict__['dims']=dims
    __main__.__dict__['dataset']=dataset
    execfile(script,__main__.__dict__)        

    # check we have the same before any pickling
    topo.sim.run(break_at)
    assert_array_equal(data[topo.sim.time()],topo.sim[look_at].activity,
                       err_msg="\nAt topo.sim.time()=%d"%topo.sim.time())

    from topo.command.basic import save_snapshot
    locn = normalize_path(os.path.join('tests',data_filename+'.typ_'))
    print "Saving snapshot to %s"%locn
    save_snapshot(locn)


def compare_with_and_without_snapshot_LoadSnapshot(script="examples/lissom.ty"):
    data_filename=os.path.split(script)[1]+"_PICKLETEST"
    snapshot_filename=os.path.split(script)[1]+"_PICKLETEST.typ_"

    locn = resolve_path(os.path.join('tests',data_filename))
    print "Loading pickle from %s"%locn
    try:
        data = pickle.load(open(locn,"rb"))
    except IOError:
        print "\nData file '"+data_filename+"' could not be opened; run _A() first"
        raise

    # retrieve parameters used when script was run
    run_for=data['run_for']
    break_at=data['break_at']
    look_at=data['look_at']

#    # CEBALERT: shouldn't need to re-list - should be able to read from data!
#    cortex_density=data['cortex_density']
#    lgn_density=data['lgn_density']
#    retina_density=data['retina_density']
#    dims=data['dims']
#    dataset=data['dataset']
    
    from topo.command.basic import load_snapshot

    locn = resolve_path(os.path.join('tests',snapshot_filename))
    print "Loading snapshot at %s"%locn

    try:
        load_snapshot(locn)
    except IOError:
        print "\nPickle file '"+snapshot_filename+"' could not be opened; run _B() first."
        raise

    assert topo.sim.time()==break_at
    assert_array_equal(data[topo.sim.time()],topo.sim[look_at].activity,
                       err_msg="\nAt topo.sim.time()=%d"%topo.sim.time())
    print "Match at %s after loading snapshot"%topo.sim.time()

    topo.sim.run(run_for-break_at)
                
    assert_array_equal(data[topo.sim.time()],topo.sim[look_at].activity,
                       err_msg="\nAt topo.sim.time()=%d"%topo.sim.time())

    print "Match at %s after running loaded snapshot"%topo.sim.time()


######### end Snapshot tests






## CEBALERT: for reference simulations - should be moved elsewhere
def run_multiple_density_comparisons(ref_script):
    from topo.misc.util import cross_product
    import subprocess
    import traceback
    import os
    
    #k = [8,10,12,13,14,34]
    #x = cross_product([k,k])

    
    x = [[ 8, 8],[ 8, 9],[ 8,10],[ 8,11],[ 8,12],[ 8,13],[ 8,14],[ 8,15],
         [24,14],[24,17],[24,20],
         [24,24],[24,48]]

    cmds = []
    for spec in x:
        c="""./topographica -c "verbose=False;BaseRN=%s;BaseN=%s;comparisons=True;stop_at_1000=False" topo/tests/reference/%s"""%(spec[0],spec[1],ref_script)
        cmds.append(c)

    results = []
    errs=[]
    for cmd in cmds:
        print 
        print "************************************************************"
        print "Executing '%s'"%cmd
        
#        errout = os.tmpfile()#StringIO.StringIO()

        p = subprocess.Popen(cmd, shell=True,stderr=subprocess.PIPE)
        p.wait()
        r = p.returncode
        
        errout = p.stderr
        #r = subprocess.call(cmd,shell=True)#,stderr=subprocess.PIPE)#errout)
        #print "TB",traceback.print_exc()
        
        if r==0:
            result = "PASS"
        else:
            result = "FAIL"
        results.append(result)

        l = errout.readlines()
        i = 0
        L=0
        for line in l:
            if line.startswith("AssertionError"):
                L=i
                break
            i+=1
        
        errs.append(l[L::])
        errout.close()

    print "================================================================================"
    print
    print "SUMMARY"
    print
    nerr = 0
    for xi,result,err in zip(x,results,errs):
        print
        print "* %s ... BaseRN=%s,BaseN=%s"%(result,xi[0],xi[1])
        if result=="FAIL":
            e = ""
            print e.join(err)
            
            nerr+=1
    print "================================================================================"
    
    return nerr




# basic test of run batch
def test_runbatch():
    from topo.misc.genexamples import find_examples
    from topo.command import run_batch
    import os
    import param
    import tempfile
    import shutil

    original_output_path = param.normalize_path.prefix
    start_output_path = tempfile.mkdtemp()
    param.normalize_path.prefix = start_output_path
    
    tiny = os.path.join(find_examples(),"tiny.ty")
    run_batch(tiny,cortex_density=1,retina_density=1,times=[1],snapshot=True,output_directory="testing123")

    new_output_path = param.normalize_path.prefix

    assert new_output_path.startswith(start_output_path)
    assert "testing123" in new_output_path # not perfect test, but better than nothing.

    base = os.path.basename(new_output_path).split(",")[0]

    def exists(endpart):
        whole = os.path.join(new_output_path,base+endpart)
        print "Checking for %s"%whole
        return os.path.isfile(whole)
    
    assert exists(".global_params.pickle")
    assert exists(".out")
    assert exists("_000001.00_V1_Activity.png")
    assert exists("_000001.00_script_repr.ty")
    assert exists("_000001.00.typ")

    print "Deleting %s"%param.normalize_path.prefix
    shutil.rmtree(param.normalize_path.prefix)
    param.normalize_path.prefix=original_output_path



def instantiate_everything(
    classes_to_exclude=("topo.base.simulation.Simulation","topo.base.simulation.Simulation"),
    modules_to_exclude=('plotting','tests','tkgui','command')):

    # default excludes currently set up for pickle tests

    import param
    
    # CEBALERT: this is basically get_PO_class_attributes from param.parameterized
    import inspect
    def get_classes(module,classes,processed_modules,module_excludes=()):
        exec "from %s import *"%module.__name__ in locals()
        dict_ = module.__dict__
        for (k,v) in dict_.items():
            if '__all__' in dict_ and inspect.ismodule(v) and k not in module_excludes:
                if k in dict_['__all__'] and v not in processed_modules:
                    get_classes(v,classes,processed_modules,module_excludes)
                processed_modules.append(v)
            else:
                if isinstance(v,type) and not isinstance(v,param.ParameterizedFunction):
                    full_class_path = v.__module__+'.'+v.__name__
                    if (not full_class_path in classes_to_exclude) and full_class_path.startswith("topo") or full_class_path.startswith("param"):
                        classes.append(full_class_path)

    classes = []
    processed_modules = []
     
    import topo
    get_classes(topo,classes,processed_modules,module_excludes=modules_to_exclude)
    get_classes(param,classes,processed_modules,module_excludes=modules_to_exclude)

    instantiated_classes = []

    for class_name in classes:
        try:
            instantiated_classes.append(eval(class_name+"()"))
        except:
            print "Could not instantiate %s"%class_name

    return instantiated_classes
