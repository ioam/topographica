import param

import numpy as np
import imagen as ig

from topo.base.arrayutil import DivideWithConstant, MultiplyWithConstant
from topo.base.projection import SheetMask, CircularMask
from topo import optimized, projection, sheet
from topo.sparse.sparsecf import SparseConnectionField, CFPLF_Hebbian_Sparse,\
                                 CFPOF_DivisiveNormalizeL1_Sparse, CFPRF_DotProduct_Sparse,\
                                 compute_sparse_joint_norm_totals, CFSPOF_SproutRetract

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

    circular_mask = param.Boolean(default=False, doc="""
        Whether the V1 sheet should be masked with a disk to reduce
        edge effects.""")

    input_aspect = param.Number(default=4.667, bounds=(0, None),
                          doc="""
        Aspect of the Gaussian input pattern""")

    input_width = param.Number(default=0.2, bounds=(0, None),
                          doc="""
        Width of the Gaussian input pattern""")

    expand_sf_test_range=param.Boolean(default=False,doc="""
        By default, measure_sine_pref() measures SF at the sizes of RF
        used, for speed, but if expand_sf_test_range is True, it will
        test over a larger range, including half the size of the
        smallest and twice the size of the largest.""")

    lgn_density = param.Number(default=16.0,bounds=(0,None),
        inclusive_bounds=(False,True),doc="""
        The nominal_density to use for the LGN.""")

    num_inputs = param.Number(default=1.5, bounds=(0,None), doc="""
        Number of inputs per unit area.""")

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
        pattern_parameters = {'size':(self.input_width if or_dim and gaussian
                                      else 3 * 0.1 if gaussian else 10.0),
                              'aspect_ratio': self.input_aspect if or_dim else 1.0,
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

    def property_setup(self, properties):
        "Specify weight initialization, response function, and learning function"
        properties = super(ModelSCAL, self).property_setup(properties)

        projection.CFProjection.cf_shape=ig.Disk(smoothing=0.0)
        projection.CFProjection.response_fn=optimized.CFPRF_DotProduct_cython()
        projection.CFProjection.learning_fn=optimized.CFPLF_Hebbian_cython()
        projection.CFProjection.weights_output_fns=[optimized.CFPOF_DivisiveNormalize_L1_cython()]
        projection.SharedWeightCFProjection.response_fn=optimized.CFPRF_DotProduct_cython()
        sheet.SettlingCFSheet.joint_norm_fn = optimized.compute_joint_norm_totals_cython
        return properties


    @Model.SettlingCFSheet
    def V1(self, properties):
        params = super(ModelSCAL, self).V1(properties)
        mask = CircularMask() if self.circular_mask else SheetMask(),
        return dict(params, mask=mask)


    @Model.CFProjection
    def lateral_inhibitory(self, src_properties, dest_properties):
        """
        Switch to divisive inhibition, otherwise parameters unchanged.
        """
        return Model.CFProjection.params(
            delay=0.05,
            name='LateralInhibitory',
            weights_generator=ig.random.GaussianCloud(
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
            weights_generator=ig.Gaussian(aspect_ratio=1.0, size=self.lateral_size),
            strength=self.latexc_strength,
            learning_rate=self.latexc_lr,
            nominal_bounds_template=sheet.BoundingBox(radius=self.lateral_radius))



@Model.definition
class ModelSCALSparse(ModelSCAL):

    afferent_density = param.Number(default=1.0, doc="""
        The density of connections in the V1 afferents.""")

    lateral_density = param.Number(default=1.0, doc="""
        The sparsity of connections in long-range laterals""")

    sprout_and_retract = param.Boolean(default=False)

    @Model.SettlingCFSheet
    def V1(self, properties):
        params = super(ModelSCALSparse, self).V1(properties)
        return dict(params, joint_norm_fn=compute_sparse_joint_norm_totals)

    @Model.SparseCFProjection
    def lr_lateral_excitatory(self, src_properties, dest_properties):
        params = super(ModelSCALSparse, self).lr_lateral_excitatory(src_properties,
                                                                    dest_properties)

        disk = ig.Disk(smoothing=0.0)
        output_fns = [CFPOF_DivisiveNormalizeL1_Sparse]
        if self.sprout_and_retract:
            cf_shape = disk
            same_shape = True
            output_fns = [CFSPOF_SproutRetract(target_sparsity=self.lateral_density),
                          CFPOF_DivisiveNormalizeL1_Sparse]
        else:
            density = self.afferent_density*(1/(np.pi/4))
            cf_shape = ig.random.BinaryUniformRandom(on_probability=min([1, density]),
                                                     mask_shape=disk,
                                                     name='LateralDensity')
            same_shape = False

        return dict(params, cf_shape=cf_shape, cf_type=SparseConnectionField,
                    same_cf_shape_for_all_cfs=same_shape,
                    response_fn = CFPRF_DotProduct_Sparse,
                    learning_fn = CFPLF_Hebbian_Sparse,
                    weights_output_fns = output_fns)


    @Model.SparseCFProjection
    def V1_afferent(self, src_properties, dest_properties):
        params = super(ModelSCALSparse, self).V1_afferent(src_properties, dest_properties)
        # Adjust density for size of disk mask
        disk = ig.Disk(smoothing=0.0)
        output_fns = [CFPOF_DivisiveNormalizeL1_Sparse]
        if self.sprout_and_retract:
            cf_shape = disk
            same_shape = True
            output_fns = [CFSPOF_SproutRetract(target_sparsity=self.afferent_density)] + output_fns
        else:
            density = self.afferent_density*(1/(np.pi/4))
            cf_shape = ig.random.BinaryUniformRandom(on_probability=min([1, density]),
                                                     mask_shape=disk,
                                                     name='AffDensity')
            same_shape = False

        return dict(params[0], cf_shape=cf_shape, cf_type = SparseConnectionField,
                    same_cf_shape_for_all_cfs=same_shape,
                    response_fn = CFPRF_DotProduct_Sparse,
                    learning_fn = CFPLF_Hebbian_Sparse,
                    weights_output_fns = output_fns)
