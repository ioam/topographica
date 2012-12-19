"""
Functions for getting C++ LISSOM data and comparing them
with Topographica's.

Before using these functions, you should set filename_base to
give the base filename path of the C++ LISSOM files, e.g.
'topo/tests/reference/or_map_topo.'
"""

# CEBHACKALERT: filename should change

from math import pi, atan2
from numpy import array
import topo
from topo.tests.utils import array_almost_equal

from topo.base.arrayutil import arg

filename_base = ""


def dprint(txt,d=True):
    if d:
        print txt



precision = 1

def get_input_params(old_compat=False):
    """

    Return iterators over list of float values for C++ LISSOM's cx,
    cy, and theta for multiple eyes, as well as sign.


    Expects log file with values held in lines like this::

      'Iteration: 000000  [Eye0 [Obj0 cx:02.1 cy:11.6 theta:074.0]]\n'

    or this:

      'Iteration: 000000  [Eye0 [Obj0 cx:23.4 cy:10.0 theta:059.6]]  [Eye1 [Obj0 cx:22.6 cy:10.5 theta:059.6]]  [Eye2 [Obj0 cx:21.7 cy:11.1 theta:059.6]]  [Eye3 [Obj0 cx:20.8 cy:11.6 theta:059.6]]\n'

    """
    logfile = filename_base+'log'
    print "Reading input params from %s"%logfile
    f = open(logfile,'r')

    # first iter is test in c++ lissom; use to get num eyes
    n_eyes = len(f.readline().split('Eye')[1::])

    input_params = dict([(i,dict(cx=list(),cy=list(),theta=list(),sign=list()))
                         for i in range(n_eyes)])

    lines = f.readlines()
    for line,lineno in zip(lines,range(len(lines))):
        eyes = line.split('Eye')[1::]
        for eye,i in zip(eyes,range(n_eyes)):

            # e.g. eye='1 [Obj0 cx:-0.2 cy:13.8 theta:011.7]]  ['
            cx,cy,theta =[W.split(":")[1].split("]")[0]
                          for W in eye.split(" ")[2:5]]

            if not old_compat:
                for X in ['cx','cy','theta']:
                    input_params[i][X].append(round(float(locals()[X]),1))
            else: # old compat: log file with degrees etc
                input_params[i]['cx'].append(float(cx))
                input_params[i]['cy'].append(float(cy))
                input_params[i]['theta'].append(float(theta))

            del cx; del cy; del theta


        if len(eyes)>1: # CeBALERLT: not general (assuming motion just because more than 1 eye)

            ##### get sign
            X1=complex(input_params[0]['cx'][lineno],
                       input_params[0]['cy'][lineno])
            X2=complex(input_params[len(eyes)-1]['cx'][lineno],
                       input_params[len(eyes)-1]['cy'][lineno])

            realdir=arg(X2-X1)

            # for 0<=realdir<2pi (instead of -pi<=realdir<pi)
            if realdir<0:realdir+=2*pi

            topo_dir = input_params[0]['theta'][lineno]+pi/2 # dir that will be given to topographica

            # if realdir & topo_dir aren't the same, it's because
            # c lissom used sign=-1 (& the dirs will be pi apart)

            E=0.05 # (imprecision from getting dir from 1-dp positions)
            if abs(realdir-topo_dir)<E:
                s=1
            elif pi-E<=abs(realdir-topo_dir)<pi+E:
                s=-1
            else:
                assert False # if using speed=0, just replace this line with s=0
                # CEBALERT: should actually handle that case!
            #####

            for i in range(n_eyes):
                input_params[i]['sign'].append(s)

    for i in input_params:
        for val in input_params[i]:
            input_params[i][val] = iter(input_params[i][val])

    return len(lines),input_params



# CEBALERT: this kind of function probably exists somewhere already.

def get_matrix(matrix_file):
    """
    Returns an array containing the data in the specified C++ LISSOM .matrix
    file.

    Ignores lines that start with a hash (#).
    """
    f = open(matrix_file)

    matrix = []

    for line in f.readlines():
        row = []

        if not line.startswith('#'):
            values = line.split()
            for v in values:
                row.append(float(v))
            matrix.append(row)

    # maybe should be setting a typecode of 'f', or maybe they should
    # actually be FixedPoint numbers...
    return array(matrix)



def unsituate(matrix,expected_diameter=None):
    """
    Return the view of matrix that contains all non-zero rows and
    columns (a guess at how to unsituate a weights matrix).

    expected_diameter can be specifed as an optional check.

    ** This function will fail if the weights matrix itself has a
    ** border row or column of zeros (or, less likely, a row or
    ** column of zeros somewhere inside the weights matrix).
    ** Never report that this function is broken: fix it, or
    ** update c++ lissom.

    e.g. for matrix
    0 0 0 0 0.0 0.0 0.0 0.0
    0 0 0 0 0.0 0.1 0.0 0.0
    0.0 0.0 0.1 0.2 0.3 0.0
    0 0 0 0 0.0 0.1 0.0 0.0
    0 0 0 0 0.0 0.0 0.0 0.0

    will return matrix[1:4,2:5] i.e.
    0.0 0.1 0.0
    0.1 0.2 0.3
    0.0 0.1 0.0
    """
    nonzeror,nonzeroc = matrix.nonzero()
    rstart = nonzeror.min()
    rstop = nonzeror.max()+1
    cstart = nonzeroc.min()
    cstop = nonzeroc.max()+1

    if expected_diameter is not None:
        assert ctop-cstart==rstop-rstart==expected_diamater,"situate_c_matrix() couldn't guess how to situate %s"

    return matrix[rstart:rstop,cstart:cstop]


def compare_elements(topo_matrix,lissom_matrix,max_dp=8,name=None):
    """
    Return the smallest number of decimal places to which all
    corresponding elements of a C++ lissom and topographica matrix match.

    max_dp specifies the greatest number of decimal places to try.

    Returns -1 if they don't match to at least 1 decimal place.
    """
    if name is None:
        name = ""
    else:
        name = name+": "
    # CB: this could be a general function, but I doubt anybody would use it.
    # Plus the hackalert below would have to be fixed.
    assert topo_matrix.shape == lissom_matrix.shape, "%stopographica array shape %s, but c++ matrix shape %s"%(name,topo_matrix.shape,lissom_matrix.shape)
    match_at=-1

    for dp in range(1,max_dp+1)[::-1]:
        # CBHACKALERT: aren't lissom_matrix values and topo_matrix values already floats?
        # Seems like whatever I do in get_matrix (e.g. use typecode='f'), unless I do astype(float)
        # here, the comparisons do not work properly.
        if array_almost_equal(topo_matrix.astype(float),lissom_matrix.astype(float),dp):
            match_at = dp
            break

    return match_at



def check_weights(sheet_name,proj_name,unit,slices=None,required_dp=6,display=True):
    """
    Assert that corresponding elements of the C++ lissom and
    Topographica weights of unit in proj_name (which projects into
    sheet_name) match to at least required_dp.

    If required_dp is 0, simply prints the smallest number of decimal
    places to which the two corresponding elements match.

    If specified, slices must be a tuple of slice objects specifying
    where the weights are (C++ lissom does not situate weights in its
    .matrix files; check_weights uses unsituate() to guess, but if
    it's wrong you can override with slices).
    """
    cTIME = "%06d"%long(topo.sim.time())
    cREGION = sheet_name
    cCONN = proj_name
    cUNIT = "%03d_%03d"%unit

    c_matrix_filename=filename_base+cTIME+'.wts.'+cREGION+'.'+cCONN+'.'+cUNIT+'.matrix'
    comparing_what = proj_name + " " + str(unit) + " t=" + str(topo.sim.time())
    dprint("Comparing %s"%comparing_what,display)
    dprint("Reading C++ data from %s"%c_matrix_filename,display)

    topo_weights = topo.sim[sheet_name].projections()[proj_name].cfs[unit].weights
    situated_c_weights = get_matrix(c_matrix_filename)

    if slices is None:
        c_weights = unsituate(situated_c_weights)
    else:
        c_weights = situated_c_weights[slices[0],slices[1]]

    match_dp = compare_elements(topo_weights,c_weights,name=comparing_what)
    dprint("...matched to "+`match_dp`+" d.p.",display)
    # could return comparing_what & dp if that information is to be used for something else

    if required_dp>0:
        assert match_dp>=required_dp, "%s: required match to %s d.p. but got %s d.p."%(comparing_what,required_dp,match_dp)


def check_activities(sheet_name,required_dp=5,display=True):
    """
    Print the smallest number of decimal places to which all
    corresponding elements of the C++ lissom and Topographica
    activities of sheet_name match.
    """
    cTIME = "%06d"%long(topo.sim.time())
    cREGION = sheet_name

    c_matrix_filename=filename_base+cTIME+'p000.'+cREGION+'_Activity.matrix'
    comparing_what = sheet_name + " activity t=" + str(topo.sim.time())
    dprint("Comparing %s"%comparing_what,display)
    dprint("Reading c++ data from %s"%c_matrix_filename,display)

    topo_act = topo.sim[sheet_name].activity
    c_act = get_matrix(c_matrix_filename)

    match_dp = compare_elements(topo_act,c_act,name=comparing_what)
    dprint("...matched to "+`match_dp`+" d.p.",display)
    # could return comparing_what & dp if that information is to be used for something else

    if required_dp>0:
        assert match_dp>=required_dp, "%s: required match to %s d.p. but got %s d.p."%(comparing_what,required_dp,match_dp)



def check_size(sheet_name,proj_name,unit,slices=None,display=True):
    cTIME = "%06d"%long(topo.sim.time())
    cREGION = sheet_name
    cCONN = proj_name
    cUNIT = "%03d_%03d"%unit

    c_matrix_filename=filename_base+cTIME+'.wts.'+cREGION+'.'+cCONN+'.'+cUNIT+'.matrix'
    comparing_what = proj_name + " " + str(unit) + " t=" + str(topo.sim.time())
    dprint("Comparing sizes of %s"%comparing_what,display)
    dprint("Reading C++ data from %s"%c_matrix_filename,display)

    topo_weights = topo.sim[sheet_name].projections()[proj_name].cfs[unit].weights
    situated_c_weights = get_matrix(c_matrix_filename)

    if slices is None:
        c_weights = unsituate(situated_c_weights)
    else:
        c_weights = situated_c_weights[slices[0],slices[1]]

    assert topo_weights.shape == c_weights.shape, "%s: topographica array shape %s, but c++ matrix shape %s"%(comparing_what,topo_weights.shape,c_weights.shape)




def _set_clissom_params(name,out_dir,**kw):
    lines = []
    fname = out_dir+"/%s.param"%name
    f = open(fname,'r')
    for line in f:
        # could we go all the way and try to write
        # the entire params file...?
        if 'set inh_rad' in line:
            line="set inh_rad=%s\n"%kw['inh_rad']
        if 'set BaseRN' in line:
            line="set BaseRN=%s\n"%kw['BaseRN']
        if 'set BaseN' in line:
            line="set BaseN=%s\n"%kw['BaseN']
        if 'set rf_radius' in line:
            line="set rf_radius=%s\n"%kw['rf_radius']
        if 'set exc_rad' in line:
            line="set exc_rad=%s\n"%kw['exc_rad']
        # exc_rad
        lines.append(line)
    f.close()
    f = open(fname,'w')
    f.writelines(lines)
    f.close()



# Command to generate lissom data for comparisons
def _clissomcmd(name):
    check = " -c 'call save_all_units.command' -c 'plot filename_format=$$$${default_filename_format} save_matrices=True' "

    def training_check(t):
        return " -c 'training t+%s' %s"%(t,check)

    def step_check():
        return " -c 'step' %s"%check


    cmd = """./lissom5 display=0 %s.param -c "call set_thresholds.command" -c "ppm_weight_scale_type=PPM_WtScale_Fixed" -c "Region::ppm_weight_fixed_multiplier=1" -c 'PlotGroup::Weights::filename_format="$$$${filebase}.$$$${06iteration}.wts.$$$${current_region}.$$$${current_plot}.$$$${03current_ui}_$$$${03current_uj}"' -c "cmd::ppm_plots=False" -c "cmd::plot_unit::weight_situate=False" """%name

    cmd+=check # 0

    for i in range(1,6): # 5
        cmd+=step_check()

    cmd+=training_check(95) #100

    cmd+=training_check(98) #198

    cmd+=training_check(2) #200

    cmd+=training_check(150) #350

    cmd+=training_check(150) #500

    cmd+=training_check(300) #800

    cmd+=training_check(200) #1000

    for i in range(4): # 5000
        cmd+=training_check(1000)

    cmd+=training_check(1500) #6500

    cmd+=training_check(1500) #8000

    cmd+=training_check(5000) #13000

    cmd+=training_check(3000) #16000

    cmd+=training_check(4000) #20000

    return cmd


import os.path
from param import normalize_path
import glob

def initialize_clissom_data(name,**kw):
    out_dir=normalize_path("topo/tests/reference/%s_BaseN%s_BaseRN%s/"%(name,kw['BaseN'],
                                                                        kw['BaseRN']))
    global filename_base
    filename_base = out_dir+"/%s."%name

    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
        clissom_support_files = glob.glob("topo/tests/reference/support_clissom/*")

        for f in clissom_support_files:
            os.system("cp %s %s"%(f,out_dir))

        os.system("cp topo/tests/reference/%s.param %s"%(name,out_dir))
        cwd = os.getcwd()
        os.chdir(out_dir)
        os.system("gzip -dc lissom5.gz > lissom5")
        os.system("chmod +x %s"%"lissom5")

        _set_clissom_params(name,out_dir,**kw)

        print "------------------------------------------------------------"
        print "Generating c++ lissom results in %s"%out_dir
        c = _clissomcmd(name)
        print c
        os.system(c)
        print "------------------------------------------------------------"
        os.chdir(cwd)
    else:
        print "Skipping c++ lissom data generation: results already exist in %s"%out_dir


