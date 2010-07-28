"""
Code used to support old snapshots, and update scripts.

$Id$
"""
__version__='$Revision: 8021 $'

import imp
import sys

# CB: If we were using pickle rather than cpickle, could subclass the
# unpickler to look for module Xs as module X if Xs can't be found,
# and probably simplify quite a lot of the legacy code installation.
#
# Maybe we could do that by trying to use cpickle initially, then
# falling back to pickle when we do a 'legacy load' of the snapshot.

# CEBALERT: should have ONE list for the update script and for this,
# rather than having (effectively) a list in each.



# CEBALERT: deal with this
# Temporary as of 12/2007, for backwards compatibility
# Image=FileImage


def _setstate(inst,state):
    for k,v in state.items():
        setattr(inst,k,v)


def preprocess_state(class_,state_mod_fn): 
    """
    Allow processing of state with state_mod_fn before
    class_.__setstate__(instance,state) is called.

    state_mod_fn must accept two arguments: instance and state.
    """
    if not hasattr(class_,'__setstate__'):
        # e.g. class_ used to be Parameterized, but now isn't
        class_.__setstate__ = _setstate

    old_setstate = class_.__setstate__
    def new_setstate(instance,state):
        # passing instance here allows us to avoid having to list
        # specific classes in SnapshotSupport, because we can
        # now test each instance.
        state_mod_fn(instance,state) 
        old_setstate(instance,state)
    class_.__setstate__ = new_setstate


# CB: this is complicated, and I'd like to remove it. Only
# being used once at the moment.
def select_setstate(class_,selector,pre_super=False,post_super=True):
    """
    Select appropriate function to call as a replacement
    for class.__setstate__ at runtime.

    selector must return None if the class_'s original method is
    to be used; otherwise, it should return a function that takes
    an instance of the class and the state.

    pre_super and post_super determine if super(class_)'s
    __setstate__ should be invoked before or after (respectively)
    calling the function returned by selector. If selector returns
    None, super(class_)'s __setstate__ is never called.
    """
    if pre_super is True and post_super is True:
        raise ValueError("Cannot call super method before and after.")

    old_setstate = class_.__setstate__
    def new_setstate(instance,state):
        setstate = selector(state) or old_setstate

        if pre_super and setstate is not old_setstate:
            super(class_,instance).__setstate__

        setstate(instance,state)

        if post_super and setstate is not old_setstate:
            super(class_,instance).__setstate__(state)


    class_.__setstate__ = new_setstate


# fake_X() vs redirect_X(): redirect simply makes the name point to
# another thing, whereas fake actually creates a new thing (e.g. new
# module)

def fake_a_class(module,old_name,new_class,new_class_args=()):
    """
    Install a class named 'old_name' in 'module'; when created,
    the class actually returns an instance of 'new_class'.

    new_class_args allow any arguments to be supplied to new_class
    before other arguments are passed at creation time.

    For use when module.old_name=new_class is not possible.
    """
    class_code = """
class %s(object):
    def __new__(cls,*args,**kw):
        all_args = new_class_args+args
        return new_class(*all_args,**kw)"""        
    exec class_code%old_name in locals()
    fake_old_class = eval(old_name,locals())

    setattr(module,old_name,fake_old_class)


def _import(x,y):
    """return module y from: 'from x import y'"""
    return __import__(x+'.'+y,fromlist=[y])

def module_redirect(name,parent,actual_module,parent_name=None):
    """
    For use when module parent.name is now actual_module.

    Use parent_name to override parent.name if necessary (e.g. when
    parent is already redirected).
    """
    if parent_name is None:
        parent_name=parent.__name__
        
    sys.modules[parent_name+'.'+name]=actual_module
    setattr(sys.modules[parent_name],name,actual_module)

    return getattr(parent,name)


def package_redirect(name,parent,actual_package):
    """
    For use when package parent.name is now actual_package.

    All .py files found in actual_package's path are added to newly
    created parent.name package.
    """
    new_package = module_redirect(name,parent,actual_package)
    
    import os,fnmatch
    mod_names = [f.split('.py')[0] for f in os.listdir(actual_package.__path__[0]) if fnmatch.fnmatch(f,'[!._]*.py')]

    for mod_name in mod_names:
        m=_import(actual_package.__name__,mod_name)
        module_redirect(mod_name,new_package,m,parent_name=parent.__name__+'.'+name)

    
    
def fake_a_module(name,source_code,parent=None,parent_name=None):
    """
    Create the module parent.name using source_code.

    Installs to sys.modules[name] unless parent is not None,
    in which case see module_redirect().
    """
    # create the module
    module = imp.new_module(name)
    exec source_code in module.__dict__

    if parent is None:
        sys.modules[name]=module
    else:
        module_redirect(name,parent,module,parent_name)


class DuplicateCheckingList(list):
    def append(self,item):
        assert item not in self, "%s already added"%item
        list.append(self,item)


# put this somewhere...
import param
param.parameterized.PicklableClassAttributes.do_not_restore+=[
    'topo.base.boundingregion.BoundingRegion',
    'topo.base.boundingregion.BoundingBox',
    'topo.base.boundingregion.BoundingCircle',
    'topo.base.boundingregion.BoundingEllipse',
    'topo.base.cf.ConnectionField',
    'topo.projection.basic.SharedWeightCF']


class SnapshotSupport(object):

    @staticmethod
    def install(svn=None):

        # CEBALERT: should add svn version test to see which hacks
        # actually need to be installed. I.e. organize these in
        # suitable way e.g. dictionary.
        # Haven't yet thought about whether or not it's actually possible
        # to get the version number before unpickling...
        import param
        global supporters
        for f in supporters:
            param.Parameterized(name='SnapshotSupport').debug("calling %s"%f.__name__)
            f()



####
# CEB: this is only to show how we could support running old scripts
# without modifying them. Currently we haven't implemented enough for
# it to be useful.
# E.g. we changed output_fn to output_fns for several classes. To
# support that in a snapshot requires intercepting the saved data and
# detecting 'output_fn=x' and replacing it with 'output_fns=[x]',
# etc. To support it in a script requires installing something in the
# class that will take .output_fn=x and actually do .output_fns=[x]. A
# concrete example is given below: CFProjection's weights_shape was
# changed to cf_shape.
def LegacySupport():
    """
    Support for running old scripts. Use in conjunction with
    SnapshotSupport.install() to avoid duplication.
    """
    # rXXXX renamed CFProjection.weights_shape to CFProjection.cf_shape 
    import topo.base.cf
    cfp = topo.base.cf.CFProjection
    type.__setattr__(cfp,'weights_shape',cfp.__dict__['cf_shape'])
####
    

def install_legacy_support():
    SnapshotSupport.install()
    LegacySupport()



######################################################################
######################################################################

# note there's no legacy support for people using CFSOM. We could
# add that if necessary.


S=supporters=DuplicateCheckingList()
# in general, newest changes should go at the start of the list.


# do not restore search_paths,prefix for resolve_path,normalize_path
# hack
import param.parameterized
param.parameterized.PicklableClassAttributes.do_not_restore+=[
    'param.normalize_path',
    'param.resolve_path']


# fixedpoint available as topo.misc.fixedpoint, not fixedpoint
import topo.misc.fixedpoint as fixedpoint
from topo.misc.util import ModuleImporter,ModuleFaker

class FixedPointImporter(ModuleImporter):

    def find_module(self, fullname, path=None):
        if fullname == 'fixedpoint' or fullname.startswith('fixedpoint.'):
            f = FixedPointFaker()
            f.path = path
            return f
        return None

class FixedPointFaker(ModuleFaker):
    def create_module(self,name):
        return fixedpoint

import sys
sys.meta_path.append(FixedPointImporter())



def removed_Enumeration():

    import param

    class Enumeration(object):
        """
        Provide support for existing code that uses Enumeration.
        """
        @staticmethod
        def _transform(kw):
            if 'available' in kw:
                kw['objects']=kw['available']
                del kw['available']
            kw['check_on_set']=True            

        def __new__(cls,*args,**kw): 
            print "no way!"
            Enumeration._transform(kw)
            n = param.ObjectSelector(*args,**kw)
            return n

        def __init__(self,*args,**kw):
            Enumeration._transform(kw)
            super(param.ObjectSelector,self).__init__(self,*args,**kw)

    param.Enumeration = Enumeration

S.append(removed_Enumeration)


def bye_bye_param():
    import param
    import topo
    package_redirect('param',topo,param)

S.append(bye_bye_param)


def renamed_output_fn_to_output_fns():
    ## rXXXX output_fn=X changed to output_fns=[x] in multiple classes
    
    def _changed_output_fn(instance,state):
        for x in 'output_fn','weights_output_fn':
            if x in state:
                fn = state[x]
                state['%ss'%x] = [fn]
                # CEBALERT: ideally, would also delete old 'output_fn' parameter,
                # but we don't currently support parameter deletion.
                del state[x] # probably does nothing

            if 'apply_%s'%x in state:
                state['apply_%ss'%x]=state['apply_%s'%x]
                del state['apply_%s'%x]

            if 'apply_%s_init'%x in state:
                state['apply_%ss_init'%x]=state['apply_%s_init'%x]
                del state['apply_%s_init'%x]
 
    # because I can't be bothered narrowing it down; does this
    # slow down legacy support installation?
    from topo.param.parameterized import Parameterized
    preprocess_state(Parameterized,_changed_output_fn)

   
    def _post_initialization_weights_output_fn(instance,state):
        if 'post_initialization_weights_output_fn' in state:
            state['post_initialization_weights_output_fns']=[state['post_initialization_weights_output_fn']]
            del state['post_initialization_weights_output_fn']
    from topo.sheet.lissom import LISSOM
    # CEBALERT: problem with multiple preprocess_state functions? 
    #preprocess_state(LISSOM,_post_initialization_weights_output_fn)


    # CEBALERT: need to handle the class parameters
    # (see ALERT in topo.param.parameterized saying that it's
    # currently not possible)




S.append(renamed_output_fn_to_output_fns)


def removed_pipeline():
    import topo.transferfn.basic,topo.base.functionfamily
    from topo import param
    class PipelineTF(topo.base.functionfamily.TransferFn):
        def __new__(self,*args,**kw):
            param.Parameterized().warning("PipelineTF is deprecated; returning output_fns list.")
            
            if 'output_fns' in kw:
                return kw['output_fns']
            else:
                return []

    topo.base.functionfamily.PipelineOF = PipelineTF
    topo.base.functionfamily.PipelineTF = PipelineTF
    
    topo.transferfn.basic.PipelineTF = PipelineTF
    topo.transferfn.basic.Pipeline = PipelineTF
    topo.transferfn.basic.PipelineOF = PipelineTF

S.append(removed_pipeline)



def rename_outputfn_to_transferfn():
    ### rXXXX moved topo.outputfn to topo.transferfn
    import topo,topo.transferfn
    package_redirect('outputfn',topo,topo.transferfn)

    ### rXXXX renamed OutputFn to TransferFn + xxxOF->xxxTF
    import topo.base.functionfamily
    import topo.transferfn.basic

    def _rename(mod):        
        for name,obj in mod.__dict__.items():
            if isinstance(obj,type) and issubclass(obj,mod.TransferFn):
                if name.endswith('TF'):
                    old_name = name[0:-2]+'OF'
                    new_class = obj
                    setattr(mod,old_name,obj)
                elif 'TransferFn' in name:
                    old_name=name.replace('Transfer','Output')
                    setattr(mod,old_name,obj)

    _rename(topo.base.functionfamily)
    _rename(topo.transferfn.basic)

S.append(rename_outputfn_to_transferfn)


def removed_InstanceMethodWrapper():
    # removed this class in rXXXX
    class InstanceMethodWrapper(object):
        """
        Wrapper for pickling instance methods.

        The constructor takes an instance method (e.g. for an object
        'sim', method sim.time) as its only argument.  The wrapper
        instance is callable, picklable, etc.
        """
        def __repr__(self):
            return repr(self.im.im_func)

        # Hope __name__ doesn't get set...
        def _fname(self):
            return self.im.im_func.func_name
        __name__ = property(_fname)

        def __init__(self,im):
            self.im = im

        def __getstate__(self):
            return (self.im.im_self,
                    self.im.im_func.func_name)

        def __setstate__(self,state):
            obj,func_name = state
            self.im = getattr(obj,func_name)

        def __call__(self,*args,**kw):
            return self.im(*args,**kw)

    import topo.param
    topo.param.InstanceMethodWrapper = InstanceMethodWrapper

S.append(removed_InstanceMethodWrapper)


def param_remove_hidden():
    # Hidden attribute removed from Parameter in r7861
    from topo import param
    def _param_remove_hidden(instance,state):
        if 'hidden' in state:
            if state['hidden'] is True:
                state['precedence']=-1
            del state['hidden']
    preprocess_state(param.Parameter,_param_remove_hidden)

S.append(param_remove_hidden)

def param_add_readonly():
    # Hidden attribute added to Parameter in r7975
    from topo import param
    def _param_add_readonly(instance,state):
        if 'readonly' not in state:
            state['readonly']=False
    preprocess_state(param.Parameter,_param_add_readonly)

S.append(param_add_readonly)


def class_selector_remove_suffixtolose():
    # suffix_to_lose removed from ClassSelectorParameter in r8031
    from topo import param
    def _class_selector_remove_suffixtolose(instance,state):
        if 'suffix_to_lose' in state:
            del state['suffix_to_lose']
    preprocess_state(param.ClassSelector,_class_selector_remove_suffixtolose)
    
S.append(class_selector_remove_suffixtolose)


def cf_rename_slice_array():
    ## slice_array was renamed to input_sheet_slice in r7548    
    def _cf_rename_slice_array(instance,state):
        if 'slice_array' in state:
            input_sheet_slice = state['slice_array']
            state['input_sheet_slice'] = input_sheet_slice
            del state['slice_array'] # probably doesn't work

    from topo.base.cf import ConnectionField
    preprocess_state(ConnectionField,_cf_rename_slice_array)

S.append(cf_rename_slice_array)

def sim_remove_time_type_attr():
    # _time_type attribute added to simulation in r7581
    # and replaced by time_type param in r8215
    def _sim_remove_time_type_attr(instance,state):
        if '_time_type' in state:
            # CB: untested code (unless someone has such a snapshot;
            # if nobody has such a snapshot, can remove this code).
            state['_time_type_param_value']=state['_time_type']
            del state['_time_type']

    from topo.base.simulation import Simulation
    preprocess_state(Simulation,_sim_remove_time_type_attr)
S.append(sim_remove_time_type_attr)



def slice_setstate_selector():
    # Allow loading of pickles created before Pickle support was added to Slice.
    #
    # In snapshots created between 7547 (Slice becomes array) and 7762
    # (inclusive; Slice got pickle support in 7763), Slice instances
    # will be missing some information.
    #
    # CB: info could be recovered if required.
    def _slice_setstate_selector(state):
        
        if isinstance(state,dict):
            return None
        else:
            import numpy
            return numpy.ndarray.__setstate__

    from topo.base.sheetcoords import Slice                
    select_setstate(Slice,_slice_setstate_selector,post_super=False)

S.append(slice_setstate_selector)


def sheet_set_shape():
    # CB: this is to work round change in SCS, but __setstate__ is never
    # called on that (method resolution order means __setstate__ comes
    # from EventProcessor instead)
    from topo.base.sheetcoords import Slice
    def _sheet_set_shape(instance,state):
        # since 7958, SCS has stored shape on creation
        if '_SheetCoordinateSystem__shape' not in state:
            m = '_SheetCoordinateSystem__'
            # all these are necessary for the calculation now,
            # but would not otherwise be restored until later
            setattr(instance,'bounds',state['bounds'])
            setattr(instance,'lbrt',state['lbrt'])
            setattr(instance,m+'xdensity',state[m+'xdensity'])
            setattr(instance,m+'xstep',state[m+'xstep'])
            setattr(instance,m+'ydensity',state[m+'ydensity'])
            setattr(instance,m+'ystep',state[m+'ystep'])
            shape = Slice(instance.bounds,instance).shape_on_sheet()
            setattr(instance,m+'shape',shape)
            state[m+'shape']=shape

    from topo.base.sheet import Sheet
    preprocess_state(Sheet,_sheet_set_shape) 
S.append(sheet_set_shape)


def removed_function_family_parameters():
    # r8001 Removed OutputFnParameter and CFPOutputFnParameter
    # r8014 Removed LearningFnParameter and ResponseFnParameter (+CFP equivalents)
    # r8028 Removed CoordinateMapperFnParameter
    # r8029 Removed PatternGeneratorParameter
    from topo import param
    from topo.base.functionfamily import OutputFn,ResponseFn,LearningFn,\
         CoordinateMapperFn
    d = {"OutputFnParameter":OutputFn,
         "ResponseFnParameter":ResponseFn,
         "LearningFnParameter":LearningFn,
         "CoordinateMapperFnParameter":CoordinateMapperFn}        

    import topo.base.functionfamily
    for name,arg in d.items():
        fake_a_class(topo.base.functionfamily,name,
                     param.ClassSelector,(arg,))

    from topo.base.cf import CFPOutputFn,CFPResponseFn,CFPLearningFn
    d = {"CFPOutputFnParameter":CFPOutputFn,
         "CFPResponseFnParameter":CFPResponseFn,
         "CFPLearningFnParameter":CFPLearningFn}         

    import topo.base.cf
    for name,arg in d.items():
        fake_a_class(topo.base.cf,name,
                     param.ClassSelector,(arg,))

    import topo.base.patterngenerator
    from topo.base.patterngenerator import PatternGenerator
    fake_a_class(topo.base.patterngenerator,"PatternGeneratorParameter",
                 param.ClassSelector,(PatternGenerator,))

S.append(removed_function_family_parameters)



def added_dynamic_time_fn():
    # for snapshots saved before r7901
    from topo import param
    class SimSingleton(object):
        """Support for old snapshots."""
        def __setstate__(self,state):
            sim = state['actual_sim']
            param.Dynamic.time_fn = sim.time

    import topo.base.simulation
    topo.base.simulation.SimSingleton=SimSingleton

S.append(added_dynamic_time_fn)

def moved_parameterized():
    # rXXXX
    # support topo.base.parameterized
    import topo.base
    module_redirect('parameterized',topo.base,topo.param.parameterized)

S.append(moved_parameterized)

def renamed_parameterizedobject():
    # rXXXX
    # support topo.base.parameterizedobject
    import topo.param
    module_redirect('parameterizedobject',topo.base,topo.param.parameterized)
    topo.base.parameterizedobject.ParameterizedObject=topo.param.parameterized.Parameterized
S.append(renamed_parameterizedobject)

def removed_parameterclasses():
    # rXXXX
    # support topo.base.parameterclasses
    import topo.param
    module_redirect('parameterclasses',topo.base,topo.param)

    new_names = ['Boolean','String','Callable','Composite','Selector',
                 'ObjectSelector','ClassSelector','List','Dict']

    for name in new_names:
        setattr(topo.base.parameterclasses,name+'Parameter',
                getattr(topo.base.parameterclasses,name))
S.append(removed_parameterclasses)

def removed_DynamicNumber():
    # DynamicNumber was removed in rXXXX
    class DynamicNumber(object):
        """
        Provide support for existing code that uses DynamicNumber:
        see __new__().
        """
        warnedA = False  # suppress warnings for the moment.
        warnedB = False

        def __new__(cls,default=None,**params):
            """
            If bounds or softbounds or any params are supplied, assume
            we're dealing with DynamicNumber declared as a parameter
            of a ParameterizedObject class.  In this case, return a
            new *Number* parameter instead.

            Otherwise, assume we're dealing with DynamicNumber
            supplied as the value of a Number Parameter. In this case,
            return a DynamicNumber (but one which is not a Parameter,
            just a simple wrapper).

            * Of course, this is not 100% reliable: if someone defines
            * a class with a DynamicNumber but doesn't pass any doc or
            * bounds or whatever. But in such cases, they'll get the
            * ParameterizedObject warning about being unable to set a
            * class attribute.

            Most of the code is to generate warning messages.

            """
            if len(params)>0:
                ####################
                m = "\n------------------------------------------------------------\nPlease update your code - instead of using the 'DynamicNumber' Parameter in the code for your class, please use the 'Number' Parameter; the Number Parameter now supports dynamic values automatically.\n\nE.g. change\n\nclass X(Parameterized):\n    y=DynamicNumber(NumberGenerator())\n\nto\n\n\nclass X(Parameterized):\n    y=Number(NumberGenerator())\n------------------------------------------------------------\n"
                if not cls.warnedA:
                    param.Parameterized().warning(m)
                    cls.warnedA=True
                ####################

                n = Number(default,**params)
                return n
            else:
                ####################
                m = "\n------------------------------------------------------------\nPlease update your code - instead of using DynamicNumber to contain a number generator, pass the number generator straight to the Number parameter:\n\nE.g. in code using the class below...\n\nclass X(Parameterized):\n    y=Number(0.0)\n\n\nchange\n\nx = X(y=DynamicNumber(NumberGenerator()))\n\nto\n\nx = X(y=NumberGenerator())\n------------------------------------------------------------\n"
                if not cls.warnedB:
                    param.Parameterized().warning(m)
                    cls.warnedB=True
                ####################
                return object.__new__(cls,default)


        def __init__(self,default=0.0,bounds=None,softbounds=None,**params):
            self.val = default
        def __call__(self):
            return self.val()

    import topo.base.parameterclasses
    topo.base.parameterclasses.DynamicNumber = DynamicNumber
    import topo.param
    topo.param.DynamicNumber = DynamicNumber

S.append(removed_DynamicNumber)


def cfproj_add_cfs():
    # cfs attribute added in r8227
    from topo.base.cf import CFProjection
    from numpy import array
    def _cfproj_add_cfs(instance,state):
        if 'cfs' not in state:
            cflist = state['_cfs']
            state['cfs'] = array(cflist)
    preprocess_state(CFProjection,_cfproj_add_cfs)

S.append(cfproj_add_cfs)

def renamed_component_libraries():
    # rXXXX renaming of component libraries
    import topo.outputfn,topo.responsefn,\
           topo.learningfn,topo.coordmapper
    package_redirect('outputfns',topo,topo.outputfn)
    package_redirect('responsefns',topo,topo.responsefn)
    package_redirect('learningfns',topo,topo.learningfn)
    package_redirect('coordmapperfns',topo,topo.coordmapper)

S.append(renamed_component_libraries)

def removed_generator():
    ### rXXXX removed topo/sheet/generator.py
    import topo.sheet
    module_redirect('generator',topo.sheet,topo.sheet)

S.append(removed_generator)

def renamed_sheets():
    import topo,topo.sheet
    package_redirect('sheets',topo,topo.sheet)

S.append(renamed_sheets)

def renamed_eps():
    import topo,topo.ep
    package_redirect('eps',topo,topo.ep)

S.append(renamed_eps)


def renamed_patterns():
    import topo.pattern
    package_redirect('patterns',topo,topo.pattern)

S.append(renamed_patterns)

def renamed_commands():
    import topo.command
    package_redirect('commands',topo,topo.command)

S.append(renamed_commands)

def renamed_projections():
    import topo.projection
    package_redirect('projections',topo,topo.projection)

    # CEBALERT: check this is necessary
    # the isn't-in-__all__ shimmy
    import sys
    import topo.projections.basic as ps,topo.projection.basic as p
    ps.CFPOF_SharedWeight = p.CFPOF_SharedWeight
    ps.SharedWeightCF = p.SharedWeightCF

S.append(renamed_projections)


def renamed_generatorsheet():
    # CEBALERT: below gives errors with snapshot-compatiblity-tests
    import topo.sheets
    module_redirect('generatorsheet',topo.sheets,topo.sheet.generator,parent_name='topo.sheets')

S.append(renamed_generatorsheet)

def renamed_functionfamilies():
    # rXXXX renamed functionfamilies
    import topo.base,topo.base.functionfamily
    module_redirect('functionfamilies',topo.base,topo.base.functionfamily)

S.append(renamed_functionfamilies)

def renamed_projfns():
    # rXXXX renamed topo.x.projfns
    import topo.outputfn.projfn,topo.responsefn.projfn,topo.learningfn.projfn
    for mod in ['outputfn','responsefn','learningfn']:
        existing_mod = _import('topo.%s'%mod,'projfn')
        module_redirect('projfns',_import('topo',mod),existing_mod,parent_name='topo.%s'%mod)
        module_redirect('projfns',_import('topo',mod+'s'),existing_mod,parent_name='topo.%ss'%mod)

S.append(renamed_projfns)

# CEBALERT: what's going on with the order in this file? Should have
# maintained a consistent order, processing most recent changes first.
def removed_numbergenerator():
    import topo.numbergen
    module_redirect('numbergenerator',topo.misc,topo.numbergen)

S.append(removed_numbergenerator)


def renamed_numbergenerators():
    # rXXXX renamed topo.misc.numbergenerators
    import topo.misc.numbergenerator
    module_redirect('numbergenerators',topo.misc,topo.misc.numbergenerator)

S.append(renamed_numbergenerators)

def renamed_patternfns():
    # rXXXX renamed topo.misc.patternfns
    import topo.misc.patternfn
    module_redirect('patternfns',topo.misc,topo.misc.patternfn)

S.append(renamed_patternfns)

def removed_ExtraPickler():
    import topo.misc.util
    # r9617 removed ExtraPickler
    class ExtraPicklerSkipper(object):
        def __setstate__(self,state):
            # print warning of what's being skipped?
            pass
    topo.misc.util.ExtraPickler=ExtraPicklerSkipper

S.append(removed_ExtraPickler)

def renamed_utils():
    # rXXXX renamed topo.misc.utils
    import topo.misc.util
    module_redirect('utils',topo.misc,topo.misc.util)

S.append(renamed_utils)

def renamed_traces():
    # rXXXX renamed topo.misc.traces
    import topo.misc.trace
    module_redirect('traces',topo.misc,topo.misc.trace)

S.append(renamed_traces)


def duplicate_SineGratingDisk():
    # rXXXX duplicate SineGratingDisk removed
    import topo.pattern.basic
    from topo.pattern import SineGrating,Disk
    # rXXXX removed these classes
    from topo import param
    class SineGratingDisk(SineGrating):
        """2D sine grating pattern generator with a circular mask."""
        mask_shape = param.Parameter(default=Disk(smoothing=0,size=1.0))
    topo.pattern.basic.SineGratingDisk = SineGratingDisk
S.append(duplicate_SineGratingDisk)


# CEB: possibly this should be higher up (above topo.patterns?)
# And were there other classes e.g. OrientationContrastPattern?
def teststimuli_removed():
    # rXXXX
    import topo.pattern
    code = \
"""
from topo.pattern.basic import SineGrating,Disk,Rectangle,Ring
from topo import param
class SineGratingDisk(SineGrating):
    mask_shape = param.Parameter(default=Disk(smoothing=0,size=1.0))

class SineGratingRectangle(SineGrating):
   mask_shape = param.Parameter(default=Rectangle(smoothing=0,size=1.0))

class SineGratingRing(SineGrating):
   mask_shape = param.Parameter(default=Ring(smoothing=0,size=1.0))
"""
    fake_a_module('teststimuli',code,parent=topo.pattern)

S.append(teststimuli_removed)


def moved_homeostatic():
    # rXXXX homeostatic of moved into basic
    import topo.outputfns
    # CEBALERT: surely a typo here?
    module_redirect('homeostatic',topo.outputfns,topo.outputfns)

S.append(moved_homeostatic)

def renamed_cfproj_weights_shape():
    # rXXXX renamed CFProjection.weights_shape to CFProjection.cf_shape
    from topo import param
    param.parameterized.PicklableClassAttributes.param_name_changes['topo.base.cf.CFProjection']={'weights_shape':'cf_shape'}

S.append(renamed_cfproj_weights_shape)

def cf_bounds_readonly():
    # rXXXX CF's bounds made into read-only attribute (since the value
    # actually comes from the slice).
    # (Problem exposed when Parameterized's __setstate__ changed to
    # set all state attributes, rather than just those in __dict__?)        
    def cf_bounds_property(instance,state):
        try:
            del state['bounds']
        except KeyError:
            pass

    from topo.base.cf import ConnectionField
    preprocess_state(ConnectionField,cf_bounds_property)

S.append(cf_bounds_readonly)


# (Currently, the code below is already run in topo.__init__ if gmpy
# isn't available.)
## If gmpy.mpq is not available, use fixedpoint.FixedPoint. 
#from topo.misc.util import gmpyImporter
#sys.meta_path.append(gmpyImporter())


def param_add_allow_None():
    # allow_None added in r9380
    from topo import param
    def _param_add_allow_None(instance,state):
        if 'allow_None' not in state and hasattr(instance.__class__,'allow_None'):
            # have to add to state or else slot won't exist on instance, but will
            # exist on class (consequence of using __slots__)
            state['allow_None']=False
    preprocess_state(param.Parameter,_param_add_allow_None)

S.append(param_add_allow_None)

def number_add_inclusive_bounds():
    # inclusive_bounds added to Number in r9789    
    from topo import param
    def _number_add_inclusive_bounds(instance,state):
        if 'inclusive_bounds' not in state:
            state['inclusive_bounds']=(True,True)
    preprocess_state(param.Number,_number_add_inclusive_bounds)

S.append(number_add_inclusive_bounds)


def onedpowerspectrum_was_in_basic():
    # rXXXX-rXXXX OneDPowerSpectrum moved back to pattern/audio 
    import topo.pattern.audio
    import topo.pattern.basic
    topo.pattern.audio.OneDPowerSpectrum=topo.pattern.basic.Spectrogram
    topo.pattern.basic.OneDPowerSpectrum=topo.pattern.audio.OneDPowerSpectrum
S.append(onedpowerspectrum_was_in_basic)


def boundingregion_not_parameterized():
    import topo.base.boundingregion

    def _boundingregion_not_parameterized(instance,state):
        for a in ['initialized', '_name_param_value', 'nopickle']:
            if a in state:
                del state[a]

    preprocess_state(topo.base.boundingregion.BoundingRegion,
                     _boundingregion_not_parameterized)

S.append(boundingregion_not_parameterized)


cf_xy_warned=False
def cf_not_parameterized():
    from topo.base.cf import ConnectionField

    def _cf_not_parameterized(instance,state):
        
        for p in [('_y_param_value','y'),('_x_param_value','x')]:
            if p[0] in state:
                state[p[1]]=state[p[0]]
                del state[p[0]]

        for p in ['_name_param_value','initialized','nopickle','bounds_template']:
            if p in state:
                del state[p]

        # rXXXX weights_slice no longer stored
        if 'weights_slice' in state:
            del state['weights_slice']

        # rXXXX input_sheet no longer stored
        if 'input_sheet' in state:
            del state['input_sheet']

        # rXXXX x,y no longer stored
        if 'x' in state: # assume 'y' also in state
            global cf_xy_warned
            if not cf_xy_warned:
                from topo import param
                param.Parameterized().warning("Not restoring ConnectionField's (x,y) location. Bounds resizing will not work -- please file a support request via the website.") # could add support by loading ResizableCFProjection for any CFProjection with CFs that have x and y, and moving x and y to the ResizableProjection.
                cf_xy_warned=True
            del state['x']
            del state['y']
            

    preprocess_state(ConnectionField,_cf_not_parameterized)

S.append(cf_not_parameterized)


def cfproj_add_flatcfs():
    # flatcfs attribute added 
    from topo.base.cf import CFProjection
    def _cfproj_add_flatcfs(instance,state):
        if 'flatcfs' not in state:
            try:
                state['flatcfs'] = list(state['cfs'].flat)
            except KeyError:
                from topo.misc.util import flatten
                state['flatcfs'] = flatten(state['_cfs'])
            
    preprocess_state(CFProjection,_cfproj_add_flatcfs)

S.append(cfproj_add_flatcfs)


def cfproj_add_n_units():
    # n_units() -> n_units 

    from topo.base.cf import CFProjection

    def get_n_units(self):
        try:
            return self.__dict__['n_units']
        except KeyError:
            n = self._calc_n_units()
            self.__dict__['n_units'] = n
            
    def set_n_units(self,n):
        self.__dict__['n_units'] = n

    type.__setattr__(CFProjection,'n_units',property(get_n_units,set_n_units))
            

S.append(cfproj_add_n_units)

def transferfn_misc():
    import topo.transferfn.misc as ttm
    import topo.transferfn.basic as ttb
    ttb.HalfRectify=ttm.HalfRectify
    ttb.PatternCombine=ttm.PatternCombine
    ttb.AttributeTrackingTF=ttm.AttributeTrackingTF
    ttb.HomeostaticResponse=ttm.HomeostaticResponse
    ttb.KernelMax=ttm.KernelMax

S.append(transferfn_misc)


def renamed_pylabplots():
    import topo.command.pylabplot
    module_redirect('pylabplots',topo.command,topo.command.pylabplot)

S.append(renamed_pylabplots)



