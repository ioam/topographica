"""
TCAL - A temporally calibrated version of GCAL
"""
import param
import imagen
from imagen.transferfn import IdentityTF
from imagen.random import GaussianRandom

import topo
from topo import transferfn
from topo.transferfn.misc import TemporalScatter
from topo.submodel import Model, ArraySpec

from topo.submodel.cgcal import ModelCGCAL


@Model.definition
class ModelTCAL(ModelCGCAL):
    """
    ModelTCAL is a calibrated instance of ModelCGCAL with the addition
    of LGN latency scattering.
    """

    continuous = param.Boolean(default=True, constant=True, doc="""
      Unlike continuous GCAL where this is optional, TCAL is always a
      continuous model.""")

    timescale = param.Number(default=1, constant=True, doc="""
       In TCAL, simulation time (topo.sim.time) is in milliseconds.""")

    saccade_duration = param.Integer(default=240,
        doc="See corresponding CGCAL docstring.")

    timestep = param.Integer(default=5, doc="""
        The length of each timestep in milliseconds. Experimental
        collaborators suggests that 5ms is the largest useful timestep.

        This timestep value corresponds to the lateral delay in V1.""")

    # Delays ands time constants

    lgn_afferent_delay = param.Number(default=5, doc="""
       The afferent delay from the retina to the LGN in milliseconds.

      15 milliseconds is the value given in my Masters thesis.""")

    v1_afferent_delay = param.Number(default=35, doc="""
       The afferent delay from the LGN to V1 in milliseconds. Note
       that this value must be greater than half the span value for
       LGN temporal scatter.

      30 milliseconds is the value given in my Masters thesis.""")

    lgn_hysteresis = param.Number(default=0.03, allow_None=True, doc="""
        The time constant for the LGN sheet (per millisecond) if
        supplied.""")

    v1_hysteresis = param.Number(default=None, allow_None=True, doc="""
        The time constant for the V1 sheet (per millisecond) if
        supplied.""")

    # Parameters affecting LGN PSTH profiles

    gain_control_delay = param.Number(default=35.0, doc="""
        Delay of lateral gain-control projections in the LGN. Primary
        parameter controlling shape of LGN PSTHs.""")

    gain_control_strength = param.Number(default=8.0, doc="""
        Strength of lateral gain-control projections in the
        LGN. Controls the overall strength of the gain control.""")

    # Parameters affecting V1 PSTH profiles

    lgn_scatter_span = param.Integer(default=60, allow_None = True, doc="""
        Temporal span of the LGN temporal scatter (in
        milliseconds). Matches the corresponding parameter of the
        TemporalScatter transfer function.

        Note: In cat, the scatter can be 100ms from retina to LGN
        alone! Check the Saule and Wolfe references in Jim's book.""")

    lgn_scatter_distribution = param.ClassSelector(imagen.PatternGenerator,
                                                   allow_None=True,
                                                   is_instance=False,
                                                   default=GaussianRandom,
      doc="""The distribution pattern generator class used for
      generating the LGN latency scatter.""")

    lgn_scatter_scale = param.Number(default=15, doc="""
        The scale of the distribution used. Note that this value
        *must* be matches to the selected pattern distribution.""")

    aff_strength=param.Number(default=5.0, bounds=(0.0,None), doc="""
        The afferent strength needs to be modified relative to
        ContinuousModelGCAL in order to compensate for the changes in
        gain control in the LGN.""")


    def _scatter_scale_offset(self):
        """
        Compute a distribution appropriate scale and offset for the
        LGN scatter distribution.
        """
        if issubclass(self.lgn_scatter_distribution, GaussianRandom):
            return (self.lgn_scatter_scale, 0.0)

        elif issubclass(self.lgn_scatter_distribution,
                        imagen.random.UniformRandom):
            return (self.lgn_scatter_scale, -self.lgn_scatter_scale/2.0)

        elif self.lgn_scatter_distribution is not None:
            raise Exception("Distribution type %r not handled" %
                            self.lgn_scatter_distribution)


    #========================#
    # Projection definitions #
    #========================#

    @Model.CFProjection
    def V1_afferent(self, src_properties, dest_properties):
        "Projection delay and learning rate modified"
        paramlist = super(ModelTCAL, self).V1_afferent(
            src_properties, dest_properties)

        scatter = IdentityTF()  # Default when distribution is None

        if self.lgn_scatter_distribution is not None:
            scale, offset = self._scatter_scale_offset()
            distribution = self.lgn_scatter_distribution(
                name='LGN Latency Scatter',
                offset=offset, scale=scale)

            scatter = TemporalScatter(timestep=self.timestep,
                                      span=self.lgn_scatter_span,
                                      distribution=distribution)

        return dict(paramlist,
                    cf_shape = imagen.Disk(),
                    same_cf_shape_for_all_cfs=True,
                    input_fns=[scatter],
                    delay = paramlist['delay']-(self.lgn_scatter_span/2.0))
