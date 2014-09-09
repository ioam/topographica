"""
Contains a variety of sensory models, specifically models for the
visual pathway.
"""
import colorsys

import topo
import param
import numbergen
import lancet
import numpy
import imagen


from imagen.patterncoordinator import PatternCoordinator, PatternCoordinatorImages
from imagen.image import ScaleChannels

from topo.base.arrayutil import DivideWithConstant
from topo.submodel import Model
from topo import sheet, transferfn

from collections import OrderedDict


class SensoryModel(Model):

    dims = param.List(default=['xy'],class_=str,doc="""
        Stimulus dimensions to include, out of the possible list:
          :'xy': Position in x and y coordinates""")

    num_inputs = param.Integer(default=2,bounds=(1,None),doc="""
        How many input patterns to present per unit area at each
        iteration, when using discrete patterns (e.g. Gaussians).""")



class VisualInputModel(SensoryModel):

    dataset = param.ObjectSelector(default='Gaussian',objects=
        ['Gaussian','Nature','FoliageA','FoliageB'],doc="""
        Set of input patterns to use::

          :'Gaussian': Two-dimensional Gaussians
          :'Nature':   Shouval's 1999 monochrome 256x256 images
          :'FoliageA': McGill calibrated LMS foliage/ image subset (5)
          :'FoliageB': McGill calibrated LMS foliage/ image subset (25)""")

    dims = param.List(default=['xy','or'],class_=str,doc="""
        Stimulus dimensions to include, out of the possible list:
          :'xy': Position in x and y coordinates
          :'or': Orientation
          :'od': Ocular dominance
          :'dy': Disparity
          :'dr': Direction of motion
          :'sf': Spatial frequency
          :'cr': Color (not implemented yet)""")

    area = param.Number(default=1.0,bounds=(0,None),
        inclusive_bounds=(False,True),doc="""
        Linear size of cortical area to simulate.
        2.0 gives a 2.0x2.0 Sheet area in V1.""")

    dim_fraction = param.Number(default=0.7,bounds=(0.0,1.0),doc="""
        Fraction by which the input brightness varies between the two
        eyes.  Only used if 'od' in 'dims'.""")

    contrast=param.Number(default=70, bounds=(0,100),doc="""
        Brightness of the input patterns as a contrast (percent). Only
        used if 'od' not in 'dims'.""")

    sf_spacing=param.Number(default=2.0,bounds=(1,None),doc="""
        Determines the factor by which successive SF channels increase
        in size.  Only used if 'sf' in 'dims'.""")

    sf_channels=param.Integer(default=2,bounds=(1,None),softbounds=(1,4),doc="""
        Number of spatial frequency channels. Only used if 'sf' in 'dims'.""")

    max_disparity = param.Number(default=4.0,bounds=(0,None),doc="""
        Maximum disparity between input pattern positions in the left
        and right eye. Only used if 'dy' in 'dims'.""")

    num_lags = param.Integer(default=4, bounds=(1,None),doc="""
        Number of successive frames before showing a new input
        pattern.  This also determines the number of connections
        between each individual LGN sheet and V1. Only used if 'dr' in
        'dims'.""")

    speed=param.Number(default=2.0/24.0,bounds=(0,None),
                       softbounds=(0,3.0/24.0),doc="""
        Distance in sheet coordinates between successive frames, when
        translating patterns. Only used if 'dr' in 'dims'.""")

    motion_buffer=param.Number(default=0.15,bounds=(0,None),doc="""
        Buffer in sheet coordinates by which the range should be
        extended where pattern are drawn from. Only used if
        'dr' in 'dims'.""")

    __abstract = True


    def property_setup(self, properties):
        properties = super(VisualInputModel, self).property_setup(properties)
        properties['binocular'] = 'od' in self.dims or 'dy' in self.dims
        properties['SF']=range(1,self.sf_channels+1) if 'sf' in self.dims and 'cr' not in self.dims else \
                         range(2,self.sf_channels+1) if 'sf' in self.dims and 'cr' in self.dims else [1]
        properties['lags'] = range(self.num_lags) if 'dr' in self.dims else [0]

        if 'dr' in self.dims and not numbergen.RandomDistribution.time_dependent:
            numbergen.RandomDistribution.time_dependent = True
            self.message('Setting time_dependent to True for motion model.')
        return properties


    def training_pattern_setup(self, **overrides):
        # all the below will eventually end up in PatternCoordinator!
        disparity_bound = 0.0
        position_bound_x = self.area/2.0+0.25
        position_bound_y = self.area/2.0+0.25

        if 'dy' in self.dims:
            disparity_bound = self.max_disparity*0.041665/2.0
            #TFALERT: Formerly: position_bound_x = self.area/2.0+0.2
            position_bound_x -= disparity_bound

        if 'dr' in self.dims:
            #TFALERT: Should probably depend on speed
            position_bound_x+=self.motion_buffer
            position_bound_y+=self.motion_buffer

        pattern_labels=['LeftRetina','RightRetina'] if self['binocular'] else ['Retina']
        # all the above will eventually end up in PatternCoordinator!
        params = dict(features_to_vary=self.dims,
                      pattern_labels=pattern_labels,
                      pattern_parameters={'size': 0.088388 if 'or' in self.dims and self.dataset=='Gaussian' \
                                           else 3*0.088388 if self.dataset=='Gaussian' else 10.0,
                                          'aspect_ratio': 4.66667 if 'or' in self.dims else 1.0,
                                          'scale': self.contrast/100.0},
                      disparity_bound=disparity_bound,
                      position_bound_x=position_bound_x,
                      position_bound_y=position_bound_y,
                      dim_fraction=self.dim_fraction,
                      reset_period=(max(self['lags'])+1),
                      speed=self.speed,
                      sf_spacing=self.sf_spacing,
                      sf_max_channel=max(self['SF']),
                      patterns_per_label=int(self.num_inputs*self.area*self.area))

        if self.dataset=='Gaussian':
            return PatternCoordinator(**dict(params, **overrides))()
        else:
            image_folder = 'images/shouval' if self.dataset=='Nature' \
                           else 'images/mcgill/foliage_a_combined' if self.dataset=='FoliageA' \
                           else 'images/mcgill/foliage_b_combined' if self.dataset=='FoliageB' \
                           else None
            return PatternCoordinatorImages(image_folder, **dict(params, **overrides))()



class EarlyVisionModel(VisualInputModel):

    retina_density = param.Number(default=24.0,bounds=(0,None),
        inclusive_bounds=(False,True),doc="""
        The nominal_density to use for the retina.""")

    lgn_density = param.Number(default=24.0,bounds=(0,None),
        inclusive_bounds=(False,True),doc="""
        The nominal_density to use for the LGN.""")

    lgnaff_radius=param.Number(default=0.375,bounds=(0,None),doc="""
        Connection field radius of a unit in the LGN level to units in
        a retina sheet.""")

    lgnlateral_radius=param.Number(default=0.5,bounds=(0,None),doc="""
        Connection field radius of a unit in the LGN level to
        surrounding units, in case gain control is used.""")

    v1aff_radius=param.Number(default=0.27083,bounds=(0,None),doc="""
        Connection field radius of a unit in V1 to units in a LGN
        sheet.""")

    gain_control = param.Boolean(default=True,doc="""
        Whether to use divisive lateral inhibition in the LGN for
        contrast gain control.""")

    gain_control_SF = param.Boolean(default=True,doc="""
        Whether to use divisive lateral inhibition in the LGN for
        contrast gain control across Spatial Frequency Sheets.""")

    strength_factor = param.Number(default=1.0,bounds=(0,None),doc="""
        Factor by which the strength of afferent connections from
        retina sheets to LGN sheets is multiplied.""")


    def property_setup(self, properties):
        properties = super(EarlyVisionModel, self).property_setup(properties)
        sheet.SettlingCFSheet.joint_norm_fn = sheet.optimized.compute_joint_norm_totals_opt
        center_polarities=['On','Off']

        # Useful for setting up sheets
        properties['polarities'] = lancet.List('polarity', center_polarities)
        properties['eyes'] = (lancet.List('eye', ['Left','Right'])
                              if properties['binocular'] else lancet.Identity())
        properties['SFs'] = (lancet.List('SF', properties['SF'])
                             if max(properties['SF'])>1 else lancet.Identity())
        return properties

    def sheet_setup(self):
        sheets = OrderedDict()
        sheets['Retina'] = self['eyes']
        sheets['LGN'] = self['polarities'] * self['eyes'] * self['SFs']
        return sheets


    @Model.ChannelGeneratorSheet
    def Retina(self, properties):
        return Model.ChannelGeneratorSheet.params(
            period=1.0,
            phase=0.05,
            nominal_density=self.retina_density,
            nominal_bounds=sheet.BoundingBox(radius=self.area/2.0
                                + self.v1aff_radius*self.sf_spacing**(max(self['SF'])-1)
                                + self.lgnaff_radius*self.sf_spacing**(max(self['SF'])-1)
                                + self.lgnlateral_radius),
            input_generator=self['training_patterns'][properties['eye']+'Retina'
                                                      if 'eye' in properties
                                                      else 'Retina'])


    @Model.SettlingCFSheet
    def LGN(self, properties):
        channel=properties['SF'] if 'SF' in properties else 1

        sf_aff_multiplier = self.sf_spacing**(max(self['SF'])-1) if self.gain_control_SF else \
                            self.sf_spacing**(channel-1)

        is_gaincontrol_sheet = self.gain_control_SF if 'SF' in properties else \
                               self.gain_control_color if 'opponent' in properties and properties['opponent']!='RedGreenBlue' else \
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
            tsettle=2 if is_gaincontrol_sheet else 0,
            strict_tsettle=1 if is_gaincontrol_sheet else 0)


    @Model.matchconditions('LGN', 'afferent')
    def afferent_conditions(self, properties):
        return {'level': 'Retina', 'eye': properties.get('eye',None)}


    @Model.SharedWeightCFProjection
    def afferent(self, src_properties, dest_properties):
        channel = dest_properties['SF'] if 'SF' in dest_properties else 1

        centerg   = imagen.Gaussian(size=0.07385*self.sf_spacing**(channel-1),
                                    aspect_ratio=1.0,
                                    output_fns=[transferfn.DivisiveNormalizeL1()])
        surroundg = imagen.Gaussian(size=(4*0.07385)*self.sf_spacing**(channel-1),
                                    aspect_ratio=1.0,
                                    output_fns=[transferfn.DivisiveNormalizeL1()])
        on_weights  = imagen.Composite(generators=[centerg,surroundg],operator=numpy.subtract)
        off_weights = imagen.Composite(generators=[surroundg,centerg],operator=numpy.subtract)

        return Model.SharedWeightCFProjection.params(
            delay=0.05,
            strength=2.33*self.strength_factor,
            name='Afferent',
            nominal_bounds_template=sheet.BoundingBox(radius=self.lgnaff_radius
                                                      *self.sf_spacing**(channel-1)),
            weights_generator=on_weights if dest_properties['polarity']=='On' else off_weights)


    @Model.matchconditions('LGN', 'lateral_gain_control')
    def lateral_gain_control_conditions(self, properties):
        return ({'level': 'LGN', 'polarity':properties['polarity']}
            if self.gain_control and self.gain_control_SF else
            {'level': 'LGN', 'polarity':properties['polarity'],
             'SF': properties.get('SF',None)}
            if self.gain_control else None)


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



class ColorEarlyVisionModel(EarlyVisionModel):

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

                individual_generator.channel_transforms.append(ScaleChannels(channel_factors = channel_factors))

        return Model.ChannelGeneratorSheet.params(
            period=1.0,
            phase=0.05,
            nominal_density=self.retina_density,
            nominal_bounds=sheet.BoundingBox(radius=self.area/2.0
                                + self.v1aff_radius*self.sf_spacing**(max(self['SF'])-1)
                                + self.lgnaff_radius*self.sf_spacing**(max(self['SF'])-1)
                                + self.lgnlateral_radius),
            input_generator=input_generator)


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
            strength=4.7*self.strength_factor/len(opponents)*(1 if dest_properties['polarity'] == 'On' else -1),
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
            strength=4.7*self.strength_factor/len(surrounds)*(-1 if dest_properties['polarity'] == 'On' else 1),
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
                 'surround':properties['surround']} if self.gain_control and 'opponent' in properties and properties['opponent']==luminosity_channel else
                {'level': 'LGN',
                 'polarity': properties['polarity']}
                if self.gain_control and \
                   self.gain_control_SF and \
                   'opponent' not in properties
                else
                {'level': 'LGN', 'polarity':properties['polarity'],
                 'SF': properties.get('SF',None)}
                if self.gain_control and 'opponent' not in properties else
                {'level': 'LGN', 'polarity':properties['polarity'],
                 'opponent':properties['opponent'],
                 'surround':properties['surround']}
                if self.gain_control_color and 'opponent' in properties and properties['opponent']!=luminosity_channel else None)
