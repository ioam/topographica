"""
Contains a model for the visual pathway with support for color.
Also, a GCAL model of the visual cortex with support for color is included.
Please note that it will be able to remove most redundancies to the
non-color EarlyVisionModel and ModelGCALColor as soon as a modular
model structure is possible.
Using this file, the results of fischer:ms14 can be replicated.
"""
import colorsys

import topo
import param
import numbergen
import lancet
import imagen

from imagen.image import ScaleChannels

from topo.base.arrayutil import DivideWithConstant
from topo.submodel import Model
from topo.submodel.earlyvision import EarlyVisionModel
from topo import sheet, transferfn

from collections import OrderedDict

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
            period=1.0,
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
