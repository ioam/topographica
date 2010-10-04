"""
Distribution class

$Id$
"""
__version__='$Revision$'
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
from math import pi

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
    undefined_vals = 0 

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
               

    def max_value_bin(self):
        """Return the bin with the largest value."""
        return self._data.keys()[argmax(self._data.values())]


    def second_max_value_bin(self):
        """
	Return the bin with the second largest value.
	If there is one bin only, return it. This is not a correct result,
	however it is practical for plotting compatibility, and it will not
	mistakenly be claimed as secondary maximum, by forcing its selectivity
	to 0.0
	"""
        if len(self._data) <= 1: 
            return self._data.keys()[ 0 ]

	k		= self.max_value_bin()
	v		= self._data.pop(k)
	m		= self.max_value_bin()
	self._data[k]	= v

        return m


    def second_peak_bin(self):
        """
	Return the bin with the second peak in the distribution.
	Unlike second_max_value_bin(), it does not return a bin which is the
	second largest value, if laying on a wing of the first peak, the second
	peak is returned only if the distribution is truly multimodal. If it isn't,
	return the first peak (for compatibility with numpy array type, and
	plotting compatibility), however the correspondong selectivity will be
	forced to 0.0
	"""
	l	= len( self._data )
        if l <= 1: 
            return self._data.keys()[ 0 ]

	ks	= self._data.keys()
	ks.sort()
	ik0	= ks.index( self._data.keys()[ argmax( self._data.values() ) ] )
	k0	= ks[ ik0 ]
	v0	= self._data[ k0 ]

	v	= v0
	k	= k0
	ik	= ik0
	while self._data[ k ] <= v:
		ik	+= 1
		if ik >= l:
			ik	= 0
		if ik == ik0:
			return k0
		v	= self._data[ k ]
		k	= ks[ ik ]
	ik1	= ik

	v	= v0
	k	= k0
	ik	= ik0
	while self._data[ k ] <= v:
		ik	-= 1
		if ik < 0:
			ik	= l - 1
		if ik == ik0:
			return k0
		v	= self._data[ k ]
		k	= ks[ ik ]
	ik2	= ik

	if ik1 == ik2:
		return ks[ ik1 ]

	ik	= ik1
	m	= 0
	while ik != ik2:
		k	= ks[ ik ]
		if self._data[ k ] > m:
			m	= self._data[ k ]
			im	= ik
		ik	+= 1
		if ik >= l:
			ik	= 0
	
	return ks[ im ]


    def weighted_average(self):
        """
        Return a continuous, interpolated equivalent of the max_value_bin().
        
        For a cyclic distribution, this is the direction of the vector
        sum (see vector_sum()).

        For a non-cyclic distribution, this is the arithmetic average
        of the data on the bin_axis, where each bin is weighted by its
        value.
        """
        if self.cyclic == True:
            return self.vector_sum()[1]
        else:
            return self._weighted_average()


    def vector_sum(self):
        """
        Return the vector sum of the data as a tuple (magnitude, avgbinnum).

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
        r = self._data.values()                                  
        theta = self._bins_to_radians(array(self._data.keys()))
        v_sum = innerproduct(r, exp(theta*1j))                  

        magnitude = abs(v_sum)
        direction = arg(v_sum)

        if v_sum == 0:
            self.undefined_vals += 1

        direction_radians = self._radians_to_bins(direction)

        # wrap the direction because arctan2 returns principal values
        wrapped_direction = wrap(self.axis_bounds[0], self.axis_bounds[1], direction_radians)
        
        return (magnitude, wrapped_direction) 


    def weighted_sum(self):
        """Return the sum of each value times its bin."""
        return innerproduct(self._data.keys(), self._data.values()) 


    def _weighted_average(self):
        """
        Return the weighted_sum divided by the sum of the values
        """
        return self._safe_divide(self.weighted_sum(),sum(self._data.values())) 


    def selectivity(self):
        """
        Return a measure of the peakedness of the distribution.  The
        calculation differs depending on whether this is a cyclic
        variable.  For a cyclic variable, returns the magnitude of the
        vector_sum() divided by the sum_value() (see
        _vector_selectivity for more details).  For a non-cyclic
        variable, returns the max_value_bin()) as a proportion of the
        sum_value() (see _relative_selectivity for more details).
        """
        if self.cyclic == True:
            return self._vector_selectivity()
        else:
            return self._relative_selectivity()


    # CEBHACKALERT: the definition of selectivity for non-cyclic
    # quantities probably needs some more thought.
    # Additionally, this fails the test in testfeaturemap
    # (see the comment there).
    def _relative_selectivity(self):
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
        if len(self._data) <= 1: 
            return 1.0

        proportion = self._safe_divide( max(self._data.values()),
                                        sum(self._data.values()) )
        offset = 1.0/len(self._data)
        scaled = (proportion-offset)/(1.0-offset)

        # negative scaled is possible 
        # e.g. 2 bins, with values that sum to less than 0.5
        # this probably isn't what should be done in those cases
        if scaled >= 0.0:
            return scaled
        else:
            return 0.0


    def _vector_selectivity(self):
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
        return self._safe_divide(self.vector_sum()[0], sum(self._data.values()))


    def second_selectivity(self):
        """
	Return the selectivity of the second largest value in the distribution.
	If there is one bin only, the selectivity is 0, since there is no second
	peack at all, and this value is also used to discriminate the validity
	of second_max_value_bin()
	Selectivity is computed in two ways depending on whether the variable is
	a cyclic, as in selectivity()
	"""
        if len(self._data) <= 1: 
            return 0.0
        if self.cyclic == True:
            return self._vector_second_selectivity()
        else:
            return self._relative_second_selectivity()


    def _relative_second_selectivity(self):
        """
        Return the value of the second maximum as a proportion of the sum_value()
	see _relative_selectivity() for further details
        """
	k		= self.max_value_bin()
	v		= self._data.pop(k)
	m		= max( self._data.values() )
	self._data[k]	= v

        proportion	= self._safe_divide( m, sum(self._data.values()) )
        offset		= 1.0/len(self._data)
        scaled		= (proportion-offset)/(1.0-offset)

	return max( scaled, 0.0 )


    def _vector_second_selectivity(self):
        """
        Return the magnitude of the vector_sum() of all bins excluding the
	maximum one, divided by the sum_value().
	see _vector_selectivity() for further details
        """
	k		= self.max_value_bin()
	v		= self._data.pop(k)
	s		= self.vector_sum()[0]
	self._data[k]	= v

        return self._safe_divide( s, sum(self._data.values()) )


    def second_peak_selectivity(self):
        """
	Return the selectivity of the second peak in the distribution.
	If the distribution has only one peak, return 0.0, and this value is
	also usefl to discriminate the validity of second_peak_bin()
	"""
        if len(self._data) <= 1: 
            return 0.0

	p1	= self.max_value_bin()
	p2	= self.second_peak_bin()
	if p1 == p2:
            return 0.0

	m		= self._data[ p2 ]
        proportion	= self._safe_divide( m, sum(self._data.values()) )
        offset		= 1.0/len(self._data)
        scaled		= (proportion-offset)/(1.0-offset)

	return max( scaled, 0.0 )


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


##    # not tested - will it be needed?
##    def relative_value(self, bin):
##        """
##        Return the value of the given bin as a proportion of the
##        sum_value().
##
##        This quantity is on a scale from 0.0 (the
##        specified bin is zero and others are nonzero) to 1.0 (the
##        specified bin is the only nonzero bin).  If the distribution is
##        empty the result is undefined; in such a case zero is returned
##        and the value returned by undefined_values() is incremented.
##        """
##        return self._safe_divide(self._data.get(bin), sum(self.values()))





        



    
