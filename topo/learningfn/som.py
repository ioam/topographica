"""
SOM-based learning functions for CFProjections.
"""


from math import ceil

import param

from topo.base.arrayutil import L2norm, array_argmax
from topo.base.boundingregion import BoundingBox
from topo.base.cf import CFPLearningFn
from topo.base.patterngenerator import PatternGenerator

from topo.pattern import Gaussian


### JABHACKALERT: This class will be removed once the examples no
### longer rely upon it
class CFPLF_SOM(CFPLearningFn):
    """
    An abstract base class of learning functions for Self-Organizing Maps.

    This implementation is obsolete and will be removed soon.
    Please see examples/cfsom_or.ty for current SOM support.
    """
    __abstract = True

    learning_radius = param.Number(default=0.0,doc=
        """
        The radius of the neighborhood function to be used for
        learning.  Typically, this value will be set by the Sheet or
        Projection owning this CFPLearningFn, but it can also be set
        explicitly by the user.
        """)

    def __init__(self,**params):
        self.warning("CFPLF_SOM is deprecated -- see the example in cfsom_or.ty for how to build a SOM")

    def __call__(self, proj, input_activity, output_activity, learning_rate, **params):
        raise NotImplementedError



### JABHACKALERT: This class will be removed once the examples no
### longer rely upon it
class CFPLF_HebbianSOM(CFPLF_SOM):
    """
    Hebbian learning rule for CFProjections to Self-Organizing Maps.

    This implementation is obsolete and will be removed soon.
    Please see examples/cfsom_or.ty for current SOM support.
    """

    learning_radius = param.Number(default=0.0)

    crop_radius_multiplier = param.Number(default=3.0,doc=
        """
        Factor by which the radius should be multiplied,
        when deciding how far from the winner to keep updating the weights.
        """)

    neighborhood_kernel_generator = param.ClassSelector(PatternGenerator,
        default=Gaussian(x=0.0,y=0.0,aspect_ratio=1.0),
        doc="Neighborhood function")


    def __call__(self, iterator, input_activity, output_activity, learning_rate, **params):
        cfs = iterator.proj.cfs.tolist() # CEBALERT: convert to use flatcfs
        rows,cols = output_activity.shape

        # This learning function does not need to scale the learning
        # rate like some do, so it does not use constant_sum_connection_rate()
        single_connection_learning_rate = learning_rate

        ### JABALERT: The learning_radius is normally set by
        ### the learn() function of CFSOM, so it doesn't matter
        ### much that the value accepted here is in matrix and
        ### not sheet coordinates.  It's confusing that anything
        ### would accept matrix coordinates, but the learning_fn
        ### doesn't have access to the sheet, so it can't easily
        ### convert from sheet coords.
        radius = self.learning_radius
        crop_radius = max(1.25,radius*self.crop_radius_multiplier)

        # find out the matrix coordinates of the winner
        #
        # NOTE: when there are multiple projections, it would be
        # slightly more efficient to calculate the winner coordinates
        # within the Sheet, e.g. by moving winner_coords() to CFSOM
        # and passing in the results here.  However, finding the
        # coordinates does not take much time, and requiring the
        # winner to be passed in would make it harder to mix and match
        # Projections and learning rules with different Sheets.
        wr,wc = array_argmax(output_activity)

        # Optimization: Calculate the bounding box around the winner
        # in which weights will be changed, to avoid considering those
        # units below.
        cmin = int(max(wc-crop_radius,0))
        cmax = int(min(wc+crop_radius+1,cols)) # at least 1 between cmin and cmax
        rmin = int(max(wr-crop_radius,0))
        rmax = int(min(wr+crop_radius+1,rows))

        # generate the neighborhood kernel matrix so that the values
        # can be read off easily using matrix coordinates.
        nk_generator = self.neighborhood_kernel_generator
        radius_int = int(ceil(crop_radius))
        rbound = radius_int + 0.5
        bb = BoundingBox(points=((-rbound,-rbound), (rbound,rbound)))

        # Print parameters designed to match fm2d's output
        #print "%d rad= %d std= %f alpha= %f" % (topo.sim._time, radius_int, radius, single_connection_learning_rate)

        neighborhood_matrix = nk_generator(bounds=bb,xdensity=1,ydensity=1,
                                           size=2*radius)

        for r in range(rmin,rmax):
            for c in range(cmin,cmax):
                cwc = c - wc
                rwr = r - wr
                lattice_dist = L2norm((cwc,rwr))
                if lattice_dist <= crop_radius:
                    cf = cfs[r][c]
                    rate = single_connection_learning_rate * neighborhood_matrix[rwr+radius_int,cwc+radius_int]
                    X = cf.get_input_matrix(input_activity)
                    cf.weights += rate * (X - cf.weights)

                    # CEBHACKALERT: see ConnectionField.__init__()
                    cf.weights *= cf.mask


