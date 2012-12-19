"""
Distribution class
"""
# To do:
#
# - wrap bins for cyclic histograms
# - check use of float() in count_mag() etc
# - clarify comment about negative selectivity
#
# - function to return value in a range (like a real histogram)
# - cache values
# - assumes cyclic axes start at 0: include a shift based on range
#
# - is there a way to make this work for arrays without mentioning
#   "array" anywhere in here?
# - should this be two classes: one for the core (which would be
#   small though) and another for statistics?



# The basic functions do not have any dependencies, but these imports
# are needed for some of the statistical functions (e.g. vector sum).
import numpy
import param

from math import pi

unavailable_scipy_optimize  = False
try:
    from scipy            import optimize
except ImportError:
    param.Parameterized().debug("scipy.optimize not available, dummy von Mises fit")
    unavailable_scipy_optimize  = True

from numpy            import cos, log
from numpy.oldnumeric import innerproduct, array, exp, argmax

from topo.base.arrayutil import arg, wrap

class Distribution(object):
    """
    Holds a distribution of the values f(x) associated with a variable x.

    A Distribution is a histogram-like object that is a dictionary of
    samples.  Each sample is an x:f(x) pair, where x is called the bin
    and f(x) is called the value(). Each bin's value is typically
    maintained as the sum of all the values that have been placed into
    it.

    The bin axis is continuous, and can represent a continuous
    quantity without discretization.  Alternatively, this class can be
    used as a traditional histogram by either discretizing the bin
    number before adding each sample, or by binning the values in the
    final Distribution.

    Distributions are bounded by the specified axis_bounds, and can
    either be cyclic (like directions or hues) or non-cyclic.  For
    cyclic distributions, samples provided outside the axis_bounds
    will be wrapped back into the bound range, as is appropriate for
    quantities like directions.  For non-cyclic distributions,
    providing samples outside the axis_bounds will result in a
    ValueError.

    In addition to the values, can also return the counts, i.e., the
    number of times that a sample has been added with the given bin.

    Not all instances of this class will be a true distribution in the
    mathematical sense; e.g. the values will have to be normalized
    before they can be considered a probability distribution.

    If keep_peak=True, the value stored in each bin will be the
    maximum of all values ever added, instead of the sum.  The
    distribution will thus be a record of the maximum value
    seen at each bin, also known as an envelope.
    """

    # Holds the number of times that undefined values have been
    # returned from calculations for any instance of this class,
    # e.g. calls to vector_direction() or vector_selectivity() when no
    # value is non-zero.  Useful for warning users when the values are
    # not meaningful.
    undefined_vals  = 0

    def __init__(self, axis_bounds=(0.0, 2*pi), cyclic=False, keep_peak=False):
        self._data = {}
        self._counts = {}

        # total_count and total_value hold the total number and sum
        # (respectively) of values that have ever been provided for
        # each bin.  For a simple distribution these will be the same as
        # sum_counts() and sum_values().
        self.total_count = 0
        self.total_value = 0.0

        self.axis_bounds = axis_bounds
        self.axis_range = axis_bounds[1] - axis_bounds[0]
        self.cyclic = cyclic
        self.keep_peak = keep_peak



    ### JABHACKALERT!  The semantics of this operation are incorrect, because
    ### an expression like x+y should not modify x, while this does.  It could
    ### be renamed __iadd__, to implement += (which has the correct semantics),
    ### but it's not yet clear how to do that.
    def __add__(self,a):
        """
        Allows add() method to be used via the '+' operator; i.e.,
        Distribution + dictionary does Distribution.add(dictionary).
        """
        self.add(a)
        return None


    def get_value(self, bin):
        """
        Return the value of the specified bin.

        (Return None if there is no such bin.)
        """
        return self._data.get(bin)


    def get_count(self, bin):
        """
        Return the count from the specified bin.

        (Return None if there is no such bin.)
        """
        return self._counts.get(bin)


    def values(self):
        """
        Return a list of values.

        Various statistics can then be calculated if desired:

          sum(vals)  (total of all values)
          max(vals)  (highest value in any bin)

        Note that the bin-order of values returned does not necessarily
        match that returned by counts().
        """
        return self._data.values()


    def counts(self):
        """
        Return a list of values.

        Various statistics can then be calculated if desired:

          sum(counts)  (total of all counts)
          max(counts)  (highest count in any bin)

        Note that the bin-order of values returned does not necessarily
        match that returned by values().
        """
        return self._counts.values()


    def bins(self):
        """
        Return a list of bins that have been populated.
        """
        return self._data.keys()


    def add(self, new_data):
        """
        Add a set of new data in the form of a dictionary of (bin,
        value) pairs.  If the bin already exists, the value is added
        to the current value.  If the bin doesn't exist, one is created
        with that value.

        Bin numbers outside axis_bounds are allowed for cyclic=True,
        but otherwise a ValueError is raised.

        If keep_peak=True, the value of the bin is the maximum of the
        current value and the supplied value.  That is, the bin stores
        the peak value seen so far.  Note that each call will increase
        the total_value and total_count (and thus decrease the
        value_mag() and count_mag()) even if the value doesn't happen
        to be the maximum seen so far, since each data point still
        helps improve the sampling and thus the confidence.
        """
        for bin in new_data.keys():

            if self.cyclic==False:
                if not (self.axis_bounds[0] <= bin <= self.axis_bounds[1]):
                    raise ValueError("Bin outside bounds.")
            # CEBALERT: Neet to support wrapping of bin values
            # else:  new_bin = wrap(self.axis_bounds[0], self.axis_bounds[1], bin)
            new_bin = bin

            if new_bin not in self._data:
                self._data[new_bin] = 0.0
                self._counts[new_bin] = 0

            new_value = new_data[bin]
            self.total_value += new_value
            self._counts[new_bin] += 1
            self.total_count += 1

            if self.keep_peak == True:
                if new_value > self._data[new_bin]: self._data[new_bin] = new_value
            else:
                self._data[new_bin] += new_value


    def sub_distr( self, distr ):
        """
        Subtract the given distribution from the current one.
        Only existing bins are modified, new bins in the given
        distribution are discarded without raising errors.

        Note that total_value and total_count are not affected, and
        keep_peak is ignored, therefore analysis relying on these
        values should not call this method.
        """
        for b in distr.bins():
            if b in self.bins():
                v   = distr._data.get( b )
                if v is not None:   self._data[ b ] -= v


    def max_value_bin(self):
        """Return the bin with the largest value."""
        return self._data.keys()[argmax(self._data.values())]

    def weighted_sum(self):
        """Return the sum of each value times its bin."""
        return innerproduct(self._data.keys(), self._data.values())


    def value_mag(self, bin):
        """Return the value of a single bin as a proportion of total_value."""
        return self._safe_divide(self._data.get(bin), self.total_value)


    def count_mag(self, bin):
        """Return the count of a single bin as a proportion of total_count."""
        return self._safe_divide(float(self._counts.get(bin)), float(self.total_count))
        # use of float()


    def _bins_to_radians(self, bin):
        """
        Convert a bin number to a direction in radians.

        Works for NumPy arrays of bin numbers, returning
        an array of directions.
        """
        return (2*pi)*bin/self.axis_range


    def _radians_to_bins(self, direction):
        """
        Convert a direction in radians into a bin number.

        Works for NumPy arrays of direction, returning
        an array of bin numbers.
        """
        return direction*self.axis_range/(2*pi)


    def _safe_divide(self,numerator,denominator):
        """
        Division routine that avoids division-by-zero errors
        (returning zero in such cases) but keeps track of them
        for undefined_values().
        """
        if denominator==0:
            self.undefined_vals += 1
            return 0
        else:
            return numerator/denominator


class Pref( dict ):
    """
    This class simply collects named arguments into a dictionary

    the main purpose is to make pretty readable the output of DistributionStatisticFn
    functions.
    In addition, trap missing keys
    """

    def __init__( self, **args ):
        dict.__init__( self, **args )

    def __getitem__( self, key ):
        try:
            return dict.__getitem__( self, key )
        except KeyError:
            return None



class DistributionStatisticFn( param.Parameterized ):
    """
    Base class for various functions performing statistics on a distribution

    """

    value_scale = param.NumericTuple( (0.0, 1.0), doc="""
            Scaling of the resulting value of the distribution statistics,
            typically the preference of a unit to feature values. The tuple
            specifies (offset, multiplier) of the output scaling""" )

# APNOTE: previously selectivity_scale[ 1 ] used to be 17, a value suitable
# for combining preference and selectivity in HSV plots. Users wishing to keep
# this value should now set it when creating SheetViews, in commands like that
# in command/analysis.py
    selectivity_scale = param.NumericTuple( (0.0, 1.0), doc="""
            Scaling of the resulting measure of the distribution peakedness,
            typically the selectivity of a unit to its preferred feature value.
            The tuple specifies (offset, multiplier) of the output scaling""" )

    __abstract = True

    def __call__(self, distribution):
        """
        Apply the distribution statistic function; must be implemented by subclasses.

        Subclasses sould be called with a Distribution as argument, return will be a
        dictionary, with Pref objects as values
        """
        raise NotImplementedError


class DescriptiveStatisticFn( DistributionStatisticFn ):
    """
    Abstract class for basic descriptive statistics

    """

    def vector_sum(self, d ):
        """
        Return the vector sum of the distribution as a tuple (magnitude, avgbinnum).

        Each bin contributes a vector of length equal to its value, at
        a direction corresponding to the bin number.  Specifically,
        the total bin number range is mapped into a direction range
        [0,2pi].

        For a cyclic distribution, the avgbinnum will be a continuous
        measure analogous to the max_value_bin() of the distribution.
        But this quantity has more precision than max_value_bin()
        because it is computed from the entire distribution instead of
        just the peak bin.  However, it is likely to be useful only
        for uniform or very dense sampling; with sparse, non-uniform
        sampling the estimates will be biased significantly by the
        particular samples chosen.

        The avgbinnum is not meaningful when the magnitude is 0,
        because a zero-length vector has no direction.  To find out
        whether such cases occurred, you can compare the value of
        undefined_vals before and after a series of calls to this
        function.

        """
        # vectors are represented in polar form as complex numbers
        h   = d._data
        r   = h.values()
        theta = d._bins_to_radians(array( h.keys() ))
        v_sum = innerproduct(r, exp(theta*1j))

        magnitude = abs(v_sum)
        direction = arg(v_sum)

        if v_sum == 0:
            d.undefined_vals += 1

        direction_radians = d._radians_to_bins(direction)

        # wrap the direction because arctan2 returns principal values
        wrapped_direction = wrap(d.axis_bounds[0], d.axis_bounds[1], direction_radians)

        return (magnitude, wrapped_direction)


    def _weighted_average(self, d ):
        """
        Return the weighted_sum divided by the sum of the values
        """
        return d._safe_divide(d.weighted_sum(),sum(d._data.values()))


    def selectivity(self, d):
        """
        Return a measure of the peakedness of the distribution.  The
        calculation differs depending on whether this is a cyclic
        variable.  For a cyclic variable, returns the magnitude of the
        vector_sum() divided by the sum_value() (see
        _vector_selectivity for more details).  For a non-cyclic
        variable, returns the max_value_bin()) as a proportion of the
        sum_value() (see _relative_selectivity for more details).
        """
        if d.cyclic == True:
            return self._vector_selectivity( d )
        else:
            return self._relative_selectivity( d )


    # CEBHACKALERT: the definition of selectivity for non-cyclic
    # quantities probably needs some more thought.
    # Additionally, this fails the test in testfeaturemap
    # (see the comment there).
    def _relative_selectivity( self, d ):
        """
        Return max_value_bin()) as a proportion of the sum_value().

        This quantity is a measure of how strongly the distribution is
        biased towards the max_value_bin().  For a smooth,
        single-lobed distribution with an inclusive, non-cyclic range,
        this quantity is an analog to vector_selectivity.  To be a
        precise analog for arbitrary distributions, it would need to
        compute some measure of the selectivity that works like the
        weighted_average() instead of the max_value_bin().  The result
        is scaled such that if all bins are identical, the selectivity
        is 0.0, and if all bins but one are zero, the selectivity is
        1.0.
        """
        # A single bin is considered fully selective (but could also
        # arguably be considered fully unselective)
        if len(d._data) <= 1:
            return 1.0

        proportion = d._safe_divide( max(d._data.values()),
                                        sum(d._data.values()) )
        offset = 1.0/len(d._data)
        scaled = (proportion-offset)/(1.0-offset)

        # negative scaled is possible
        # e.g. 2 bins, with values that sum to less than 0.5
        # this probably isn't what should be done in those cases
        if scaled >= 0.0:
            return scaled
        else:
            return 0.0


    def _vector_selectivity( self, d ):
        """
        Return the magnitude of the vector_sum() divided by the sum_value().

        This quantity is a vector-based measure of the peakedness of
        the distribution.  If only a single bin has a non-zero value(),
        the selectivity will be 1.0, and if all bins have the same
        value() then the selectivity will be 0.0.  Other distributions
        will result in intermediate values.

        For a distribution with a sum_value() of zero (i.e. all bins
        empty), the selectivity is undefined.  Assuming that one will
        usually be looking for high selectivity, we return zero in such
        a case so that high selectivity will not mistakenly be claimed.
        To find out whether such cases occurred, you can compare the
        value of undefined_values() before and after a series of
        calls to this function.
        """
        return d._safe_divide(self.vector_sum( d )[0], sum(d._data.values()))


    __abstract = True



class DescriptiveBimodalStatisticFn( DescriptiveStatisticFn ):
    """
    Abstract class for descriptive statistics of two-modes distributions

    """

    def second_max_value_bin( self, d ):
        """
        Return the bin with the second largest value.
        If there is one bin only, return it. This is not a correct result,
        however it is practical for plotting compatibility, and it will not
        mistakenly be claimed as secondary maximum, by forcing its selectivity
        to 0.0
        """
        h   = d._data
        if len( h ) <= 1:
            return h.keys()[ 0 ]

        k       = self.max_value_bin()
        v       = h.pop(k)
        m       = self.max_value_bin()
        h[ k ]  = v

        return m


    def second_selectivity( self, d ):
        """
        Return the selectivity of the second largest value in the distribution.
        If there is one bin only, the selectivity is 0, since there is no second
        peack at all, and this value is also used to discriminate the validity
        of second_max_value_bin()
        Selectivity is computed in two ways depending on whether the variable is
        a cyclic, as in selectivity()
        """
        if len( d._data ) <= 1:
            return 0.0
        if d.cyclic == True:
            return self._vector_second_selectivity( d )
        else:
            return self._relative_second_selectivity( d )


    def _relative_second_selectivity( self, d ):
        """
        Return the value of the second maximum as a proportion of the sum_value()
        see _relative_selectivity() for further details
        """
        h   = d._data
        k               = d.max_value_bin()
        v               = h.pop(k)
        m               = max( h.values() )
        h[k]   = v

        proportion      = d._safe_divide( m, sum( h.values() ) )
        offset          = 1.0/len(h)
        scaled          = (proportion-offset)/(1.0-offset)

        return max( scaled, 0.0 )


    def _vector_second_selectivity( self, d ):
        """
        Return the magnitude of the vector_sum() of all bins excluding the
        maximum one, divided by the sum_value().
        see _vector_selectivity() for further details
        """
        h   = d._data
        k               = d.max_value_bin()
        v               = h.pop(k)
        s               = d.vector_sum()[0]
        h[k]   = v

        return self._safe_divide( s, sum( h.values() ) )


    def second_peak_bin( self, d ):
        """
        Return the bin with the second peak in the distribution.
        Unlike second_max_value_bin(), it does not return a bin which is the
        second largest value, if laying on a wing of the first peak, the second
        peak is returned only if the distribution is truly multimodal. If it isn't,
        return the first peak (for compatibility with numpy array type, and
        plotting compatibility), however the correspondong selectivity will be
        forced to 0.0
        """
        h   = d._data
        l   = len( h )
        if l <= 1:
            return h.keys()[ 0 ]

        ks  = h.keys()
        ks.sort()
        ik0 = ks.index( h.keys()[ argmax( h.values() ) ] )
        k0  = ks[ ik0 ]
        v0  = h[ k0 ]

        v   = v0
        k   = k0
        ik  = ik0
        while h[ k ] <= v:
            ik  += 1
            if ik >= l:
                ik      = 0
            if ik == ik0:
                return k0
            v   = h[ k ]
            k   = ks[ ik ]
        ik1 = ik

        v   = v0
        k   = k0
        ik  = ik0
        while h[ k ] <= v:
            ik  -= 1
            if ik < 0:
                ik  = l - 1
            if ik == ik0:
                return k0
            v   = h[ k ]
            k   = ks[ ik ]
        ik2 = ik

        if ik1 == ik2:
            return ks[ ik1 ]

        ik  = ik1
        m   = 0
        while ik != ik2:
            k   = ks[ ik ]
            if h[ k ] > m:
                m   = h[ k ]
                im  = ik
            ik  += 1
            if ik >= l:
                ik  = 0

        return ks[ im ]


    def second_peak_selectivity( self, d ):
        """
        Return the selectivity of the second peak in the distribution.

        If the distribution has only one peak, return 0.0, and this value is
        also usefl to discriminate the validity of second_peak_bin()
        """
        h   = d._data
        if len( h ) <= 1:
            return 0.0

        p1  = d.max_value_bin()
        p2  = self.second_peak_bin( d )
        if p1 == p2:
            return 0.0

        m           = h[ p2 ]
        proportion  = d._safe_divide( m, sum( h.values() ) )
        offset      = 1.0 / len( h )
        scaled      = (proportion - offset) / (1.0 - offset)

        return max( scaled, 0.0 )


    def second_peak( self, d ):
        """
        Return preference and selectivity of the second peak in the distribution.

        It is just the combination of second_peak_bin() and
        second_peak_selectivity(), with the advantage of avoiding a duplicate
        call of second_peak_bin(), if the user is interested in both preference
        and selectivity, as often is the case.
        """
        h   = d._data
        if len( h ) <= 1:
            return ( h.keys()[ 0 ], 0.0 )

        p1  = d.max_value_bin()
        p2  = self.second_peak_bin( d )
        if p1 == p2:
            return ( p1, 0.0 )

        m           = h[ p2 ]
        proportion  = d._safe_divide( m, sum( h.values() ) )
        offset      = 1.0 / len( h )
        scaled      = (proportion - offset) / (1.0 - offset)

        return ( p2, max( scaled, 0.0 ) )


    __abstract = True



class DSF_MaxValue( DescriptiveStatisticFn ):
    """
    Return the peak value of the given distribution

    """

    def __call__( self, d ):
        p   = self.value_scale[ 1 ] * ( d.max_value_bin() + self.value_scale[ 0 ] )
        s   = self.selectivity_scale[ 1 ] * ( self.selectivity( d ) + self.selectivity_scale[ 0 ] )

        return { "": Pref( preference=p, selectivity=s ) }



class DSF_WeightedAverage( DescriptiveStatisticFn ):
    """
    Return the main mode of the given distribution

    The prefence value ia a continuous, interpolated equivalent of the max_value_bin().
    For a cyclic distribution, this is the direction of the vector
    sum (see vector_sum()).
    For a non-cyclic distribution, this is the arithmetic average
    of the data on the bin_axis, where each bin is weighted by its
    value.
    Such a computation will generally produce much more precise maps using
    fewer test stimuli than the discrete method.  However, weighted_average
    methods generally require uniform and full-range sampling, which is not
    always feasible.
    For measurements at evenly-spaced intervals over the full range of
    possible parameter values, weighted_averages are a good measure of the
    underlying continuous-valued parameter preference, assuming that neurons
    are tuned broadly enough (and/or sampled finely enough) that they
    respond to at least two of the tested parameter values.  This method
    will not usually give good results when those criteria are not met, i.e.
    if the sampling is too sparse, not at evenly-spaced intervals, or does
    not cover the full range of possible values.  In such cases
    max_value_bin should be used, and the number of test patterns will
    usually need to be increased instead.

    """

    def __call__( self, d ):
        p   = self.vector_sum( d )[1]  if d.cyclic  else self._weighted_average( d )
        p   = self.value_scale[ 1 ] * ( p + self.value_scale[ 0 ] )
        s   = self.selectivity_scale[ 1 ] * ( self.selectivity( d ) + self.selectivity_scale[ 0 ] )

        return { "": Pref( preference=p, selectivity=s ) }



class DSF_TopTwoValues( DescriptiveBimodalStatisticFn ):
    """
    Return the two max values of distributions in the given matrix

    """

    def __call__( self, d ):
        r               = {}
        p               = self.value_scale[ 1 ] * ( d.max_value_bin() + self.value_scale[ 0 ] )
        s               = self.selectivity_scale[ 1 ] * ( self.selectivity( d ) + self.selectivity_scale[ 0 ] )
        r[ "" ]         = Pref( preference=p, selectivity=s )
        p               = self.second_max_value_bin( d )
        s               = self.second_selectivity( d )
        p               = self.value_scale[ 1 ] * ( p + self.value_scale[ 0 ] )
        s               = self.selectivity_scale[ 1 ] * ( s + self.selectivity_scale[ 0 ] )
        r[ "Mode2" ]    = Pref( preference=p, selectivity=s )

        return r



class DSF_BimodalPeaks( DescriptiveBimodalStatisticFn ):
    """
    Return the two peak values of distributions in the given matrix

    """

    def __call__( self, d ):
        r               = {}
        p               = self.value_scale[ 1 ] * ( d.max_value_bin() + self.value_scale[ 0 ] )
        s               = self.selectivity_scale[ 1 ] * ( self.selectivity( d ) + self.selectivity_scale[ 0 ] )
        r[ "" ]         = Pref( preference=p, selectivity=s )
        p, s            = self.second_peak( d )
        p               = self.value_scale[ 1 ] * ( p + self.value_scale[ 0 ] )
        s               = self.selectivity_scale[ 1 ] * ( s + self.selectivity_scale[ 0 ] )
        r[ "Mode2" ]    = Pref( preference=p, selectivity=s )

        return r



class VonMisesStatisticFn( DistributionStatisticFn ):
    """
    Base class for von Mises statistics

    """

    # values to fit the maximum value of k parameter in von Mises distribution,
    # as a function of the number of bins in the distribution. Useful for
    # keeping selectivity in range 0..1. Values derived offline from distribution
    # with a single active bin, and total bins from 8 to 32
    vm_kappa_fit    = ( 0.206, 0.614 )

    # level of activity in units confoundable with noise. Used in von Mises fit,
    # for two purposes: if the standard deviation of a distribution is below this
    # value, the distribution is assumed to lack any mode; it is the maximum level
    # of random noise added to a distribution before the fit optimization, for
    # stability reasons
    noise_level     = 0.001

    # exit code of the distribution fit function. Codes are function-specific and
    # each fit function, if provide exit codes, should have corresponding string translation
    fit_exit_code   = 0

    user_warned_if_unavailable = False

    __abstract = True

    def _orth( self, t ):
        """
        Return the orthogonal orientation
        """
        if t < 0.5 * pi:
            return t + 0.5 * pi
        return t - 0.5 * pi


    def _in_pi( self, t ):
        """
        Reduce orientation from -pi..2pi to 0..pi
        """
        if t > pi:
            return t - pi
        if t < 0:
            return t + pi
        return t


    def von_mises( self, pars, x ):
        """
        Compute a simplified von Mises function.

        Original formulation in Richard von Mises, "Wahrscheinlichkeitsrechnung
        und ihre Anwendungen in der Statistik und theoretischen Physik", 1931,
        Deuticke, Leipzig; see also Mardia, K.V. and Jupp, P.E., " Directional
        Statistics", 1999, J. Wiley, p.36;
        http://en.wikipedia.org/wiki/Von_Mises_distribution
        The two differences are that this function is a continuous probability
        distribution on a semi-circle, while von Mises is on the full circle,
        and that the normalization factor, which is the inverse of the modified
        Bessel function of first kind and 0 degree in the original, is here a fit parameter.
        """
        a, k, t = pars
        return a * exp( k * ( cos( 2 * ( x - t ) ) - 1 ) )

    def von2_mises( self, pars, x ):
        """
        Compute a simplified bimodal von Mises function

        Two superposed von Mises functions, with different peak and bandwith values
        """
        p1  = pars[ : 3 ]
        p2  = pars[ 3 : ]
        return self.von_mises( p1, x ) + self.von_mises( p2, x )

    def von_mises_res( self, pars, x, y ):
        return y - self.von_mises( pars, x )

    def von2_mises_res( self, pars, x, y ):
        return y - self.von2_mises( pars, x )

    def norm_sel( self, k, n ):
        m   = ( self.vm_kappa_fit[ 0 ] + n * self.vm_kappa_fit[ 1 ] ) ** 2
        return log( 1 + k ) / log( 1 + m )

    def fit_vm( self, distribution ):
        """
        computes the best fit of the monovariate von Mises function in the
        semi-circle.
        Return a tuple with the orientation preference, in the same range of
        axis_bounds, the orientation selectivity, and an estimate of the
        goodness-of-fit, as the variance of the predicted orientation
        preference. The selectivity is given by the bandwith parameter of the
        von Mises function, modified for compatibility with other selectivity
        computations in this class. The bandwith parameter is transposed in
        logaritmic scale, and is normalized by the maximum value for the number
        of bins in the distribution, in order to give roughly 1.0 for a
        distribution with one bin at 1.0 an all the other at 0.0, and 0.0 for
        uniform distributions. The normalizing factor of the selectivity is fit
        for the total number of bins, using fit parameters computed offline.
        There are conditions that prevents apriori the possibility to fit the
        distribution:
            * not enough bins, at least 4 are necessary
            * the distribution is too flat, below the noise level
        and conditions of aposteriori failures:
            * "ier" flag returned by leastsq out of ( 1, 2, 3, 4 )
            * no estimated Jacobian around the solution
            * negative bandwith (the peak of the distribution is convex)
        Note that these are the minimal conditions, their fulfillment does not
        warrant unimodality, is up to the user to check the goodness-of-fit value
        for an accurate acceptance of the fit.
        """
        if unavailable_scipy_optimize:
            if not VonMisesStatisticFn.user_warned_if_unavailable:
                param.Parameterized().warning("scipy.optimize not available, dummy von Mises fit")
                VonMisesStatisticFn.user_warned_if_unavailable=True
            self.fit_exit_code  = 3
            return 0, 0, 0

        to_pi   = pi / distribution.axis_range
        x       = to_pi * numpy.array( distribution.bins() )
        n       = len( x )
        if n < 5:
            param.Parameterized().warning( "no von Mises fit possible with less than 4 bins" )
            self.fit_exit_code  = -1
            return 0, 0, 0

        y   = numpy.array( distribution.values() )
        if y.std() < self.noise_level:
            self.fit_exit_code  = 1
            return 0, 0, 0

        rn  = self.noise_level * numpy.random.random_sample( y.shape )
        p0  = ( 1.0, 1.0, distribution.max_value_bin() )
        r   = optimize.leastsq( self.von_mises_res, p0, args = ( x, y + rn ), full_output = True )

        if not r[ -1 ] in ( 1, 2, 3, 4 ):
            self.fit_exit_code  = 100 + r[ -1 ]
            return 0, 0, 0

        residuals   = r[ 2 ][ 'fvec' ]
        jacobian    = r[ 1 ]
        bandwith    = r[ 0 ][ 1 ]
        tuning      = r[ 0 ][ 2 ]

        if bandwith < 0:
            self.fit_exit_code  = 1
            return 0, 0, 0

        if jacobian is None:
            self.fit_exit_code  = 2
            return 0, 0, 0

        error       = ( residuals ** 2 ).sum() / ( n - len( p0 ) )
        covariance  = jacobian * error
        g   = covariance[ 2, 2 ]
        p   = self._in_pi( tuning ) / to_pi
        s   = self.norm_sel( bandwith, n )
        self.fit_exit_code  = 0
        return p, s, g

    def vm_fit_exit_codes ( self ):
        if self.fit_exit_code == 0:
            return "succesfull exit"
        if self.fit_exit_code == -1:
            return "not enough bins for this fit"
        if self.fit_exit_code == 1:
            return "flat distribution"
        if self.fit_exit_code == 2:
            return "flat distribution"
        if self.fit_exit_code == 3:
            return "missing scipy.optimize import"
        if self.fit_exit_code > 110:
            return "unknown exit code"
        if self.fit_exit_code > 100:
            return "error " + str( self.fit_exit_code - 100 ) + " in scipy.optimize.leastsq"

        return "unknown exit code"


    def fit_v2m( self, distribution ):
        """
        computes the best fit of the bivariate von Mises function in the
        semi-circle.
        Return the tuple:
        (
            orientation1_preference, orientation1_selectivity, goodness_of_fit1,
            orientation2_preference, orientation2_selectivity, goodness_of_fit2
        )
        See fit_vm() for considerations about selectivity and goodness_of_fit
        """
        null    = 0, 0, 0, 0, 0, 0
        if unavailable_scipy_optimize:
            if not VonMisesStatisticFn.user_warned_if_unavailable:
                param.Parameterized().warning("scipy.optimize not available, dummy von Mises fit")
                VonMisesStatisticFn.user_warned_if_unavailable=True
            self.fit_exit_code  = 3
            return null

        to_pi   = pi / distribution.axis_range
        x       = to_pi * numpy.array( distribution.bins() )
        n       = len( x )
        if n < 9:
            param.Parameterized().warning( "no bimodal von Mises fit possible with less than 8 bins" )
            self.fit_exit_code  = -1
            return null
        y       = numpy.array( distribution.values() )
        if y.std() < self.noise_level:
            self.fit_exit_code  = 1
            return null

        rn  = self.noise_level * numpy.random.random_sample( y.shape )
        t0  = distribution.max_value_bin()
        p0  = ( 1.0, 1.0, t0, 1.0, 1.0, self._orth( t0 ) )
        r   = optimize.leastsq( self.von2_mises_res, p0, args = ( x, y + rn ), full_output = True )
        if not r[ -1 ] in ( 1, 2, 3, 4 ):
            self.fit_exit_code  = 100 + r[ -1 ]
            return null
        residuals   = r[ 2 ][ 'fvec' ]
        jacobian    = r[ 1 ]
        bandwith_1  = r[ 0 ][ 1 ]
        tuning_1    = r[ 0 ][ 2 ]
        bandwith_2  = r[ 0 ][ 4 ]
        tuning_2    = r[ 0 ][ 5 ]
        if jacobian is None:
            self.fit_exit_code  = 2
            return null
        if bandwith_1 < 0:
            self.fit_exit_code  = 1
            return null
        if bandwith_2 < 0:
            self.fit_exit_code  = 1
            return null

        error       = ( residuals ** 2 ).sum() / ( n - len( p0 ) )
        covariance  = jacobian * error
        g1  = covariance[ 2, 2 ]
        g2  = covariance[ 5, 5 ]
        p1  = self._in_pi( tuning_1 ) / to_pi
        p2  = self._in_pi( tuning_2 ) / to_pi
        s1  = self.norm_sel( bandwith_1, n )
        s2  = self.norm_sel( bandwith_2, n )
        self.fit_exit_code  = 0
        return p1, s1, g1, p2, s2, g2

    def __call__(self,  distribution):
        """
        Apply the distribution statistic function; must be implemented by subclasses.

        """
        raise NotImplementedError



class DSF_VonMisesFit( VonMisesStatisticFn ):
    """
    Return the main mode of distribution in the given matrix, by fit with von Mises function

    """

    worst_fit   = param.Number( default=0.5, bounds=(0.0,None), softbounds=(0.0,1.0), doc="""
            worst good-of-fitness value for accepting the distribution as monomodal""" )

    # default result in case of failure of the fit
    null_result = { "": Pref( preference=0, selectivity=0, goodness_of_fit=0 ), "Modes": Pref( number=0 ) }

    def __call__( self, distribution ):
        f   = self.fit_vm( distribution )
        if self.fit_exit_code != 0 or f[ -1 ] > self.worst_fit:
            return self.null_result
        results             = {}
        p, s, g             = f
        p                   = self.value_scale[ 1 ] * ( p + self.value_scale[ 0 ] )
        s                   = self.selectivity_scale[ 1 ] * ( s + self.selectivity_scale[ 0 ] )
        results[ "" ]       = Pref( preference=p, selectivity=s, goodness_of_fit=g )
        results[ "Modes" ]  = Pref( number=1 )

        return results


class DSF_BimodalVonMisesFit( VonMisesStatisticFn ):
    """
    Return the two modes of distributions in the given matrix, by fit with von Mises function

    The results of the main mode are available in
    self.{preference,selectivity,good_of_fit}, while the second mode results are
    in the first element of the self.more_modes list, as a dictionary with keys
    preference,selectivity,good_of_fit.
    """

    worst_fit   = param.Number( default=0.5, bounds=(0.0,None), softbounds=(0.0,1.0), doc="""
            worst good-of-fitness value for accepting the distribution as mono- or bi-modal""" )

    # default result in case of failure of the fit
    null_result = {
        "":         Pref( preference=0, selectivity=0, goodness_of_fit=0 ),
        "Mode2":    Pref( preference=0, selectivity=0, goodness_of_fit=0 ),
        "Modes":    Pref( number=0 )
    }

    def _analyze_distr( self, d ):
        """
        Analyze the given distribution with von Mises bimodal fit.

        The distribution is analyzed with both unimodal and bimodal fits, and a
        decision about the number of modes is made by comparing the goodness of
        fit. It is a quick but inaccurate way of estimating the number of modes.
        Return preference, selectivity, goodness of fit for both modes, and the
        estimated numer of modes, None if even the unimodal fit failed. If the
        distribution is unimodal, values of the second mode are set to 0. The main
        mode is always the one with the largest selectivity (von Mises bandwith).
        """
        no1 = False
        f   = self.fit_vm( d )
        if self.fit_exit_code != 0:
            no1 = True
        p, s, g = f
        f2  = self.fit_v2m( d )
        if self.fit_exit_code != 0 or f2[ 2 ] > self.worst_fit:
            if no1 or f[ -1 ] > self.worst_fit:
                return None
            return p, s, g, 0, 0, 0, 1
        p1, s1, g1, p2, s2, g2  = f2
        if g1 > g:
            return p, s, g, 0, 0, 0, 1

        if s2 > s1:
            return p2, s2, g2, p1, s1, g1, 2

        return p1, s1, g1, p2, s2, g2, 2


    def __call__( self, distribution ):
        f   = self._analyze_distr( distribution )
        if f is None:
            return self.null_result

        results             = {}
        p, s, g             = f[ : 3 ]
        p                   = self.value_scale[ 1 ] * ( p + self.value_scale[ 0 ] )
        s                   = self.selectivity_scale[ 1 ] * ( s + self.selectivity_scale[ 0 ] )
        results[ "" ]       = Pref( preference=p, selectivity=s, goodness_of_fit=g )
        p, s, g, n          = f[ 3 : ]
        p                   = self.value_scale[ 1 ] * ( p + self.value_scale[ 0 ] )
        s                   = self.selectivity_scale[ 1 ] * ( s + self.selectivity_scale[ 0 ] )
        results[ "Mode2" ]  = Pref( preference=p, selectivity=s, goodness_of_fit=g )
        results[ "Modes" ]  = Pref( number=n )

        return results



