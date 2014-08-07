import topo
import param
import imagen

from topo import projection, responsefn, learningfn, transferfn, sheet
import topo.learningfn.optimized
import topo.transferfn.optimized
import topo.responsefn.optimized
import topo.sheet.optimized
import topo.transferfn.misc

from topo.submodel import Model, order_projections
from topo.submodel.earlyvision import ColorEarlyVisionModel



class ModelGCAL(ColorEarlyVisionModel):

    cortex_density=param.Number(default=47.0,bounds=(0,None),
        inclusive_bounds=(False,True),doc="""
        The nominal_density to use for V1.""")

    homeostasis = param.Boolean(default=True, doc="""
        Whether or not the homeostatic adaption should be applied in V1"""),

    t_init = param.Number(default=0.15, doc="""
        The initial V1 threshold value. This value is static in the L and GCL models
        and adaptive in the AL and GCAL models.""")

    latexc_radius=param.Number(default=0.104,bounds=(0,None),doc="""
        Size of the radius of the lateral excitatory connections within V1.""")

    latinh_radius=param.Number(default=0.22917,bounds=(0,None),doc="""
        Size of the radius of the lateral inhibitory connections within V1.""")

    aff_lr=param.Number(default=0.1,bounds=(0.0,None),doc="""
        Learning rate for the afferent projection(s) to V1.""")

    exc_lr=param.Number(default=0.0,bounds=(0.0,None),doc="""
        Learning rate for the lateral excitatory projection to V1.""")

    inh_lr=param.Number(default=0.3,bounds=(0.0,None),doc="""
        Learning rate for the lateral inhibitory projection to V1.""")

    aff_strength=param.Number(default=1.0,bounds=(0.0,None),doc="""
        Overall strength of the afferent projection to V1.""")

    exc_strength=param.Number(default=1.7,bounds=(0.0,None),doc="""
        Overall strength of the lateral excitatory projection to V1.""")

    inh_strength=param.Number(default=1.4,bounds=(0.0,None),doc="""
        Overall strength of the lateral inhibitory projection to V1.""")

    expand_sf_test_range=param.Boolean(default=False,doc="""
        By default, measure_sine_pref() measures SF at the sizes of RF
        used, for speed, but if expand_sf_test_range is True, it will
        test over a larger range, including half the size of the
        smallest and twice the size of the largest.""")


    def setup_attributes(self, attrs):
        attrs = super(ModelGCAL, self).setup_attributes(attrs)
        "Specify weight initialization, response function, and learning function"

        projection.CFProjection.cf_shape=imagen.Disk(smoothing=0.0)
        projection.CFProjection.response_fn=responsefn.optimized.CFPRF_DotProduct_opt()
        projection.CFProjection.learning_fn=learningfn.optimized.CFPLF_Hebbian_opt()
        projection.CFProjection.weights_output_fns=[transferfn.optimized.CFPOF_DivisiveNormalizeL1_opt()]
        projection.SharedWeightCFProjection.response_fn=responsefn.optimized.CFPRF_DotProduct_opt()
        return attrs

    def setup_sheets(self):
        sheets = super(ModelGCAL,self).setup_sheets()
        sheets['V1'] = [{}]
        return sheets


    @Model.SettlingCFSheet
    def V1(self, properties):
        return Model.SettlingCFSheet.params(
            tsettle=16,
            plastic=True,
            joint_norm_fn=topo.sheet.optimized.compute_joint_norm_totals_opt,
            output_fns=[transferfn.misc.HomeostaticResponse(t_init=self.t_init,
                                                            learning_rate=0.01 if self.homeostasis else 0.0)],
            nominal_density=self.cortex_density,
            nominal_bounds=sheet.BoundingBox(radius=self.area/2.0))


    @Model.matchconditions('V1', 'V1_afferent')
    def V1_afferent_conditions(self, properties):
        return {'level': 'LGN'}


    @Model.CFProjection
    def V1_afferent(self, src_properties, dest_properties):
        sf_channel = src_properties['SF'] if 'SF' in src_properties else 1
        # Adjust delays so same measurement protocol can be used with and without gain control.
        LGN_V1_delay = 0.05 if self.gain_control else 0.10

        name=''
        if 'eye' in src_properties: name+=src_properties['eye']
        if 'opponent' in src_properties:
            name+=src_properties['opponent']+src_properties['surround']
        name+=('LGN'+src_properties['polarity']+'Afferent')
        if sf_channel>1: name+=('SF'+str(src_properties['SF']))

        gaussian_size = 2.0 * self.v1aff_radius *self.sf_spacing**(sf_channel-1)
        weights_generator = imagen.random.GaussianCloud(gaussian_size=gaussian_size)

        return [Model.CFProjection.params(
                delay=LGN_V1_delay+lag,
                dest_port=('Activity','JointNormalize','Afferent'),
                name= name if lag==0 else name+('Lag'+str(lag)),
                learning_rate=self.aff_lr,
                strength=self.aff_strength*(1.0 if not self.gain_control else 1.5),
                weights_generator=weights_generator,
                nominal_bounds_template=sheet.BoundingBox(radius=
                                            self.v1aff_radius*self.sf_spacing**(sf_channel-1)))
                for lag in self.attrs.Lags]


    @Model.matchconditions('V1', 'lateral_excitatory')
    def lateral_excitatory_conditions(self, properties):
        return {'level': 'V1'}


    @Model.CFProjection
    def lateral_excitatory(self, src_properties, dest_properties):
        return Model.CFProjection.params(
            delay=0.05,
            name='LateralExcitatory',
            weights_generator=imagen.Gaussian(aspect_ratio=1.0, size=0.05),
            strength=self.exc_strength,
            learning_rate=self.exc_lr,
            nominal_bounds_template=sheet.BoundingBox(radius=self.latexc_radius))


    @Model.matchconditions('V1', 'lateral_inhibitory')
    def lateral_inhibitory_conditions(self, properties):
        return {'level': 'V1'}


    @Model.CFProjection
    def lateral_inhibitory(self, src_properties, dest_properties):
        return Model.CFProjection.params(
            delay=0.05,
            name='LateralInhibitory',
            weights_generator=imagen.random.GaussianCloud(gaussian_size=0.15),
            strength=-1.0*self.inh_strength,
            learning_rate=self.inh_lr,
            nominal_bounds_template=sheet.BoundingBox(radius=self.latinh_radius))


    def _setup_analysis(self):
        # TODO: This is different in gcal.ty, stevens/gcal.ty and gcal_od.ty
        # And depends whether gain control is used or not
        import topo.analysis.featureresponses
        topo.analysis.featureresponses.FeatureMaps.selectivity_multiplier=2.0
        topo.analysis.featureresponses.FeatureCurveCommand.contrasts=[1, 10, 30, 50, 100]
        if 'dr' in self.dims:
            topo.analysis.featureresponses.MeasureResponseCommand.durations=[(max(self.attrs.Lags)+1)*1.0]
        if 'sf' in self.dims:
            from topo.analysis.command import measure_sine_pref
            sf_relative_sizes = [self.sf_spacing**(sf_channel-1) for sf_channel in self.attrs.SF]
            wide_relative_sizes=[0.5*sf_relative_sizes[0]] + sf_relative_sizes + [2.0*sf_relative_sizes[-1]]
            relative_sizes=(wide_relative_sizes if self.expand_sf_test_range else sf_relative_sizes)
            #The default 2.4 spatial frequency value here is
            #chosen because it results in a sine grating with bars whose
            #width approximately matches the width of the Gaussian training
            #patterns, and thus the typical width of an ON stripe in one of the
            #receptive fields
            measure_sine_pref.frequencies = [2.4*s for s in relative_sizes]



class ExamplesGCAL(ModelGCAL):
    """
    Reproduces the results of the legacy examples/gcal.ty file.
    """

    def __init__(self, **params):
        super(ExamplesGCAL, self).__init__(time_dependent=False, **params)
        if set(self.dims) != set([ 'xy', 'or']):
            raise Exception("ExamplesGCAL only reproducible for dims = ['xy', 'or']")


    def setup(self,setup_options):
        super(ExamplesGCAL, self).setup(setup_options)
        if setup_options is True or 'sheets' in setup_options:
            self.sheets.Retina.update(nominal_bounds=sheet.BoundingBox(radius=self.area/2.0+1.125))
            self.sheets.LGNOn.update(nominal_bounds=sheet.BoundingBox(radius=self.area/2.0+0.75))
            self.sheets.LGNOff.update(nominal_bounds=sheet.BoundingBox(radius=self.area/2.0+0.75))
            self.sheets.V1.update(nominal_density=48)
        if setup_options is True or 'projections' in setup_options:
            order_projections(self, ['afferent',
                                     'lateral_gain_control',
                                     ('V1_afferent', {'polarity':'On'}),
                                     ('V1_afferent', {'polarity':'Off'}),
                                     'lateral_excitatory',
                                     'lateral_inhibitory'])
