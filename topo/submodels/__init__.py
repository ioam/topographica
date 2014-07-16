"""
A hierarchy of submodel classes, which allow building a model of the visual pathway.
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


class Specification(object):
    @property
    def spec_type(self):
        return self._spec_type

    def __init__(self, spec_type, parameters=None):
        self._spec_type = spec_type
        self.parameters = {}
        for param_name, default_value in spec_type.params().items():
            self.parameters[param_name]=default_value.default
        if parameters is not None: self.parameters.update(parameters)


class SheetSpec(Specification):
    """
    SheetSpec acts as a template for sheet objects. It is also possible to resolve the
    actual sheet object after it has been instantiated.

    The following attributes can be accessed:
    :'properties': Dictionary specifying the properties of the sheet. There must be a value given
    for the key 'level'.
    :'spec_type': Subclass of topo.base.sheet.Sheet.(read-only)
    :'parameters': Dictionary specifying which parameters should be passed to the sheet object
    specified with spec_type. Keys are the parameter names, values the parameter values.
    :'matchconditions': Dictionary specifying the matchconditions of the sheet. This may be used
    to determine which other sheets this sheet should connect to.
    """

    def __init__(self, spec_type, properties, properties_order=None, parameters=None, matchconditions=None):
        """
        Initialize a SheetSpec object. All arguments but parameters are just passed to the internal
        attributes. For parameters, additional key-value pairs with all possible parameters for the
        sheet type specified with sheet_type are added. This allows a lookup which parameters can
        be set.
        """
        super(SheetSpec,self).__init__(spec_type, parameters)

        if properties_order:
            properties_ordered = OrderedDict()
            for k in properties_order:
                if k in properties:
                    properties_ordered[k] = properties[k]

            self.properties = properties_ordered
        else:
            self.properties = properties

        self.matchconditions = matchconditions
        if self.matchconditions is None: self.matchconditions={}


    def resolve(self):
        """
        Returns the actual sheet object after it has been instantiated.
        """
        from topo import sim
        return eval('sim.'+str(self))


    def __call__(self):
        """
        Instantiate the sheet and register it in topo.sim.
        """
        topo.sim[str(self)]=self.spec_type(**self.parameters)


    def __str__(self):
        """
        Returns a string representation combined from the properties values.
        This might be used as name for the actual sheet object.
        """
        name=''
        for prop in self.properties.itervalues():
            name+=prop

        return name



class ProjectionSpec(Specification):
    """
    ProjectionSpec acts as a template for projections. It is also possible to resolve the
    actual projection after it has been instantiated.

    The following attributes can be accessed:
    :'src': SheetSpec of the source sheet
    :'dest': SheetSpec of the destionation sheet
    :'spec_type': Subclass of topo.base.projection.Projection
    :'match_name': Name of the matchcondition which has been used to set this projection up.
    This might be used to set the parameters of the ProjectionSpec
    :'parameters': Dictionary specifying which parameters should be passed to the projection
    specified with connection_type. Keys are the parameter names, values the parameter values.
    """

    def __init__(self, spec_type, src, dest, match_name=None, parameters=None):
        """
        Initialize a ProjectionSpec object. All arguments but parameters are just passed to the internal
        attributes. For parameters, additional key-value pairs with all possible parameters for the
        projection type specified with connection_type are added. This allows a lookup which parameters can
        be set. Furthermore, parameters['src'] and parameters['dest'] are removed, as these must be set
        with the 'src' and 'dest' arguments instead.
        """
        super(ProjectionSpec, self).__init__(spec_type, parameters)

        self.src = src
        self.dest = dest
        self.match_name = match_name
        # These parameters are directly passed into topo.sim.connect()!
        del self.parameters['src']
        del self.parameters['dest']


    def resolve(self):
        """
        Returns the actual projection after it has been instantiated.
        """
        from topo import sim
        return eval('sim.'+str(self.dest)+'.'+self.parameters['name'])


    def __call__(self):
        """
        Instantiate the projection and register it in topo.sim.
        """
        topo.sim.connect(str(self.src),str(self.dest),self.spec_type,**self.parameters)


class SensoryModel(param.Parameterized):
    dims = param.List(default=['xy'],class_=str,doc="""
        Stimulus dimensions to include, out of the possible list:
          :'xy': Position in x and y coordinates""")

    num_inputs = param.Integer(default=2,bounds=(1,None),doc="""
        How many input patterns to present per unit area at each
        iteration, when using discrete patterns (e.g. Gaussians).""")

    sheet_parameters_mapping = param.Dict(default={},doc="""
        This dictionary is used to specify the parameters of sheets. It maps the level of a SheetSpec
        object (key) to either:
        a. a method which accepts the SheetSpec object as first and only argument, which then modifies
        the parameters attribute of the SheetSpec object accordingly, or
        b. a dictionary specifying the parameters of the SheetSpec object.""")

    sheet_matchcondition_mapping = param.Dict(default={},doc="""
        This dictionary is used to specify which other sheets a sheet should connect to, whereas
        the sheet for which the mapping is created here is the destination sheet. It maps the
        level of a SheetSpec object (key) to either:
        a. a method which accepts the SheetSpec object as first and only argument, which then modifies
        the matchconditions attribute of the SheetSpec object accordingly, or
        b. a dictionary specifying the matchconditions of the SheetSpec object.""")

    match_parameter_mapping = param.Dict(default=OrderedDict(),doc="""
        This dictionary is used to specify the parameters of projections. It maps the match_name of a 
        ProjectionSpec object (key) to either:
        a. a method which accepts the ProjectionSpec object as first and only argument, which then
        modifies the parameters attribute of the ProjectionSpec object accordingly, or
        b. a dictionary specifying the parameters of the ProjectionSpec object.

        The order of this mapping is respected while creating the sheets. That is, the sheets to be connected
        using the first ProjectionSpecification in this mapping are created first, and so on. To make use
        of this constraint, the match_parameter_mapping must be of the type collections.OrderedDict
        as the dict type in Python is unordered by default!
        """)

    match_connectiontype_mapping = param.Dict(default={}, doc="""
        This dictionary is used to specify the connection type of projections. It maps a matchconditions
        name of a SheetSpec object (key) to the connection type to be used (value). The value must be a
        subclass of topo.base.projection.Projection""")

    available_setup_options = ['training_patterns','sheets','projections','analysis']

    available_instantiate_options = ['sheets','projections']

    __abstract = True

    def __init__(self, setup_options=True, **params):
        super(SensoryModel,self).__init__(**params)
        self.training_patterns = AttrTree()
        self.sheets = AttrTree()
        self.projections = AttrTree()
        self.setup(setup_options)


    def setup(self,setup_options):
        """
        This method can be used to setup certain aspects of the submodel.
        If setup_options=True, all setup methods are called.
        setup_options can also be a list, whereas the following list items are processed
        (see also available_setup_options):
        :'training_patterns': fills the training_patterns AttrTree with pattern generator instances. The path
        is the name of the retina. Usually calls PatternCoordinator to do this.
        :'setup_sheets': determines the amount of sheets, their types and names
        sets sheet parameters according to the sheet_parameters_mapping dictionary
        sets sheet matchconditions according to the sheet_matchcondition_mapping dictionary
        :'projections': determines which connections should be present between the sheets according to the
        matchconditions of SheetSpec objects, using match_connectiontype_mapping to specify the connection type
        and sets their parameters according to the match_parameter_mapping dictionary
        """

        if setup_options==True:
            setup_options = self.available_setup_options

        if 'training_patterns' in setup_options:
            self._setup_training_patterns()
        if 'sheets' in setup_options:
            self._setup_sheets()
            self._set_sheet_parameters()
            self._set_sheet_matchconditions()
        if 'projections' in setup_options:
            self._setup_projections()
            self._set_projection_parameters()
        if 'analysis' in setup_options:
            self._setup_analysis()


    def _setup_training_patterns(self):
        """
        Adds new PatternGenerators to self.training_patterns, with
        the name of the retina where the training patterns should
        be installed as path.
        """
        raise NotImplementedError


    def _setup_sheets(self):
        """
        Adds new SheetSpec items to self.sheets, with the
        name of the name of the sheet as path.
        """
        raise NotImplementedError


    def _set_sheet_parameters(self):
        for ((_,), sheet_item) in self.sheets.path_items.items():
            if(callable(self.sheet_parameters_mapping[sheet_item.properties['level']])):
                self.sheet_parameters_mapping[sheet_item.properties['level']](sheet_item)
            else:
                sheet_item.parameters.update(self.sheet_parameters_mapping[sheet_item.properties['level']])


    def _set_sheet_matchconditions(self):
        for ((_,), sheet_item) in self.sheets.path_items.items():
            if(callable(self.sheet_matchcondition_mapping[sheet_item.properties['level']])):
                self.sheet_matchcondition_mapping[sheet_item.properties['level']](sheet_item)
            else:
                sheet_item.matchconditions.update(self.sheet_matchcondition_mapping[sheet_item.properties['level']])


    def _setup_projections(self):
        # Loop through all possible combinations of SheetSpec objects in self.sheets
        # If the src_sheet fulfills all criteria specified in dest_sheet.matchconditions,
        # create a new ProjectionSpec object and add this item to self.projections
        self.projections = AttrTree()

        for src_sheet, dest_sheet in itertools.product(self.sheets.path_items.values(), self.sheets.path_items.values()):
            for matchname, matchconditions in dest_sheet.matchconditions.items():
                is_match=True
                for incoming_key, incoming_value in matchconditions.items():
                    if incoming_key not in src_sheet.properties \
                    or str(src_sheet.properties[incoming_key]) not in str(incoming_value):
                        is_match=False
                        break

                if is_match:
                    self.projections.set_path(str(dest_sheet)+'.'+str(src_sheet)+'.'+matchname, 
                                         ProjectionSpec(self.match_connectiontype_mapping[matchname],
                                                        src_sheet, dest_sheet, matchname))


    def _set_projection_parameters(self):
        for ((_,_,_), proj) in self.projections.path_items.items():
            if(callable(self.match_parameter_mapping[proj.match_name])):
                self.match_parameter_mapping[proj.match_name](proj)
            else: 
                proj.parameters.update(self.match_parameter_mapping[proj.match_name])


    def _setup_analysis(self):
        """
        Set up appropriate defaults for analysis functions in topo.analysis.featureresponses
        """
        pass


    def __call__(self,instantiate_options=True):
        """
        Instantiates all sheets / projections in self.sheets / self.projections and registers them in
        topo.sim
        instantiate_options is a list, which can contain the following list items
        (see also available_instantiate_options):
        :'sheets': instantiates all sheets and registers them in topo.sim
        :'projections': instantiates all projections and registers them in topo.sim
        """
        if instantiate_options==True:
            instantiate_options=self.available_instantiate_options

        if 'sheets' in instantiate_options:
            self.message('Sheets:\n')
            for sheet_item in self.sheets.path_items.itervalues():
                self.message(sheet_item)
                sheet_item()
            self.message('\n\n')

        if 'projections' in instantiate_options:
            self.message('Connections:\n')
            #Ugly hack to take order in match_parameter_mapping into account
            #As soon as weight initialization is done with time_dependent=True,
            #this can be simplified to:
            #for proj in self.projections.path_items.itervalues():
            for proj in \
                sorted(self.projections.path_items.itervalues(),
                       key=lambda projection: self.match_parameter_mapping.keys().index(projection.match_name)):
                self.message('Connect ' + str(proj.src) + ' with ' + str(proj.dest) + \
                             ' (Match name: ' + proj.match_name + \
                             ', connection name: ' + str(proj.parameters['name']) + ')')
                proj()


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

    __abstract = True

    def __init__(self, setup_options=True, **params):
        super(VisualInputModel,self).__init__([], **params)
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
            self.message('time_dependent set to true for motion model!')
            # This list could be any list of the form
            # [x_1,x_2,...,x_n]
            # where x_1, x_2, ... are any arbitrary integers
            self.lags = range(self.num_lags)
        else:
            self.num_lags=1
            self.lags = [0]

        self.setup(setup_options)


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

    def __init__(self, setup_options=True, **params):
        super(EarlyVisionModel,self).__init__([], **params)

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

        self.setup(setup_options)


    def _setup_sheets(self):
        retina_product = lancet.Args(level='Retina')
        if self.eyes:
            retina_product = retina_product * lancet.List('eye', self.eyes)

        for retina_item in retina_product.specs:
            sheet_ref=SheetSpec(sheet.GeneratorSheet,retina_item,['eye','level'])
            self.sheets.set_path(str(sheet_ref), sheet_ref)

        lgn_product = lancet.Args(level='LGN') * lancet.List('polarity', self.center_polarities)
        if self.eyes:
            lgn_product= lgn_product * lancet.List('eye', self.eyes)
        if max(self.SF)>1:
            lgn_product = lgn_product * lancet.List('SF', self.SF)

        lgn_order=['eye','level','polarity','SF']
        for lgn_item in lgn_product.specs:
            sheet_ref=SheetSpec(sheet.optimized.SettlingCFSheet_Opt,lgn_item,lgn_order)
            self.sheets.set_path(str(sheet_ref), sheet_ref)


    def _set_retina_sheets_parameters(self,retina_sheet_item):
        properties=retina_sheet_item.properties
        generator_name=properties['eye']+'Retina' if 'eye' in properties else 'Retina'

        parameters={'period':1.0, 'phase':0.05, 'nominal_density':self.retina_density,
                    'nominal_bounds':sheet.BoundingBox(radius=self.area/2.0 + \
                        self.v1aff_radius*self.sf_spacing**(max(self.SF)-1) + \
                        self.lgnaff_radius*self.sf_spacing**(max(self.SF)-1) + \
                        self.lgnlateral_radius),
                    'input_generator':self.training_patterns[generator_name]}

        retina_sheet_item.parameters.update(parameters)


    def _set_lgn_sheets_parameters(self,lgn_sheet_item):
        properties=lgn_sheet_item.properties
        channel=properties['SF'] if 'SF' in properties else 1

        parameters={'measure_maps':False, 'output_fns': [transferfn.misc.HalfRectify()],
                    'nominal_density':self.lgn_density,
                    'nominal_bounds':sheet.BoundingBox(radius=self.area/2.0 + \
                        self.v1aff_radius*self.sf_spacing**(channel-1) + self.lgnlateral_radius),
                    'tsettle':2 if self.gain_control else 0,
                    'strict_tsettle': 1 if self.gain_control else 0}

        lgn_sheet_item.parameters.update(parameters)


    def _set_lgn_sheets_matchconditions(self, lgn_sheet_item):
        """
        A matchcondition is created allowing incoming projections of retina sheets of the same eye as the LGN sheet.
        If gain control is enabled, also connect to LGN sheets of the same polarity (and, if SF is used, the
        same SF channel).
        """
        properties=lgn_sheet_item.properties

        lgn_sheet_item.matchconditions['Afferent']=\
            {'level': 'Retina', 'eye': properties['eye']} if 'eye' in properties else {'level': 'Retina'}
        if self.gain_control:
            lgn_sheet_item.matchconditions['LateralGC']=\
                {'level': 'LGN', 'polarity':properties['polarity'], 'SF': properties['SF']} if 'SF' in properties \
                else {'level': 'LGN', 'polarity':properties['polarity']}

    def _specify_lgn_afferent_projection(self, proj):
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
        parameters={'delay':0.05, 'strength':2.33*self.strength_factor, 'name':'Afferent',
                    'nominal_bounds_template':sheet.BoundingBox(radius=self.lgnaff_radius*self.sf_spacing**(channel-1)),
                    'weights_generator':on_weights if proj.dest.properties['polarity']=='On' else off_weights}

        proj.parameters.update(parameters)


    def _specify_lateralgc_projection(self, proj):
        #TODO: Are those 0.25 the same as lgnlateral_radius/2.0?
        parameters={'delay':0.05, 'dest_port':('Activity'),'activity_group':(0.6,DivideWithConstant(c=0.11)),
                    'weights_generator':pattern.Gaussian(size=0.25,
                                                         aspect_ratio=1.0,
                                                         output_fns=[transferfn.DivisiveNormalizeL1()]),
                    'nominal_bounds_template':sheet.BoundingBox(radius=0.25),
                    'name':'LateralGC'+proj.src.properties['eye'] if 'eye' in proj.src.properties else 'LateralGC',
                    'strength':0.6/len(self.eyes) if self.eyes else 0.6}

        proj.parameters.update(parameters)


class ColorEarlyVisionModel(EarlyVisionModel):
    gain_control_color = param.Boolean(default=False,doc="""
        Whether to use divisive lateral inhibition in the LGN for contrast gain control in color sheets.""")

    def __init__(self, setup_options=True, **params):
        super(ColorEarlyVisionModel,self).__init__([], **params)
        
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

        self.setup(setup_options)


    def _setup_sheets(self):
        retina_product = lancet.Args(level='Retina')
        if self.eyes:
            retina_product = retina_product * lancet.List('eye', self.eyes)
        if self.cone_types:
            retina_product = retina_product * lancet.List('cone', self.cone_types)

        retina_order = ['eye','level','cone']
        for retina_item in retina_product.specs:
            sheet_ref=SheetSpec(sheet.GeneratorSheet,retina_item,retina_order)
            self.sheets.set_path(str(sheet_ref), sheet_ref)

        lgn_product = lancet.Args(level='LGN') * lancet.List('polarity', self.center_polarities)
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

        lgn_order = ['eye','level','polarity','SF','opponent','surround']
        for lgn_item in lgn_product.specs:
            sheet_ref=SheetSpec(sheet.optimized.SettlingCFSheet_Opt,lgn_item,lgn_order)
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
        properties=lgn_sheet_item.properties

        if 'opponent' in properties:
            lgn_sheet_item.matchconditions['AfferentCenter']=\
                {'level': 'Retina','cone': properties['opponent'], 'eye': properties['eye']} if 'eye' in properties \
                else {'level': 'Retina','cone': properties['opponent']}
            lgn_sheet_item.matchconditions['AfferentSurround']=\
                {'level': 'Retina','cone': properties['surround'], 'eye': properties['eye']} if 'eye' in properties \
                else {'level': 'Retina','cone': properties['surround']}
        else:
            lgn_sheet_item.matchconditions['Afferent']=\
                {'level': 'Retina', 'eye': properties['eye']} if 'eye' in properties else \
                {'level': 'Retina'}

        if self.gain_control and 'opponent' not in properties:
            lgn_sheet_item.matchconditions['LateralGC']=\
                {'level': 'LGN', 'polarity':properties['polarity'], 'SF': properties['SF']} if 'SF' in properties \
                else {'level': 'LGN', 'polarity':properties['polarity']}

        if self.gain_control_color and 'opponent' in properties:
            lgn_sheet_item.matchconditions['LateralGC']={'level': 'LGN', 'polarity':properties['polarity'],
                                                         'opponent':properties['opponent'], 
                                                         'surround':properties['surround']}


    def _specify_lgn_afferent_projection(self, proj): # Is that needed?
        super(ColorEarlyVisionModel,self)._specify_lgn_afferent_projection(proj)
        if 'opponent' in proj.dest.properties:
            proj.parameters['name']+=proj.dest.properties['opponent']+proj.src.properties['cone']


    def _specify_lgn_afferentcenter_projection(self, proj):
        #TODO: It shouldn't be too hard to figure out how many retina sheets it connects to,
        #      then all the below special cases can be generalized!
        #TODO: strength=+strength_scale for 'On', strength=-strength_scale for 'Off'
        #TODO: strength=+strength_scale for dest_properties['opponent']=='Blue'
        #      dest_properties['surround']=='RedGreen' and dest_properties['polarity']=='On'
        #TODO: strength=-strength_scale for above, but 'Off'
        #TODO: strength=+strength_scale/len(cone_types) for Luminosity 'On'
        #TODO: strength=-strength_scale/len(cone_types) for Luminosity 'Off'
        parameters={'delay':0.05, 'strength':2.33*self.strength_factor,
                    'weights_generator':pattern.Gaussian(size=0.07385,
                                                         aspect_ratio=1.0,
                                                         output_fns=[transferfn.DivisiveNormalizeL1()]),
                    'name':'AfferentCenter'+proj.src.properties['cone'],
                    'nominal_bounds_template':sheet.BoundingBox(radius=self.lgnaff_radius)}

        proj.parameters.update(parameters)


    def _specify_lgn_afferentsurround_projection(self, proj):
        #TODO: strength=-strength_scale for 'On', +strength_scale for 'Off'
        #TODO: strength=-strength_scale/2 for dest_properties['opponent']=='Blue'
        #      dest_properties['surround']=='RedGreen' and dest_properties['polarity']=='On'
        #TODO: strength=+strength_scale/2 for above, but 'Off'
        #TODO: strength=-strength_scale/len(cone_types) for Luminosity 'On'
        #TODO: strength=+strength_scale/len(cone_types) for Luminosity 'Off'
        parameters={'delay':0.05, 'strength':2.33*self.strength_factor,
                    'weights_generator':pattern.Gaussian(size=4*0.07385,
                                                         aspect_ratio=1.0,
                                                         output_fns=[transferfn.DivisiveNormalizeL1()]),
                    'name':'AfferentSurround'+proj.src.properties['cone'],
                    'nominal_bounds_template':sheet.BoundingBox(radius=self.lgnaff_radius)}

        proj.parameters.update(parameters)


