"""
Contains a model for the visual pathway with support for color
including a version of the GCAL model with color support.

Please note that it will be able to remove most redundancies to the
non-color EarlyVisionModel and ModelGCALColor as soon as a more
modular system is implemented.


This file allows the results of fischer:ms14 to be replicated.
"""

import colorsys

import topo
import param
import imagen
import numbergen
import lancet


from topo import projection, responsefn, learningfn, transferfn, sheet
import topo.learningfn.optimized
import topo.transferfn.optimized
import topo.responsefn.optimized
import topo.sheet.optimized
import topo.transferfn.misc

from imagen.image import ScaleChannels

from topo.base.arrayutil import DivideWithConstant
from collections import OrderedDict

from topo.submodel import Model, ArraySpec # pyflakes:ignore (API import)
from topo.submodel.earlyvision import EarlyVisionModel

@Model.definition
class ColorEarlyVisionModel(EarlyVisionModel):
    """
    An EarlyVisionModel extended with color support.
    """

    allowed_dims = EarlyVisionModel.allowed_dims + ['cr']

    gain_control_color = param.Boolean(default=False,doc="""
        Whether to use divisive lateral inhibition in the LGN for
        contrast gain control in color sheets.""")

    cone_scale=param.List(default=[0.9,1.0,0.97],doc="""
        Scaling factors for the [L,M,S] cones.  Default values are from De Paula (2007).
        Allows individual photoreceptor channels to be boosted or reduced relative
        to each other, e.g. to approximate the final result of a homeostatic process
        not being simulated.""")

    color_strength=param.Number(default=0.75,bounds=(0.0,None),doc="""
        Ratio between strengths of LGN color vs. luminosity channel connections to V1.
        Examples::

          :0.00: Monochrome simulation
          :0.50: Equal weight to color vs. luminosity channels
          :0.75: Equal weight to each channel (assuming 6 color and 2 lum channels)
          :1.00: No luminosity channels

        Note that luminosity channels are not required for developing monochromatic
        responses, so even for color_strength=1.0 there are normally
        orientation-selective and not color-selective neurons.""")

    color_sim_type=param.ObjectSelector(default='Trichromatic',objects=
        ['Dichromatic','Trichromatic'],doc="""
        Whether the simulation should be dichromatic or trichromatic when
        'cr' in dims.""")


    def property_setup(self, properties):
        properties = super(ColorEarlyVisionModel, self).property_setup(properties)

        properties['SF']=range(1,self.sf_channels+1) if 'sf' in self.dims and 'cr' not in self.dims else \
                         range(2,self.sf_channels+1) if 'sf' in self.dims and 'cr' in self.dims else [1]
        properties['SFs'] = (lancet.List('SF', properties['SF'])
                             if max(properties['SF'])>1 else lancet.Identity())

        cr = 'cr' in self.dims
        #TFALERT: Dichromatic simulations have not been tested!
        opponent_types_center =   ['Red','Green','Blue','RedGreenBlue'] if cr \
                                    and self.color_sim_type=='Trichromatic' else \
                                  ['Green','Blue','GreenBlue'] if cr \
                                    and self.color_sim_type=='Dichromatic' else []
        opponent_types_surround = ['Green','Red','RedGreen','RedGreenBlue'] if cr \
                                    and self.color_sim_type=='Trichromatic' else \
                                  ['Green','Green','GreenBlue'] if cr \
                                    and self.color_sim_type=='Dichromatic' else []
        self.ColorToChannel = {'Red':0, 'Green':1, 'Blue':2} if cr else {}

        # Definitions useful for setting up sheets
        opponent_specs =[dict(opponent=el1, surround=el2) for el1, el2
                         in zip(opponent_types_center,
                                opponent_types_surround)]
        properties['opponents'] = (lancet.Args(specs=opponent_specs)
                                   if opponent_types_center else lancet.Identity())
        return properties


    def sheet_setup(self):
        sheets = OrderedDict()
        sheets['Retina'] = self['eyes']
        sheets['LGN'] = (self['polarities'] * self['eyes']
                         * (self['SFs'] + self['opponents']))
        return sheets


    @Model.ChannelGeneratorSheet
    def Retina(self, properties):
        input_generator=self['training_patterns'][properties['eye']+'Retina'
                                                     if 'eye' in properties
                                                     else 'Retina']
        if 'cr' in self.dims and self.dataset!='Gaussian':
            for pattern_number, individual_generator in enumerate(input_generator.generators):
                brightness_difference=numbergen.UniformRandom(lbound=(-1.0+self.dim_fraction)/2.0,
                                                              ubound=(1.0-self.dim_fraction)/2.0,
                                                              seed=456+pattern_number,
                                                              name="Dim"+str(pattern_number))
                if 'eye' in properties and properties['eye']=='Left':
                    hsv = colorsys.rgb_to_hsv(*self.cone_scale)
                    hsv_dimmed=(hsv[0],hsv[1],hsv[2]+brightness_difference)
                    channel_factors = list(colorsys.hsv_to_rgb(*hsv_dimmed))
                elif 'eye' in properties and properties['eye']=='Right':
                    hsv = colorsys.rgb_to_hsv(*self.cone_scale)
                    hsv_dimmed=(hsv[0],hsv[1],hsv[2]-brightness_difference)
                    channel_factors = list(colorsys.hsv_to_rgb(*hsv_dimmed))
                else:
                    channel_factors = self.cone_scale

                individual_generator.channel_transforms.append(
                    ScaleChannels(channel_factors = channel_factors))

        return Model.ChannelGeneratorSheet.params(
            period=self['period'],
            phase=0.05,
            nominal_density=self.retina_density,
            nominal_bounds=sheet.BoundingBox(radius=self.area/2.0
                                + self.v1aff_radius*self.sf_spacing**(max(self['SF'])-1)
                                + self.lgnaff_radius*self.sf_spacing**(max(self['SF'])-1)
                                + self.lgnlateral_radius),
            input_generator=input_generator)


    #TFALERT: This method is duplicated. The only change compared to the corresponding
    #method in EarlyVisionModel is the more complex gain_control variable.
    @Model.SettlingCFSheet
    def LGN(self, properties):
        channel=properties['SF'] if 'SF' in properties else 1

        sf_aff_multiplier = self.sf_spacing**(max(self['SF'])-1) if self.gain_control_SF else \
                            self.sf_spacing**(channel-1)

        luminosity_channel='RedGreenBlue' if self.color_sim_type=='Trichromatic' else 'GreenBlue'

        gain_control = self.gain_control_SF if 'SF' in properties else \
                       self.gain_control_color if 'opponent' in properties and \
                                                properties['opponent']!=luminosity_channel else \
                       self.gain_control

        return Model.SettlingCFSheet.params(
            mask = topo.base.projection.SheetMask(),
            measure_maps=False,
            output_fns=[transferfn.misc.HalfRectify()],
            nominal_density=self.lgn_density,
            nominal_bounds=sheet.BoundingBox(radius=self.area/2.0
                                             + self.v1aff_radius
                                             * sf_aff_multiplier
                                             + self.lgnlateral_radius),
            tsettle=2 if gain_control else 0,
            strict_tsettle=1 if gain_control else 0)


    @Model.matchconditions('LGN', 'afferent')
    def afferent_conditions(self, properties):
        return ({'level': 'Retina', 'eye': properties.get('eye')}
                if 'opponent' not in properties else None)


    @Model.matchconditions('LGN', 'afferent_center')
    def afferent_center_conditions(self, properties):
        return ({'level': 'Retina',
                 'eye': properties.get('eye',None)}
                if 'opponent' in properties else None)


    @Model.SharedWeightCFProjection
    def afferent_center(self, src_properties, dest_properties):
        opponents=[]
        for color, color_code in self.ColorToChannel.items():
            if color in dest_properties['opponent']:
                opponents.append(color_code)

        return [Model.SharedWeightCFProjection.params(
            delay=0.05,
            strength=(4.7/2.33)*self.lgnaff_strength/len(opponents)*(1 if dest_properties['polarity'] == 'On' else -1),
            src_port='Activity%d'%opponent,
            dest_port='Activity',
            weights_generator=imagen.Gaussian(size=0.07385,
                                              aspect_ratio=1.0,
                                              output_fns=[transferfn.DivisiveNormalizeL1()]),
            name='AfferentCenter'+str(opponent),
            nominal_bounds_template=sheet.BoundingBox(radius=self.lgnaff_radius))
            for opponent in opponents]


    @Model.matchconditions('LGN', 'afferent_surround')
    def afferent_surround_conditions(self, properties):
        return ({'level': 'Retina',
                 'eye': properties.get('eye',None)}
                if 'surround' in properties else None)


    @Model.SharedWeightCFProjection
    def afferent_surround(self, src_properties, dest_properties):
        surrounds=[]
        for color, color_code in self.ColorToChannel.items():
            if color in dest_properties['surround']:
                surrounds.append(color_code)

        return [Model.SharedWeightCFProjection.params(
            delay=0.05,
            strength=(4.7/2.33)*self.lgnaff_strength/len(surrounds)*(-1 if dest_properties['polarity'] == 'On' else 1),
            src_port='Activity%d'%surround,
            dest_port='Activity',
            weights_generator=imagen.Gaussian(size=0.07385*(4 if dest_properties['opponent'] is not 'Blue' else 1),
                                              aspect_ratio=1.0,
                                              output_fns=[transferfn.DivisiveNormalizeL1()]),
            name='AfferentSurround'+str(surround),
            nominal_bounds_template=sheet.BoundingBox(radius=self.lgnaff_radius))
            for surround in surrounds]


    @Model.matchconditions('LGN', 'lateral_gain_control')
    def lateral_gain_control_conditions(self, properties):
        # The projection itself is defined in the super class
        luminosity_channel='RedGreenBlue' if self.color_sim_type=='Trichromatic' else 'GreenBlue'
        return ({'level': 'LGN', 'polarity':properties['polarity'],
                 'opponent':properties['opponent'],
                 'surround':properties['surround']}
                if (self.gain_control and 'opponent' in properties \
                                      and properties['opponent']==luminosity_channel) or \
                   (self.gain_control_color and 'opponent' in properties
                                            and properties['opponent']!=luminosity_channel)
                else
                {'level': 'LGN',
                 'polarity': properties['polarity']}
                if self.gain_control and \
                   self.gain_control_SF and \
                   'opponent' not in properties
                else
                {'level': 'LGN', 'polarity':properties['polarity'],
                 'SF': properties.get('SF',None)}
                if self.gain_control and 'opponent' not in properties
                else None)


    #TFALERT: This method is duplicated. The only change compared to
    #lateral_gain_control in EarlyVisionModel is the introduction of color_factor
    @Model.SharedWeightCFProjection
    def lateral_gain_control(self, src_properties, dest_properties):
        #TODO: Are those 0.25 the same as lgnlateral_radius/2.0?
        name='LateralGC'
        if 'eye' in src_properties:
            name+=src_properties['eye']
        if 'SF' in src_properties and self.gain_control_SF:
            name+=('SF'+str(src_properties['SF']))

        #Using color_factor, outputs are comparable regardless
        #whether gain control is used or not
        color_factor=0.25 if 'cr' in self.dims else 1

        return Model.SharedWeightCFProjection.params(
            delay=0.05,
            dest_port=('Activity'),
            activity_group=(0.6*color_factor,DivideWithConstant(c=0.11)),
            weights_generator=imagen.Gaussian(size=0.25,
                                              aspect_ratio=1.0,
                                              output_fns=[transferfn.DivisiveNormalizeL1()]),
            nominal_bounds_template=sheet.BoundingBox(radius=0.25),
            name=name,
            strength=0.6/(2 if self['binocular'] else 1))


@Model.definition
class ModelGCALInheritingColor(ColorEarlyVisionModel):
    """
    This class file is identical to ModelGCAL (gcal.py) except for
     inheritinf from ColorEarlyVisionModel instead of
     EarlyVisionModel. Color-specific changes are implemented in the
     ModelGCAL subclass of this file.
    """

    cortex_density=param.Number(default=47.0,bounds=(0,None),
        inclusive_bounds=(False,True),doc="""
        The nominal_density to use for V1.""")

    homeostasis = param.Boolean(default=True, doc="""
        Whether or not the homeostatic adaption should be applied in V1""")

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


    def property_setup(self, properties):
        properties = super(ModelGCALInheritingColor, self).property_setup(properties)
        "Specify weight initialization, response function, and learning function"

        projection.CFProjection.cf_shape=imagen.Disk(smoothing=0.0)
        projection.CFProjection.response_fn=responsefn.optimized.CFPRF_DotProduct_opt()
        projection.CFProjection.learning_fn=learningfn.optimized.CFPLF_Hebbian_opt()
        projection.CFProjection.weights_output_fns=[transferfn.optimized.CFPOF_DivisiveNormalizeL1_opt()]
        projection.SharedWeightCFProjection.response_fn=responsefn.optimized.CFPRF_DotProduct_opt()
        return properties

    def sheet_setup(self):
        sheets = super(ModelGCALInheritingColor,self).sheet_setup()
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
                for lag in self['lags']]


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


    def analysis_setup(self):
        # TODO: This is different in gcal.ty, stevens/gcal.ty and gcal_od.ty
        # And depends whether gain control is used or not
        import topo.analysis.featureresponses
        topo.analysis.featureresponses.FeatureMaps.selectivity_multiplier=2.0
        topo.analysis.featureresponses.FeatureCurveCommand.contrasts=[1, 10, 30, 50, 100]
        if 'dr' in self.dims:
            topo.analysis.featureresponses.MeasureResponseCommand.durations=[(max(self['lags'])+1)*1.0]
        if 'sf' in self.dims:
            from topo.analysis.command import measure_sine_pref
            sf_relative_sizes = [self.sf_spacing**(sf_channel-1) for sf_channel in self['SF']]
            wide_relative_sizes=[0.5*sf_relative_sizes[0]] + sf_relative_sizes + [2.0*sf_relative_sizes[-1]]
            relative_sizes=(wide_relative_sizes if self.expand_sf_test_range else sf_relative_sizes)
            #The default 2.4 spatial frequency value here is
            #chosen because it results in a sine grating with bars whose
            #width approximately matches the width of the Gaussian training
            #patterns, and thus the typical width of an ON stripe in one of the
            #receptive fields
            measure_sine_pref.frequencies = [2.4*s for s in relative_sizes]


@Model.definition
class ModelGCALColor(ModelGCALInheritingColor):
    """
    Implementing of ModelGCAL including color support.

    As such, this class demonstrates the exact changes needed to the
    cortical sheet to support color, namely different strengths from
    the LGN to V1 depending on the type of LGN sheet (i.e. the
    luminosity sheet) as well as the addition of measurement code.

    This class can be used to replicate the results in fischer:ms14
    """
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

        #TFALERT: Changes regarding color begin
        if 'opponent' in src_properties:
            # Determine strength per channel from how many luminosity and color channels there are
            num_tot=len(self['polarities'])*len(self['opponents'])
            num_lum=len(self['polarities'])
            num_col=num_tot-num_lum
            color_scale=((1.0*num_tot/num_lum*(1.0-self.color_strength)) if src_properties['opponent']=="RedGreenBlue" else
                         (1.0*num_tot/num_col*self.color_strength))
        else: color_scale=1.0
        #TFALERT: Changes regarding color end

        #TFALERT: Mind the change in the strength compared to the non-color version
        return [Model.CFProjection.params(
                delay=LGN_V1_delay+lag,
                dest_port=('Activity','JointNormalize','Afferent'),
                name= name if lag==0 else name+('Lag'+str(lag)),
                learning_rate=self.aff_lr,
                strength=self.aff_strength*color_scale*
                            (1.0 if (not self.gain_control
                                     or ('opponent' in src_properties
                                         and not self.gain_control_color))
                            else 1.5),
                weights_generator=weights_generator,
                nominal_bounds_template=sheet.BoundingBox(radius=
                                            self.v1aff_radius*self.sf_spacing**(sf_channel-1)))
                for lag in self['lags']]


    def analysis_setup(self):
        super(ModelGCALColor, self).analysis_setup()
        if 'cr' in self.dims:
            from topo.analysis.command import measure_hue_pref, measure_od_pref
            from featuremapper.metaparams import contrast2scale, hue2rgbscaleNewRetina, ocular2leftrightscaleNewRetina
            measure_hue_pref.metafeature_fns=[contrast2scale, hue2rgbscaleNewRetina]
            measure_od_pref.metafeature_fns=[contrast2scale, ocular2leftrightscaleNewRetina]
