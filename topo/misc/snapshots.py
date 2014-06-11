

###################################################################################
# SNAPSHOT STUFF
###################################################################################

import inspect
import __main__

from param.parameterized import Parameterized, Parameter

# CEBALERT: Can't this stuff move to the ParameterizedMetaclass?
class PicklableClassAttributes(object):
    """
    Supports pickling of Parameterized class attributes for a given module.

    When requested to be pickled, stores a module's PO classes' attributes,
    and any given startup_commands. On unpickling, executes the startup
    commands and sets the class attributes.
    """

    # classes that aren't parameterized any more
    do_not_restore = []

    deleted_params = {"Simulation": ["time_type","time_type_args"]}


    # Support for changing parameter names
    # CEBALERT: doesn't support things like changing output_fn to output_fns,
    # where we also need to do output_fn=x -> output_fns=[x].
    # Should implement fuller support in legacy, and remove this from here.
    param_name_changes = {}
    # e.g. you change topo.pattern.Gaussian.aspect_ratio to aspect_ration
    # _param_name_changes['topo.pattern.Gaussian']={'aspect_ratio':'aspect_ration'}
    #
    # (not yet finished - do we need to add information about version numbers?)

    # CEBALERT: same comments as above about doing this more cleanly
    param_moves = {}

    # pylint: disable-msg=R0903

    # CB: might have mixed up module and package in the docs.
    def __init__(self,module,exclusions=(),startup_commands=()):
        """
        module: a module object, such as topo

        Any submodules listed by name in exclusions will not have their
        classes' attributes saved.
        """
        self.module=module
        self.exclude=exclusions
        self.startup_commands=startup_commands

    def __getstate__(self):
        """
        Return a dictionary of self.module's PO classes' attributes, plus
        self.startup_commands.
        """
        class_attributes = {}
        self.get_PO_class_attributes(self.module,class_attributes,[],exclude=self.exclude)

        # CB: we don't want to pickle anything about this object except what
        # we want to have executed on unpickling (this object's not going to be hanging around).
        return {'class_attributes':class_attributes,
                'startup_commands':self.startup_commands}

    def __setstate__(self,state):
        """
        Execute the startup commands and set class attributes.
        """
        self.startup_commands = state['startup_commands']

        for cmd in self.startup_commands:
            exec cmd in __main__.__dict__

        to_restore = {}

        ########## pre-processing (renames, moves, etc)
        for class_path,state in state['class_attributes'].items():
            # from e.g. "topo.base.parameter.Parameter", we want "topo.base.parameter"

            if class_path in self.do_not_restore:
                #print "Did not restore:",class_path
                break

            for p_name,p_obj in state.items():
                if p_name in self.param_moves.get(class_path,{}):
                    assert p_name not in self.param_name_changes.get(class_path,{})

                    if len(self.param_moves[class_path][p_name]) == 2:
                        new_class_path,new_p_name = self.param_moves[class_path][p_name]
                    if len(self.param_moves[class_path][p_name]) == 3:
                        new_class_path,new_p_name,fn = self.param_moves[class_path][p_name]
                        p_obj = fn(p_obj)


                    if new_class_path not in to_restore:
                        to_restore[new_class_path] = {}

                    Parameterized().message("%s.%s has been moved to %s.%s"%(class_path,p_name,new_class_path,new_p_name))
                    assert new_p_name not in to_restore[new_class_path]
                    to_restore[new_class_path][new_p_name]=p_obj


                elif p_name in self.param_name_changes.get(class_path,{}):
                    if isinstance(self.param_name_changes[class_path][p_name],tuple):
                        new_p_name, fn = self.param_name_changes[class_path][p_name]
                        p_obj = fn(p_obj)
                    else:
                        new_p_name= self.param_name_changes[class_path][p_name]

                    if class_path not in to_restore:
                        to_restore[class_path] = {}

                    Parameterized().message("%s's %s parameter has been renamed to %s."%(class_path,p_name,new_p_name))
                    to_restore[class_path][new_p_name] = p_obj

                else:
                    if class_path not in to_restore:
                        to_restore[class_path] = {}
                    to_restore[class_path][p_name]= p_obj


        ########## restoring
        for class_path in to_restore:
            module_path = class_path[0:class_path.rindex('.')]
            class_name = class_path[class_path.rindex('.')+1::]
            deleted_params = self.deleted_params.get(class_name, [])

            try:
                module = __import__(module_path,fromlist=[module_path])
            except:
                Parameterized().warning("Could not find module '%s' to restore parameter values of '%s' (module might have been moved or renamed; if you are using this module, please file a support request via topographica.org"%(module_path,class_path))
                break

            try:
                class_=getattr(module,class_name)
            except:
                Parameterized().warning("Could not find class '%s' to restore its parameter values (class might have been removed or renamed; if you are using this class, please file a support request via topographica.org)."%class_path)
                break

            for p_name,p_obj in to_restore[class_path].items():
                try:
                    if p_name in deleted_params:
                        pass
                    elif p_name not in class_.params():
                        # CEBALERT: GlobalParams's source code never has
                        # parameters. If we move Parameter saving and
                        # restoring to Parameterized, could allow
                        # individual classes to customize Parameter
                        # restoration.
                        if class_.__name__!='GlobalParams':
                            Parameterized(name='load_snapshot').warning("%s.%s found in snapshot, but '%s' is no longer defined as a Parameter by the current version of %s. If you are using this class, please file a support request via topographica.org." % (class_.__name__, p_name,p_name,class_.__name__))
                    else:
                        setattr(class_,p_name,p_obj)
                except:
                    Parameterized(name='load_snapshot').warning("%s.%s found in snapshot, but '%s' but could not be restored to the current version of %s. If you are using this class, please file a support request via topographica.org." % (class_.__name__, p_name,p_name,class_.__name__))

    # CB: I guess this could be simplified
    def get_PO_class_attributes(self,module,class_attributes,processed_modules,exclude=()):
        """
        Recursively search module and get attributes of Parameterized classes within it.

        class_attributes is a dictionary {module.path.and.Classname: state}, where state
        is the dictionary {attribute: value}.

        Something is considered a module for our purposes if inspect says it's a module,
        and it defines __all__. We only search through modules listed in __all__.

        Keeps a list of processed modules to avoid looking at the same one
        more than once (since e.g. __main__ contains __main__ contains
        __main__...)

        Modules can be specifically excluded if listed in exclude.
        """
        dict_ = module.__dict__
        for (k,v) in dict_.items():
            if '__all__' in dict_ and inspect.ismodule(v) and k not in exclude:
                if k in dict_['__all__'] and v not in processed_modules:
                    self.get_PO_class_attributes(v,class_attributes,processed_modules,exclude)
                    processed_modules.append(v)

            else:
                if isinstance(v,type) and issubclass(v,Parameterized):

                    # Note: we take the class name as v.__name__, not
                    # k, because k might be just a label for the true
                    # class. For example, if someone imports a class
                    # using 'as', the name in the local namespace
                    # could be different from the name when the class
                    # was defined.  It is correct to set the
                    # attributes on the true class.
                    full_class_path = v.__module__+'.'+v.__name__
                    class_attributes[full_class_path] = {}
                    # Parameterized classes always have parameters in
                    # __dict__, never in __slots__
                    for (name,obj) in v.__dict__.items():
                        if isinstance(obj,Parameter) and obj.pickle_default_value:
                            class_attributes[full_class_path][name] = obj

