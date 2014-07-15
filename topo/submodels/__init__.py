"""
TODO: Write summary
"""

from collections import OrderedDict
import itertools

import numpy

import param
import lancet
import numbergen

import topo
from topo import sheet,transferfn,pattern,projection
from topo.base.sheet import Sheet
from topo.base.arrayutil import DivideWithConstant

from dataviews.collector import AttrTree

from topo.pattern.patterncoordinator import PatternCoordinator, PatternCoordinatorImages


class SheetRef(object):
    """
    SheetRef acts as a template for sheet objects. It is also possible to resolve the
    actual sheet object after it has been instantiated.

    The following attributes can be accessed:
    :'identifier': Dictionary specifying the identifier of the sheet. There must be a value given
    for the key 'layer'.
    :'sheet_type': Subclass of topo.base.sheet.Sheet.(read-only)
    :'parameters': Dictionary specifying which parameters should be passed to the sheet object
    specified with sheet_type. Keys are the parameter names, values the parameter values.
    :'matchconditions': Dictionary specifying the matchconditions of the sheet. This may be used
    to determine which other sheets this sheet should connect to.
    """

    @property
    def sheet_type(self):
        return self._sheet_type


    def __init__(self, identifier, sheet_type, parameters=None, matchconditions=None):
        """
        Initialize a SheetRef object. All arguments but parameters are just passed to the internal
        attributes. For parameters, additional key-value pairs with all possible parameters for the
        sheet type specified with sheet_type are added. This allows a lookup which parameters can
        be set.
        """
        self.identifier = identifier
        self._sheet_type = sheet_type
        self.parameters = {}
        for param_name, default_value in sheet_type.params().items():
            self.parameters[param_name]=default_value.default
        if parameters is not None: self.parameters.update(parameters)

        self.matchconditions = matchconditions
        if self.matchconditions is None: self.matchconditions={}


    def resolve(self):
        """
        Returns the actual sheet object after it has been instantiated.
        """
        from topo import sim
        return eval('sim.'+str(self)) 


    def __str__(self):
        """
        Returns a string representation combined from the identifier values.
        This might be used as name for the actual sheet object.
        """
        ident=self.identifier
        if ident['layer']=='LGN':
            name=''
            if 'eye' in ident:
                name+=ident['eye']
            name+=('LGN'+ident['polarity'])
            if 'SF' in ident and ident['SF']>1:
                name+=('SF'+str(ident['SF']))
            if 'opponent' in ident:
                name+=(ident['opponent']+'-'+ident['surround'])
        elif ident['layer']=='Retina':
            name=''
            if 'eye' in ident:
                name+=ident['eye']
            name+='Retina'
            if 'cone' in ident:
                name+=ident['cone']
        elif ident['layer']=='V1':
            name='V1'
        else:
            raise NameError('No name representation for sheet in layer' + ident['layer'])

        return name



class ProjectionRef(object):
    """
    ProjectionRef acts as a template for projections. It is also possible to resolve the
    actual projection after it has been instantiated.

    The following attributes can be accessed:
    :'src': SheetRef of the source sheet
    :'dst': SheetRef of the destionation sheet
    :'connection_type': Subclass of topo.base.projection.Projection
    :'match_name': Name of the matchcondition which has been used to set this projection up.
    This might be used to set the parameters of the ProjectionRef
    :'parameters': Dictionary specifying which parameters should be passed to the projection
    specified with connection_type. Keys are the parameter names, values the parameter values.
    """

    @property
    def connection_type(self):
        return self._connection_type


    def __init__(self, src, dst, connection_type, match_name=None, parameters=None):
        """
        Initialize a ProjectionRef object. All arguments but parameters are just passed to the internal
        attributes. For parameters, additional key-value pairs with all possible parameters for the
        projection type specified with connection_type are added. This allows a lookup which parameters can
        be set. Furthermore, parameters['src'] and parameters['dest'] are removed, as these must be set
        with the 'src' and 'dst' arguments instead.
        """
        self.src = src
        self.dst = dst
        self.match_name = match_name
        self.parameters = {}
        self._connection_type = connection_type
        for param_name, default_value in connection_type.params().items():
            self.parameters[param_name]=default_value.default
        if parameters is not None: self.parameters.update(parameters)
        # These parameters are directly passed into topo.sim.connect()!
        del self.parameters['src']
        del self.parameters['dest']


    def resolve(self):
        """
        Returns the actual projection after it has been instantiated.
        """
        from topo import sim
        return eval('sim.'+str(self.dst)+'.'+self.parameters['name'])


class SensoryModel(param.Parameterized): # TODO: declare abstract
    dims = param.List(default=['xy'],class_=str,doc="""
        Stimulus dimensions to include, out of the possible list:
          :'xy': Position in x and y coordinates""")

    num_inputs = param.Integer(default=2,bounds=(1,None),doc="""
        How many input patterns to present per unit area at each
        iteration, when using discrete patterns (e.g. Gaussians).""")

    sheet_parameters_mapping = param.Dict(default={},doc="""
        This dictionary is used to specify the parameters of sheets. It maps the layer of a SheetRef
        object (key) to either:
        a. a method which accepts the SheetRef object as first and only argument, which then modifies
        the parameters attribute of the SheetRef object accordingly, or
        b. a dictionary specifying the parameters of the SheetRef object.""")

    sheet_matchcondition_mapping = param.Dict(default={},doc="""
        This dictionary is used to specify which other sheets a sheet should connect to, whereas
        the sheet for which the mapping is created here is the destination sheet. It maps the
        layer of a SheetRef object (key) to either:
        a. a method which accepts the SheetRef object as first and only argument, which then modifies
        the matchconditions attribute of the SheetRef object accordingly, or
        b. a dictionary specifying the matchconditions of the SheetRef object.""")

    match_parameter_mapping = param.Dict(default=OrderedDict(),doc="""
        This dictionary is used to specify the parameters of projections. It maps the match_name of a 
        ProjectionRef object (key) to either:
        a. a method which accepts the ProjectionRef object as first and only argument, which then
        modifies the parameters attribute of the ProjectionRef object accordingly, or
        b. a dictionary specifying the parameters of the ProjectionRef object.

        The order of this mapping is respected while creating the sheets. That is, the sheets to be connected
        using the first ProjectionSpecification in this mapping are created first, and so on. To make use
        of this constraint, the match_parameter_mapping must be of the type collections.OrderedDict
        as the dict type in Python is unordered by default!
        """)

    match_connectiontype_mapping = param.Dict(default={}, doc="""
        This dictionary is used to specify the connection type of projections. It maps a matchconditions
        name of a SheetRef object (key) to the connection type to be used (value). The value must be a
        subclass of topo.base.projection.Projection""")

    def __init__(self, **params):
        super(SensoryModel,self).__init__(**params)
        self.sheets = AttrTree()
        self.projections = AttrTree()
        self.training_patterns = AttrTree()


    def setup(self,training_patterns=True,sheets=True,sheet_parameters=True,matchconditions=True,
              projections=True,projection_parameters=True,analysis=True):
        """
        This method can be used to setup certain aspects of the submodel. By default, all parts are setup.
        :'training_patterns': fills the training_patterns AttrTree with pattern generator instances. The path
        is the name of the retina. Usually calls PatternCoordinator to do this.
        :'setup_sheets': determines the amount of sheets, their types and names
        :'sheet_parameters': set sheet parameters according to the sheet_parameters_mapping dictionary
        :'matchconditions': set sheet matchconditions according to the sheet_matchcondition_mapping dictionary
        :'projections': determines which connections should be present between the sheets according to the
        matchconditions of SheetRef objects, using match_connectiontype_mapping to specify the connection type
        :'projection_paramters': set projection parameters according to the match_parameter_mapping dictionary
        """

        if(training_patterns):
            self._setup_training_patterns()
        if(sheets):
            self._setup_sheets()
        if(sheet_parameters):
            self._set_sheet_parameters()
        if(matchconditions):
            self._set_sheet_matchconditions()
        if(projections):
            self._setup_projections()
        if(projection_parameters):
            self._set_projection_parameters()
        if(analysis):
            self._setup_analysis()


    def _setup_training_patterns(self):
        """
        TODO: Add documentation what subclasses are supposed to do.
        """
        raise NotImplementedError


    def _setup_sheets(self):
        """
        TODO: Add documentation what subclasses are supposed to do.
        """
        raise NotImplementedError


    def _set_sheet_parameters(self):
        for ((_,), sheet_item) in self.sheets.path_items.items():
            if(callable(self.sheet_parameters_mapping[sheet_item.identifier['layer']])):
                self.sheet_parameters_mapping[sheet_item.identifier['layer']](sheet_item)
            else:
                sheet_item.parameters.update(self.sheet_parameters_mapping[sheet_item.identifier['layer']])


    def _set_sheet_matchconditions(self):
        for ((_,), sheet_item) in self.sheets.path_items.items():
            if(callable(self.sheet_matchcondition_mapping[sheet_item.identifier['layer']])):
                self.sheet_matchcondition_mapping[sheet_item.identifier['layer']](sheet_item)
            else:
                sheet_item.matchconditions.update(self.sheet_matchcondition_mapping[sheet_item.identifier['layer']])


    def _setup_projections(self):
        # Loop through all possible combinations of SheetRef objects in self.sheets
        # If the src_sheet fulfills all criteria specified in dst_sheet.matchconditions,
        # create a new ProjectionRef object and add this item to self.projections
        self.projections = AttrTree()

        for src_sheet, dst_sheet in itertools.product(self.sheets.path_items.values(), self.sheets.path_items.values()):
            for matchname, matchconditions in dst_sheet.matchconditions.items():
                is_match=True
                for incoming_key, incoming_value in matchconditions.items():
                    if incoming_key not in src_sheet.identifier \
                    or str(src_sheet.identifier[incoming_key]) not in str(incoming_value):
                        is_match=False
                        break

                if is_match:
                    self.projections.set_path(str(dst_sheet)+'.'+str(src_sheet)+'.'+matchname, 
                                         ProjectionRef(src_sheet, dst_sheet, 
                                                       self.match_connectiontype_mapping[matchname],matchname))


    def _set_projection_parameters(self):
        for ((_,_,_), proj) in self.projections.path_items.items():
            if(callable(self.match_parameter_mapping[proj.match_name])):
                self.match_parameter_mapping[proj.match_name](proj)
            else: 
                proj.parameters.update(self.match_parameter_mapping[proj.match_name])


    def _setup_analysis(self):
        """
        TODO: Add documentation what subclasses are supposed to do.
        """
        raise NotImplementedError


    def _instantiate_sheets(self):
        print 'Sheets:\n'
        for ((sheet_name,), sheet_item) in self.sheets.path_items.items():
            print sheet_name
            topo.sim[sheet_name]=sheet_item.sheet_type(**sheet_item.parameters)
        print '\n\n'


    def _instantiate_projections(self):
        print 'Connections:\n'
        #Ugly hack to take order in match_parameter_mapping into account
        #As soon as weight initialization is done with time_dependent=True,
        #this can be simplified to:
        #for ((_, _, projection_name), proj) in self.projections.path_items.items():
        for ((_, _, projection_name), proj) in \
            sorted(self.projections.path_items.items(),
                   key=lambda projection: self.match_parameter_mapping.keys().index(projection[1].match_name)):
            print 'Connect ' + str(proj.src) + ' with ' + str(proj.dst) + ' (Match name: ' + proj.match_name + \
                  ', connection name: ' + str(proj.parameters['name']) + ')'
            topo.sim.connect(str(proj.src),str(proj.dst),proj.connection_type,**proj.parameters)
        print '\n\n'


    def __call__(self,sheets=True,projections=True):
        """
        Instantiates all sheets / projections in self.sheets / self.projections and registers them in
        topo.sim
        """
        if(sheets):
            self._instantiate_sheets()
        if(projections):
            self._instantiate_projections()


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

    num_lags = param.Integer(default=4, bounds=(1,9),softbounds=(1,6),doc="""
        Number of successive frames before showing a new input pattern.
        This also determines the number of connections between each individual
        LGN sheet and V1. Only used if 'dr' in 'dims'.""")

    speed=param.Number(default=2.0/24.0,bounds=(0,None),softbounds=(0,3.0/24.0),doc="""
        Distance in sheet coordinates between successive frames, when
        translating patterns. Only used if 'dr' in 'dims'.""")

    def __init__(self, **params):
        super(VisualInputModel,self).__init__(**params)
        if 'od' in self.dims or 'dy' in self.dims:
            self.eyes=['Left','Right']
        else:
            self.eyes=[]

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
            print 'time_dependent set to true for motion model!'
            # This list could be any list of the form
            # [x_1,x_2,...,x_n]
            # where x_1, x_2, ... are any arbitrary integers
            self.lags = range(self.num_lags)
        else:
            self.num_lags=1
            self.lags = [0]


    def _setup_training_patterns(self):
        # all the below will eventually end up in PatternCoordinator!
        disparity_bound = 0.0
        position_bound_x = self.area/2.0+0.25
        position_bound_y = self.area/2.0+0.25

        if 'dy' in self.dims:
            disparity_bound = self.max_disparity*0.041665/2.0
            position_bound_x -= disparity_bound #TFALERT: Formerly: position_bound_x = self.area/2.0+0.2            

        if self.eyes:
            pattern_labels=[s + 'Retina' for s in self.eyes]
        else:
            pattern_labels=['Retina']
        # all the above will eventually end up in PatternCoordinator!

        pattern_generators = PatternCoordinator(
            features_to_vary=self.dims,
            pattern_labels=pattern_labels,
            pattern_parameters={'size': 0.088388 if 'or' in self.dims else 3*0.088388, 
                                'aspect_ratio': 4.66667 if 'or' in self.dims else 1.0, 
                                'scale': self.contrast/100.0},
            disparity_bound=disparity_bound,
            position_bound_x=position_bound_x,
            position_bound_y=position_bound_y,
            dim_fraction=self.dim_fraction,
            reset_period=(max(self.lags)+1)*1.0,
            speed=self.speed,
            sf_spacing=self.sf_spacing,
            sf_max_channel=max(self.SF),
            patterns_per_label=int(self.num_inputs*self.area*self.area))()

        for name, pattern_generator in pattern_generators.iteritems():
            self.training_patterns.set_path(name, pattern_generator)


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
        Connection field radius of a unit in the LGN layer to units in a retina sheet.""")

    lgnlateral_radius=param.Number(default=0.5,bounds=(0,None),doc="""
        Connection field radius of a unit in the LGN layer to surrounding units,
        in case gain control is used.""")

    v1aff_radius=param.Number(default=0.27083,bounds=(0,None),doc="""
        Connection field radius of a unit in V1 to units in a LGN sheet.""")

    gain_control = param.Boolean(default=True,doc="""
        Whether to use divisive lateral inhibition in the LGN for contrast gain control.""")

    strength_factor = param.Number(default=1.0,bounds=(0,None),doc="""
        Factor by which the strength of afferent connections from retina sheets
        to LGN sheets is multiplied.""")

    def __init__(self, **params):
        super(EarlyVisionModel,self).__init__(**params)

        self.center_polarities=['On','Off']

        # TODO: Get the names from the match parameters when defining them for skipping keys
        self.match_parameter_mapping['Afferent']=self._specify_lgn_afferent_projection
        self.match_connectiontype_mapping['Afferent']=projection.SharedWeightCFProjection
        if self.gain_control:
            self.match_parameter_mapping['LateralGC']=self._specify_lateralgc_projection
            self.match_connectiontype_mapping['LateralGC']=projection.SharedWeightCFProjection

        self.sheet_parameters_mapping['Retina']=self._set_retina_sheets_parameters
        self.sheet_parameters_mapping['LGN']=self._set_lgn_sheets_parameters

        self.sheet_matchcondition_mapping['Retina']={}
        self.sheet_matchcondition_mapping['LGN']=self._set_lgn_sheets_matchconditions


    def _setup_sheets(self):
        retina_product = lancet.Args(layer='Retina')
        if self.eyes:
            retina_product = retina_product * lancet.List('eye', self.eyes)

        for retina_item in retina_product.specs:
            sheet_ref=SheetRef(retina_item,sheet.GeneratorSheet)
            self.sheets.set_path(str(sheet_ref), sheet_ref)

        lgn_product = lancet.Args(layer='LGN') * lancet.List('polarity', self.center_polarities)
        if self.eyes:
            lgn_product= lgn_product * lancet.List('eye', self.eyes)
        if max(self.SF)>1:
            lgn_product = lgn_product * lancet.List('SF', self.SF)

        for lgn_item in lgn_product.specs:
            sheet_ref=SheetRef(lgn_item,sheet.optimized.SettlingCFSheet_Opt)
            self.sheets.set_path(str(sheet_ref), sheet_ref)


    def _set_retina_sheets_parameters(self,retina_sheet_item):
        identifier=retina_sheet_item.identifier

        retina_sheet_item.parameters['period']=1.0
        retina_sheet_item.parameters['phase']=0.05
        retina_sheet_item.parameters['nominal_density']=self.retina_density
        retina_sheet_item.parameters['nominal_bounds']=sheet.BoundingBox(radius=self.area/2.0 + \
                            self.v1aff_radius*self.sf_spacing**(max(self.SF)-1) + \
                            self.lgnaff_radius*self.sf_spacing**(max(self.SF)-1) + \
                            self.lgnlateral_radius)

        name=identifier['eye']+'Retina' if 'eye' in identifier else 'Retina'
        retina_sheet_item.parameters['input_generator']=self.training_patterns[name]


    def _set_lgn_sheets_parameters(self,lgn_sheet_item):
        identifier=lgn_sheet_item.identifier
        channel=identifier['SF'] if 'SF' in identifier else 1

        lgn_sheet_item.parameters['measure_maps']=False
        lgn_sheet_item.parameters['output_fns']=[transferfn.misc.HalfRectify()]
        lgn_sheet_item.parameters['nominal_density']=self.lgn_density
        lgn_sheet_item.parameters['nominal_bounds']=sheet.BoundingBox(radius=self.area/2.0 + \
            self.v1aff_radius*self.sf_spacing**(channel-1) + self.lgnlateral_radius)
        if self.gain_control:
            lgn_sheet_item.parameters['tsettle']=2
            lgn_sheet_item.parameters['strict_tsettle']=1
        else:
            lgn_sheet_item.parameters['tsettle']=0
            lgn_sheet_item.parameters['strict_tsettle']=0


    def _set_lgn_sheets_matchconditions(self, lgn_sheet_item):
        """
        A matchcondition is created allowing incoming projections of retina sheets of the same eye as the LGN sheet.
        If gain control is enabled, also connect to LGN sheets of the same polarity (and, if SF is used, the
        same SF channel).
        """
        identifier=lgn_sheet_item.identifier

        lgn_sheet_item.matchconditions['Afferent']={'layer': 'Retina'}
        if 'eye' in identifier:
            lgn_sheet_item.matchconditions['Afferent'].update({'eye': identifier['eye']})
        if self.gain_control:
            lgn_sheet_item.matchconditions['LateralGC']={'layer': 'LGN', 'polarity':identifier['polarity']}
            if 'SF' in identifier:
                lgn_sheet_item.matchconditions['LateralGC'].update({'SF': identifier['SF']})


    def _specify_lgn_afferent_projection(self, proj):
        channel = proj.dst.identifier['SF'] if 'SF' in proj.dst.identifier else 1

        centerg   = pattern.Gaussian(size=0.07385*self.sf_spacing**(channel-1),
                                     aspect_ratio=1.0,
                                     output_fns=[transferfn.DivisiveNormalizeL1()])
        surroundg = pattern.Gaussian(size=(4*0.07385)*self.sf_spacing**(channel-1),
                                     aspect_ratio=1.0,
                                     output_fns=[transferfn.DivisiveNormalizeL1()])
        on_weights  = pattern.Composite(generators=[centerg,surroundg],operator=numpy.subtract)
        off_weights = pattern.Composite(generators=[surroundg,centerg],operator=numpy.subtract)

        proj.parameters['delay']=0.05
        #TODO: strength=+strength_scale/len(cone_types) for 'On' center
        #TODO: strength=-strength_scale/len(cone_types) for 'Off' center
        #TODO: strength=-strength_scale/len(cone_types) for 'On' surround
        #TODO: strength=+strength_scale/len(cone_types) for 'Off' surround
        proj.parameters['strength']=2.33*self.strength_factor
        proj.parameters['name']='Afferent'
        proj.parameters['nominal_bounds_template']=\
            sheet.BoundingBox(radius=self.lgnaff_radius*self.sf_spacing**(channel-1))
        proj.parameters['weights_generator']=on_weights if proj.dst.identifier['polarity']=='On' else off_weights


    def _specify_lateralgc_projection(self, proj):
        proj.parameters['delay']=0.05
        proj.parameters['dest_port']=('Activity')
        proj.parameters['activity_group']=(0.6,DivideWithConstant(c=0.11))
        #TODO: Are those 0.25 the same as lgnlateral_radius/2.0?
        proj.parameters['weights_generator']=pattern.Gaussian(size=0.25,
                                                              aspect_ratio=1.0,
                                                              output_fns=[transferfn.DivisiveNormalizeL1()])
        proj.parameters['nominal_bounds_template']=sheet.BoundingBox(radius=0.25)
        proj.parameters['name']='LateralGC'
        if 'eye' in proj.src.identifier:
            proj.parameters['name']+=proj.src.identifier['eye']
        proj.parameters['strength']=0.6
        if self.eyes:
            proj.parameters['strength']/=len(self.eyes)


class ColorEarlyVisionModel(EarlyVisionModel):
    gain_control_color = param.Boolean(default=False,doc="""
        Whether to use divisive lateral inhibition in the LGN for contrast gain control in color sheets.""")

    def __init__(self, **params):
        super(ColorEarlyVisionModel,self).__init__(**params)
        
        if 'cr' in self.dims:
            self.opponent_types_center   = ['Red',   'Green', 'Blue',     'RedGreenBlue']
            self.opponent_types_surround = ['Green', 'Red',   'RedGreen', 'RedGreenBlue']
            self.cone_types              = ['Red','Green','Blue']

            self.match_parameter_mapping['AfferentCenter']=self._specify_lgn_afferentcenter_projection
            self.match_parameter_mapping['AfferentSurround']=self._specify_lgn_afferentsurround_projection
            self.match_connectiontype_mapping['AfferentCenter']=projection.SharedWeightCFProjection
            self.match_connectiontype_mapping['AfferentSurround']=projection.SharedWeightCFProjection
        else:
            self.opponent_types_center   = []
            self.opponent_types_surround = []
            self.cone_types              = []


    def _setup_sheets(self):
        retina_product = lancet.Args(layer='Retina')
        if self.eyes:
            retina_product = retina_product * lancet.List('eye', self.eyes)
        if self.cone_types:
            retina_product = retina_product * lancet.List('cone', self.cone_types)

        for retina_item in retina_product.specs:
            sheet_ref=SheetRef(retina_item,sheet.GeneratorSheet)
            self.sheets.set_path(str(sheet_ref), sheet_ref)

        lgn_product = lancet.Args(layer='LGN') * lancet.List('polarity', self.center_polarities)
        if self.eyes:
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

        for lgn_item in lgn_product.specs:
            sheet_ref=SheetRef(lgn_item,sheet.optimized.SettlingCFSheet_Opt)
            self.sheets.set_path(str(sheet_ref), sheet_ref)


    def _set_lgn_sheets_matchconditions(self, lgn_sheet_item):
        """
        If it is a sheet related to color, two ProjectionMatchConditions objects named AfferentCenter
        and AfferentSurround are created allowing incoming projections of retina sheets of the same eye
        as the LGN sheet, whereas the retina sheet must have the same cone type as the opponent center
        / opponent surround.

        If the sheet is not related to color, a ProjectionMatchCondition object
        named Afferent is created allowing incoming projections of retina sheets of the same eye as the LGN sheet.
        """
        identifier=lgn_sheet_item.identifier

        if 'opponent' in identifier:
            lgn_sheet_item.matchconditions['AfferentCenter']={'layer': 'Retina','cone': identifier['opponent']}
            lgn_sheet_item.matchconditions['AfferentSurround']={'layer': 'Retina','cone': identifier['surround']}
            if 'eye' in identifier:
                lgn_sheet_item.matchconditions['AfferentCenter'].update({'eye': identifier['eye']})
                lgn_sheet_item.matchconditions['AfferentSurround'].update({'eye': identifier['eye']})
        else:
            lgn_sheet_item.matchconditions['Afferent']={'layer': 'Retina'}
            if 'eye' in identifier:
                lgn_sheet_item.matchconditions['Afferent'].update({'eye': identifier['eye']})

        if self.gain_control and 'opponent' not in identifier:
            lgn_sheet_item.matchconditions['LateralGC']={'layer': 'LGN', 'polarity':identifier['polarity']}
            if 'SF' in identifier:
                lgn_sheet_item.matchconditions['LateralGC'].update({'SF': identifier['SF']})

        if self.gain_control_color and 'opponent' in identifier:
            lgn_sheet_item.matchconditions['LateralGC']={'layer': 'LGN', 'polarity':identifier['polarity'],
                                                         'opponent':identifier['opponent'], 
                                                         'surround':identifier['surround']}


    def _specify_lgn_afferent_projection(self, proj): # Do we need that?
        super(ColorEarlyVisionModel,self)._specify_lgn_afferent_projection(proj)
        if 'opponent' in proj.dst.identifier:
            proj.parameters['name']+=proj.dst.identifier['opponent']+proj.src.identifier['cone']

    def _specify_lgn_afferentcenter_projection(self, proj):  # specify_lgn_afferentcenter_projection(self, src, dst) : return {}
        proj.parameters['delay']=0.05
        #TODO: It shouldn't be too hard to figure out how many retina sheets it connects to,
        #      then all the below special cases can be generalized!
        #TODO: strength=+strength_scale for 'On', strength=-strength_scale for 'Off'
        #TODO: strength=+strength_scale for dest_identifier['opponent']=='Blue'
        #      dest_identifier['surround']=='RedGreen' and dest_identifier['polarity']=='On'
        #TODO: strength=-strength_scale for above, but 'Off'
        #TODO: strength=+strength_scale/len(cone_types) for Luminosity 'On'
        #TODO: strength=-strength_scale/len(cone_types) for Luminosity 'Off'
        proj.parameters['strength']=2.33*self.strength_factor
        proj.parameters['weights_generator']=pattern.Gaussian(size=0.07385,
                                                              aspect_ratio=1.0,
                                                              output_fns=[transferfn.DivisiveNormalizeL1()])
        proj.parameters['name']='AfferentCenter'+proj.src.identifier['cone']
        proj.parameters['nominal_bounds_template']=sheet.BoundingBox(radius=self.lgnaff_radius)


    def _specify_lgn_afferentsurround_projection(self, proj):
        proj.parameters['delay']=0.05
        #TODO: strength=-strength_scale for 'On', +strength_scale for 'Off'
        #TODO: strength=-strength_scale/2 for dest_identifier['opponent']=='Blue'
        #      dest_identifier['surround']=='RedGreen' and dest_identifier['polarity']=='On'
        #TODO: strength=+strength_scale/2 for above, but 'Off'
        #TODO: strength=-strength_scale/len(cone_types) for Luminosity 'On'
        #TODO: strength=+strength_scale/len(cone_types) for Luminosity 'Off'
        proj.parameters['strength']=2.33*self.strength_factor
        proj.parameters['weights_generator']=pattern.Gaussian(size=4*0.07385,
                                                              aspect_ratio=1.0,
                                                              output_fns=[transferfn.DivisiveNormalizeL1()])
        proj.parameters['name']='AfferentSurround'+proj.src.identifier['cone']
        proj.parameters['nominal_bounds_template']=sheet.BoundingBox(radius=self.lgnaff_radius)


