"""
A set of tools which allow specifying a model consisting of sheets
organized in levels, and projections connecting these sheets. The
sheets have an attribute matchconditions allowing to specify which
other (incoming) sheets a sheet should connect to.

Instances of the LabelDecorator decorator are offered for setting
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

from topo.misc.commandline import global_params


class Specification(object):
    @property
    def spec_type(self):
        return self._spec_type


    def update_parameters(self, params):
        self.parameters.update(params)


    def resolve(self):
        """
        Returns the actual projection after it has been instantiated.
        """
        from topo import sim
        return eval('sim.'+str(self))


    def __init__(self, spec_type):
        self._spec_type = spec_type
        self.parameters = {}
        for param_name, default_value in spec_type.params().items():
            self.parameters[param_name]=default_value.default


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

    name_ordering = ['eye','level', 'cone', 'polarity',
                     'SF','opponent','surround']

    @property
    def level(self):
        return self.properties['level']

    def __init__(self, spec_type, properties):
        """
        Initialize a SheetSpec object. All arguments but parameters
        are just passed to the internal attributes. For parameters,
        additional key-value pairs with all possible parameters for
        the sheet type specified with sheet_type are added. This
        allows a lookup which parameters can be set.
        """
        super(SheetSpec,self).__init__(spec_type)

        if 'level' not in properties:
            raise Exception("SheetSpec always requires 'level' in properties")


        properties = [(k, properties[k]) for k in self.name_ordering
                      if k in properties]

        self.properties = OrderedDict(properties)
        self.matchconditions={}


    def update_matchconditions(self, matchconditions):
        self.matchconditions.update(matchconditions)


    def __call__(self):
        """
        Instantiate the sheet and register it in topo.sim.
        """
        topo.sim[str(self)]=self.spec_type(**self.parameters)


    def resolve(self):
        """
        Returns the actual sheet object after it has been
        instantiated.
        """
        from topo import sim
        return eval('sim.'+str(self))


    def __str__(self):
        """
        Returns a string representation combined from the properties
        values.  This might be used as name for the actual sheet
        object.
        """
        name=''
        for prop in self.properties.itervalues():
            name+=prop

        return name

    def __repr__(self):
        type_name = self._spec_type.__name__
        properties_repr = ', '.join("%r:%r" % (k,v) for (k,v)
                                    in self.properties.items())
        return "SheetSpec(%s, {%s})" % (type_name, properties_repr)



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

    def __init__(self, spec_type, src, dest, match_name=None, properties=None):
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
        super(ProjectionSpec, self).__init__(spec_type)

        self.src = src
        self.dest = dest
        self.match_name = match_name

        self.properties = {} if properties is None else properties
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

    def __str__(self):
        return str(self.dest)+'.'+self.parameters['name']

    def __repr__(self):
        type_name = self._spec_type.__name__
        properties_repr = "{"+ ', '.join("%r:%r" % (k,v) for (k,v) in self.properties.items()) +"}"
        args = (type_name, self.src, self.dest,
                self.match_name,
                ", %s" % properties_repr if self.properties else '')
        return "ProjectionSpec(%s, %r, %r, %r%s)" % args



class LabelDecorator(object):
    """
    Decorator class which can be instantiated to create a decorator
    object. This object can then be used to decorate methods or
    functions with a label argument and optionally a type.

    After decorating several methods or functions, the dictionary of
    all the decorated callables can be accessed via the labelled
    attribute. Any types supplies are accessible through the types
    attribute.
    """
    def __init__(self):
        self.labelled = {}
        self.types = {}

    def __call__(self, label, obj_type=None):
        def decorator(f):
            @wraps(f)
            def inner(*args, **kwargs):
                return f(*args, **kwargs)

            self.labelled[label] = inner
            if obj_type is not None:
                self.types[label] = obj_type
            return inner
        return decorator



class Model(param.Parameterized):
    """
    The available setup options are:

        :'training_patterns': fills the training_patterns AttrTree
        with pattern generator instances. The path is the name of the
        input sheet. Usually calls PatternCoordinator to do this.
        :'setup_sheets': determines the number of sheets, their types
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
    __abstract = True

    level =           LabelDecorator()
    matchconditions = LabelDecorator()
    connection =         LabelDecorator()


    def _register_global_params(self, params):
        """
        Register the parameters of this object as global parameters
        available for users to set from the command line.  Values
        supplied as global parameters will override those of the given
        dictionary of params.
        """

        for param_name, param_value in self.params().items():
            global_params.add(**{param_name:param_value})

        params.update(global_params.get_param_values())


    def __init__(self, setup_options=True, register=True, **params):
        if register:
            self._register_global_params(params)
        super(Model,self).__init__(**params)

        self.training_patterns = AttrTree()
        self.sheets = AttrTree()
        self.projections = AttrTree()

        self.setup(setup_options)

    #==============================================#
    # Public methods to be implemented by modelers #
    #==============================================#

    def setup_attributes(self):
        """
        Method to precompute any useful self attributes from the class
        parameters. For instance, if there is a ``num_lags``
        parameter, this method could compute the actual projection
        delays and store it in self.lags.

        In addition, this method can be used to configure class
        attributes of the model components.
        """
        pass


    def setup_training_patterns(self):
        """
        Returns a dictionary of PatternGenerators to be added to
        self.training_patterns, with the target sheet names as keys
        and pattern generators as values.
        """
        raise NotImplementedError


    def setup_sheets(self):
        """
        Adds new SheetSpec items to the self.sheets AttrTree.
        Must return a list of SheetSpec objects.
        """
        raise NotImplementedError


    def setup_analysis(self):
        """
        Set up appropriate defaults for analysis functions in
        topo.analysis.featureresponses.
        """
        pass


    #====================================================#
    # Remaining methods should not need to be overridden #
    #====================================================#

    def setup(self,setup_options):
        """
        This method can be used to setup certain aspects of the
        submodel.  If setup_options=True, all setup methods are
        called.  setup_options can also be a list, whereas all list
        items of available_setup_options are accepted.

        Available setup options are:
        'training_patterns','sheets','projections' and 'analysis'.

        Please consult the docstring of the Model class for more
        information about each setup option.
        """
        available_setup_options = ['attributes',
                                   'training_patterns',
                                   'sheets',
                                   'projections',
                                   'analysis']

        if setup_options==True:
            setup_options = available_setup_options

        if 'attributes' in setup_options:
            self.setup_attributes()
        if 'training_patterns' in setup_options:
            training_patterns = self.setup_training_patterns()
            for name, training_pattern in training_patterns.items():
                self.training_patterns.set_path(name, training_pattern)
        if 'sheets' in setup_options:
            sheet_specs = self.setup_sheets()
            for sheet_spec in sheet_specs:
                self.sheets.set_path(str(sheet_spec), sheet_spec)
            self._update_sheet_specs()
        if 'projections' in setup_options:
            self._compute_projection_specs()
        if 'analysis' in setup_options:
            self._setup_analysis()


    def _update_sheet_specs(self):
        for sheet_spec in self.sheets.path_items.values():
            param_method = self.level.labelled.get(sheet_spec.level, None)
            if not param_method:
                raise Exception("Parameters for sheet level %r not specified" % sheet_spec.level)

            updated_params = param_method(self,sheet_spec.properties)
            sheet_spec.update_parameters(updated_params)

            matchcondition = self.matchconditions.labelled.get(sheet_spec.level, False)
            if matchcondition:
                sheet_spec.update_matchconditions(matchcondition(self,sheet_spec.properties))


    def _matchcondition_applies(self, matchconditions, src_sheet):
        """
        Given a dictionary of properties to match and a target sheet
        spec, test if the matchcondition applies.
        """
        matches=True
        if matchconditions is None:
            return False
        for incoming_key, incoming_value in matchconditions.items():
            if incoming_key in src_sheet.properties and \
                    str(src_sheet.properties[incoming_key]) not in str(incoming_value):
                matches=False
                break

        return matches


    def _compute_projection_specs(self):
        """
        Loop through all possible combinations of SheetSpec objects in
        self.sheets If the src_sheet fulfills all criteria specified
        in dest_sheet.matchconditions, create a new ProjectionSpec
        object and add this item to self.projections.
        """

        sheetspec_product = itertools.product(self.sheets.path_items.values(),
                                              self.sheets.path_items.values())
        for src_sheet, dest_sheet in sheetspec_product:
            for matchname, matchconditions in dest_sheet.matchconditions.items():

                if self._matchcondition_applies(matchconditions, src_sheet):
                    proj = ProjectionSpec(self.connection.types[matchname],
                                          src_sheet, dest_sheet, matchname)
                    paramsets = self.connection.labelled[matchname](self, proj)
                    paramsets = [paramsets] if isinstance(paramsets, dict) else paramsets
                    for paramset in paramsets:
                        proj = ProjectionSpec(self.connection.types[matchname],
                                              src_sheet, dest_sheet, matchname)
                        proj.update_parameters(paramset)
                        path = (str(dest_sheet), str(src_sheet), paramset['name'])
                        self.projections.set_path(path, proj)


    def __call__(self,instantiate_options=True):
        """
        Instantiates all sheets or projections in self.sheets or
        self.projections and registers them in the topo.sim instance.

        If instantiate_options=True, all items are initialised
        instantiate_options can also be a list, whereas all list items
        of available_instantiate_options are accepted.

        Available instantiation options are: 'sheets' and
        'projections'.

        Please consult the docstring of the Model class for more
        information about each instantiation option.
        """

        available_instantiate_options = ['sheets','projections']
        if instantiate_options==True:
            instantiate_options=available_instantiate_options

        if 'sheets' in instantiate_options:
            self.message('Sheets:\n')
            for sheet_spec in self.sheets.path_items.itervalues():
                self.message(sheet_spec)
                sheet_spec()
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
