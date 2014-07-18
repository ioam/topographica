"""
A set of tools which allow specifying a model consisting of sheets
organized in levels, and projections connecting these sheets. The
sheets have an attribute matchconditions allowing to specify which
other (incoming) sheets a sheet should connect to.

Instances of the RegisteredMethod decorator are offered for setting
parameters/matchconditions for a sheet within a level, as well as
parameters for projections.
"""

from collections import OrderedDict
import itertools
from functools import wraps

import param

import topo
from topo import sheet,transferfn,pattern,projection
from topo.base.sheet import Sheet

from dataviews.collector import AttrTree

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
    SheetSpec acts as a template for sheet objects. It is also
    possible to resolve the actual sheet object after it has been
    instantiated.

    The following attributes can be accessed:

    :'properties': Dictionary specifying the properties of the
    sheet. There must be a value given for the key 'level'.
    :'spec_type': Subclass of topo.base.sheet.Sheet.(read-only)
    :'parameters': Dictionary specifying which parameters should be
    passed to the sheet object specified with spec_type. Keys are the
    parameter names, values the parameter values.
    :'matchconditions': Dictionary specifying the matchconditions of
    the sheet. This may be used to determine which other sheets this
    sheet should connect to.
    """

    def __init__(self, spec_type, properties, name_ordering=None,
                 parameters=None, matchconditions=None):
        """
        Initialize a SheetSpec object. All arguments but parameters
        are just passed to the internal attributes. For parameters,
        additional key-value pairs with all possible parameters for
        the sheet type specified with sheet_type are added. This
        allows a lookup which parameters can be set.
        """
        super(SheetSpec,self).__init__(spec_type, parameters)

        if name_ordering:
            properties = [(k, properties[k]) for k in name_ordering
                          if k in properties]
        self.properties = OrderedDict(properties)

        self.matchconditions = matchconditions
        if self.matchconditions is None: self.matchconditions={}


    def __call__(self):
        """
        Instantiate the sheet and register it in topo.sim.
        """
        topo.sim[str(self)]=self.spec_type(**self.parameters)


    def resolve(self):
        """
        Returns the actual sheet object after it has been instantiated.
        """
        from topo import sim
        return eval('sim.'+str(self))


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
    ProjectionSpec acts as a template for projections. It is also
    possible to resolve the actual projection after it has been
    instantiated.

    The following attributes can be accessed:

    :'src': SheetSpec of the source sheet
    :'dest': SheetSpec of the destination sheet
    :'spec_type': Subclass of topo.base.projection.Projection
    :'match_name': Name of the matchcondition which has been used to
    set this projection up.  This might be used to set the parameters
    of the ProjectionSpec
    :'parameters': Dictionary specifying which parameters should be
    passed to the projection specified with connection_type. Keys are
    the parameter names, values the parameter values.
    """

    def __init__(self, spec_type, src, dest, match_name=None,
                 parameters=None, properties=None):
        """
        Initialize a ProjectionSpec object. All arguments but
        parameters are just passed to the internal attributes. For
        parameters, additional key-value pairs with all possible
        parameters for the projection type specified with
        connection_type are added. This allows a lookup which
        parameters can be set. Furthermore, parameters['src'] and
        parameters['dest'] are removed, as these must be set with the
        'src' and 'dest' arguments instead.
        """
        super(ProjectionSpec, self).__init__(spec_type, parameters)

        self.src = src
        self.dest = dest
        self.match_name = match_name
        self.properties = properties
        # These parameters are directly passed into topo.sim.connect()!
        ignored_keys = ['src', 'dest']
        self.parameters = dict((k,v) for (k,v) in self.parameters.items()
                               if k not in ignored_keys)

    def __call__(self):
        """
        Instantiate the projection and register it in topo.sim.
        """
        topo.sim.connect(str(self.src),str(self.dest),self.spec_type,
                         **self.parameters)


    def resolve(self):
        """
        Returns the actual projection after it has been instantiated.
        """
        from topo import sim
        return eval('sim.'+str(self.dest)+'.'+self.parameters['name'])


class RegisteredMethod(object):
    def __init__(self):
        self.registry = {}
        self.types = {}
        self.options = {}

    def __call__(self, key, obj_type=None, option=None):
        def decorator(f):
            @wraps(f)
            def inner(*args, **kwargs):
                return f(*args, **kwargs)

            self.registry[key] = inner
            if obj_type is not None:
                self.types[key] = obj_type
            if option is not None:
                self.options[key] = option

            return inner
        return decorator


class Model(param.Parameterized):
    """
    The available setup options are:

        :'training_patterns': fills the training_patterns AttrTree
        with pattern generator instances. The path is the name of the
        input sheet. Usually calls PatternCoordinator to do this.
        :'setup_sheets': determines the amount of sheets, their types
        and names sets sheet parameters according to the registered
        methods in level sets sheet matchconditions according to the
        registered methods in matchconditions
        :'projections': determines which connections should be present
        between the sheets according to the matchconditions of
        SheetSpec objects, using connect to specify the
        connection type and sets their parameters according to the
        registered methods in connect


    The available instantiate options are:

        :'sheets': instantiates all sheets and registers them in
        topo.sim
        :'projections': instantiates all projections and registers
        them in topo.sim
    """

    available_setup_options = ['training_patterns','sheets','projections','analysis']

    available_instantiate_options = ['sheets','projections']

    __abstract = True

    level = RegisteredMethod()
    matchconditions = RegisteredMethod()
    connect = RegisteredMethod()

    def __init__(self, setup_options=True, **params):
        super(Model,self).__init__(**params)

        self.training_patterns = AttrTree()
        self.sheets = AttrTree()
        self.projections = AttrTree()

        self.setup(setup_options)


    def setup(self,setup_options):
        """
        This method can be used to setup certain aspects of the
        submodel.  If setup_options=True, all setup methods are
        called.  setup_options can also be a list, whereas all list
        items of available_setup_options are accepted.
        """

        if setup_options==True:
            setup_options = self.available_setup_options

        if 'training_patterns' in setup_options:
            self.setup_training_patterns()
        if 'sheets' in setup_options:
            self.setup_sheets()
            self._set_sheet_parameters()
            self._set_sheet_matchconditions()
        if 'projections' in setup_options:
            self._setup_projections()
            self._set_projection_parameters()
        if 'analysis' in setup_options:
            self._setup_analysis()


    def setup_training_patterns(self):
        """
        Adds new PatternGenerators to self.training_patterns, with
        the name of the input sheet where the training patterns should
        be installed as path.
        """
        raise NotImplementedError


    def setup_sheets(self):
        """
        Adds new SheetSpec items to self.sheets.
        The AttrTree path is named after the sheet name.
        """
        raise NotImplementedError


    def _setup_projections(self):
        # Loop through all possible combinations of SheetSpec objects in self.sheets
        # If the src_sheet fulfills all criteria specified in dest_sheet.matchconditions,
        # create a new ProjectionSpec object and add this item to self.projections
        self.projections = AttrTree()

        for src_sheet, dest_sheet in itertools.product(self.sheets.path_items.values(),
                                                       self.sheets.path_items.values()):
            for matchname, matchconditions in dest_sheet.matchconditions.items():
                is_match=True
                if matchconditions is None:
                    continue
                for incoming_key, incoming_value in matchconditions.items():
                    if incoming_key in src_sheet.properties and \
                        str(src_sheet.properties[incoming_key]) not in str(incoming_value):
                            is_match=False
                            break

                if is_match:
                    options = self.connect.options.get(matchname, {})
                    options.update({'matchname':[matchname]})
                    combinations = [i for i in options.values()]
                    for combination_prod in itertools.product(*combinations):
                        properties={}
                        for idx, option in enumerate(options.keys()):
                            properties.update({option:combination_prod[idx]})
                        appendix=''
                        for key, value in properties.items():
                            if key is not 'matchname':
                                appendix+=key
                                appendix+=str(value)
                        self.projections.set_path(str(dest_sheet)+'.'+str(src_sheet)+'.'+matchname+appendix,
                                                  ProjectionSpec(self.connect.types[matchname],
                                                                 src_sheet, dest_sheet, matchname,
                                                                 properties=properties))


    def _set_sheet_parameters(self):
        for sheet_item in self.sheets.path_items.values():
            if(callable(self.level.registry[sheet_item.properties['level']])):
                sheet_item.parameters.update(self.level.registry[sheet_item.properties['level']]
                                             (self,sheet_item.properties))
            else:
                sheet_item.parameters.update(self.level.registry[sheet_item.properties['level']])


    def _set_sheet_matchconditions(self):
        for sheet_item in self.sheets.path_items.values():
            matchcondition = self.matchconditions.registry.get(sheet_item.properties['level'], False)
            if(callable(matchcondition)):
                sheet_item.matchconditions.update(self.matchconditions.registry[sheet_item.properties['level']]
                                                  (self,sheet_item.properties))
            elif matchcondition:
                sheet_item.matchconditions.update(matchcondition)


    def _set_projection_parameters(self):
        for proj in self.projections.path_items.values():
            proj.parameters.update(self.connect.registry[proj.match_name](self,proj))


    def _setup_analysis(self):
        """
        Set up appropriate defaults for analysis functions in topo.analysis.featureresponses
        """
        pass


    def __call__(self,instantiate_options=True):
        """
        Instantiates all sheets / projections in self.sheets /
        self.projections and registers them in topo.sim If
        instantiate_options=True, all items are initialised
        instantiate_options can also be a list, whereas all list items
        of available_instantiate_options are accepted.
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
            #Ugly hack to take the order to initialize sheets into account
            #As soon as weight initialization is done with time_dependent=True,
            #this can be simplified to:
            #for proj in self.projections.path_items.itervalues():
            connection_order=['Afferent','AfferentCenter','AfferentSurround',
                              'LateralGC','AfferentV1On','AfferentV1Off',
                              'LateralV1Excitatory','LateralV1Inhibitory']
            for proj in sorted(self.projections.path_items.itervalues(),
                               key=lambda projection: connection_order.index(projection.match_name)):
                self.message('Connect ' + str(proj.src) + ' with ' + str(proj.dest) + \
                             ' (Match name: ' + proj.match_name + \
                             ', connection name: ' + str(proj.parameters['name']) + ')')
                proj()
