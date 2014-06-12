"""
General utility functions and classes.
"""

import re
import random
import numpy
import functools



def NxN(tuple):
    """
    Converts a tuple (X1,X2,...,Xn) to a string 'X1xX2x...xXn'
    """
    return 'x'.join([`N` for N in tuple])



enum = enumerate


class Struct:
    """
    A simple structure class, taking keyword args and assigning them to attributes.

    For instance:

    >>> s = Struct(foo='a',bar=1)
    >>> s.foo
    'a'
    >>> s.bar
    1


    From http://www.norvig.com/python-iaq.html
    """
    def __init__(self, **entries): self.__dict__.update(entries)

    def __repr__(self):
        #
        args = ['%s=%s' % (k, repr(v)) for (k,v) in vars(self).items()]
        return 'Struct(%s)' % ', '.join(args)



def flat_indices(shape):
    """
    Returns a list of the indices needed to address or loop over all
    the elements of a 1D or 2D matrix with the given shape. E.g.:

    flat_indices((3,)) == [0,1,2]
    """
    if len(shape) == 1:
        return [(x,) for x in range(shape[0])]
    else:
        rows,cols = shape
        return [(r,c) for r in range(rows) for c in range(cols)]



def flatten(l):
    """
    Flattens a list.

    Written by Bearophile as published on the www.python.org newsgroups.
    Pulled into Topographica 3/5/2005.
    """
    if type(l) != list:
        return l
    else:
        result = []
        stack = []
        stack.append((l,0))
        while len(stack) != 0:
            sequence, j = stack.pop(-1)
            while j < len(sequence):
                if type(sequence[j]) != list:
                    k, j = j, j+1
                    while j < len(sequence) and \
                          (type(sequence[j]) != list):
                        j += 1
                    result.extend(sequence[k:j])
                else:
                    stack.append((sequence, j+1))
                    sequence, j = sequence[j], 0
        return result



"""
Return the cross-product of a variable number of lists (e.g. of a list of lists).

Use to obtain permutations, e.g.
l1=[a,b]
l2=[c,d]
cross_product([l1,l2]) =
[[a,c], [a,d], [b,c], [b,d]]


From:
http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/159975
"""
# Need to re-write so someone other than Python knows what might happen when this runs
cross_product=lambda ss,row=[],level=0: len(ss)>1 \
   and reduce(lambda x,y:x+y,[cross_product(ss[1:],row+[i],level+1) for i in ss[0]]) \
   or [row+[i] for i in ss[0]]



# JABALERT: Should frange be replaced with numpy.arange or numpy.linspace?
def frange(start, end=None, inc=1.0, inclusive=False):
    """
    A range function that accepts float increments.

    Otherwise, works just as the inbuilt range() function.  If
    inclusive is False, as in the default, the range is exclusive (not
    including the end value), as in the inbuilt range(). If inclusive
    is true, the range may include the end value.

    'All theoretic restrictions apply, but in practice this is
    more useful than in theory.'

    From: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66472
    """
    if end == None:
        end = start + 0.0
        start = 0.0

    # Increments of zero would lead to an infinite loop, which can happen if
    # this is mistakenly called with a integer-based rational expression like 1/2.
    assert ((inc>0 and start<=end) or (inc<0 and start>=end))

    L = []
    while 1:
        next = start + len(L) * inc
        if inclusive:
          if inc > 0 and next > end: break
          elif inc < 0 and next < end: break
        else:
          if inc > 0 and next >= end: break
          elif inc < 0 and next <= end: break
        L.append(next)

    return L



def shortclassname(x):
    """
    Returns the class name of x as a string with the leading package information removed.

    E.g. if x is of type "<class 'topo.base.sheet.Sheet'>", returns
    "Sheet"
    """
    return re.sub("'>","",re.sub(".*[.]","",repr(type(x))))



def profile(command,n=50,sorting=('cumulative','time'),strip_dirs=False):
    """
    Profile the given command (supplied as a string), printing
    statistics about the top n functions when ordered according to
    sorting.

    sorting defaults to ordering by cumulative time and then internal
    time; see http://docs.python.org/lib/profile-stats.html for other
    sorting options.

    By default, the complete paths of files are not shown. If there
    are multiple files with the same name, you might wish to set
    strip_dirs=False to make it easier to follow the output.


    Examples:

    - profile loading a simulation:
    profile('execfile("examples/hierarchical.ty")')

    - profile running an already loaded simulation:
    profile('topo.sim.run(10)')

    - profile running a whole simulation:
    profile('execfile("examples/lissom_oo_or.ty");topo.sim.run(20000)')

    - profile running a simulation, but from the commandline:
    ./topographica examples/hierarchical.ty -c "from topo.misc.util import profile; profile('topo.sim.run(10)')"
    """
    # This function simply wraps some functions from the cProfile
    # module, making profiling easier.
    import cProfile, pstats


    # CB: leaves around "filename": should give this a proper name and maybe
    # put in /tmp/ and maybe allow someone to choose where to save it
    cProfile.run(command,'filename')
    prof_stats = pstats.Stats('filename')

    if strip_dirs:prof_stats.strip_dirs()

    prof_stats.sort_stats(*sorting).print_callees(n)
    ### the above lets us see which times are due to which calls
    ### unambiguously, while the version below only reports total time
    ### spent in each object, not the time due to that particular
    ### call.
    prof_stats.sort_stats(*sorting).print_stats(n)




def weighted_sample(seq,weights=[]):
    """
    Select randomly from the given sequence.

    The weights, if given, should be a sequence the same length as
    seq, as would be passed to weighted_sample_idx().
    """
    if not weights:
        return seq[random.randrange(len(seq))]
    else:
        assert len(weights) == len(seq)
        return seq[weighted_sample_idx(weights)]


def weighted_sample_idx(weights):
    """
    Return an integer generated by sampling the discrete distribution
    represented by the sequence of weights.

    The integer will be in the range [0,len(weights)).  The weights
    need not sum to unity, but can contain any non-negative values
    (e.g., [1 1 1 100] is a valid set of weights).

    To use weights from a 2D numpy array w, specify w.ravel() (not the
    w.flat iterator).
    """
    total = sum(weights)
    if total == 0:
        return random.randrange(len(weights))
    index = random.random() * total
    accum = 0
    for i,x in enumerate(weights):
        accum += x
        if index < accum:
            return i


def idx2rowcol(idx,shape):
    """
    Given a flat matrix index and a 2D matrix shape, return the (row,col)
    coordinates of the index.
    """
    assert len(shape) == 2
    rows,cols = shape

    return idx/cols,idx%cols



def rowcol2idx(r,c,shape):
    """
    Given a row, column, and matrix shape, return the corresponding index
    into the flattened (raveled) matrix.
    """
    assert len(shape) == 2
    rows,cols = shape

    return r * cols + c



def centroid(pts,weights):
    """
    Return the centroid of a weighted set of points as an array.

    The pts argument should be an array of points, one per row,
    and weights should be a vector of weights.
    """
    # CEBALERT: use numpy.sum? Worthwhile if weights is a numpy.array.
    return numpy.dot(numpy.transpose(pts),weights)/sum(weights)



def signabs(x):
    """
    Split x into its sign and absolute value.

    Returns a tuple (sign(x),abs(x)).  Note: sign(0) = 1, unlike
    numpy.sign.
    """

    if x < 0:
        sgn = -1
    else:
        sgn = 1

    return sgn,abs(x)


def linearly_interpolate(table,value):
    """
    Interpolate an appropriate value from the given list of values, by number.

    Assumes the table is a list of items to be returned for integer values,
    and interpolates between those items for non-integer values.
    """

    lower_index=int(value)
    upper_index=lower_index+1

    # Intermediate value; interpolate or return exact value as appropriate
    if lower_index+1<len(table):
       lookup=table[lower_index]+(value%1.0)*(table[upper_index]-table[lower_index])

    # Upper bound -- return largest value
    elif lower_index+1==len(table):
       lookup=table[len(table)-1]

    # Over upper bound -- return largest value and print warning
    # JABALERT: Printing a warning message is not necessarily the most
    # useful behavior. Should at least provide some identification of
    # where the warning is coming from. Should add bounds_error and/or
    # bounds_warn options. (Could turn into a ParameterizedFunction so
    # that any message includes an identification, and so that
    # warnings-as-errors will work.) Would be nice if we could use the
    # equivalent function from scipy, but we can't yet depend on scipy
    # being available.
    else:
       lookup=table[len(table)-1]
       print "Warning -- value %f out of range; returning maximum of %f" % (value,lookup)

    return lookup



# CB: note that this has only really been tested for output;
# I've never tried using it to e.g. read multiple files.
class MultiFile(object):
    """
    For all file_like_objs passed on initialization, provides a
    convenient way to call any of file's methods (on all of them).

    E.g. The following would cause 'test' to be written into two
    files, as well as to stdout:

    import sys
    f1 = open('file1','w')
    f2 = open('file2','w')
    m = MultiFile(f1,f2,sys.stdout)
    m.write('test')
    """
    def __init__(self,*file_like_objs):
        self.file_like_objs=file_like_objs
        self.__provide_file_methods()

    def __provide_file_methods(self):
        # Provide a version of all the methods of the type file that
        # don't start with '_'. In each case, the provided version
        # loops over all the file_like_objs, calling the file method
        # on all of them.
        file_methods = [attr for attr in file.__dict__
                        if not attr.startswith('_')
                        and callable(file.__dict__[attr])]

        for method in file_methods:
            def looped_method(method_,*args,**kw):
                all_out = []
                for output in self.file_like_objs:
                    out = getattr(output,method_)(*args,**kw)
                    all_out.append(out)
                return all_out

            setattr(self,method,functools.partial(looped_method,method))




# CEBALERT: should be moved to legacy, once that file is reorganized
# so that classes can be imported from it relatively independently,
# without requiring all the legacy functions to be loaded.
# (Right now, topo.__init__ can't import gmpyFaker from
# topo.misc.legacy because importing topo.misc.legacy causes various
# pieces of code to run that depend on topo.sim existing.)

############################################################
# Alternative module faking using import hooks (see
# http://www.python.org/dev/peps/pep-0302/).
# Based on http://orestis.gr/blog/2008/12/20/python-import-hooks/.
import sys,imp
class ModuleFaker(object):
    def load_module(self,name):
        if name not in sys.modules:
            module = self.create_module(name)
            module.__file__ = self.path
            sys.modules[name] = module
            if '.' in name:
                parent_name, child_name = name.rsplit('.', 1)
                setattr(sys.modules[parent_name], child_name, module)
        return sys.modules[name]

    def create_module(self,name):
        raise NotImplementedError

class ModuleImporter(object):
    def find_module(self,fullname,path=None):
        raise NotImplementedError

class gmpyFaker(ModuleFaker):
    def create_module(self,name):
        module = imp.new_module(name)
        # CEBALERT: not sure what precision should be used for FixedPoint to
        # replace rational. Should we set the precision really high?
        code = \
"""
from __future__ import division
import topo.misc.fixedpoint as fixedpoint
import param
class mpq(object):
    def __new__(self,*args,**kw):
        n = fixedpoint.FixedPoint(eval(str(args[0])),precision=4)
        param.Parameterized().warning("gmpy.mpq('%s') replaced by fixedpoint.FixedPoint('%s')"%(args[0],n))
        return n
"""
        exec code in module.__dict__
        return module

class gmpyImporter(ModuleImporter):

    def find_module(self, fullname, path=None):
        if fullname == 'gmpy' or fullname.startswith('gmpy.'):
            import param
            param.Parameterized().warning('Module "gmpy" is not available. gmpy.mpq is provided by using fixedpoint.FixedPoint.')
            g = gmpyFaker()
            g.path = path
            return g
        return None


def unit_value(str):
    m = re.match(r'([^\d]*)(\d*\.?\d+)([^\d]*)', str)
    if m:
        g = m.groups()
        return ' '.join((g[0], g[2])).strip(), float(g[1])
    else:
        return int(str)
