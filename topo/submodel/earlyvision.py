"""
Contains a variety of sensory models, specifically models for the
visual pathway.
"""
import topo
import param
import numbergen
import lancet
import numpy
import imagen


from imagen.patterncoordinator import PatternCoordinator, PatternCoordinatorImages

from topo.base.arrayutil import DivideWithConstant
from topo.submodel import Model, ArraySpec # pyflakes:ignore (API import)
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

    allowed_dims = ['xy', 'or', 'od', 'dy', 'dr', 'sf']

    period = param.Number(default=None, allow_None=True, doc="""
       Simulation time between pattern updates on the generator
       sheets. If None, the model is allowed to compute an appropriate
       value for the period property (a period of 1.0 is typical)""")

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
          :'cr': Color (if available, see submodels.color)""")

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

    align_orientations = param.Boolean(default=None,
                                       allow_None=True, doc="""
        Whether or not to align pattern orientations together if
        composing multiple patterns together. If None,
        align_orientations will be set to True when speed is non-zero
        (and 'dr' in dims), otherwise it is set to False.""")

    __abstract = True


    def property_setup(self, properties):

        disallowed_dims = [dim for dim in self.dims if dim not in self.allowed_dims]
        if disallowed_dims:
            raise Exception('%s not in the list of allowed dimensions'
                            % ','.join(repr(d) for d in disallowed_dims))

        properties = super(VisualInputModel, self).property_setup(properties)

        # The default period for most Topographica models is 1.0
        properties['period'] = 1.0 if self.period is None else self.period
        properties['binocular'] = 'od' in self.dims or 'dy' in self.dims
        properties['SF']=range(1,self.sf_channels+1) if 'sf' in self.dims else [1]
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

        align_orientations = (bool(self.speed) and ('dr' in self.dims)
                              if self.align_orientations is None
                              else self.align_orientations)
        if 'dr' in self.dims:
            position_bound_x+=self.speed*max(self['lags'])
            position_bound_y+=self.speed*max(self['lags'])

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
                      reset_period=(max(self['lags'])*self['period'] + self['period']),
                      speed=self.speed,
                      align_orientations = align_orientations,
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


@Model.definition
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

    center_size = param.Number(default=0.07385,bounds=(0,None),doc="""
        The size of the central Gaussian used to compute the
        center-surround receptive field.""")

    surround_size = param.Number(default=4*0.07385,bounds=(0,None),doc="""
        The size of the surround Gaussian used to compute the
        center-surround receptive field.""")

    gain_control_size = param.Number(default=0.25,bounds=(0,None),doc="""
        The size of the divisive inhibitory suppressive field used for
        contrast-gain control in the LGN sheets. This also acts as the
        corresponding bounds radius.""")

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

    @Model.GeneratorSheet
    def Retina(self, properties):
        return Model.GeneratorSheet.params(
            period=self['period'],
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

        gain_control = self.gain_control_SF if 'SF' in properties else self.gain_control

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
        return {'level': 'Retina', 'eye': properties.get('eye',None)}


    @Model.SharedWeightCFProjection
    def afferent(self, src_properties, dest_properties):
        channel = dest_properties['SF'] if 'SF' in dest_properties else 1

        centerg   = imagen.Gaussian(size=self.center_size*self.sf_spacing**(channel-1),
                                    aspect_ratio=1.0,
                                    output_fns=[transferfn.DivisiveNormalizeL1()])
        surroundg = imagen.Gaussian(size=self.surround_size*self.sf_spacing**(channel-1),
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

        return Model.SharedWeightCFProjection.params(
            delay=0.05,
            dest_port=('Activity'),
            activity_group=(0.6,DivideWithConstant(c=0.11)),
            weights_generator=imagen.Gaussian(size=self.gain_control_size,
                                              aspect_ratio=1.0,
                                              output_fns=[transferfn.DivisiveNormalizeL1()]),
            nominal_bounds_template=sheet.BoundingBox(radius=self.gain_control_size),
            name=name,
            strength=0.6/(2 if self['binocular'] else 1))
