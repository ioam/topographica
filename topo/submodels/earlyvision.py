"""
Contains a variety of sensory models, specifically models for the visual pathway.
"""
import param
import lancet
import numpy
import numbergen

from topo.base.arrayutil import DivideWithConstant
from topo.submodels import Model, SheetSpec
from topo import sheet,transferfn,pattern,projection
from topo.pattern.patterncoordinator import PatternCoordinator, PatternCoordinatorImages

class SensoryModel(Model):
    dims = param.List(default=['xy'],class_=str,doc="""
        Stimulus dimensions to include, out of the possible list:
          :'xy': Position in x and y coordinates""")

    num_inputs = param.Integer(default=2,bounds=(1,None),doc="""
        How many input patterns to present per unit area at each
        iteration, when using discrete patterns (e.g. Gaussians).""")


class VisualInputModel(SensoryModel):
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
        Fraction by which the input brightness varies between the two eyes.
        Only used if 'od' in 'dims'.""")

    contrast=param.Number(default=70, bounds=(0,100),doc="""
        Brightness of the input patterns as a contrast (percent). Only used if
        'od' not in 'dims'.""")

    sf_spacing=param.Number(default=2.0,bounds=(1,None),doc="""
        Determines the factor by which successive SF channels increase in size.
        Only used if 'sf' in 'dims'.""")

    sf_channels=param.Integer(default=2,bounds=(1,None),softbounds=(1,4),doc="""
        Number of spatial frequency channels. Only used if 'sf' in 'dims'.""")

    max_disparity = param.Number(default=4.0,bounds=(0,None),doc="""
        Maximum disparity between input pattern positions in the left and
        right eye. Only used if 'dy' in 'dims'.""")

    num_lags = param.Integer(default=4, bounds=(1,None),doc="""
        Number of successive frames before showing a new input pattern.
        This also determines the number of connections between each individual
        LGN sheet and V1. Only used if 'dr' in 'dims'.""")

    speed=param.Number(default=2.0/24.0,bounds=(0,None),softbounds=(0,3.0/24.0),doc="""
        Distance in sheet coordinates between successive frames, when
        translating patterns. Only used if 'dr' in 'dims'.""")

    __abstract = True


    def setup_attributes(self):
        super(VisualInputModel, self).setup_attributes()
        if 'od' in self.dims or 'dy' in self.dims:
            self.eyes=['Left','Right']
        else:
            self.eyes=['']

        if 'sf' in self.dims:
            # This list could be any list of the form
            # [x_1,x_2,...,x_n]
            # where x_1, x_2, ... are any arbitrary integers
            self.SF=range(1,self.sf_channels+1)
        else:
            self.sf_channels=1
            self.SF=[1]

        if 'dr' in self.dims:
            param.Dynamic.time_dependent = True
            numbergen.RandomDistribution.time_dependent = True
            self.message('time_dependent set to true for motion model!')
            # This list could be any list of the form
            # [x_1,x_2,...,x_n]
            # where x_1, x_2, ... are any arbitrary integers
            self.lags = range(self.num_lags)
        else:
            self.num_lags=1
            self.lags = [0]


    def setup_training_patterns(self):
        # all the below will eventually end up in PatternCoordinator!
        disparity_bound = 0.0
        position_bound_x = self.area/2.0+0.25
        position_bound_y = self.area/2.0+0.25

        if 'dy' in self.dims:
            disparity_bound = self.max_disparity*0.041665/2.0
            position_bound_x -= disparity_bound #TFALERT: Formerly: position_bound_x = self.area/2.0+0.2

        pattern_labels=[s + 'Retina' for s in self.eyes]
        # all the above will eventually end up in PatternCoordinator!

        return PatternCoordinator(
            features_to_vary=self.dims,
            pattern_labels=pattern_labels,
            pattern_parameters={'size': 0.088388 if 'or' in self.dims else 3*0.088388,
                                'aspect_ratio': 4.66667 if 'or' in self.dims else 1.0,
                                'scale': self.contrast/100.0},
            disparity_bound=disparity_bound,
            position_bound_x=position_bound_x,
            position_bound_y=position_bound_y,
            dim_fraction=self.dim_fraction,
            reset_period=(max(self.lags)+1),
            speed=self.speed,
            sf_spacing=self.sf_spacing,
            sf_max_channel=max(self.SF),
            patterns_per_label=int(self.num_inputs*self.area*self.area))()


class EarlyVisionModel(VisualInputModel):
    retina_density = param.Number(default=24.0,bounds=(0,None),
        inclusive_bounds=(False,True),doc="""
        The nominal_density to use for the retina.""")

    lgn_density = param.Number(default=24.0,bounds=(0,None),
        inclusive_bounds=(False,True),doc="""
        The nominal_density to use for the LGN.""")

    cortex_density=param.Number(default=47.0,bounds=(0,None),
        inclusive_bounds=(False,True),doc="""
        The nominal_density to use for V1.""")

    lgnaff_radius=param.Number(default=0.375,bounds=(0,None),doc="""
        Connection field radius of a unit in the LGN level to units in a retina sheet.""")

    lgnlateral_radius=param.Number(default=0.5,bounds=(0,None),doc="""
        Connection field radius of a unit in the LGN level to surrounding units,
        in case gain control is used.""")

    v1aff_radius=param.Number(default=0.27083,bounds=(0,None),doc="""
        Connection field radius of a unit in V1 to units in a LGN sheet.""")

    gain_control = param.Boolean(default=True,doc="""
        Whether to use divisive lateral inhibition in the LGN for contrast gain control.""")

    strength_factor = param.Number(default=1.0,bounds=(0,None),doc="""
        Factor by which the strength of afferent connections from retina sheets
        to LGN sheets is multiplied.""")


    def setup_attributes(self):
        super(EarlyVisionModel, self).setup_attributes()
        self.center_polarities=['On','Off']


    def setup_sheets(self):
        sheet_specs = []
        retina_product = lancet.Args(level='Retina')
        if len(self.eyes)>1:
            retina_product = retina_product * lancet.List('eye', self.eyes)

        for retina_properties in retina_product.specs:
            sheet_specs.append(SheetSpec(sheet.GeneratorSheet,retina_properties))

        lgn_product = lancet.Args(level='LGN') * lancet.List('polarity', self.center_polarities)
        if len(self.eyes)>1:
            lgn_product= lgn_product * lancet.List('eye', self.eyes)
        if max(self.SF)>1:
            lgn_product = lgn_product * lancet.List('SF', self.SF)

        for lgn_properties in lgn_product.specs:
            sheet_specs.append(SheetSpec(sheet.optimized.SettlingCFSheet_Opt,lgn_properties))
        return sheet_specs


    @Model.level('Retina')
    def retinal_sheet_parameters(self, properties):
        return {'period':1.0,
                'phase':0.05,
                'nominal_density':self.retina_density,
                'nominal_bounds':sheet.BoundingBox(radius=self.area/2.0 + \
                    self.v1aff_radius*self.sf_spacing**(max(self.SF)-1) + \
                    self.lgnaff_radius*self.sf_spacing**(max(self.SF)-1) + \
                    self.lgnlateral_radius),
                'input_generator':self.training_patterns[properties['eye']+'Retina' if 'eye' in properties
                                                             else 'Retina']}


    @Model.level('LGN')
    def LGN_sheet_parameters(self, properties):
        channel=properties['SF'] if 'SF' in properties else 1

        return {'measure_maps':False,
                'output_fns': [transferfn.misc.HalfRectify()],
                'nominal_density':self.lgn_density,
                'nominal_bounds':sheet.BoundingBox(radius=self.area/2.0 + \
                    self.v1aff_radius*self.sf_spacing**(channel-1) + self.lgnlateral_radius),
                'tsettle':2 if self.gain_control else 0,
                'strict_tsettle': 1 if self.gain_control else 0}


    @Model.matchconditions('LGN')
    def LGN_matchconditions(self, properties):
        """
        A matchcondition is created allowing incoming projections of
        retina sheets of the same eye as the LGN sheet.  If gain
        control is enabled, also connect to LGN sheets of the same
        polarity (and, if SF is used, the same SF channel).
        """
        return {'Afferent':  {'level': 'Retina', 'eye': properties.get('eye',None)},
                'LateralGC': {'level': 'LGN', 'polarity':properties['polarity'],
                              'SF': properties.get('SF',None)}
                              if self.gain_control else None}


    @Model.connection('Afferent', projection.SharedWeightCFProjection)
    def LGN_afferent_projections(self, proj):
        channel = proj.dest.properties['SF'] if 'SF' in proj.dest.properties else 1

        centerg   = pattern.Gaussian(size=0.07385*self.sf_spacing**(channel-1),
                                     aspect_ratio=1.0,
                                     output_fns=[transferfn.DivisiveNormalizeL1()])
        surroundg = pattern.Gaussian(size=(4*0.07385)*self.sf_spacing**(channel-1),
                                     aspect_ratio=1.0,
                                     output_fns=[transferfn.DivisiveNormalizeL1()])
        on_weights  = pattern.Composite(generators=[centerg,surroundg],operator=numpy.subtract)
        off_weights = pattern.Composite(generators=[surroundg,centerg],operator=numpy.subtract)

        #TODO: strength=+strength_scale/len(cone_types) for 'On' center
        #TODO: strength=-strength_scale/len(cone_types) for 'Off' center
        #TODO: strength=-strength_scale/len(cone_types) for 'On' surround
        #TODO: strength=+strength_scale/len(cone_types) for 'Off' surround
        return {'delay':0.05,
                'strength':2.33*self.strength_factor,
                'name':'Afferent',
                'nominal_bounds_template':sheet.BoundingBox(radius=self.lgnaff_radius*self.sf_spacing**(channel-1)),
                'weights_generator':on_weights if proj.dest.properties['polarity']=='On' else off_weights}


    @Model.connection('LateralGC', projection.SharedWeightCFProjection)
    def LGN_lateral_projections(self, proj):
        #TODO: Are those 0.25 the same as lgnlateral_radius/2.0?
        return {'delay':0.05,
                'dest_port':('Activity'),
                'activity_group':(0.6,DivideWithConstant(c=0.11)),
                'weights_generator':pattern.Gaussian(size=0.25,
                                                     aspect_ratio=1.0,
                                                     output_fns=[transferfn.DivisiveNormalizeL1()]),
                'nominal_bounds_template':sheet.BoundingBox(radius=0.25),
                'name':'LateralGC'+proj.src.properties['eye'] if 'eye' in proj.src.properties else 'LateralGC',
                'strength':0.6/len(self.eyes)}


class ColorEarlyVisionModel(EarlyVisionModel):
    gain_control_color = param.Boolean(default=False,doc="""
        Whether to use divisive lateral inhibition in the LGN for contrast gain control in color sheets.""")


    def setup_attributes(self):
        super(ColorEarlyVisionModel, self).setup_attributes()
        if 'cr' in self.dims:
            self.opponent_types_center   = ['Red',   'Green', 'Blue',     'RedGreenBlue']
            self.opponent_types_surround = ['Green', 'Red',   'RedGreen', 'RedGreenBlue']
            self.cone_types              = ['Red','Green','Blue']
        else:
            self.opponent_types_center   = []
            self.opponent_types_surround = []
            self.cone_types              = []



    def setup_sheets(self):
        sheet_specs = []
        retina_product = lancet.Args(level='Retina')
        if len(self.eyes)>1:
            retina_product = retina_product * lancet.List('eye', self.eyes)
        if self.cone_types:
            retina_product = retina_product * lancet.List('cone', self.cone_types)

        for retina_properties in retina_product.specs:
            sheet_specs.append(SheetSpec(sheet.GeneratorSheet, retina_properties))

        lgn_product = lancet.Args(level='LGN') * lancet.List('polarity', self.center_polarities)
        if len(self.eyes)>1:
            lgn_product= lgn_product * lancet.List('eye', self.eyes)
        if max(self.SF)>1 and self.opponent_types_center:
            lgn_product = lgn_product * (lancet.List('SF', self.SF)
                + lancet.Args(specs=[dict(opponent=el1, surround=el2)
                              for el1, el2 in zip(self.opponent_types_center, self.opponent_types_surround)]))
        elif max(self.SF)>1:
            lgn_product = lgn_product * lancet.List('SF', self.SF)
        elif self.opponent_types_center:
            lgn_product = lgn_product * lancet.Args(specs=[dict(opponent=el1, surround=el2)
                              for el1, el2 in zip(self.opponent_types_center, self.opponent_types_surround)])

        for lgn_properties in lgn_product.specs:
            sheet_specs.append(SheetSpec(sheet.optimized.SettlingCFSheet_Opt,lgn_properties))
        return sheet_specs



    @Model.matchconditions('LGN')
    def LGN_matchconditions(self, properties):
        """
        If it is a sheet related to color, two
        ProjectionMatchConditions objects named AfferentCenter and
        AfferentSurround are created allowing incoming projections of
        retina sheets of the same eye as the LGN sheet, whereas the
        retina sheet must have the same cone type as the opponent
        center / opponent surround.

        If the sheet is not related to color, a
        ProjectionMatchCondition object named Afferent is created
        allowing incoming projections of retina sheets of the same eye
        as the LGN sheet.
        """
        return {'AfferentCenter':{'level': 'Retina',
                                  'cone': properties['opponent'],
                                  'eye': properties.get('eye',None)}
                                  if 'opponent' in properties else None,

                'AfferentSurround':{'level': 'Retina',
                                    'cone': properties['surround'],
                                    'eye': properties.get('eye',None)}
                                    if 'surround' in properties else None,

                'Afferent':{'level': 'Retina', 'eye': properties.get('eye')}
                            if 'opponent' not in properties else None,

                'LateralGC':{'level': 'LGN',
                             'polarity': properties['polarity'],
                             'SF': properties.get('SF',None)}
                             if self.gain_control and 'opponent' not in properties else
                            {'level': 'LGN', 'polarity':properties['polarity'],
                             'opponent':properties['opponent'],
                             'surround':properties['surround']}
                             if self.gain_control_color and 'opponent' in properties else None}


    @Model.connection('Afferent', projection.SharedWeightCFProjection)
    def LGN_afferent_projections(self, proj):
        parameters = super(ColorEarlyVisionModel,self).LGN_afferent_projections(proj)
        if 'opponent' in proj.dest.properties:
            parameters['name']+=proj.dest.properties['opponent']+proj.src.properties['cone']
        return parameters


    @Model.connection('AfferentCenter', projection.SharedWeightCFProjection)
    def LGN_afferent_center_projections(self, proj):
        #TODO: It shouldn't be too hard to figure out how many retina sheets it connects to,
        #      then all the below special cases can be generalized!
        #TODO: strength=+strength_scale for 'On', strength=-strength_scale for 'Off'
        #TODO: strength=+strength_scale for dest_properties['opponent']=='Blue'
        #      dest_properties['surround']=='RedGreen' and dest_properties['polarity']=='On'
        #TODO: strength=-strength_scale for above, but 'Off'
        #TODO: strength=+strength_scale/len(cone_types) for Luminosity 'On'
        #TODO: strength=-strength_scale/len(cone_types) for Luminosity 'Off'
        return {'delay':0.05,
                'strength':2.33*self.strength_factor,
                'weights_generator':pattern.Gaussian(size=0.07385,
                                                     aspect_ratio=1.0,
                                                     output_fns=[transferfn.DivisiveNormalizeL1()]),
                'name':'AfferentCenter'+proj.src.properties['cone'],
                'nominal_bounds_template':sheet.BoundingBox(radius=self.lgnaff_radius)}


    @Model.connection('AfferentSurround', projection.SharedWeightCFProjection)
    def LGN_afferent_surround_projections(self, proj):
        #TODO: strength=-strength_scale for 'On', +strength_scale for 'Off'
        #TODO: strength=-strength_scale/2 for dest_properties['opponent']=='Blue'
        #      dest_properties['surround']=='RedGreen' and dest_properties['polarity']=='On'
        #TODO: strength=+strength_scale/2 for above, but 'Off'
        #TODO: strength=-strength_scale/len(cone_types) for Luminosity 'On'
        #TODO: strength=+strength_scale/len(cone_types) for Luminosity 'Off'
        return {'delay':0.05,
                'strength':2.33*self.strength_factor,
                'weights_generator':pattern.Gaussian(size=4*0.07385,
                                                     aspect_ratio=1.0,
                                                     output_fns=[transferfn.DivisiveNormalizeL1()]),
                'name':'AfferentSurround'+proj.src.properties['cone'],
                'nominal_bounds_template':sheet.BoundingBox(radius=self.lgnaff_radius)}


