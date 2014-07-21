import topo
import param
import imagen

from topo import projection, responsefn, learningfn, transferfn, sheet
import topo.learningfn.optimized
import topo.transferfn.optimized
import topo.responsefn.optimized
import topo.sheet.optimized
import topo.transferfn.misc

from topo.submodels import Model, SheetSpec
from topo.submodels.earlyvision import ColorEarlyVisionModel



class ModelGCAL(ColorEarlyVisionModel):

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


    def setup_attributes(self):
        super(ModelGCAL, self).setup_attributes()
        "Specify weight initialization, response function, and learning function"

        projection.CFProjection.cf_shape=imagen.Disk(smoothing=0.0)
        projection.CFProjection.response_fn=responsefn.optimized.CFPRF_DotProduct_opt()
        projection.CFProjection.learning_fn=learningfn.optimized.CFPLF_Hebbian_opt()
        projection.CFProjection.weights_output_fns=[transferfn.optimized.CFPOF_DivisiveNormalizeL1_opt()]
        projection.SharedWeightCFProjection.response_fn=responsefn.optimized.CFPRF_DotProduct_opt()


    def setup_sheets(self):
        return dict(V1=[{}],**super(ModelGCAL,self).setup_sheets())


    @Model.level('V1', sheet.SettlingCFSheet)
    def V1_sheet_parameters(self, properties):
        return {'tsettle':16,
                'plastic':True,
                'joint_norm_fn':topo.sheet.optimized.compute_joint_norm_totals_opt,
                'output_fns':[transferfn.misc.HomeostaticResponse(t_init=self.t_init,
                                                learning_rate=0.01 if self.homeostasis else 0.0)],
                'nominal_density':self.cortex_density,
                'nominal_bounds':sheet.BoundingBox(radius=self.area/2.0)}


    @Model.matchconditions('V1')
    def V1_matchconditions(self, properties):
        """
        V1 connects to all LGN sheets.

        Furthermore, it connects to itself with two projections:
            * one lateral connection which is excitatory (short-range)
            * one lateral connection which is inhibitory (long-range)
        """
        # TODO: Combine Afferent V1 On and Afferent V1 Off
        # As soon as time_dependent=True for weights
        return {'AfferentV1OnMatch': {'level': 'LGN', 'polarity': 'On'},
                'AfferentV1OffMatch':{'level': 'LGN', 'polarity': 'Off'},
                'LateralV1ExcitatoryMatch': {'level': 'V1'},
                'LateralV1InhibitoryMatch': {'level': 'V1'}}


    @Model.connection('AfferentV1OnMatch',  projection.CFProjection)
    @Model.connection('AfferentV1OffMatch', projection.CFProjection)
    def V1_afferent_projections(self, proj):
        sf_channel = proj.src.properties['SF'] if 'SF' in proj.src.properties else 1
        # Adjust delays so same measurement protocol can be used with and without gain control.
        LGN_V1_delay = 0.05 if self.gain_control else 0.10

        name=''
        if 'eye' in proj.src.properties: name+=proj.src.properties['eye']
        if 'opponent' in proj.src.properties:
            name+=proj.src.properties['opponent']+proj.src.properties['surround']
        name+=('LGN'+proj.src.properties['polarity']+'Afferent')
        if sf_channel>1: name+=('SF'+str(proj.src.properties['SF']))

        return [{'delay':LGN_V1_delay+lag,
                 'dest_port':('Activity','JointNormalize','Afferent'),
                 'name':        name if lag==0 else name+('Lag'+str(lag)),
                 'learning_rate':self.aff_lr,
                 'strength':self.aff_strength*(1.0 if not self.gain_control else 1.5),
                 'weights_generator':imagen.random.GaussianCloud(gaussian_size=
                                        2.0*self.v1aff_radius*self.sf_spacing**(sf_channel-1)),
                 'nominal_bounds_template':sheet.BoundingBox(radius=
                                            self.v1aff_radius*self.sf_spacing**(sf_channel-1))}
                for lag in self.lags]


    @Model.connection('LateralV1ExcitatoryMatch', projection.CFProjection)
    def V1_lateralexcitatory_projections(self, proj):
        return {'delay':0.05,
                'name':'LateralExcitatory',
                'weights_generator':imagen.Gaussian(aspect_ratio=1.0, size=0.05),
                'strength':self.exc_strength,
                'learning_rate':self.exc_lr,
                'nominal_bounds_template':sheet.BoundingBox(radius=self.latexc_radius)}


    @Model.connection('LateralV1InhibitoryMatch', projection.CFProjection)
    def V1_lateralinhibitory_projections(self, proj):
        return {'delay':0.05,
                'name':'LateralInhibitory',
                'weights_generator':imagen.random.GaussianCloud(gaussian_size=0.15),
                'strength':-1.0*self.inh_strength,
                'learning_rate':self.inh_lr,
                'nominal_bounds_template':sheet.BoundingBox(radius=self.latinh_radius)}


    def _setup_analysis(self):
        # TODO: This is different in gcal.ty, stevens/gcal.ty and gcal_od.ty
        # And depends whether gain control is used or not
        import topo.analysis.featureresponses
        topo.analysis.featureresponses.FeatureMaps.selectivity_multiplier=2.0
        topo.analysis.featureresponses.FeatureCurveCommand.contrasts=[1, 10, 30, 50, 100]
        if 'dr' in self.dims:
            topo.analysis.featureresponses.MeasureResponseCommand.durations=[(max(self.lags)+1)*1.0]
        if 'sf' in self.dims:
            from topo.analysis.command import measure_sine_pref
            sf_relative_sizes = [self.sf_spacing**(sf_channel-1) for sf_channel in self.SF]
            wide_relative_sizes=[0.5*sf_relative_sizes[0]] + sf_relative_sizes + [2.0*sf_relative_sizes[-1]]
            relative_sizes=(wide_relative_sizes if self.expand_sf_test_range else sf_relative_sizes)
            #The default 2.4 spatial frequency value here is
            #chosen because it results in a sine grating with bars whose
            #width approximately matches the width of the Gaussian training
            #patterns, and thus the typical width of an ON stripe in one of the
            #receptive fields
            measure_sine_pref.frequencies = [2.4*s for s in relative_sizes]


