import param

import imagen

from topo.base.arrayutil import DivideWithConstant, MultiplyWithConstant
from topo import sheet

from . import Model
from .gcal import ModelGCAL
from .earlyvision import EarlyVisionModel


@Model.definition
class EarlyVisionSCAL(EarlyVisionModel):
    """
    EarlyVisionModel subclass with spatially calibrated extents
    used for SCAL and other models.
    """

    area = param.Number(default=2.0,bounds=(0,None),
        inclusive_bounds=(False,True),doc="""
        Linear size of cortical area to simulate.

        SCAL and other spatially calibrated variants of GCAL require
        cortical areas larger than 1.0x1.0 to avoid strong suppressive
        edge effects.""")

    expand_sf_test_range=param.Boolean(default=False,doc="""
        By default, measure_sine_pref() measures SF at the sizes of RF
        used, for speed, but if expand_sf_test_range is True, it will
        test over a larger range, including half the size of the
        smallest and twice the size of the largest.""")

    lgn_density = param.Number(default=16.0,bounds=(0,None),
        inclusive_bounds=(False,True),doc="""
        The nominal_density to use for the LGN.""")

    num_inputs = param.Number(default=1.5, bounds=(0,None))

    lgnaff_strength = param.Number(default=14, doc="""
        Overall strength of the afferent projection from the retina to
        the LGN sheets.""")

    #=================#
    # Spatial extents #
    #=================#

    center_size = param.Number(default=0.2, bounds=(0, None), doc="""
        The size of the central Gaussian used to compute the
        center-surround receptive field.""")

    surround_size = param.Number(default=0.3, bounds=(0, None), doc="""
        The size of the surround Gaussian used to compute the
        center-surround receptive field.""")

    gain_control_size = param.Number(default=0.8, bounds=(0, None), doc="""
        The size of the divisive inhibitory suppressive field used for
        contrast-gain control in the LGN sheets. This also acts as the
        corresponding bounds radius.""")

    lgnaff_radius = param.Number(default=0.4, bounds=(0, None), doc="""
        Connection field radius of a unit in the LGN level to units in
        a retina sheet.""")

    lgnlateral_radius = param.Number(default=0.8, bounds=(0, None), doc="""
        Connection field radius of a unit in the LGN level to
        surrounding units, in case gain control is used.""")

    def training_pattern_setup(self, **overrides):
        """
        Only the size of Gaussian training patterns has been modified.
        The 'aspect_ratio' and 'scale' parameter values are unchanged.
        """
        or_dim = 'or' in self.dims
        gaussian = (self.dataset == 'Gaussian')
        pattern_parameters = {'size':(0.2 if or_dim and gaussian
                                      else 3 * 0.1 if gaussian else 10.0),
                              'aspect_ratio': 4.6667 if or_dim else 1.0,
                              'scale': self.contrast / 100.0}
        return super(EarlyVisionSCAL, self).training_pattern_setup(
            pattern_parameters=pattern_parameters,
            position_bound_x=self.area/2.0+self.v1aff_radius,
            position_bound_y=self.area/2.0+self.v1aff_radius)


    def analysis_setup(self):
        super(EarlyVisionSCAL, self).analysis_setup()
        from topo.analysis.command import measure_sine_pref, measure_or_pref

        sf_relative_sizes = [self.sf_spacing ** (sf_channel - 1)
                             for sf_channel in self['SF']]

        wide_relative_sizes = ([0.5 * sf_relative_sizes[0]]
                               + sf_relative_sizes
                               + [2.0 * sf_relative_sizes[-1]])

        relative_sizes = (wide_relative_sizes if self.expand_sf_test_range
                          else sf_relative_sizes)
        frequencies = [1.5 * s for s in relative_sizes]
        measure_sine_pref.frequencies = frequencies
        measure_or_pref.frequencies= frequencies



@Model.definition
class ModelSCAL(EarlyVisionSCAL, ModelGCAL):
    """
    Spatially-tuned GCAL (SCAL) calibrated to represent a 3 degree
    parafoveal region of macaque primary visual cortex, assuming a
    3 mm/deg magnification factor and 0.71 mm orientation hypercolumn
    distance.

    Changes from ModelGCAL include relative strengths, homeostatic
    sparsity constraints, connection radii and switching from
    subtractive to divisive inhibition. The explanation of the
    calibration process is explained in a forthcoming notebook.
    """

    area = param.Number(default=2.0,bounds=(0,None),
        inclusive_bounds=(False,True),doc="""
        Linear size of cortical area to simulate.

        SCAL and other spatially calibrated variants of GCAL require
        cortical areas larger than 1.0x1.0 to avoid strong suppressive
        edge effects.""")

    aff_strength = param.Number(default=2.4, bounds=(0.0, None), doc="""
        Overall strength of the afferent projection to V1.""")

    exc_strength = param.Number(default=1.4, bounds=(0.0, None), doc="""
        Overall strength of the lateral excitatory projection to V1.""")

    inh_strength = param.Number(default=2.0, bounds=(0.0, None), doc="""
        Overall strength of the lateral inhibitory projection to V1.""")

    t_init = param.Number(default=0.45, doc="""
        The initial threshold value for homeostatic adaptation in V1.""")

    t_settle = param.Integer(default=16, doc="""
        Number of settling steps before applying a reset in the V1 sheet.""")

    #=================#
    # Spatial extents #
    #=================#

    latexc_radius = param.Number(default=0.1, bounds=(0, None), doc="""
        Radius of the lateral excitatory bounds within V1.""")

    latinh_radius = param.Number(default=0.18, bounds=(0, None), doc="""
        Radius of the lateral inhibitory bounds within V1.""")

    latexc_size = param.Number(default=0.06, bounds=(0, None), doc="""
        Size of the lateral excitatory connections within V1.""")

    latinh_size = param.Number(default=0.115, bounds=(0, None), doc="""
        Size of the lateral inhibitory connections within V1.""")

    v1aff_radius = param.Number(default=0.5, bounds=(0, None), doc="""
        Connection field radius of a unit in V1 to units in a LGN
        sheet.""")

    #=====================#
    # Divisive inhibition #
    #=====================#

    division_constant = param.Number(default=1.0, doc="""
        The constant offset on the denominator for divisive lateral
        inhibition to avoid divide-by-zero errors:

        divide(x,maximum(y,0) + division_constant).""")

    #=========================#
    # Long-range connectivity #
    #=========================#

    laterals = param.Boolean(default=False, doc="""
        Instantiate long-range lateral connections. Expensive!""")

    latexc_strength=param.Number(default=0, doc="""
        Lateral excitatory connection strength""")

    latexc_lr=param.Number(default=1.0, doc="""
        Lateral excitatory connection learning rate.""")

    # Excitatory connection profiles #

    lateral_radius = param.Number(default=1.25, bounds=(0, None), doc="""
        Radius of the lateral excitatory bounds within V1Exc.""")

    lateral_size = param.Number(default=2.5, bounds=(0, None), doc="""
        Size of the lateral excitatory connections within V1Exc.""")

    @Model.CFProjection
    def lateral_inhibitory(self, src_properties, dest_properties):
        """
        Switch to divisive inhibition, otherwise parameters unchanged.
        """
        return Model.CFProjection.params(
            delay=0.05,
            name='LateralInhibitory',
            weights_generator=imagen.random.GaussianCloud(
                gaussian_size=self.latinh_size),
            strength=self.inh_strength,
            activity_group=(0.6,
                            DivideWithConstant(c=self.division_constant)),
            learning_rate=self.inh_lr,
            nominal_bounds_template=sheet.BoundingBox(
                radius=self.latinh_radius))


    @Model.matchconditions('V1', 'lr_lateral_excitatory')
    def lr_lateral_excitatory_conditions(self, properties):
        return {'level': 'V1'} if self.laterals else {'level': None}


    @Model.CFProjection
    def lr_lateral_excitatory(self, src_properties, dest_properties):
        return Model.CFProjection.params(
            delay=0.1,
            name='LRExcitatory',
            activity_group=(0.9, MultiplyWithConstant()),
            weights_generator=imagen.Gaussian(aspect_ratio=1.0, size=self.lateral_size),
            strength=self.latexc_strength,
            learning_rate=self.latexc_lr,
            nominal_bounds_template=sheet.BoundingBox(radius=self.lateral_radius))
