"""
Continuous GCAL - A continuous version of vanilla GCAL
"""
import math, copy
from collections import OrderedDict

import param
from param import ParamOverrides

import topo
from topo.submodel import Model, ArraySpec, select
from topo.submodel.gcal import ModelGCAL

import numbergen
from imagen.transferfn import IdentityTF
from imagen.patterncoordinator import XCoordinator, YCoordinator, FeatureCoordinator

from topo import transferfn
from topo.transferfn.misc import TemporalScatter

#from .. import Continuous
# with param.logging_level('CRITICAL'):
#     Model.register_decorator(Continuous)


@Model.definition
class ModelCGCAL(ModelGCAL):
    """
    A continuous version of GCAL, changing as few settings as
    necessary to obtain a continuous model of time.
    """

    GCAL_sequence = param.Boolean(default=True, doc="""
        Whether to match the GCAL training sequence or not (for
        Gaussians).

        Relies on bad, fragile hacks and is anly required for
        comparison purposes and debugging.""")

    continuous = param.Boolean(default=True, doc="""
       Switch between Contunuous GCAL and regular GCAL for debugging
       purposes and to compare behaviour.""")

    timescale = param.Number(default=240.0, constant=True, doc="""
       Multiplicative factor between simulation time and milliseconds:

          milliseconds = topo.sim.time() * timescale.

       NOTE: This is a conversion factor and is NOT topo.sim.time()!""")

    saccade_duration = param.Integer(default=240, doc="""
        The *maximum* length of saccade i.e the largest possible
        multiple of timestep will be used that fits in this
        duration. This parameter is used to compute a concrete value
        of the saccade_duration property.

        NOTE: The notion of a 'saccade' is what links earlier models
        with activity resets (such as GCAL) to a continuous
        timebase. In short, this parameter corresponds to the temporal
        duration used to present each training stimulus.

        The notion of a saccade is appropriate for primate visual
        development but is not *necessary* in continuous models.""")

    timestep = param.Integer(default=12, doc="""
        The simulation time (milliseconds) used to 'clock' the model.""")

    # Delays and time constants

    lgn_afferent_delay = param.Number(default=12.0, doc="""
       The afferent delay (milliseconds) from the retina to the LGN.""")

    v1_afferent_delay = param.Number(default=12.0, doc="""
       The afferent delay (simulation time) from the LGN to V1.""")

    lgn_hysteresis = param.Number(default=0.05, allow_None=True, doc="""
        The time constant for the LGN sheet (per millisecond) if supplied.""")

    v1_hysteresis = param.Number(default=None, allow_None=True, doc="""
        The time constant for the V1 sheet (per millisecond) if supplied.""")

    # Parameters affecting LGN PSTH profiles

    gain_control_delay = param.Number(default=12.0, doc="""
        Millisecond felay of lateral gain-control projections in the
        LGN. Primary parameter controlling shape of LGN PSTHs.""")

    gain_control_strength = param.Number(default=0.6, doc="""
        Strength of lateral gain-control projections in the
        LGN. Controls the overall strength of the gain control.""")


    # Inclusion of 'dr' in the list below is a hack - it is only there
    # to enable the 'period' parameter to the PatternCoordinator when
    # 'period' should be available regardless of the dimension used.
    dims = param.List(['xy', 'or', 'dr'], doc="""
      The addition of 'dr' allows for direction map development (for
      non-zero speeds) and allows the reset period to be customized.""")

    speed = param.Number(default=0.0, doc="""
      The speed of translation of the training patterns.""")


    # Existing parameters tweaked for tuning.

    lgn_aff_strength=param.Number(default=0.7, bounds=(0.0,None),doc="""
        Overall strength of the afferent projection to the LGN.

        Note: This parameter overrides the behaviour of the
        strength_factor parameter.""")

    aff_strength=param.Number(default=1.1, doc="""
        Overall strength of the afferent projection to V1.

        Note: This parameter overrides the behaviour of the
        aff_strength parameter.""")

    learning_rate = param.Number(default=1.0, doc="""
       Overall scaling factor for projection learning rates where a
       value of 1.0 (default) doesn't modify the learning rates
       relative to GCAL.""")

    snapshot_learning = param.NumericTuple(default=None, allow_None=True,
                                           length=3, doc="""
                                           Three tuple e.g (240,130,0.051)""")

    kappa_bias = param.Number(default=None, allow_None=True)


    def __init__(self, **params):
        super(ModelCGCAL, self).__init__(**params)
        if (not self.continuous) and self.lgn_aff_strength==0.7:
            self.lgn_aff_strength=2.33
            self.warning('Setting lgn_aff_strength from 0.7 to 2.33 as continuous=False')
        if (not self.continuous) and self.lgn_aff_strength==1.1:
            self.aff_strength=1.5
            self.warning('Setting aff_strength from 1.1 to 1.5 as continuous=False')

    def property_setup(self, properties):
        properties = super(ModelCGCAL, self).property_setup(properties)

        # In simulation time units
        properties['period'] = self.timestep / self.timescale if self.continuous else 1.0
        properties['steps_per_saccade'] = (self.saccade_duration // self.timestep)
        properties['saccade_duration'] = (properties['steps_per_saccade'] * properties['period']
                                          if self.continuous else 1.0)

        properties['lags'] = [0]          # Disables multiple lagged projections (dim='dr')
        return properties


    def training_pattern_setup(self, **overrides):
        assert not (self.GCAL_sequence and self.kappa_bias)
        if self.kappa_bias:
            OR_coordinator = VonMisesORCoordinator.instance(kappa=self.kappa_bias)
            feature_coordinators = OrderedDict([('xy', [XCoordinator,YCoordinator]),
                                                ('or', OR_coordinator)])
            overrides['feature_coordinators'] = feature_coordinators

        return super(ModelCGCAL,
                     self).training_pattern_setup(
                         **dict(overrides,
                                reset_period=self['saccade_duration']))


    #============================#
    # Temporal scaling equations #
    #============================#

    def projection_learning_rate(self, rate):
        """
        For afferent, excitatory V1 and inhibitory V1.
        """
        if not self.continuous: return rate
        if self.snapshot_learning: return rate
        return self.learning_rate * (rate / self['steps_per_saccade'])


    def homeostatic_learning_rate(self, rate=0.01):
        """
        A rate of 0.01 is default - can parameterize later if needed.

        Note: The learning rate only needs adjusted for the number of
        steps if homeostasis is continually applied.
        """
        if not self.homeostasis:  return 0.0
        elif not self.continuous: return rate
        else:                     return rate / self['steps_per_saccade']


    def hysteresis_constant(self, constant):
        """
        Compute the *continuous* hysteresis constant for V1 and LGN.

        If constant is set to None, hysteresis is disabled.
        """
        if not self.continuous: return 1.0
        return 1.0 if constant is None else (constant * self.timestep)


    #===================#
    # Sheet definitions #
    #===================#


    @Model.Continuous
    def LGN(self, properties):
        """
        Filters parameters based on sheet type and applies hysteresis
        for continuous models.

        Note that there is a difference between the two orderings:

        * [hysteresis, rectify]: Applies hysteresis on the voltage or
                                 some other real biophysical variable

        * [rectify, hysteresis]: Applies hysteresis to the
                                 positive-valued 'spiking' variable.

        """
        filtered =   ['tsettle', 'strict_tsettle'] if self.continuous else []
        params =  {k:v for k,v in super(ModelCGCAL, self).LGN(properties).items()
                   if k not in filtered}

        lgn_time_constant = (self.hysteresis_constant(self.lgn_hysteresis)
                             if self.continuous else 1.0)
        hysteresis = transferfn.Hysteresis(time_constant=lgn_time_constant)
        return dict(params, output_fns=[transferfn.misc.HalfRectify(), hysteresis])



    @Model.Continuous
    def V1(self, properties):
        parameters = super(ModelCGCAL, self).V1(properties)
        parameters = {k:v for k,v in parameters.items()
                      if k not in (['tsettle'] if self.continuous else [])}

        v1_time_constant = (self.hysteresis_constant(self.v1_hysteresis)
                            if self.continuous else 1.0)
        hysteresis = transferfn.Hysteresis(time_constant=v1_time_constant)

        homeostasis = transferfn.misc.HomeostaticResponse(
            period=0.0,
            t_init = self.t_init,
            target_activity = self.target_activity,
            learning_rate=self.homeostatic_learning_rate())

        if self.snapshot_learning:
            parameters['snapshot_learning'] = self.snapshot_learning

        return dict(parameters, output_fns = [homeostasis])


    #========================#
    # Projection definitions #
    #========================#


    @Model.SharedWeightCFProjection
    def afferent(self, src_properties, dest_properties):
        "Names set to avoid duplicate projection names."
        name = 'AfferentOn' if dest_properties['polarity']=='On' else 'AfferentOff'
        lgn_aff = super(ModelCGCAL, self).afferent(src_properties, dest_properties)
        return dict(lgn_aff, name=name,
                    strength = self.lgn_aff_strength,
                    delay=self.lgn_afferent_delay / self.timescale)


    @Model.CFProjection
    def V1_afferent(self, src_properties, dest_properties):
        "Projection delay and learning rate modified"
        paramlist = super(ModelCGCAL, self).V1_afferent(src_properties, dest_properties)[0]
        return dict(paramlist,
                    delay=self.v1_afferent_delay / self.timescale,
                    strength = self.aff_strength,
                    learning_rate = self.projection_learning_rate(self.aff_lr))


    @Model.SharedWeightCFProjection
    def lateral_gain_control(self, src_properties, dest_properties):
        "Projection delay modified"
        params = super(ModelCGCAL, self).lateral_gain_control(src_properties, dest_properties)
        return dict(params,
                    strength = self.gain_control_strength,
                    delay=self.gain_control_delay / self.timescale)


    @Model.CFProjection
    def lateral_excitatory(self, src_properties, dest_properties):
        "Projection delay and learning rate modified"
        params = super(ModelCGCAL, self).lateral_excitatory(src_properties, dest_properties)
        return dict(params,
                    delay=self.timestep / self.timescale,
                    learning_rate = self.projection_learning_rate(self.exc_lr))


    @Model.CFProjection
    def lateral_inhibitory(self, src_properties, dest_properties):
        "Projection delay and learning rate modified"
        params = super(ModelCGCAL, self).lateral_inhibitory(src_properties, dest_properties)
        return dict(params,
                    delay=self.timestep / self.timescale,
                    learning_rate = self.projection_learning_rate(self.inh_lr))


    def setup(self,*args,**params):
        spec = super(ModelCGCAL, self).setup(*args, **params)
        if self.GCAL_sequence and self.continuous:
            time_factor = int(self.saccade_duration/self.timescale)
            # By default, should be 240 for TCAL, 1 for GCAL
            apply_GCAL_training_sequence(spec, time_factor)
            return spec
        else:
            return spec


class VonMisesORCoordinator(FeatureCoordinator):
    """
    Coordinator that allows the introduction of orientation biases.
    """

    mu = param.Number(default=0)

    kappa = param.Number(default=10)

    def __call__(self, pattern, pattern_label, pattern_number, master_seed, **params):
        p = ParamOverrides(self,params,allow_extra_keywords=True)
        new_pattern=copy.copy(pattern)
        new_pattern.orientation = pattern.get_value_generator('orientation')+\
                                  numbergen.VonMisesRandom(
                                      mu = self.mu,
                                      kappa = self.kappa,
                                      seed=master_seed+21+pattern_number,
                                      name=("OrientationCoordinator" + str(pattern_number)))
        return new_pattern


#===========================#
# Necessary to emulate GCAL #
#===========================#


from gmpy import mpq

class distort(object):

    def __init__(self, time_factor):
        self.time_factor = time_factor

    def __call__(self):
        time = param.Dynamic.time_fn()
        if time <= 0.05:   return time
        else:              return (time // self.time_factor)+mpq(1,20)


def apply_GCAL_training_sequence(model, time_factor):
    """
    Apply some hacks on the deeply nested numbergen time functions to
    get the same training sequence as for vanilla GCAL. For use with
    continuous=False.

    Not strictly not required for any of these models to work.
    """
    model.warning("Modifying time functions to reproduce GCAL Gaussian sequence")

    for sweeper in model.training_patterns.Retina.generators:
        gaussian = sweeper.generator
        for p in ['orientation', 'x', 'y']:
            binary_op_or = gaussian.get_value_generator(p)
            binary_op_or.rhs.time_fn = distort(time_factor)
