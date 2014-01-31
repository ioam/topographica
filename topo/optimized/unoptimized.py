"""
Provides unoptimized fallbacks for Cython optimized components.
"""

import param

from topo.base.cf import ResponseFn, CFPOutputFn, CFPRF_Plugin, CFPLF_Plugin
from topo.base.functionfamily import DotProduct, LearningFn, Hebbian, TransferFn, IdentityTF
from topo.learningfn import BCMFixed
from topo.transferfn import DivisiveNormalizeL1

from topo.learningfn.projfn import CFPLF_Trace as CFPLF_Trace_cython # pyflakes:ignore (optimized version provided)


class CFPRF_DotProduct_cython(CFPRF_Plugin):
    """
    Wrapper written to allow transparent non-optimized fallback;
    equivalent to CFPRF_Plugin(single_cf_fn=DotProduct()).
    """

    single_cf_fn = param.ClassSelector(ResponseFn, DotProduct(),readonly=True)

    def __init__(self,**params):
        super(CFPRF_DotProduct_cython,self).__init__(**params)


class CFPLF_Hebbian_cython(CFPLF_Plugin):
    """Same as CFPLF_Plugin(single_cf_fn=Hebbian()); just for non-optimized fallback."""
    single_cf_fn = param.ClassSelector(LearningFn,default=Hebbian(),readonly=True)


class CFPLF_BCMFixed_cython(CFPLF_Plugin):
    """Same as CFPLF_Plugin(single_cf_fn=BCMFixed()); just for non-optimized fallback."""
    single_cf_fn = param.ClassSelector(LearningFn,default=BCMFixed(),readonly=True)


class CFPOF_DivisiveNormalizeL1_cython(CFPOutputFn):
    """
    Non-optimized version of CFPOF_DivisiveNormalizeL1_cython.

    Same as CFPOF_Plugin(single_cf_fn=DivisiveNormalizeL1()), except
    that it supports joint normalization using the norm_total
    property of ConnectionField.
    """

    single_cf_fn = param.ClassSelector(TransferFn,
                                       default=DivisiveNormalizeL1(norm_value=1.0),
                                       constant=True)

    def __call__(self, iterator, **params):
        """
        Uses the cf.norm_total attribute to allow optimization
        by computing the sum separately, and to allow joint
        normalization. After use, cf.norm_total is deleted because
        the value it would have has been changed.
        """
        # CEBALERT: fix this here and elsewhere
        if type(self.single_cf_fn) is not IdentityTF:
            norm_value = self.single_cf_fn.norm_value
            current_sum = 0.0
            for cf, i in iterator():
                current_sum += cf.norm_total
            if current_sum > 0.0000000000001:
                factor = norm_value / current_sum
                cf.weights *= factor
            del cf.norm_total