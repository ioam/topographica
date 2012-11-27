"""
Extensions to pickle allowing items in __main__ to be saved.
"""

# CEBALERT: move into snapshots.py?

import new
import pickle
import types
import __main__
from StringIO import StringIO

import copy

def _name_is_main(obj):
    # CEBALERT: see IPython hack in commandline.py
    return obj.__module__ == "__main__" or obj.__module__ == "__mynamespace__"



class PickleMain(object):
    """
    Pickle support for types and functions defined in __main__.

    When pickled, saves types and functions defined in __main__ by
    value (i.e. as bytecode). When unpickled, loads previously saved
    types and functions back into __main__.
    """
    def _create_pickler(self):
        # Usually we use the cPickle module rather than the pickle
        # module (because cPickle is faster), but here we need control
        # over the pickling process so we use pickle.
        #
        # Additionally, we create a Pickler instance to avoid changing
        # defaults in the pickle module itself, so that there are no side
        # effects for code elsewhere (although we don't use pickle
        # anywhere else ourselves...).

        self.pickled_bytecode = StringIO()
        self.pickler = pickle.Pickler(self.pickled_bytecode,-1)

        # CB: pickle.Pickler's dispatch attribute is a class
        # attribute (I don't know why, but it is...), so before
        # modifying this instance's dispatch attribute we make sure
        # modifications will affect only this instance.
        self.pickler.dispatch = copy.copy(self.pickler.dispatch)

        self.pickler.dispatch[new.code] = save_code
        self.pickler.dispatch[new.function] = save_function
        self.pickler.dispatch[dict] = save_module_dict
        self.pickler.dispatch[new.classobj] = save_classobj
        self.pickler.dispatch[new.instancemethod] = save_instancemethod
        self.pickler.dispatch[new.module] = save_module
        self.pickler.dispatch[type] = save_type

        # CB: maybe this should be registered from elsewhere
        import param
        self.pickler.dispatch[param.parameterized.ParameterizedMetaclass] = save_type


    def __getstate__(self):
        self._create_pickler()

        bytecode = {}
        for name,obj in __main__.__dict__.items():
            if not name.startswith('_'):
                if isinstance(obj,types.FunctionType) or isinstance(obj,type):
                    # (could be extended to other types, I guess
                    if _name_is_main(obj):
                        #CB: how do I print out info via Parameterized?
                        print "%s is defined in __main__: saving bytecode."%name
                        bytecode[name] = obj

        self.pickler.dump(bytecode)
        return {'pickled_bytecode':self.pickled_bytecode}


    def __setstate__(self,state):
        bytecode = pickle.load(StringIO(state['pickled_bytecode'].getvalue()))

        for name,obj in bytecode.items():
            print "%s restored from bytecode into __main__"%name
            __main__.__dict__[name] = obj





### Copied from http://code.activestate.com/recipes/572213/ ###

# Original docstring
#
# Extend pickle module to allow pickling of interpreter state
# including any interactively defined functions and classes.
#
# This module is not required for unpickling such pickle files.
#
# >>> import savestate, pickle, __main__
# >>> pickle.dump(__main__, open('savestate.pickle', 'wb'), 2)

# (note that we're not actually using it to pickle __main__, and I've
# removed the lines that change pickle's defaults)


def save_code(self, obj):
    """ Save a code object by value """
    args = (
        obj.co_argcount, obj.co_nlocals, obj.co_stacksize, obj.co_flags, obj.co_code,
        obj.co_consts, obj.co_names, obj.co_varnames, obj.co_filename, obj.co_name,
        obj.co_firstlineno, obj.co_lnotab, obj.co_freevars, obj.co_cellvars
    )
    self.save_reduce(new.code, args, obj=obj)

def save_function(self, obj):
    """ Save functions by value if they are defined interactively """
    if _name_is_main(obj) or obj.func_name == '<lambda>':
        args = (obj.func_code, obj.func_globals, obj.func_name, obj.func_defaults, obj.func_closure)
        self.save_reduce(new.function, args, obj=obj)
    else:
        self.save_global(obj)
        #pickle.Pickler.save_global(self, obj)

def save_global_byname(self, obj, modname, objname):
    """ Save obj as a global reference. Used for objects that pickle does not find correctly. """
    self.write('%s%s\n%s\n' % (pickle.GLOBAL, modname, objname))
    self.memoize(obj)

def save_module_dict(self, obj, main_dict=vars(__import__('__main__'))):
    """ Special-case __main__.__dict__. Useful for a function's func_globals member. """
    if obj is main_dict:
        save_global_byname(self, obj, '__main__', '__dict__')
    else:
        return self.save_dict(obj)
        #return pickle.Pickler.save_dict(self, obj)      # fallback to original

def save_classobj(self, obj):
    """ Save an interactively defined classic class object by value """
    if _name_is_main(obj):
        args = (obj.__name__, obj.__bases__, obj.__dict__)
        self.save_reduce(new.classobj, args, obj=obj)
    else:
        name = str(obj).split('.')[-1]  # CEB: hack to find classic class name
        self.save_global(obj,name)
        #pickle.Pickler.save_global(self, obj, name)

def save_instancemethod(self, obj):
    """ Save an instancemethod object """
    # Instancemethods are re-created each time they are accessed so this will not be memoized
    args = (obj.im_func, obj.im_self, obj.im_class)
    self.save_reduce(new.instancemethod, args)

def save_module(self, obj):
    """ Save modules by reference, except __main__ which also gets its contents saved by value """
    if _name_is_main(obj):
        self.save_reduce(__import__, (obj.__name__,), obj=obj, state=vars(obj).copy())
    elif obj.__name__.count('.') == 0:
        self.save_reduce(__import__, (obj.__name__,), obj=obj)
    else:
        save_global_byname(self, obj, *obj.__name__.rsplit('.', 1))

def save_type(self, obj):
    if getattr(new, obj.__name__, None) is obj:
        # Types in 'new' module claim their module is '__builtin__' but are not actually there
        save_global_byname(self, obj, 'new', obj.__name__)
    elif _name_is_main(obj):
        # Types in __main__ are saved by value

        # Make sure we have a reference to type.__new__
        if id(type.__new__) not in self.memo:
            self.save_reduce(getattr, (type, '__new__'), obj=type.__new__)
            self.write(pickle.POP)

        # Copy dictproxy to real dict
        d = dict(obj.__dict__)
        # Clean up unpickleable descriptors added by Python
        d.pop('__dict__', None)
        d.pop('__weakref__', None)

        args = (type(obj), obj.__name__, obj.__bases__, d)
        self.save_reduce(type.__new__, args, obj=obj)
    else:
        # Fallback to default behavior: save by reference
        self.save_global(obj)
        #pickle.Pickler.save_global(self, obj)
###############################################################
