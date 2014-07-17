"""
Additional FeatureCoordinators specific to cortical modelling work,
supplementing the general-purpose ones in imagen.patterncoordinator.
"""

import copy

import param
from param.parameterized import ParamOverrides

from imagen.patterncoordinator import FeatureCoordinator
from imagen import Sweeper

import numbergen

class DisparityCoordinator(FeatureCoordinator):
    """
    Coordinates the disparity (difference of pattern locations) of two pattern generators.
    The pattern_label of the generators must contain 'Left' or 'Right'
    """

    disparity_bound = param.Number(default=4.0*0.041665/2.0,doc="""
        Maximum difference of the pattern locations between the two eyes (on the x axis).""")

    def __call__(self, pattern, pattern_label, pattern_number, master_seed, **params):
        p = ParamOverrides(self,params,allow_extra_keywords=True)
        new_pattern=copy.copy(pattern)

        if(pattern_label.count('Left')):
            new_pattern.x = pattern.get_value_generator('x')-\
                numbergen.UniformRandom(lbound=-p.disparity_bound,
                                        ubound=p.disparity_bound,
                                        seed=master_seed+45+pattern_number,
                                        name="DisparityCoordinator"+str(pattern_number))
        elif(pattern_label.count('Right')):
            new_pattern.x = pattern.get_value_generator('x')+\
                numbergen.UniformRandom(lbound=-p.disparity_bound,
                                        ubound=p.disparity_bound,
                                        seed=master_seed+45+pattern_number,
                                        name="DisparityCoordinator"+str(pattern_number))
        else:
            self.warning('Skipping region %s; Disparity is defined only for Left and Right retinas.' % pattern)

        return new_pattern



class OcularityCoordinator(FeatureCoordinator):
    """
    Coordinates the ocularity (brightness difference) of two pattern generators.
    The pattern_label of the generators must contain 'Left' or 'Right'
    """

    dim_fraction = param.Number(default=0.7,bounds=(0.0,1.0),doc="""
        Fraction by which the pattern brightness varies between the two eyes.""")

    def __call__(self, pattern, pattern_label, pattern_number, master_seed, **params):
        p = ParamOverrides(self,params,allow_extra_keywords=True)
        new_pattern=copy.copy(pattern)
        if(pattern_label.count('Left')):
            new_pattern.scale = (1-p.dim_fraction) + p.dim_fraction * \
                                (2.0-numbergen.UniformRandom(lbound=0,
                                                             ubound=2,
                                                             seed=master_seed+55+pattern_number,
                                                             name="OcularityCoordinator"+str(pattern_number)))
        elif(pattern_label.count('Right')):
            new_pattern.scale = (1-p.dim_fraction) + p.dim_fraction * \
                                 numbergen.UniformRandom(lbound=0,
                                                         ubound=2,
                                                         seed=master_seed+55+pattern_number,
                                                         name="OcularityCoordinator"+str(pattern_number))
        else:
            self.warning('Skipping region %s; Ocularity is defined only for Left and Right retinas.' % pattern)

        return new_pattern



class SpatialFrequencyCoordinator(FeatureCoordinator):
    """
    Coordinates the size of pattern generators. This is useful when multiple spatial frequency
    channels are used, to cover a wide range of sizes of pattern generators.
    """

    sf_spacing = param.Number(default=2.0,bounds=(0.0,None),doc="""Determines the factor by which 
        successive SF channels increase in size. Together with sf_max_channel, this is used
        to compute the upper bound of the size of the supplied pattern generator.""")

    sf_max_channel = param.Integer(default=2,bounds=(2,None),softbounds=(1,4),doc="""Highest
        spatial frequency channel. Together with sf_spacing, this is used
        to compute the upper bound of the size of the supplied pattern generator.""")

    def __call__(self, pattern, pattern_label, pattern_number, master_seed, **params):
        p = ParamOverrides(self,params,allow_extra_keywords=True)
        new_pattern=copy.copy(pattern)
        new_pattern.size=pattern.get_value_generator('size')*\
                         numbergen.UniformRandom(lbound=1,
                                                 ubound=p.sf_spacing**(p.sf_max_channel-1),
                                                 seed=master_seed+77+pattern_number,
                                                 name="SpatialFrequencyCoordinator"+str(pattern_number))

        return new_pattern


class MotionCoordinator(FeatureCoordinator):
    """
    Coordinates the motion of patterns.
    """

    reset_period = param.Number(default=4,bounds=(0.0,None),doc="""
        Period between generating each new translation episode.""")

    speed = param.Number(default=2.0/24.0,bounds=(0.0,None),doc="""
        The speed with which the pattern should move,
        in sheet coordinates per time_fn unit.""")

    time_fn = param.Callable(default=param.Dynamic.time_fn,doc="""
        Function to generate the time used as a base for translation.""")

    def __call__(self, pattern, pattern_label, pattern_number, master_seed, **params):
        p = ParamOverrides(self,params,allow_extra_keywords=True)

        assert(param.Dynamic.time_dependent), "param.Dynamic.time_dependent!=True for motion"
        assert(numbergen.RandomDistribution.time_dependent), "numbergen.RandomDistribution.time_dependent!=True for motion" 

        moved_pattern = Sweeper(generator=copy.deepcopy(pattern),
                                speed=p.speed,
                                reset_period=p.reset_period,
                                time_fn=p.time_fn)

        return moved_pattern



feature_coordinators=[('od',OcularityCoordinator),
                      ('dy',DisparityCoordinator),
                      ('sf',SpatialFrequencyCoordinator),
                      ('dr',MotionCoordinator)]
