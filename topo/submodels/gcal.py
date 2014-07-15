import topo
import param
import imagen

from dataviews.collector import AttrTree

from topo import projection,responsefn,learningfn,transferfn,sheet,pattern
import topo.learningfn.optimized
import topo.transferfn.optimized
import topo.responsefn.optimized
import topo.sheet.optimized
import topo.transferfn.misc
import topo.pattern.random

from topo.submodels import EarlyVisionModel, ColorEarlyVisionModel, SheetRef


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


    def __init__(self, **params):
        super(ModelGCAL,self).__init__(**params)

        for l in self.lags:
            self.match_parameter_mapping['AfferentV1On'+str(l)]=self._specify_V1afferent_projection
            self.match_parameter_mapping['AfferentV1Off'+str(l)]=self._specify_V1afferent_projection
            self.match_connectiontype_mapping['AfferentV1On'+str(l)]=projection.CFProjection
            self.match_connectiontype_mapping['AfferentV1Off'+str(l)]=projection.CFProjection

        self.match_parameter_mapping['LateralV1Excitatory']=self._specify_V1lateralexcitatory_projection
        self.match_parameter_mapping['LateralV1Inhibitory']=self._specify_V1lateralinhibitory_projection
        self.match_connectiontype_mapping['LateralV1Excitatory']=projection.CFProjection
        self.match_connectiontype_mapping['LateralV1Inhibitory']=projection.CFProjection

        self.sheet_parameters_mapping['V1']=self._set_V1_sheet_parameters
        self.sheet_matchcondition_mapping['V1']=self._set_V1_sheet_matchconditions

        ### Specify weight initialization, response function, and learning function
        projection.CFProjection.cf_shape=imagen.Disk(smoothing=0.0)
        projection.CFProjection.response_fn=responsefn.optimized.CFPRF_DotProduct_opt()
        projection.CFProjection.learning_fn=learningfn.optimized.CFPLF_Hebbian_opt()
        projection.CFProjection.weights_output_fns=[transferfn.optimized.CFPOF_DivisiveNormalizeL1_opt()]
        projection.SharedWeightCFProjection.response_fn=responsefn.optimized.CFPRF_DotProduct_opt()


    def _setup_sheets(self):
        super(ModelGCAL,self)._setup_sheets()
        sheet_ref=SheetRef({'layer':'V1'},sheet.SettlingCFSheet)
        self.sheets.set_path(str(sheet_ref), sheet_ref)


    def _set_V1_sheet_parameters(self,v1_sheet_item):
        homeostatic_learning_rate = 0.01 if self.homeostasis else 0.0

        v1_sheet_item.parameters['tsettle']=16
        v1_sheet_item.parameters['plastic']=True
        v1_sheet_item.parameters['joint_norm_fn']=topo.sheet.optimized.compute_joint_norm_totals_opt
        v1_sheet_item.parameters['output_fns']=[transferfn.misc.HomeostaticResponse(t_init=self.t_init,
                                                    learning_rate=homeostatic_learning_rate)]
        v1_sheet_item.parameters['nominal_density']=self.cortex_density
        v1_sheet_item.parameters['nominal_bounds']=sheet.BoundingBox(radius=self.area/2.0)


    def _set_V1_sheet_matchconditions(self, v1_sheet_item):
        """
        V1 connects to all LGN sheets.
        Furthermore, it connects to itself with two projections:
            * one lateral connection which is excitatory (short-range)
            * one lateral connection which is inhibitory (long-range)
        """
        # TODO: Combine Afferent V1 On and Afferent V1 Off
        # As soon as time_dependent=True for weights
        for l in self.lags:
            v1_sheet_item.matchconditions['AfferentV1On'+str(l)]={'layer': 'LGN', 'polarity': 'On'}
            v1_sheet_item.matchconditions['AfferentV1Off'+str(l)]={'layer': 'LGN', 'polarity': 'Off'}
        v1_sheet_item.matchconditions['LateralV1Excitatory']={'layer': 'V1'}
        v1_sheet_item.matchconditions['LateralV1Inhibitory']={'layer': 'V1'}


    def _specify_V1afferent_projection(self, proj):
        sf_channel = proj.src.identifier['SF'] if 'SF' in proj.src.identifier else 1
        lag = proj.match_name[-1]
        # Adjust delays so same measurement protocol can be used with and without gain control.
        LGN_V1_delay = 0.05 if self.gain_control else 0.10

        proj.parameters['delay']=LGN_V1_delay+int(lag)
        proj.parameters['dest_port']=('Activity','JointNormalize','Afferent')
        proj.parameters['weights_generator']=\
            pattern.random.GaussianCloud(gaussian_size=2.0*self.v1aff_radius*self.sf_spacing**(sf_channel-1))
        proj.parameters['nominal_bounds_template']=\
            sheet.BoundingBox(radius=self.v1aff_radius*self.sf_spacing**(sf_channel-1))
        proj.parameters['name']=''
        if 'eye' in proj.src.identifier:
            proj.parameters['name']+=proj.src.identifier['eye']
        if 'opponent' in proj.src.identifier:
            proj.parameters['name']+=proj.src.identifier['opponent']+proj.src.identifier['surround']
        proj.parameters['name']+=('LGN'+proj.src.identifier['polarity']+'Afferent')
        if int(lag)>0:
            proj.parameters['name']+=('Lag'+lag)
        if sf_channel>1:
            proj.parameters['name']+=('SF'+str(proj.src.identifier['SF']))
        proj.parameters['learning_rate']=self.aff_lr#/len(self.lags) #TODO: Divide by num_aff
        proj.parameters['strength']=self.aff_strength*(1.0 if not self.gain_control else 1.5) # Divide by num_aff?


    def _specify_V1lateralexcitatory_projection(self, proj):
        proj.parameters['delay']=0.05
        proj.parameters['name']='LateralExcitatory'
        proj.parameters['weights_generator']=pattern.Gaussian(aspect_ratio=1.0, size=0.05)
        proj.parameters['strength']=self.exc_strength
        proj.parameters['nominal_bounds_template']=sheet.BoundingBox(radius=self.latexc_radius)
        proj.parameters['learning_rate']=self.exc_lr 


    def _specify_V1lateralinhibitory_projection(self, proj):
        proj.parameters['delay']=0.05
        proj.parameters['name']='LateralInhibitory'
        proj.parameters['weights_generator']=pattern.random.GaussianCloud(gaussian_size=0.15)
        proj.parameters['strength']=-1.0*self.inh_strength
        proj.parameters['nominal_bounds_template']=sheet.BoundingBox(radius=self.latinh_radius)
        proj.parameters['learning_rate']=self.inh_lr


    def _setup_analysis(self):
        ### Set up appropriate defaults for analysis
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
            # TODO: Where the heck is the 2.4 coming from?
            measure_sine_pref.frequencies = [2.4*s for s in relative_sizes]


