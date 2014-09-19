"""
A set of objects that allows declarative specification of a model
including training patterns, sheets and projections.

The components of a model specification can be individually inspected,
modified, resolved or instantiated.
"""

import topo
import param

from dataviews.collector import AttrTree
from collections import OrderedDict


class Specification(param.Parameterized):
    """
    Specifications are templates for sheet or projection objects which
    may be resolved to the corresponding simulation object once
    instantiated.

    All specifications have the following attribute:

    :'parameters': Keyword argument dictionary specifying which
    parameters should be passed to the sheet or projection object.
    """

    def update(self, **params):
        """
        Convenience method to easy update specification parameters.
        """
        self.parameters.update(params)

    @property
    def modified_parameters(self):
        "Dictionary of modified specification parameters"
        return {k:v for k, v in self.parameters.items()
                if self.default_parameters[k] != v}


    @property
    def resolved_type(self):
        return self._object_type


    def resolve(self):
        """
        Returns the object in topo.sim corresponding to this object,
        typically a Sheet or a Projection.

        The appropriate object must be available in topo.sim.
        """
        raise NotImplementedError

    def __lt__(self, other):
        return self.sort_precedence < other.sort_precedence

    def __eq__(self, other):
        return self.sort_precedence == other.sort_precedence

    def __init__(self, object_type):
        self._object_type = object_type
        self.parameters = {}
        self.sort_precedence = 0

        if not hasattr(object_type,'params'):
            self.default_parameters = {}
        else:
            for param_name, default_value in object_type.params().items():
                self.parameters[param_name]=default_value.default
            self.default_parameters = dict(**self.parameters)

    def summary(self, printed=True):
        """
        Generate a succinct summary of the Specification object. If
        printed is set to True, the summary is printed, otherwise it
        is returned as a string.
        """
        raise NotImplementedError


    def __getitem__(self, key):
        "Convenient property access."
        return self.properties[key]

    def keys(self):
        "The list of available property keys."
        return self.properties.keys()

    def items(self):
        "The property items."
        return self.properties.items()



class ArraySpec(Specification):
    """
    A simple specification used to resolve numpy arrays relative to a
    Topographica simulation (i.e. topo.sim). This class is primarily
    aimed for specifying arrays to a Collector.
    """

    def __init__(self, pathspec, properties={}):
        """
        ArraySpec uses a fairly unsophisticated implementation, making
        use of eval to resolve the desired array.

       :'pathspec': A string specifying how to access the array
                    relative to topo.sim.
       :'properties': Optional specification of array properties
        """
        import numpy
        self.pathspec = pathspec
        super(ArraySpec,self).__init__(numpy.ndarray)
        self.properties = OrderedDict(properties)


    def resolve(self):
        from topo import sim
        return eval("sim.%s" % self.pathspec)


    def __call__(self):
        raise NotImplementedError


    def __str__(self):
        return "topo.sim.%s" % self.pathspec


    def summary(self, printed=True):
        summary = "%s : Numpy array" % self
        if printed: print summary
        else:       return summary


    def __repr__(self):
        properties_repr = ', '.join("%r:%r" % (k,v) for (k,v)
                                    in self.properties.items())
        return "ArraySpec(%r, {%s})" % (self.pathspec, properties_repr)



class SheetSpec(Specification):
    """
    SheetSpec acts as a template for sheet objects.
    """

    name_ordering = ['eye','level', 'cone', 'polarity',
                     'SF','opponent','surround']

    @property
    def level(self):
        return self.properties['level']


    def __init__(self, sheet_type, properties):
        """
        Initialize a SheetSpec object of a certain Sheet type with the
        given properties.

       :'sheet_type': Subclass of topo.base.sheet.Sheet.
       :'properties': Dictionary specifying the properties of the
       sheet. There must be a value given for the key 'level'.
        """
        super(SheetSpec,self).__init__(sheet_type)

        if 'level' not in properties:
            raise Exception("SheetSpec always requires 'level' property.")


        properties = [(k, properties[k]) for k in self.name_ordering
                      if k in properties]

        self.sheet_type = sheet_type
        self.properties = OrderedDict(properties)


    def resolve(self):
        from topo import sim
        return sim[str(self)]


    def __call__(self):
        """
        Instantiate the sheet and register it in topo.sim.
        """
        properties = dict(self.parameters['properties'], **self.properties)
        topo.sim[str(self)]=self.sheet_type(**dict(self.parameters,
                                                   properties=properties))

    def __str__(self):
        """
        Returns a string representation of the SheetSpec from the
        properties values.
        """
        name=''
        for prop in self.properties.itervalues():
            name+=str(prop)

        return name

    def summary(self, printed=True):
        summary = "%s : %s" % (self, self.sheet_type.name)
        if printed: print summary
        else:       return summary

    def __repr__(self):
        type_name = self.sheet_type.__name__
        properties_repr = ', '.join("%r:%r" % (k,v) for (k,v)
                                    in self.properties.items())
        return "SheetSpec(%s, {%s})" % (type_name, properties_repr)



class ProjectionSpec(Specification):
    """
    ProjectionSpec acts as a template for projection objects.
    """

    def __init__(self, projection_type, src, dest):
        """
        Initialize a ProjectionSpec object of a certain Projection
        type with the given src and dest SheetSpecs.

       :'projection_type': Subclass of topo.base.projection.Projection
       :'src': SheetSpec of the source sheet
       :'dest': SheetSpec of the destination sheet
        """
        super(ProjectionSpec, self).__init__(projection_type)

        self.projection_type = projection_type
        self.src = src
        self.dest = dest
        self.properties = {}

        # These parameters are directly passed into topo.sim.connect()!
        ignored_keys = ['src', 'dest']
        self.parameters = dict((k,v) for (k,v) in self.parameters.items()
                               if k not in ignored_keys)


    def resolve(self):
        from topo import sim
        return sim[str(self.dest)].projections(self.parameters['name'])


    def __call__(self):
        """
        Instantiate the projection and register it in topo.sim.
        """
        topo.sim.connect(str(self.src),str(self.dest),
                         self.projection_type,
                         **self.parameters)

    def __str__(self):
        return str(self.dest)+'.' + self.parameters['name']


    def summary(self, printed=True):
        summary = "%s [%s -> %s] : %s" % (self, self.src, self.dest,
                                          self.projection_type.name)
        if printed: print summary
        else:       return summary

    def __repr__(self):
        type_name = self.projection_type.__name__
        return "ProjectionSpec(%s, %r, %r)" % (type_name, self.src, self.dest)



class ModelSpec(Specification):
    """
    ModelSpec acts as a template for Topographica model including
    training patterns, sheets and projections.
    """

    def __init__(self, model, properties):
        self.training_patterns = AttrTree()
        self.sheets = AttrTree()
        self.projections = AttrTree()

        self._instantiated = False

        self.properties = properties
        super(ModelSpec, self).__init__(model)
        self.model= model

    def resolve(self):
        from topo import sim     # pyflakes:ignore (needed for eval)
        return eval('sim.model')

    def __call__(self, instantiate_options=True, verbose=False):
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
        msglevel = self.message if verbose else self.debug

        if self._instantiated:
            msglevel('ModelSpec %r already instantiated. Returning.' % self.model.name)
            return

        available_instantiate_options = ['sheets','projections']
        if instantiate_options==True:
            instantiate_options=available_instantiate_options

        if 'sheets' in instantiate_options:
            for sheet_spec in self.sheets.path_items.itervalues():
                msglevel('Level ' + sheet_spec.level + ': Sheet ' + str(sheet_spec))
                sheet_spec()

        if 'projections' in instantiate_options:
            for proj in sorted(self.projections):
                msglevel('Match: ' + proj.matchname + ': Connection ' + str(proj.src) + \
                             '->' + str(proj.dest) + ' ' + proj.parameters['name'])
                proj()
        self._instantiated = True


    def summary(self, printed=True):
        name = self.model.name
        heading_line = '=' * len(name)
        summary = [heading_line, name, heading_line, '']

        for sheet_spec in sorted(self.sheets):
            summary.append(sheet_spec.summary(printed=False))
            projections = [proj for proj in self.projections
                           if str(proj.dest)==str(sheet_spec)]
            for projection_spec in sorted(projections, key=lambda p: str(p)):
                summary.append("   " + projection_spec.summary(printed=False))
            summary.append('')

        if printed: print "\n".join(summary)
        else:       return "\n".join(summary)


    def __str__(self):
        return self.model.__class__.__name__

    def _repr_pretty_(self, p, cycle):
        p.text(self.summary(printed=False))


    def modifications(self, components=['model', 'sheets', 'projections']):
        """
        Display the names of all modified parameters for the specified
        set of components.

        By default all modified parameters are listed - first with the
        model parameters, then the sheet parameters and lastly the
        projection parameters.
        """
        mapping = {'model': [self],
                   'sheets':self.sheets,
                   'projections':self.projections}

        lines = []
        for component in components:
            heading = "=" * len(component)
            lines.extend([heading, component.capitalize(), heading, ''])
            specs = mapping[component]
            padding = max(len(str(spec)) for spec in specs)
            for spec in sorted(specs):
                modified = [str(el) for el in sorted(spec.modified_parameters)]
                lines.append("%s : [%s]" % (str(spec).ljust(padding), ", ".join(modified)))
            lines.append('')
        print "\n".join(lines)
