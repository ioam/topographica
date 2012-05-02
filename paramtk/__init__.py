"""
Classes linking Parameters to Tkinter.

TkParameterized allows flexible graphical representation and
manipulation of the parameters of a Parameterized instance or class.

ParametersFrame and ParametersFrameWithApply extend TkParameterized,
displaying all the Parameters together in a list. Both allow these
Parameters to be edited; ParametersFrame applies changes immediately
as they are made, whereas ParametersFrameWithApply makes no changes
until a confirmation is given (by pressing the 'Apply' button).

Using these classes to display parameters has several benefits,
including that, automatically:

- changes to the Parameters in the GUI are reflected in the objects
  themselves without any additional code;

- each Parameter is represented by an appropriate widget (e.g. slider
  for a Number);

- type and range checking is handled (by virtue of using parameters);

- doc strings are displayed as pop-up help for each parameter;

- parameter names are formatted nicely for display;

- changes to parameter values in the GUI can be associated with
  function calls.


Examples
========

(1) Display the parameters of an object inside an existing window

You want to display all parameters of a parameterized instance
inside an existing containter (e.g. a window or a frame):

  # existing Parameterized instance g
  from topo import pattern
  g = pattern.Gaussian()
  
  # existing window t
  import Tkinter
  t = Tkinter.Toplevel()
  
  # display all the parameters of g in t
  from topo.param.tk import ParametersFrame
  ParametersFrame(t,g)
  #should be ParametersFrame(t,g).pack(); see ALERT in ParametersFrame
  

(2) Display the parameters of an object in a standalone window

You want a new window displaying only the parameters of your object:

  # existing Parameterized instance g
  from topo import pattern
  g = pattern.Gaussian()
  
  # display all the parameters of g in a new window
  from topo.param.tk import edit_parameters
  edit_parameters(g)
  

(3) Flexible GUI layout using TkParameterized

You want to display only some of the parameters of one or more
Parameterized instances:

 ## Existing, non-GUI code
 from topo import param

 class Object1(param.Parameterized):
     duration = param.Number(2.0,bounds=(0,None),doc='Duration of measurement')
     displacement = param.Number(0.0,bounds=(-1,1),doc='Displacement from point A')

 class Object2(param.Parameterized):
     active_today = param.Boolean(True,doc='Whether or not to count today')
     operator_name = param.String('A. Person',doc='Operator today')

 o1 = Object1()
 o2 = Object2()

 ## Existing window
 import Tkinter
 t = Tkinter.Toplevel()

 ## Flexible GUI representation: display o1.duration, o1.displacement,
 ## and o2.active_today inside t, ignoring o2.operator_name
 from topo.param.tk import TkParameterized

 t1 = TkParameterized(t,o1)
 t2 = TkParameterized(t,o2)

 t1.pack_param('duration',side='left')
 t1.pack_param('displacement',side='bottom')
 t2.pack_param('active_today',side='right')


(4) ?

TkParameterized is itself a subclass of Parameterized, so a
TkParameterized class can have its own parameters (in addition to
representing those of an external parameterized instance or class).

  ## Existing class
  from topo import params
  
  class X(param.Parameterized):
      one = param.Boolean(True)
      two = param.Boolean(True)
  
                                                      
  ## Panel to represent an instance of X 
  from Tkinter import Frame
  from topo.param.tk import TkParameterized

  class XPanel(TkParameterized,Frame):
  
      dock = param.Boolean(False,doc='Whether to attach this Panel')
      
      def __init__(self,master,x):
          self.pack_param('dock',side='top',on_set=self.handle_dock)
          self.pack_param('one',side='left')
          self.pack_param('two',side='right')

      def handle_dock(self):
          if self.dock:
              # dock the window
          else:
              # undock the window        
  

  ## Running the code
  t = Tkinter.Toplevel()
  x = X()
  XPanel(t,x)


$Id$
"""

# CEBALERT: moving todo
# (1) move icons from topo/tkgui.
# (2) update documentation


# CB: This file is too long because the param/gui interface code has
# become too long, and needs cleaning up.  I'm still working on it
# (still have to attend to simple ALERTs and do a one-pass cleanup)

# It's quite likely that the way TkParameterizedBase is implemented
# could be simplified. Right now, it still contains leftovers of
# various attempts to get everything working. But it does seem to
# work!


## import logging
## import string,time
## log_name= 'guilog_%s'%string.join([str(i) for i in list(time.gmtime())],"")

## logging.basicConfig(level=logging.DEBUG,
##                     format='%(asctime)s %(levelname)s %(message)s',
##                     filename='topo/tkgui/%s'%log_name,
##                     filemode='w')
## from os import popen
## version = popen('svnversion -n').read()
## logging.info("tkgui logging started for %s"%version)

import __main__
import copy
import decimal
import os.path
import ImageTk, Image, ImageOps
import Tkinter as T


from inspect import getdoc

from tkMessageBox import _show,QUESTION,YESNO

import param.parameterized
from param.parameterized import Parameterized,ParameterizedMetaclass,\
     classlist

import param

from external import Combobox,OrderedDict,Progressbar

from param import Boolean,String,Number,Selector,ClassSelector,\
     ObjectSelector,Callable,Dynamic,Parameter,List,HookList,\
     Filename,resolve_path


# (part of an existing ALERT - search this file)
_last_one_set = None


# CEBALERT: Tkinter.BooleanVar.get() doesn't support None. This is a
# hack because there's no way in the GUI to visually distinguish a
# "None" from a "False".
def _BooleanVar_get(instance):
    try:
        return instance._tk.getboolean(instance._tk.globalgetvar(instance._name)) # i.e. BooleanVar.get()
    except T.TclError:
        return instance._tk.globalgetvar(instance._name) # i.e. Variable.get()


root = None
def initialize():
    """
    Add extension Tcl/Tk code to the Tk instance at
    Tkinter._default_root (creating the Tk instance first if
    necessary).
    """
    global root

    if root is not None:
        print "param.tk already initialized; ignoring call to param.tk.initialize()"
        return

    if T._default_root is not None:
        root = T._default_root
    else:
        root = T.Tk()
        root.withdraw()

    # Until tklib, tcllib, and scrodget become more commonly
    # available, we include them in tkgui.
    externaltcl_path = os.path.join(os.path.split(__file__)[0],"tcl")
    root.tk.call("lappend","auto_path",externaltcl_path)

    T.BooleanVar.get = _BooleanVar_get



def inverse(dict_):
    """
    Return the inverse of dictionary dict_.
    
    (I.e. return a dictionary with keys that are the values of dict_,
    and values that are the corresponding keys from dict_.)

    The values of dict_ must be unique.
    """
    idict = dict([(value,key) for key,value in dict_.iteritems()])
    if len(idict)!=len(dict_):
        raise ValueError("Dictionary has no inverse (values not unique).")
    return idict


def lookup_by_class(dict_,class_):
    """
    Look for class_ or its superclasses in the keys of dict_; on
    finding a match, return the value (return None if no match found).

    Searches from the most immediate class to the most distant
    (i.e. from class_ to the final superclass of class_).
    """
    v = None
    for c in classlist(class_)[::-1]:
        if c in dict_:
            v = dict_[c] 
            break
    return v


def keys_sorted_by_value(d):
    """
    Return the keys of dictionary d sorted by value.
    """
    # By Daniel Schult, 2004/01/23
    # http://aspn.activestate.com/ASPN/Python/Cookbook/Recipe/52306
    items=d.items()
    backitems=[ [v[1],v[0]] for v in items]
    backitems.sort()
    return [ backitems[i][1] for i in range(0,len(backitems))]


def keys_sorted_by_value_unique(d, **sort_kwargs):
    """
    Return the keys of d, sorted by value.

    The values of d must be unique (see inverse)
    """
    values = d.values()
    values.sort(**sort_kwargs)
    i = inverse(d)
    return [i[val] for val in values]


def keys_sorted_by_value_unique_None_safe(d, **sort_kwargs):
    """
    None is handled separately: if present, it always comes out at the
    end of the list. Allows callers to use any sort function without
    worrying that None will not match the other objects (e.g. for
    using an attribute present on all the other objects, such as
    precedence of sheets).
    """
    if 'None' in d:
        assert d['None'] is None
        None_in_d = True
    else:
        None_in_d = False
        
    if None_in_d:
        del d['None']
        
    sorted_keys = keys_sorted_by_value_unique(d,**sort_kwargs)

    if None_in_d:
        d['None']=None
        sorted_keys.append('None')
        
    return sorted_keys


def is_button(widget):
    """
    Simple detection of Button-like widgets that are not Checkbuttons
    (i.e. widgets that do not require a separate label).
    """
    # CEBALERT: document why try/except is needed
    try:
        button = 'command' in widget.config() and not hasattr(widget,'toggle')
    except T.TclError:
        button = False
    return button


#################################################################
# Very basic wrapper for scrodget
class ScrodgetWidget:
    def _require(self, master):
        master.tk.call("package", "require", "scrodget") 

    def __init__(self, master, cnf={}, **kw):
        self._require(master)
        T.Widget.__init__(self, master, 'scrodget', cnf, kw)


class Scrodget(ScrodgetWidget, T.Widget):
    def associate(self,widget=None,*args):
        return self.tk.call(self._w,"associate",widget)
#################################################################



# CEB: workaround for tkinter lagging behind tk (tk must have changed
# the type of a returned value).  This is copied almost exactly from
# tkMessageBox. If there are other things like this, we could have the
# gui load some 'dynamic patches' to tkinter on startup, which could
# then be removed when tkinter is updated (they'd all be in one place,
# and no tkgui code would have to change).
def askyesno(title=None, message=None, **options):
    "Ask a question; return true if the answer is yes"
    s = _show(title, message, QUESTION, YESNO, **options)
    return str(s) == "yes"



# Buttons are not naturally represented by parameters?
#
# Maybe we should have a parent class that implements the
# non-Parameter specific stuff, then one that bolts on the
# Parameter-specific stuff, and then instead of Button we'd
# have TopoButton, or something like that...
class Button(Callable):
    """
    A GUI-specific parameter to display a button.

    Can be associated with an image by specifying an image_path
    (i.e. location of an image suitable for PIL, e.g. a PNG, TIFF, or
    JPEG image) and optionally a size (width,height) tuple.

    Note that the button size can also be set when there is no image,
    but instead of being presumed to be in pixels, it is presumed to
    be in text units (a Tkinter feature: see
    e.g. http://effbot.org/tkinterbook/button.htm). Therefore, to
    place two identically sized buttons next to each other, with one
    displaying text and the other an image, you first have to convert
    one of the sizes to the other's units.
    """
    # CEBALERT: we should probably solve the above for users,
    # but what a pain!
    __slots__ = ['image_path','size','_hack']

    def __init__(self,default=None,image_path=None,size=None,**params):
        Callable.__init__(self,default=default,**params)
        self.image_path = image_path
        self.size = size
        self._hack = []

# CB: would create the photoimage on construction and store it as an
# attribute, except that it gives "RuntimeError: Too early to create
# image". Must be happening before tk starts, or something. So
# instead, return image on demand. Also, because of PIL bug (see
# topoconsole.py "got to keep references to the images") we store
# a reference to the image each time in _hack.
    def get_image(self):
        """
        Return an ImageTk.PhotoImage of the image at image_path
        (or None if image_path is None or an Image cannot be created).
        """
        image = None
        if self.image_path:
            image=ImageTk.PhotoImage(ImageOps.fit(
                Image.open(resolve_path(self.image_path)),self.size or (32,32)))
            self._hack.append(image)

        return image



            
# Note that TkParameterized extends TkParameterizedBase by adding
# widget-drawing abilities; documentation for using these classes
# begins at a more useful and simple level in TkParameterized (the
# documentation for TkParameterizedBase is more complex).
class TkParameterizedBase(Parameterized):
    """
    A Parameterized subclass that maintains Tkinter.Variable shadows
    (proxies) of its Parameters. The Tkinter Variable shadows are kept
    in sync with the Parameter values, and vice versa.

    Optionally performs the same for an *additional* shadowed
    Parameterized (extraPO). The Parameters of the extra
    shadowed PO are available via this object (via both the usual
    'dot' attribute access and dedicated parameter accessors
    declared in this class). 

    The Tkinter.Variable shadows for this Parameterized and any
    extra shadowed one are available under their corresponding
    parameter names in the _tkvars dictionary.

    (See note 1 for complications arising from name clashes.)


    Parameters being represented by TkParameterizedBase also
    have a 'translators' dictionary, allowing mapping between string
    representations of the objects and the objects themselves (for use
    with e.g. a Tkinter.OptionMenu). More information about the
    translators is available from specific translator-related methods
    in this class.


    Notes
    =====
    
    (1) (a) There is an order of precedance for parameter lookup:
        this PO > shadowed PO.

        Therefore, if you create a Parameter for this PO
        with the same name as one of the shadowed PO's Parameters, only
        the Parameter on this PO will be shadowed.

        Example: 'name' is a common attribute. As a
        Parameterized, this object has a 'name' Parameter. Any
        shadowed PO will also have a 'name' Parameter. By default,
        this object's name will be shadowed at the expense of the name
        of the extra shadowed PO.

        The precedence order can be reversed by setting the attribute
        'self_first' on this object to False.


        (b) Along the same lines, an additional complication can arise
        relating specifically to 'dot' attribute lookup.  For
        instance, a sublass of TkParameterized might also
        inherit from Tkinter.Frame. Frame has many of its own
        attributes, including - for example - 'size'. If we shadow a
        Parameterized that has a 'size' Parameter, the
        Parameterized's size Parameter will not be available as
        .size because ('dot') attribute lookup begins on the local
        object and is not overridden by 'self_first'. Using the
        parameter accessors .get_parameter_object('size') or
        .get_parameter_value('size') (and the equivalent set versions)
        avoids this problem.
        


    (2) If a shadowed PO's Parameter value is modified elsewhere, the
        Tkinter Variable shadow is NOT updated until that Parameter value
        or shadow value is requested from this object. Thus requesting the
        value will always return an up-to-date result, but any GUI display
        of the Variable might display a stale value (until a GUI refresh
        takes place).
    """

    # CEBNOTE: avoid (as far as possible) defining Parameters for this
    # object because they might clash with Parameters of objects it
    # eventually represents.


    # CEBNOTE: Regarding note 1a above...it would be possible - with
    # some extra work - to shadow Parameters that are duplicated on
    # this PO and extraPO. Among other changes, things like the
    # _tkvars dict would need different (e.g. name on this PO and
    # name on extraPO)

    # CEBNOTE: Regarding note 1b...might be less confusing if we stop
    # parameters of shadowed POs being available as attributes (and
    # use only the parameter access methods instead). But having them
    # available as attributes is really convenient.

    # CEBNOTE: Regarding note 2 above...if it becomes a problem, we
    # could have some autorefresh of the vars or a callback of some
    # kind in the parameterized object itself. E.g a
    # refresh-the-widgets-on-focus-in method could make the gui in
    # sync with the actual object (so changes outside the gui could
    # show up when a frame takes focus). Or there could be timer
    # process.

    # CEB: because of note 1, attributes of this class should have
    # names that are unlikely to clash (or they should be private);
    # this will make it easier for creators and users of subclasses to
    # avoid name clashes.

    # must exist *before* an instance is init'd
    # (for __getattribute__)
    _extraPO = None

    # CEBALERT: Parameterized repr method leads to recursion error.
    def __repr__(self): return object.__repr__(self)    


    def _setup_params(self,**params):
        """
        Parameters that are not in this object itself but are in the
        extraPO get set on extraPO. Then calls Parameterized's
        _setup_params().
        """
        ### a parameter might be passed in for one of the extra_pos;
        ### if a key in the params dict is not a *parameter* of this
        ### PO, then try it on the extra_pos
        for n,p in params.items():
            if n not in self.params():
                self.set_parameter_value(n,p)
                del params[n]

        Parameterized._setup_params(self,**params)

    # CEBALERT: rename extraPO...but to what?
    # Rename change_PO() and anything else related.
    def __init__(self,extraPO=None,self_first=True,live_update=True,**params):
        """


        Translation between displayed values and objects
        ------------------------------------------------

        A Parameter has a value, but that might need some processing
        to become a value suitable for display. For instance, the
        SheetMask() object <SheetMask SheetMask0001923> ...



        Important attributes
        --------------------

        * _extraPO
        

        * self_first
        Determines precedence order for Parameter lookup:
        if True, Parameters of this object take priority whenever
        there is a name clash; if False, Parameters of extraPO take
        priority.


        

        * obj2str_fn & str2obj_fn

        * translator_creators

        (Note that in the various dictionaries above, the entry for
        Parameter serves as a default, since keys are looked up by
        class, so any Parameter type not specifically listed will be
        covered by the Parameter entry.)



        * _tkvars

        
        """
        if not (extraPO is None or isinstance(extraPO,ParameterizedMetaclass) \
                or isinstance(extraPO,Parameterized)):
            raise TypeError("%s is not a Parameterized instance or class."%extraPO)

        # make self.first etc private

        self._live_update = live_update
        self.self_first = self_first

        ## Which Tkinter Variable to use for each Parameter type
        # (Note that, for instance, we don't include Number:DoubleVar.
        # This is because we use Number to control the type, so we
        # don't need restrictions from DoubleVar.)
        self._param_to_tkvar = {Boolean:T.BooleanVar,
                                Parameter:T.StringVar}

        # CEBALERT: Parameter is the base parameter class, but ... 
        # at least need a test that will fail when a new param type added
        # Rename
        self.trans={Parameter:Eval_ReprTranslator,
                    Dynamic:Eval_ReprTranslator,
                    ObjectSelector:String_ObjectTranslator,
                    ClassSelector:CSPTranslator,
                    Number:Eval_ReprTranslator,
                    Boolean:BoolTranslator,
                    String:DoNothingTranslator,
                    List:ListTranslator,
                    HookList:ListTranslator} # CBALERT: sort out inherit.
        
        self.change_PO(extraPO)
        super(TkParameterizedBase,self).__init__(**params)


    def change_PO(self,extraPO):
        """
        Shadow the Parameters of extraPO.
        """
        self._extraPO = extraPO
        self._tkvars = {}
        self.translators = {}

        # (reverse list to respect precedence)
        for PO in self._source_POs()[::-1]:
            self._init_tkvars(PO)


    def _init_tkvars(self,PO):
        """
        Create Tkinter Variable shadows of all Parameters of PO.        
        """
        for name,param in PO.params().items():
            self._create_tkvar(PO,name,param)
            

    def _create_tkvar(self,PO,name,param_obj):
        """
        Add _tkvars[name] to represent the parameter object with the specified name.
        
        The appropriate Variable is used for each Parameter type.

        Also adds tracing mechanism to keep the Variable and Parameter
        values in sync, and updates the translator dictionary to map
        string representations to the objects themselves.
        """
        # CEBALERT: should probably delete any existing tkvar for name
        self._create_translator(name,param_obj)

        tkvar = lookup_by_class(self._param_to_tkvar,type(param_obj))()
        self._tkvars[name] = tkvar

        # overwrite Variable's set() with one that will handle
        # transformations to string
        tkvar._original_set = tkvar.set
        tkvar.set = lambda v,x=name: self._tkvar_set(x,v)

        tkvar.set(self.get_parameter_value(name,PO))
        tkvar._last_good_val=tkvar.get() # for reverting
        tkvar.trace_variable('w',lambda a,b,c,p_name=name: self._handle_gui_set(p_name))
        # CB: Instead of a trace, could we override the Variable's
        # set() method i.e. trace it ourselves?  Or does too much
        # happen in tcl/tk for that to work?
        
        # Override the Variable's get() method to guarantee an
        # out-of-date value is never returned.  In cases where the
        # tkinter val is the most recently changed (i.e. when it's
        # edited in the gui, resulting in a trace_variable being
        # called), the _original_get() method is used.
        # CEBALERT: what about other users of the variable? Could they
        # be surprised by the result from get()?
        tkvar._original_get = tkvar.get
        tkvar.get = lambda x=name: self._tkvar_get(x)


################################################################################
# 
################################################################################

    def _handle_gui_set(self,p_name):
        """
        * The callback to use for all GUI variable traces/binds *
        """
        if self._live_update:
            self._update_param_from_tkvar(p_name)


    def _tkvar_set(self,param_name,val):
        """
        Set the tk variable to (the possibly transformed-to-string) val.
        """
        self.debug("_tkvar_set(%s,%s)"%(param_name,val))
        val = self._object2string(param_name,val)
        tkvar = self._tkvars[param_name]
        tkvar._original_set(val) # trace not called because we're already in trace,
                                  # and tk disables trace activation during trace

    
    # CB: separate into update and get?
    def _tkvar_get(self,param_name):
        """
        Return the value of the tk variable representing param_name.
        
        (Before returning the variable's value, ensures it's up to date.)
        """
        tk_val = self._tkvars[param_name]._original_get() 
        po_val = self.get_parameter_value(param_name)

        po_stringrep = self._object2string(param_name,po_val)

        if not self.translators[param_name].last_string2object_failed and not tk_val==po_stringrep:
            self._tkvars[param_name]._original_set(po_stringrep)
        return tk_val         

        
    def _tkvar_changed(self,name):
        """
        Return True if the displayed value does not equal the object's
        value (and False otherwise).
        """
        self.debug("_tkvar_changed(%s)"%name)
        displayed_value = self._string2object(name,self._tkvars[name]._original_get())
        object_value = self.get_parameter_value(name) #getattr(self._extraPO,name)

        # use equality check then identity check because e.g.  val
        # starts at 0.5, type 0.8, then type 0.5, need that to be
        # changed is False, but some types cannot be equality compared
        # (can be identity compared).
        # CEBALERT: need to add a unit test to ensure this keeps working.
        # Plus, I need to think about this, because while the above is
        # true for floats, identity tests make more sense for many types
        # (i.e. you want to know the object is the same).
        try:
            if displayed_value != object_value:
                changed = True
            else:
                changed = False
        except:
            if displayed_value is not object_value:
                changed = True
            else:
                changed = False

        self.debug("..._v_c return %s"%changed)
        return changed


    def _update_param_from_tkvar(self,param_name):
        """
        Attempt to set the parameter represented by param_name to the
        value of its corresponding Tkinter Variable.

        If setting the parameter fails (e.g. an inappropriate value
        is set for that Parameter type), the Variable is reverted to
        its previous value.

        (Called by the Tkinter Variable's trace_variable() method.)
        """
        self.debug("TkPOb._update_param_from_tkvar(%s)"%param_name)
        
        parameter,sourcePO=self.get_parameter_object(param_name,with_source=True)

        ### can only edit constant parameters for class objects
        if parameter.constant is True and not isinstance(sourcePO,type):
            return  ### HIDDEN

        tkvar = self._tkvars[param_name]
        
        if self._tkvar_changed(param_name):
            # don't attempt to set if there was a string-to-object translation error
            if self.translators[param_name].last_string2object_failed:
                return   ### HIDDEN 

            # (use _original_get() because we don't want the tkvar to be reset to
            # the parameter's current value!)
            val = self._string2object(param_name,tkvar._original_get())

            try: 
                self._set_parameter(param_name,val)
            except: # everything
                tkvar.set(tkvar._last_good_val)
                raise # whatever the parameter-setting error was

            self.debug("set %s to %s"%(param_name,val))
                
            if hasattr(tkvar,'_on_modify'):
                tkvar._on_modify()

        ### call any function associated with GUI set()
        if hasattr(tkvar,'_on_set'):

            # CEBALERT: provide a way of allowing other gui components
            # to figure out where a callback error might have come
            # from. Callback instances (the Callback class is defined
            # in Tkinter.py) store a widget, but often it appears to
            # be the Tk instance - which is of no use in later
            # determining where an error might have originated.
            global _last_one_set
            if hasattr(self,'master'):
                _last_one_set = self.master

            tkvar._on_set()


################################################################################
# 
################################################################################



    def _source_POs(self):
        """
        Return a list of Parameterizeds in which to find
        Parameters.
        
        The list is ordered by precedence, as defined by self_first.
        """
        if not self._extraPO:
            sources = [self]
        elif self.self_first:
            sources = [self,self._extraPO]
        else:
            sources = [self._extraPO,self]
        return sources




    def get_source_po(self,name):
        """
        Return the Parameterized which contains the parameter 'name'.
        """
        sources = self._source_POs()

        for po in sources:
            if name in po.params():
                return po


        raise AttributeError(self._attr_err_msg(name,sources))

        
    def get_parameter_object(self,name,parameterized_object=None,with_source=False):
        """
        Return the Parameter *object* (not value) specified by name,
        from the source_POs in this object (or the
        specified parameterized_object).

        If with_source=True, returns also the source parameterizedobject.
        """
        source = parameterized_object or self.get_source_po(name)
        parameter_object = source.params()[name]

        if not with_source:
            return parameter_object
        else:
            return parameter_object,source



######################################################################
# Attribute lookup

##### these guarantee only to get/set parameters #####
    def get_parameter_value(self,name,parameterized_object=None):
        """
        Return the value of the parameter specified by name.

        If a parameterized_object is specified, looks for the parameter there.
        Otherwise, looks in the source_POs of this object.
        """
        source = parameterized_object or self.get_source_po(name)
        return source.get_value_generator(name) 

    # CEBALERT: shouldn't this use __set_parameter? Presumably doing
    # that kind of thing is part of the cleanup required in this file.
    def set_parameter_value(self,name,val,parameterized_object=None):
        """
        Set the value of the parameter specified by name to val.

        Updates the corresponding tkvar.
        """
        source = parameterized_object or self.get_source_po(name)
        object.__setattr__(source,name,val)

        # update the tkvar
        if name in self._tkvars:
            self._tkvars[name]._original_set(self._object2string(name,val))


######################################################

########## these lookup attributes in order ##########
# (i.e. you could get attribute of self rather than a parameter)
# (might remove these to save confusion: they are useful except when 
#  someone would be surprised to get an attribute of e.g. a Frame (like 'size') when
#  they were expecting to get one of their parameters. Also, means you can't set
#  an attribute a on self if a exists on one of the shadowed objects)
# (also they (have to) ignore self_first)
    
    def __getattribute__(self,name):
        """
        If the attribute is found on this object, return it. Otherwise,
        return the attribute from the extraPO, if it exists.
        If there is no match, raise an attribute error.
        """
        try:
            return object.__getattribute__(self,name)
        except AttributeError:
            extraPO = object.__getattribute__(self,'_extraPO')

            if hasattr(extraPO,name):
                return getattr(extraPO,name) # HIDDEN!

            _attr_err_msg = object.__getattribute__(self,'_attr_err_msg')
                
            raise AttributeError(_attr_err_msg(name,[self,extraPO]))
                    

    def __setattr__(self,name,val):
        """
        If the attribute already exists on this object, set it. If the attribute
        is found on the extraPO, set it there. Otherwise, set the
        attribute on this object (i.e. add a new attribute).
        """
        # use dir() not hasattr() because hasattr uses __getattribute__
        if name in dir(self):
            
            if name in self.params():
                self.set_parameter_value(name,val,self)
            else:
                object.__setattr__(self,name,val)
                
        elif name in dir(self._extraPO):

            if name in self._extraPO.params():
                self.set_parameter_value(name,val,self._extraPO)
            else:
                object.__setattr__(self._extraPO,name,val)

        else:

            # name not found, so set on this object
            object.__setattr__(self,name,val)   
#######################################################


######################################################################



    

######################################################################
# Translation between GUI (strings) and true values

    def _create_translator(self,name,param):
        self.debug("_create_translator(%s,%s)"%(name,param))
        
        translator_type = lookup_by_class(self.trans,type(param))

        # Dynamic parameters only *might* contain a 
        # dynamic value; if such a parameter really is dynamic, we
        # overwrite any more specific class found above
        # (e.g. a Number with a dynamic value will have a numeric
        # translator from above, so we replace that)
        if param_is_dynamically_generated(param,self.get_source_po(name)) or name in self.allow_dynamic:
            translator_type = self.trans[Dynamic]
            
        self.translators[name]=translator_type(param,initial_value=self.get_parameter_value(name))

        self.translators[name].msg_handler = self.msg_handler




    # CEBALERT: doc replace & rename to plastic or something
    def _object2string(self,param_name,obj,replace=True):
        """
        If val is one of the objects in param_name's translator,
        translate to the string.
        """
        self.debug("object2string(%s,%s)"%(param_name,obj))
        translator = self.translators[param_name]

        if not replace:
            translator=copy.copy(translator)
            
        return translator.object2string(obj)


    def _string2object(self,param_name,string):
        """
        Change the given string for the named parameter into an object.
        
        If there is a translator for param_name, translate the string
        to the object; otherwise, call convert_string2obj on the
        string.
        """
        self.debug("string2object(%s,%s)"%(param_name,string))
        translator = self.translators[param_name]
        o = translator.string2object(string)
        self.debug("...s2o return %s, type %s"%(o,type(o)))
        return o

######################################################################

    def _attr_err_msg(self,attr_name,objects):
        """
        Helper method: return the 'attr_name is not in objects' message.
        """
        if not hasattr(objects,'__len__'):objects=[objects]

        error_string = "'%s' not in %s"%(attr_name,objects.pop(0))

        for o in objects:
            error_string+=" or %s"%o
            
        return error_string


    def _set_parameter(self,param_name,val):
        """
        Helper method:
        """
        # use set_in_bounds if it exists
        # i.e. users of widgets get their values cropped
        # (no warnings/errors, so e.g. a string in a
        # tagged slider just goes to the default value)
        # CEBALERT: set_in_bounds not valid for POMetaclass?
        parameter,sourcePO=self.get_parameter_object(param_name,with_source=True)

        # CEBHACKALERT: GeneratorSheet.input_generator should be a
        # property? But it's a Parameter...
        # Setting input_generator rather than calling set_input_generator()
        # is probably a trap...
        if param_name=='input_generator' and hasattr(sourcePO,'set_input_generator'):
            sourcePO.set_input_generator(val)
        elif hasattr(parameter,'set_in_bounds') and isinstance(sourcePO,Parameterized):
            parameter.set_in_bounds(sourcePO,val)
        else:
            setattr(sourcePO,param_name,val)
                        









class TkParameterized(TkParameterizedBase):
    """
    Provide widgets for Parameters of itself and up to one additional
    Parameterized instance or class.

    A subclass that defines a Parameter p can display it appropriately
    for manipulation by the user simply by calling
    pack_param('p'). The GUI display and the actual Parameter value
    are automatically synchronized (though see technical notes in
    TkParameterizedBase's documentation for more details).

    In general, pack_param() adds a Tkinter.Frame containing a label
    and a widget: 

    ---------------------                     The Parameter's
    |                   |                     'representation'
    | [label]  [widget] |<----frame
    |                   |
    ---------------------

    In the same way, an instance of this class can be used to display
    the Parameters of an existing object. By passing in extraPO=x,
    where x is an existing Parameterized instance or class, a
    Parameter q of x can also be displayed in the GUI by calling
    pack_param('q').

    For representation in the GUI, Parameter values might need to be
    converted between their real values and strings used for display
    (e.g. for a ClassSelector, the options are really class objects,
    but the user is presented with a list of strings to choose
    from). Such translation is handled and documented in the
    TkParameterizedBase; the default behaviors can be overridden if
    required.

    (Note that this class simply adds widget drawing to
    TkParameterizedBase. More detail about the shadowing of
    Parameters is available in the documentation for
    TkParameterizedBase.)
    """

    # CEBNOTE: as for TkParameterizedBase, avoid declaring
    # Parameters here (to avoid name clashes with any additional
    # Parameters this might eventually be representing).

    pretty_parameters = Boolean(default=True,precedence=-1,
        doc="""Whether to format parameter names, or display the
        variable names instead.

        Example use:
          TkParameterized.pretty_parameters=False
    
        (This causes all Parameters throughout the GUI to be displayed
        with variable names.)
        """)


    def __init__(self,master,extraPO=None,self_first=True,
                 msg_handler=None,**params):
        """
        Initialize this object with the arguments and attributes
        described below:
        
        extraPO: optional Parameterized object for which to shadow
        Parameters (in addition to Parameters of this object; see
        superclass)

        self_first: if True, Parameters on this object take precedence
        over any ones with the same names in the extraPO (i.e. what
        to do if there are name clashes; see superclass)


        Important attributes
        ====================
        
        * param_immediately_apply_change

        Some types of Parameter are represented with widgets where
        a complete change can be instantaneous (e.g.  when
        selecting from an option list, the selection should be
        applied straightaway). Others are represented with widgets
        that do not finish their changes instantaneously
        (e.g. entry into a text box is not considered finished
        until Return is pressed).

        * widget_creators

        A dictionary of methods to create a widget for each Parameter
        type. For special widget options (specific to each particular
        parameter), see the corresponding method's docstring.

        * representations

        After pack_param() is called, a Parameter's representation
        consists of the tuple (frame,widget,label,pack_options) - the
        enclosing frame, the value-containing widget, the label
        holding the Parameter's name, and any options supplied for
        pack(). These can all be accessed through the representations
        dictionary, under the Parameter's name.
        """
        self.master = master
        self.msg_handler = msg_handler

        self.representations = {}

        # CEBALER: doc
        self.allow_dynamic = []

        self.param_immediately_apply_change = {Boolean:True,
                                               Selector:True,
                                               Number:False,
                                               Parameter:False,
                                               Filename:True}

        TkParameterizedBase.__init__(self,extraPO=extraPO,
                                     self_first=self_first,
                                     **params)

        self.balloon = Balloon(master)

        # CEBALERT: what about subclasses of Number (e.g. Integer,
        # which should get a slider that jumps between integers...
        # maybe that already happens)?
        self.widget_creators = {
            Boolean:self._create_boolean_widget,
            Dynamic:self._create_string_widget,
            Number:self._create_number_widget,
            Button:self._create_button_widget,
            String:self._create_string_widget,
            Selector:self._create_selector_widget,
            List:self._create_list_widget,
            HookList:self._create_list_widget,
            Filename:self._create_fileselector_widget,
            }
        
        self.representations = {}  
        

        # CEBNOTE: it would be nice to sort out menus properly
        # (i.e. parameterize them)
        self.popup_menu = Menu(master, tearoff=0)
        self.dynamic_var = T.BooleanVar()
        self.popup_menu.add("checkbutton",indexname="dynamic",
                            label="Enter dynamic value?",
                            state="disabled",command=self._switch_dynamic,
                            variable=self.dynamic_var)


        ### Right-click menu for widgets
        master.option_add("*Menu.tearOff", "0") 
        self.menu = Menu(master)
        self.menu.insert_command('end',label='Properties',
            command=lambda:self._edit_PO_in_currently_selected_widget())



    def _right_click(self, event, widget):
        """
        Popup the right-click menu.
        """
        self._currently_selected_widget = widget

        # need an actual mechanism for populating the menu, rather than this!!
        ### copied from edit_PO_in_currently...
        param_name = None
        for name,representation in self.representations.items():
            if self._currently_selected_widget is representation['widget']:
                param_name=name
                break
        # CEBALERT: should have used get_parameter_value(param_name)?
        PO_to_edit = self._string2object(param_name,self._tkvars[param_name].get()) 
        ###
        
        if hasattr(PO_to_edit,'params'):
            self.menu.tk_popup(event.x_root, event.y_root)


    # CEBALERT: rename
    def _edit_PO_in_currently_selected_widget(self):
        """
        Open a new window containing a ParametersFrame (actually, a
        type(self)) for the PO in _currently_selected_widget.
        """
        # CEBALERT: simplify this lookup by value
        param_name = None
        for name,representation in self.representations.items():
            if self._currently_selected_widget is representation['widget']:
                param_name=name
                break

        # CEBALERT: should have used get_parameter_value(param_name)?
        PO_to_edit = self._string2object(param_name,self._tkvars[param_name].get()) 

        parameter_window = AppWindow(self)
        parameter_window.title(PO_to_edit.name+' parameters')

        ### CEBALERT: confusing? ###
        title=T.Label(parameter_window, text="("+param_name + " of " + (self._extraPO.name or 'class '+self._extraPO.__name__) + ")")
        title.pack(side = "top")
        self.balloon.bind(title,getdoc(self.get_parameter_object(param_name)))
        ############################

        # uh-oh 
        if not isinstance(self,ParametersFrame):
            p_type = ParametersFrameWithApply
            parameter_frame = p_type(parameter_window,parameterized_object=PO_to_edit,msg_handler=self.msg_handler)

        else:
            p_type = type(self)
            parameter_frame = p_type(parameter_window,parameterized_object=PO_to_edit,msg_handler=self.msg_handler,on_set=self.on_set,on_modify=self.on_modify)

        parameter_frame.pack()



    def _update_dynamic_menu_entry(self,param_name):
        """Keep track of status of dynamic entry."""
        param,po = self.get_parameter_object(param_name,with_source=True)
        currently_dynamic = param_is_dynamically_generated(param,po)
        if hasattr(param,'_value_is_dynamic') and not currently_dynamic:
            self._right_click_param = param_name
            state = "normal"
        else:
            self._right_click_param = None
            state = "disabled"
        self.popup_menu.entryconfig("dynamic",state=state)
        self.dynamic_var.set(currently_dynamic or \
                             param_name in self.allow_dynamic) 
        

    def _param_right_click(self,event,param_name):
        """Display a popup menu when user right clicks on a parameter."""
        self._update_dynamic_menu_entry(param_name)
        self.popup_menu.tk_popup(event.x_root,event.y_root)



################################################################################
# 
################################################################################
 
    def _update_param_from_tkvar(self,param_name,force=False):
        """
        Prevents the superclass's _update_param_from_tkvar() method from being
        called unless:
        
        * param_name is a Parameter type that has changes immediately
          applied (see doc for param_immediately_apply_change
          dictionary);

        * force is True.

        (I.e. to update a parameter for which
        param_immediately_apply_change[type(parameter)]==False, call
        this method with force=True. E.g. when <Return> is pressed in
        a text box, this method is called with force=True.)
        """
        self.debug("TkPO._update_param_from_tkvar(%s)"%param_name)
        
        param_obj = self.get_parameter_object(param_name)
        
        if not lookup_by_class(self.param_immediately_apply_change,
                               type(param_obj)) and not force:
            return
        else:
            super(TkParameterized,self)._update_param_from_tkvar(param_name)


    def _handle_gui_set(self,p_name,force=False):
        """Override the superclass's method to X and allow status indications."""
        #logging.info("%s._handle_gui_set(%s,force=%s)"%(self,p_name,force))
        if self._live_update:
            self._update_param_from_tkvar(p_name,force)

        self._indicate_tkvar_status(p_name)



    #### Simulate GUI actions
    def gui_set_param(self,param_name,val):
        """Simulate setting the parameter in the GUI."""
        self._tkvar_set(param_name,val)  # ERROR: presumably calls trace stuff twice
        self._handle_gui_set(param_name,force=True)

    def gui_get_param(self,param_name):
        """Simulate getting the parameter in the GUI."""
        return self._tkvars[param_name].get()
    ####


################################################################################
# End 
################################################################################





################################################################################
#
################################################################################

    # some refactoring required: should be a base method that's to do
    # with adding a representation for a parameter. then this stuff
    # would go in it.
    def _post_add_param(self,param_name):
        l = self.representations[param_name]['label']
        if l is not None:
            l.bind('<<right-click>>',lambda event: \
                   self._param_right_click(event,param_name))


    def pack_param(self,name,parent=None,widget_options={},
                   on_set=None,on_modify=None,**pack_options):
        """
        Create a widget for the Parameter name, configured according
        to widget_options, and pack()ed according to the pack_options.

        Pop-up help is automatically set from the Parameter's doc.

        The widget and label (if appropriate) are enlosed in a Frame
        so they can be manipulated as a single unit (see the class
        docstring). The representation
        (frame,widget,label,pack_options) is returned (as well as
        being stored in the representations dictionary).


        * parent is an existing widget that is to be the parent
        (master) of the widget created for this paramter. If no parent
        is specified, defaults to the originally supplied master
        (i.e. that set during __init__).

        * on_set is an optional function to call whenever the
        Parameter's corresponding Tkinter Variable's trace_variable
        indicates that it has been set (this does not necessarily mean
        that the widget's value has changed). When the widget is created,
        the on_set method will be called (because the creation of the
        widget triggers a set in Tkinter).

        * on_modify is an optional function to call whenever the
        corresponding Tkinter Variable is actually changed.
        

        widget_options specified here override anything that might have been
        set elsewhere (e.g. Button's size can be overridden here
        if required).


        
        Examples of use:
        pack_param(name)
        pack_param(name,side='left')
        pack_param(name,parent=frame3,on_set=some_func)
        pack_param(name,widget_options={'width':50},side='top',expand='yes',fill='y')
        """
        frame = T.Frame(parent or self.master)

        widget,label = self._create_widget(name,frame,widget_options,on_set,on_modify)

        # checkbuttons are 'widget label' rather than 'label widget'
        if widget.__class__ is T.Checkbutton:  # type(widget) doesn't seem to work
            widget_side='left'; label_side='right'
        else:
            label_side='left'; widget_side='right'
            
        if label: label.pack(side=label_side) # label can be None (e.g. for Button)
        widget.pack(side=widget_side,expand='yes',fill='x')

        representation = {"frame":frame,"widget":widget,
                          "label":label,"pack_options":pack_options,
                          "on_set":on_set,"on_modify":on_modify,
                          "widget_options":widget_options}                       
        self.representations[name] = representation

        # If there's a label, balloon's bound to it - otherwise, bound
        # to enclosing frame.
        # (E.g. when there's [label] [text_box], only want balloon for
        # label (because maybe more help will be present for what's in
        # the box) but when there's [button], want popup help over the
        # button.)
        param_obj = self.get_parameter_object(name)
        help_text = getdoc(param_obj)

        if param_obj.default is not None:
            # some params appear to have no docs!!!
            if help_text is not None:
                help_text+="\n\nDefault: %s"%self._object2string(name,param_obj.default,replace=False)
        
        self.balloon.bind(label or frame,help_text)
        
        frame.pack(pack_options)

        self._indicate_tkvar_status(name)

        self._post_add_param(name)
        return representation


    def hide_param(self,name):
        """Hide the representation of Parameter 'name'."""
        if name in self.representations:
            self.representations[name]['frame'].pack_forget()
        # CEBNOTE: forgetting label and widget rather than frame would
        # just hide while still occupying space (i.e. the empty frame
        # stays in place, and so widgets could later be inserted at
        # exact same place)
        #self.representations[name]['label'].pack_forget()
        #self.representations[name]['widget'].pack_forget()
        # unhide_param would need modifying too
        

    def unhide_param(self,name,new_pack_options={}):
        """
        Un-hide the representation of Parameter 'name'.

        Any new pack options supplied overwrite the originally
        supplied ones, but the parent of the widget remains the same.
        """
        # CEBNOTE: new_pack_options not really tested. Are they useful anyway?
        if name in self.representations:
            pack_options = self.representations[name]['pack_options']
            pack_options.update(new_pack_options)
            self.representations[name]['frame'].pack(pack_options)


    def unpack_param(self,name):
        """
        Destroy the representation of Parameter 'name'.

        (unpack and then pack a param if you want to put it in a different
        frame; otherwise simply use hide and unhide)
        """
        f = self.representations[name]['frame']
        w = self.representations[name]['widget']
        l = self.representations[name]['label']

        del self.representations[name]

        for x in [f,w,l]:
            x.destroy()


    def repack_param(self,name):

        f = self.representations[name]['frame']
        w = self.representations[name]['widget']
        l = self.representations[name]['label']
        o = self.representations[name]['pack_options']
        on_set = self.representations[name]['on_set']
        on_modify = self.representations[name]['on_modify']
        
        w.destroy(); l.destroy()        

        param_obj,PO = self.get_parameter_object(name,with_source=True)
        self._create_tkvar(PO,name,param_obj)
        
        self.pack_param(name,f,on_set=on_set,on_modify=on_modify,**o)


    def _switch_dynamic(self,name=None,dynamic=False):

        param_name = name or self._right_click_param
        param,po = self.get_parameter_object(param_name,with_source=True)
        if not hasattr(param,'_value_is_dynamic'):
            return
        
        if param_name in self.allow_dynamic:
            self.allow_dynamic.remove(param_name)
        else:
            self.allow_dynamic.append(param_name)

        self.repack_param(param_name)





################################################################################
#
################################################################################





################################################################################
# WIDGET CREATION
################################################################################

    def _create_widget(self,name,master,widget_options={},on_set=None,on_modify=None):
        """
        Return widget,label for parameter 'name', each having the master supplied

        The appropriate widget creation method is found from the
        widget_creators dictionary; see individual widget creation
        methods for details to each type of widget.
        """
        # select the appropriate widget-creation method;
        # default is self._create_string_widget... 
        widget_creation_fn = self._create_string_widget

        param_obj,source_po = self.get_parameter_object(name,with_source=True)

        if not (param_is_dynamically_generated(param_obj,source_po) or name in self.allow_dynamic):
            # ...but overwrite that with a more specific one, if possible
            for c in classlist(type(param_obj))[::-1]:
                if self.widget_creators.has_key(c):
                    widget_creation_fn = self.widget_creators[c]
                    break
        elif name not in self.allow_dynamic:
            self.allow_dynamic.append(name)

        if on_set is not None:
            self._tkvars[name]._on_set=on_set

        if on_modify is not None:
            self._tkvars[name]._on_modify=on_modify

        widget=widget_creation_fn(master,name,widget_options)

        # Is widget a button (but not a checkbutton)? If so, no label wanted.
        # CEBALERT 'notNonelabel': change to have a label with no text
        if is_button(widget): 
            label = None
        else:
            label = T.Label(master,text=self._pretty_print(name))

        # disable widgets for constant params
        if param_obj.constant and isinstance(source_po,Parameterized):
            # (need to be able to set on class, hence check it's PO not POMetaclass
            widget.config(state='disabled')
        
        widget.bind('<<right-click>>',lambda event: self._right_click(event, widget))

        return widget,label

        
    def _create_button_widget(self,frame,name,widget_options):
        """
        Return a FocusTakingButton to represent Parameter 'name'.

        Buttons require a command, which should have been specified as the
        'on_set' function passed to pack_param().

        After creating a button for a Parameter param, self.param() also
        executes the button's command.

        If the Button was declared with an image, the button will
        have that image (and no text); otherwise, the button will display
        the (possibly pretty_print()ed) name of the Parameter.        
        """
        try:
            command = self._tkvars[name]._on_set
        except AttributeError:
            raise TypeError("No command given for '%s' button."%name)

        del self._tkvars[name]._on_set # because we use Button's command instead

        # Calling the parameter (e.g. self.Apply()) is like pressing the button:
        self.__dict__["_%s_param_value"%name]=command
        # like setattr(self,name,command) but without tracing etc

        # (...CEBNOTE: and so you can't edit a tkparameterizedobject
        # w/buttons with another tkparameterizedobject because the
        # button parameters all skip translation etc. Instead should
        # handle their translation. But we're not offering a GUI
        # builder so it doesn't matter.)

        button = FocusTakingButton(frame,command=command)

        button_param = self.get_parameter_object(name)

        image = button_param.get_image()
        if image:
            button['image']=image
            #button['relief']='flat'
        else:
            button['text']=self._pretty_print(name)
            

        # and set size from Button
        #if size_param.size:
        #    button['width']=size[0]
        #    button['height']=size[1]

        button.config(**widget_options) # widget_options override things from parameter
        return button


    def _create_fileselector_widget(self,frame,name,widget_options):
        widget = HackFileEntry(frame,self._tkvars[name])
        return widget


    def update_selector(self,name):

        if name in self.representations:
            widget_options = self.representations[name]["widget_options"]

            new_range,widget_options = self._X(name,widget_options)

            w = self.representations[name]['widget']
            # hACK: tuple to work around strange list parsing tkinter/tcl
            w.configure(values=tuple(new_range)) # what a mess
            #w.configure(state='readonly') # CEBALERT: why necessary?
            # does it get changed somewhere else by mistake? e.g. does
            # plotgrouppanel switch disabled to normal and normal to
            # disabled without checking that normal isn't readonly?


    def _X(self,name,widget_options):

        # CEBALERT: need to document how & why people should use 'sort_fn_args'
        # and 'new_default' when calling pack_param(). Also, simplify it if
        # possible.
        self.translators[name].update()
        
        new_range = self.translators[name].cache.keys()

        if 'sort_fn_args' not in widget_options:
            # no sort specified: defaults to sort()
            new_range.sort()
        else:
            sort_fn_args = widget_options['sort_fn_args']
            del widget_options['sort_fn_args']
            if sort_fn_args is not None:
                new_range = keys_sorted_by_value_unique_None_safe(self.translators[name].cache,**sort_fn_args)

        assert len(new_range)>0 # CB: remove    

        tkvar = self._tkvars[name]
        

        if 'new_default' in widget_options:
            if widget_options['new_default']:
                current_value = new_range[0]
            del widget_options['new_default']
        else:
            current_value = self._object2string(name,self.get_parameter_value(name))
            if current_value not in new_range:
                current_value = new_range[0] # whatever was there is out of date now

        tkvar.set(current_value)
        return new_range,widget_options
        

    def _create_selector_widget(self,frame,name,widget_options):
        """
        Return a Tkinter.OptionMenu to represent Parameter 'name'.

        In addition to Tkinter.OptionMenu's usual options, the
        following additional ones may be included in widget_options:

        * sort_fn_args: if widget_options includes 'sort_fn_args',
          these are passed to the sort() method of the list of
          *objects* available for the parameter, and the names are
          displayed sorted in that order.  If 'sort_fn_args' is not
          present, the default is to sort the list of names using its
          sort() method.

        * new_default: if widget_options includes 'new_default':True,
          the currently selected value for the widget will be set
          to the first item in the (possibly sorted as above) range.
          Otherwise, the currently selected value will be left as the
          current value.
        """
        #param = self.get_parameter_object(name)
        #self._update_translator(name,param)

        ## sort the range for display
        # CEBALERT: extend OptionMenu so that it
        # (a) supports changing its option list (subject of a previous ALERT)
        # (b) supports sorting of its option list
        # (c) supports selecting a new default
        new_range,widget_options = self._X(name,widget_options)
        tkvar = self._tkvars[name]

        # Combobox looks bad with standard theme on my ubuntu
        # (and 'changed' marker - blue text - not visible).
        w = Combobox(frame,textvariable=tkvar,
                     values=new_range,state='readonly',
                     **widget_options)

        # Combobox (along with Checkbutton?) somehow sets its
        # associated textvariable without calling that textvariable's
        # set() method.  Therefore, to update the Selector's help text
        # when an item is selected, we bind to the
        # <<ComboboxSelected>> event.
        def _combobox_updated(event,name=name):
            w = self.representations[name]['widget']
            help_text =  getdoc(
                self._string2object(
                    name,
                    self._tkvars[name]._original_get()))

            self.balloon.bind(w,help_text)

        w.bind("<<ComboboxSelected>>",_combobox_updated)

        help_text = getdoc(self._string2object(name,tkvar._original_get()))
        self.balloon.bind(w,help_text)
        return w

    def _list_edit(self,param_name):
        val = self.get_parameter_value(param_name)

        param_obj = self.get_parameter_object(param_name)
        class_=None
        if hasattr(param_obj,'class_') and hasattr(param_obj.class_,'get_range'):
            # i.e. we can represent with ClassSelector
            class_ = param_obj.class_

        parameterized_instance = list_to_parameterized(val,class_)

        parameter_window = AppWindow(self)
        #parameter_window.title(PO_to_edit.name+' parameters')

        parameter_frame = EditingParametersFrameWithApply(parameter_window,parameterized_object=parameterized_instance,show_labels=False,on_close=lambda:self._handle_gui_set(param_name))

        # CEBALERT: more dynamic class changes to make it impossible
        # to follow what is happening...ParametersFrame needs some
        # reorganization...
        def _forgotten_why(itself):
            ### refresh()
            po_val = self.get_parameter_value(param_name)
            po_stringrep = self._object2string(param_name,po_val)
            self._tkvars[param_name]._original_set(po_stringrep)
            ###

        if _forgotten_why not in parameter_frame._apply_hooks:
            parameter_frame._apply_hooks.append(_forgotten_why)


        parameter_frame.pack()


    def _create_list_widget(self,frame,name,widget_options):
        #param = self.get_parameter_object(name)
        #value = self.get_parameter_value(name)

        X = lambda event=None,x=name: self._list_edit(x)

        w = ListWidget(frame,variable=self._tkvars[name],
                       cmd=X,**widget_options)
        #w = ListWidget(frame,variable=tkvar,**widget_options)
        
                    
        #help_text = getdoc(self._string2object(name,tkvar._original_get()))
        #self.balloon.bind(w,help_text)
        return w

    

    def _create_number_widget(self,frame,name,widget_options):
        """
        Return a TaggedSlider to represent parameter 'name'.

        The slider's bounds are set to those of the Parameter.
        """
        w = TaggedSlider(frame,variable=self._tkvars[name],**widget_options)
        param = self.get_parameter_object(name)

        lower_bound,upper_bound = param.get_soft_bounds()
        
        if upper_bound is not None and lower_bound is not None:
            # TaggedSlider needs BOTH bounds (neither can be None)
            w.set_bounds(lower_bound,upper_bound,inclusive_bounds=param.inclusive_bounds) 


        # have to do the lookup because subclass might override default
        if not lookup_by_class(self.param_immediately_apply_change,type(param)):
            w.bind('<<TagReturn>>', lambda e=None,x=name: self._handle_gui_set(x,force=True))
            w.bind('<<TagFocusOut>>', lambda e=None,x=name: self._handle_gui_set(x,force=True))
            w.bind('<<SliderSet>>', lambda e=None,x=name: self._handle_gui_set(x,force=True))
            
        return w


    def _create_boolean_widget(self,frame,name,widget_options):
        """Return a Tkinter.Checkbutton to represent parameter 'name'."""
        # CB: might be necessary to pass actions to command option of Checkbutton;
        # could be cause of test pattern boolean not working?
        return T.Checkbutton(frame,variable=self._tkvars[name],**widget_options)

        
    def _create_string_widget(self,frame,name,widget_options):
        """Return a Tkinter.Entry to represent parameter 'name'."""
        widget = T.Entry(frame,textvariable=self._tkvars[name],**widget_options)
        param = self.get_parameter_object(name)
        if not lookup_by_class(self.param_immediately_apply_change,type(param)):
            widget.bind('<Return>', lambda e=None,x=name: self._handle_gui_set(x,force=True))
            widget.bind('<FocusOut>', lambda e=None,x=name: self._handle_gui_set(x,force=True))
        return widget

################################################################################
# End WIDGET CREATION
################################################################################



    # CB: the colors etc for indication are only temporary
    def _indicate_tkvar_status(self,param_name,status=None):
        """
        Set the parameter's label to:
         - blue if the GUI value differs from that set on the object
         - red if the text doesn't translate to a correct value
         - black if the GUI and object have the same value
        """
        if self.translators[param_name].last_string2object_failed:
            status = 'error'

        self._set_widget_status(param_name,status)


    # this scheme is incompatible with tile
    # (tile having the right idea about how to do this kind of thing!)
    def _set_widget_status(self,param_name,status):

        if param_name in self.representations:
            if 'widget' in self.representations[param_name]:
                
                widget = self.representations[param_name]['widget']
                states = {'error'   : 'red',
                          'changed' : 'blue',
                          None      : 'black'}

                if is_button(widget):
                    # can't change state of button
                    return

                try:
                    widget.config(foreground=states[status])
                except T.TclError:  #CEBALERT uh-oh
                    pass

    def _pretty_print(self,s):
        """
        Convert a Parameter name s to a string suitable for display,
        if pretty_parameters is True.
        """
        if not self.pretty_parameters:
            return s
        else:
            n = s.replace("_"," ")
            n = n.capitalize()
            return n


# CEBALERT: is there no "file entry" widget for Tkinter?  I see there
# is one for Tix, but while that is listed as being in Python's
# standard library, it's rarely actually included...
import tkFileDialog
class HackFileEntry(T.Frame):
    def __init__(self,master,var,**config):
        T.Frame.__init__(self,master)
        self.var = var
        self.button = T.Button(self,textvariable=self.var,command=self.cmd)
        self.button.pack()

    def cmd(self):
        filename = tkFileDialog.askopenfilename()
        if filename!="":
            self.var.set(filename)


######################################################################
######################################################################

class Translator(object):
    """
    Abstract class that

    Translators handle translation between objects and their
    string representations in the GUI.

        last_string2object_failed is a flag that can be set to indicate that
        the last string-to-object translation failed.
        (TkParameterized checks this attribute for indicating errors to
        the user.)

    """
    last_string2object_failed = False # CEBALERT: why class attr?

    def __init__(self,param,initial_value=None):
        self.param = param
        self.msg_handler = None
    
    def string2object(self,string_):
        raise NotImplementedError

    def object2string(self,object_):
        raise NotImplementedError

    def _pass_out_msg(self,msg):
        if self.msg_handler:
            self.msg_handler.dynamicinfo(msg)

    def __copy__(self):
        """Copy only translator-specific state."""
        copy = self.__class__(self.param)
        copy.last_string2object_failed = self.last_string2object_failed
        copy.msg_handler = self.msg_handler
        return copy


class DoNothingTranslator(Translator):
    """
    Performs no translation. For use with Parameter types such as
    Boolean and String, where the representation
    of the object in the GUI is the object itself.
    """
    def string2object(self,string_):
        return string_

    def object2string(self,object_):
        return object_


class BoolTranslator(DoNothingTranslator):
    def string2object(self,string_):
        if string_=='None':
            return None
        else:
            return bool(string_)


# Error messages: need to change how they're reported
from param.parameterized import script_repr
class ListTranslator(Translator):

    def __init__(self,param,initial_value=None):
        super(ListTranslator,self).__init__(param)
        self.list_=initial_value

    def string2object(self,string_):
        return self.list_
    
    def object2string(self,object_):
        self.list_=object_
        return script_repr(self.list_,[],"",[]).replace("\n","")


class Eval_ReprTranslator(Translator):
    """
    Translates a string to an object by eval()ing the string in
    __main__.__dict__ (i.e. as if the string were typed at the
    commandline), and translates an object to a string by
    repr(object).
    """
    
    last_object = None
    last_string = None

    def __init__(self,param,initial_value=None):
        super(Eval_ReprTranslator,self).__init__(param,initial_value)
        self.last_string = self.object2string(initial_value)
        self.last_object = initial_value        

    # the whole last_string deal is required because of execing in main
    def string2object(self,string_):
        if string_!=self.last_string:
            try:
                self.last_object = eval(string_,__main__.__dict__)
                self.last_string = string_
                self._pass_out_msg(" ")
                #print "OUT:"
            except Exception,inst:
                #print "OUT:", str(sys.exc_info()[0])[11::]+" ("+str(inst)+")"
                m = str(inst) # CEBALERT: clean up
                self._pass_out_msg(m)
                self.last_string2object_failed=True
                return string_ # HIDDEN

        self.last_string2object_failed=False
        return self.last_object


    def object2string(self,object_):
        if object_==self.last_object:
            return self.last_string
        else:
            string_=script_repr(object_,[],"",[]).replace("\n","")
            self.last_object = object_
            self.last_string = string_
            return string_

    def __copy__(self):
        n = super(Eval_ReprTranslator,self).__copy__()
        n.last_string = self.last_string
        n.last_object = self.last_object
        return n


# CEBALERT: I hacked on support for non-hashable types like array (now
# have cache as {string: id(object)} and _cache_objects as
# {id(object): object}). The whole concept of translators needs
# revisiting anyway.
class String_ObjectTranslator(Translator):

    cache = property(lambda self: dict([(nam,self._cache_objects[objid])
                                        for nam,objid in self._cache.items()]))

    _cache = {}
    _cache_objects = {}
    
    def __init__(self,param,initial_value=None):
        super(String_ObjectTranslator,self).__init__(param,initial_value)
        self._cache = {}
        self._cache_objects = {}
        self.update()
        
    def string2object(self,string_):
        if string_ in self._cache:
            return self._cache_objects[self._cache[string_]]
        else:
            return string_
        
    def object2string(self,object_):
        inverse_cache = inverse(self._cache)
        if id(object_) in inverse_cache:
            return inverse_cache[id(object_)]
        else:
            return object_


    def update(self):
        for nam,obj in self.param.get_range().items():
            self._cache[nam] = id(obj)
            self._cache_objects[id(obj)] = obj


    def __copy__(self):
        n = super(String_ObjectTranslator,self).__copy__()
        n._cache = self._cache
        n._cache_objects = self._cache_objects
        return n
    
        

class CSPTranslator(String_ObjectTranslator):
        
    def string2object(self,string_):
        obj = super(CSPTranslator,self).string2object(string_)
        ## instantiate if it's just a class
        if isinstance(obj,type) and isinstance(string_,str):
            obj = obj()
            self._cache[string_]=id(obj)
            self._cache_objects[id(obj)]=obj

        return obj
        
    def object2string(self,object_):
        ## replace class if we already have object
        for name,objid in self._cache.items():
            obj = self._cache_objects[objid]
            if type(object_) is obj or type(object_) is type(obj):
                self._cache[name]=id(object_)
                self._cache_objects[id(object_)]= object_
        ##
        return super(CSPTranslator,self).object2string(object_)


    def __copy__(self):
        # because this one's object2string can modify cache
        n = Translator.__copy__(self)
        n._cache = copy.copy(self._cache)
        n._cache_objects = copy.copy(self._cache_objects)
        return n


def param_is_dynamically_generated(param,po):

    if not hasattr(param,'_value_is_dynamic'):
        return False

    if isinstance(po,Parameterized):
        return param._value_is_dynamic(po)
    elif isinstance(po,ParameterizedMetaclass):
        return param._value_is_dynamic(None)
    else:
        raise ValueError("po must be a Parameterized or ParameterizedMetaclass.")


class ParametersFrame(TkParameterized,T.Frame):
    """
    Displays and allows instantaneous editing of the Parameters
    of a supplied Parameterized.

    Changes made to Parameter representations on the GUI are
    immediately applied to the underlying object.
    """
    Defaults = Button(doc="""Return values to class defaults.""")

    Refresh = Button(doc="Return values to those currently set on the object (or, if editing a class, to those currently set on the class).")  

    # CEBALERT: this is a Frame, so close isn't likely to make
    # sense. But fortunately the close button acts on master.
    # Just be sure not to use this button when you don't want
    # the master window to vanish (e.g. in the model editor).
    Close = Button(doc="Close the window. (If applicable, asks if unsaved changes should be saved).")

    display_threshold = Number(default=0,precedence=-10,doc="Parameters with precedence below this value are not displayed.")

    show_labels = Boolean(default=True)

    def __init__(self,master,parameterized_object=None,on_set=None,
                 on_modify=None,msg_handler=None,on_close=None,**params):
        """
        Create a ParametersFrame with the specifed master, and
        representing the Parameters of parameterized_object.

        on_set is an optional function to call whenever any of the
        GUI variables representing Parameter values is set() by the
        GUI (i.e. by the user). Since a variable's value is not
        necessarily changed by such a set(), on_modify is another
        optional function to call only when a GUI variable's value
        actually changes. (See TkParameterized for more detail.)
        """
        T.Frame.__init__(self,master,borderwidth=1,relief='raised')

        self.on_set = on_set
        self.on_modify = on_modify

        TkParameterized.__init__(self,master,
                                 extraPO=parameterized_object,
                                 self_first=False,
                                 msg_handler=msg_handler,
                                 **params)

        self.on_set = on_set
        self.on_modify = on_modify
        self.on_close = on_close

        ## Frame for the Parameters
        self._params_frame = T.Frame(self)
        self._params_frame.pack(side='top',expand='yes',fill='both')

        self.params_to_display = {}
        self.currently_displayed_params = {}

        if parameterized_object:
            self.set_PO(parameterized_object)

        self._create_button_panel()


        # CEBALERT: just because callers assume this pack()s itself.
        # Really it should be left to callers i.e. this should be removed.
        self.pack(expand='yes',fill='both') 


    def hidden_param(self,name):
        """Return True if a parameter's precedence is below the display threshold."""
        # interpret a precedence of None as 0
        precedence = self.get_parameter_object(name).precedence or 0 
        return precedence<self.display_threshold
        

    def _create_button_panel(self):
        """
        Add the buttons in their own panel (frame).
        """
        ## Buttons
        #
        # Our button order (when all buttons present):
        # [Defaults] [Refresh] [Apply] [Close]
        # 
        # Our button - Windows
        # Close(yes) - OK
        # Close(no ) - Cancel
        # [X]        - Cancel
        # Apply      - Apply
        # Defaults   - 
        # Refresh    - Reset
        #
        # I think Windows users will head for the window's [X]
        # when they want to close and cancel their changes,
        # because they won't know if [Close] saves their changes
        # or not (until they press it, and find that it asks).
        #
        #
        # Some links that discuss and address what order to use for buttons:
        #
        # http://java.sun.com/products/jlf/ed2/book/HIG.Dialogs2.html
        # http://developer.kde.org/documentation/books/kde-2.0-development/ch08lev1sec6.html
        # http://developer.kde.org/documentation/standards/kde/style/dialogs/index.html
        # http://doc.trolltech.com/qq/qq19-buttons.html

        
        # Catch click on the [X]: like clicking [Close]
        # CEBALERT: but what if this frame isn't in its own window!
        try:
            self.master.protocol("WM_DELETE_WINDOW",self._close_button)
        except AttributeError:
            pass

        buttons_frame = T.Frame(self,borderwidth=1,relief='sunken')
        self.buttons_frame = buttons_frame
        buttons_frame.pack(side="bottom",expand="no")
        
        self._buttons_frame_left = T.Frame(buttons_frame)
        self._buttons_frame_left.pack(side='left',expand='yes',fill='x')

        self._buttons_frame_right = T.Frame(buttons_frame)
        self._buttons_frame_right.pack(side='right',expand='yes',fill='x')

        self.pack_param('Defaults',parent=self._buttons_frame_left,
                        on_set=self._defaults_button,side='left')
        self.pack_param('Refresh',parent=self._buttons_frame_left,
                        on_set=self._refresh_button,side='left')
        self.pack_param('Close',parent=self._buttons_frame_right,
                        on_set=self._close_button,side='right')


    def _refresh_button(self):
        """See Refresh parameter."""
        for name in self.params_to_display.keys():
            self._tkvars[name].get()


    def _defaults_button(self):
        """See Defaults parameter."""
        assert isinstance(self._extraPO,Parameterized)

        defaults = self._extraPO.defaults()

        for param_name,val in defaults.items():
            if not self.hidden_param(param_name):
                self.gui_set_param(param_name,val)#_tkvars[param_name].set(val)

                # CEBALERT: taggedsliders need to have tag_set() called to update slider
                w = self.representations[param_name]['widget']
                if hasattr(w,'tag_set'):w.tag_set()


        # CEBALERT: why doesn't this first check that something has actually changed?
        if self.on_modify:
            self.on_modify()
            
        if self.on_set:
            self.on_set()


        
        self.update_idletasks()

        
        
    def _close_button(self):
        """See Close parameter."""
        if self.on_close:
            self.on_close()
            
        T.Frame.destroy(self) # hmm
        self.master.destroy()


    def set_PO(self,parameterized_object):
        self.change_PO(parameterized_object)

        title = "Parameters of "+ (parameterized_object.name or str(parameterized_object)) # (name for class is None)

        try:
            self.master.title(title)
        except AttributeError:
            # can only set window title on a window (model editor puts frame in another frame)
            pass

        self.__dict__['_name_param_value'] = title
        
        
        ### Pack all of the non-hidden Parameters
        self.params_to_display = {}
        for n,p in parameterized_object.params().items():
            if not self.hidden_param(n):
                self.params_to_display[n]=p
                    
        self.pack_params_to_display()

        # hide Defaults button for classes
        if isinstance(parameterized_object,type):
            self.hide_param('Defaults')
        else:
            self.unhide_param('Defaults')    


    def _wipe_currently_displayed_params(self):
        """Wipe old labels and widgets from screen."""
        for rep in self.currently_displayed_params.values():
            for w in rep:
                try:
                    rep[w].destroy()
                except: # e.g. buttons have None for label ('notNonelabel')
                    pass
                

    def _grid_param(self,parameter_name,row):
        widget = self.representations[parameter_name]['widget']
        label = self.representations[parameter_name]['label']

        # CB: (I know about the code duplication here & in tkpo)
        param_obj = self.get_parameter_object(parameter_name)
        help_text = getdoc(param_obj)

        if param_obj.default is not None:
            # some params appear to have no docs!!!
            if help_text is not None:
                help_text+="\n\nDefault: %s"%self._object2string(parameter_name,param_obj.default,replace=False)
        
        if self.show_labels:
            label.grid(row=row,column=0,
                       padx=2,pady=2,sticky=T.E)

            self.balloon.bind(label, help_text)

        # We want widgets to stretch to both sides...
        posn=T.E+T.W
        # ...except Checkbuttons, which should be left-aligned.
        if widget.__class__==T.Checkbutton:
            posn=T.W

        widget.grid(row=row,
                    column=1,
                    padx=2,
                    pady=2,
                    sticky=posn)

        # widgets expand to fill frame
        widget.master.grid_columnconfigure(1,weight=2)

        self._post_add_param(parameter_name)




    def _make_representation(self,name):
        if name in self.representations:
            for n,w in self.representations[name].items():
                try:
                    w.destroy()
                except: #e.g. buttons have None for label ('notNonelabel')
                    pass
                del self.representations[name][n]
        
        widget,label = self._create_widget(name,self._params_frame,
                                           on_set=self.on_set,
                                           on_modify=self.on_modify)

        label.bind("<Double-Button-1>",lambda event=None,x=name: self.switch_dynamic(x))

        self.representations[name]={'widget':widget,'label':label}
        self._indicate_tkvar_status(name)

        

    def pack_params_to_display(self):
        self._wipe_currently_displayed_params()

        ### sort Parameters by reverse precedence
        parameter_precedences = {}
        for name,parameter in self.params_to_display.items():
            parameter_precedences[name]=parameter.precedence
        sorted_parameter_names = keys_sorted_by_value(parameter_precedences)
            
        ### create the labels & widgets
        for name in self.params_to_display:
            self._make_representation(name)
            
        ### add widgets & labels to screen in a grid
        rows = range(len(sorted_parameter_names))
        for row,parameter_name in zip(rows,sorted_parameter_names): 
            self._grid_param(parameter_name,row)

        self.currently_displayed_params = dict([(param_name,self.representations[param_name])
                                          for param_name in self.params_to_display])
        #self.event_generate("<<SizeRight>>")


    # CEBALERT: rename
    def _edit_PO_in_currently_selected_widget(self):
        """
        Open a new window containing a ParametersFrame (actually, a
        type(self)) for the PO in _currently_selected_widget.
        """
        # CEBALERT: simplify this lookup by value
        param_name = None
        for name,representation in self.representations.items():
            if self._currently_selected_widget is representation['widget']:
                param_name=name
                break

        # CEBALERT: should have used get_parameter_value(param_name)?
        PO_to_edit = self._string2object(param_name,self._tkvars[param_name].get()) 

        parameter_window = AppWindow(self)
        parameter_window.title(PO_to_edit.name+' parameters')

        ### CEBALERT: confusing? ###
        title=T.Label(parameter_window, text="("+param_name + " of " + (self._extraPO.name or 'class '+self._extraPO.__name__) + ")")
        title.pack(side = "top")
        self.balloon.bind(title,getdoc(self.get_parameter_object(param_name,self._extraPO)))
        ############################

        # CEBALERT: don't want EditingParametersFrameWithApply
        t = type(self)
        if t.__name__=='EditingParametersFrameWithApply':
            t = ParametersFrameWithApply
            
        parameter_frame = t(parameter_window,parameterized_object=PO_to_edit,msg_handler=self.msg_handler,on_set=self.on_set,on_modify=self.on_modify)
        parameter_frame.pack()

        # CEBALERT: need to get the list item to update in parent if editing via a right click
        # properties frame. need to get a new representation into translator.
        #parameter_frame._apply_hooks.append(lambda *args:self._refresh_value(param_name))


        # CEBALERT: need to sort out all this stuff in the tkpo/pf
        # hierarchy
        
##     def unpack_param(self,param_name):
##     def hide_param(self,param_name):
##     def unhide_param(self,param_name):

    def repack_param(self,param_name):

        self._refresh_value(param_name)
        
        r = self.representations[param_name]
        widget,label = r['widget'],r['label']
        row = int(widget.grid_info()['row'])

        widget.destroy()
        label.destroy()

        param = self.get_parameter_object(param_name)
        
        self._create_translator(param_name,param)
        self._make_representation(param_name)
        self._grid_param(param_name,row)            

    def _refresh_value(self,param_name):
        pass



class ParametersFrameWithApply(ParametersFrame):
    """
    Displays and allows editing of the Parameters of a supplied
    Parameterized.

    Changes made to Parameter representations in the GUI are not
    applied to the underlying object until Apply is pressed.
    """

    # CEBENHANCEMENT: might be nice to make Apply button blue like the
    # unapplied changes, but can't currently set button color.
    Apply = Button(doc="""Set object's Parameters to displayed values.\n
                          When editing a class, sets the class defaults
                          (i.e. acts on the class object).""")
    
    def __init__(self,master,parameterized_object=None,
                 on_set=None,on_modify=None,**params):
        self._apply_hooks=[]
        super(ParametersFrameWithApply,self).__init__(master,
                                                      parameterized_object,
                                                      on_set,on_modify,
                                                      **params)
        self._live_update = False

        ### CEBALERT: describe why this apply is different from Apply
        for p in self.param_immediately_apply_change:
            self.param_immediately_apply_change[p]=True
            
        
        self.pack_param('Apply',parent=self._buttons_frame_right,
                        on_set=self._apply_button,side='left')

        assert self.has_unapplied_change() is False, "ParametersFrame altered a value on opening. If possible, please file a bug report on the website describing what you were doing when you received this error."

        # CEBALERT: should use existing code
        self.representations['Apply']['widget']['state']='disabled'


    def _create_string_widget(self,frame,name,widget_options):
        # don't want immediate updates, so unbind update events
        w= super(ParametersFrameWithApply,self)._create_string_widget(frame,name,widget_options)
        w.unbind('<Return>')
        w.unbind('<FocusOut>')
        return w


    def set_PO(self,parameterized_object):
        super(ParametersFrameWithApply,self).set_PO(parameterized_object)
                                          
        # (don't want to update parameters immediately)
        for v in self._tkvars.values():
            v._checking_get = v.get
            v.get = v._original_get


    def has_unapplied_change(self):
        """Return True if any one of the packed parameters' displayed values is different from
        that on the object."""
        for name in self.params_to_display.keys():
            if self._tkvar_changed(name):
                return True
        return False

    def _indicate_tkvar_status(self,param_name,status=None):
        if self._tkvar_changed(param_name):
            status = 'changed'

        super(ParametersFrameWithApply,self)._indicate_tkvar_status(param_name,status)
        
    
    def _handle_gui_set(self,p_name,force=False):
        #print "ParametersFrame._handle_gui_set",p_name
        TkParameterized._handle_gui_set(self,p_name,force)

        if 'Apply' in self.representations:
            w=self.representations['Apply']['widget']
            if self.has_unapplied_change():
                state='normal'
            else:
                state='disable'

            w.config(state=state)
            
    def _close_button(self):
        # CEBERRORALERT: dialog box should include a cancel button
        # Also, changes are *not* applied if one of the boxes is in
        # error.
        if self.has_unapplied_change() \
               and askyesno("Close","Apply changes before closing?"):
            self._apply_button()
        super(ParametersFrameWithApply,self)._close_button()


    def update_parameters(self):
        if isinstance(self._extraPO,type):
            for name in self.params_to_display.keys():
                #if self._tkvar_changed(name):
                self._update_param_from_tkvar(name)
        else:
            for name,param in self.params_to_display.items():
                if not param.constant:  #and self._tkvar_changed(name):
                    self._update_param_from_tkvar(name)


    def _apply_button(self):
        self.update_parameters()
        self._refresh_button(overwrite_error=False)
        # CEBALERT: because overriding a method that\s already been
        # installed as a callback does nothing
        for h in self._apply_hooks:
            h(self)

        # CEBALERT: how does apply button's status change now? Doesn't
        # work properly for list editing; stays grey until clicked twice.

    def _refresh_value(self,param_name):
        po_val = self.get_parameter_value(param_name)
        po_stringrep = self._object2string(param_name,po_val)
        self._tkvars[param_name]._original_set(po_stringrep)

        
    def _refresh_button(self,overwrite_error=True):
        for name in self.params_to_display.keys():
            if self.translators[name].last_string2object_failed and not overwrite_error:
                pass
            else:
                self._refresh_value(name)
                #print self._tkvars[name]._checking_get()
                # CEBALERT: taggedsliders need to have tag_set() called to update slider
                w = self.representations[name]['widget']
                if hasattr(w,'tag_set'):w.tag_set()


##     def _defaults_button(self):
##         """See Defaults parameter."""
##         assert isinstance(self._extraPO,Parameterized)

##         defaults = self._extraPO.defaults()

##         for param_name,val in defaults.items():
##             if not self.hidden_param(param_name):
##                 self._tkvars[param_name].set(val)

##         if self.on_modify: self.on_modify()
##         if self.on_set: self.on_set()
##         self.update_idletasks()


# CB: can override tracefn so that Apply/Refresh buttons are enabled/disabled as appropriate

def edit_parameters(parameterized,with_apply=True,**params):
    """
    Edit the Parameters of a supplied parameterized instance or class.

    Specify with_apply=False for a ParametersFrame (which immediately
    updates the object - no need to press the Apply button).

    Extra params are passed to the ParametersFrame constructor.
    """
    if not with_apply:
        pf_class = ParametersFrame
    else:
        pf_class = ParametersFrameWithApply

    return pf_class(T.Toplevel(),parameterized,**params)










# Barely wrapped tooltip from tklib.
# CB: this isn't the right way to do it, and it breaks menubar
# tips for some reason, but user code didn't have to change.

class Balloon(T.Widget):
    
    _tkname = '::tooltip::tooltip'

    def __init__(self,master,cnf={},**kw):
        master.tk.call("package","require","tooltip")
        T.Widget.__init__(self, master,self._tkname, cnf, kw)

    def bind(self,*args):
        """
        e.g. for a Button b and a Menu m with item 'Quit' in a T.Toplevel t
        
        balloon = Balloon(t)
        balloon.bind(b,'some guidance')
        balloon.bind(m,'Quit','more guidance')
        """
        if len(args)>2:            
            self.tk.call(self._tkname,args[0]._w,'-index',args[1],args[2])
        else:
            self.tk.call(self._tkname,*args)

##     def tagbind(self,*args,**kw):
##         print "### Balloon.tagbind(): not yet implemented error ###"



# CEBALERT: should be renamed to something like IndexMenu, but then
# I am not sure if some of our tk hacks would work (e.g. in topoconsole,
# we set something for Menu on linux so that the popup behavior is
# reasonable).
class Menu(T.Menu):
    """
    Tkinter Menu, but with a way to access entries by name.

    Entries can be accessed via the label supplied when the entry is
    add()ed or insert()ed. For an entry whose label could change, you
    can supply 'indexname', which can then be used to access the entry
    no matter what the label might have become.
    """
    ## (Original Menu class is in lib/python2.4/lib-tk/Tkinter.py)
    
    def get_tkinter_index(self,index):
        """
        Return the Tkinter index, whether given an indexname or index
        (where index could be an int or Tkinter position e.g. 'end').
        """
        if isinstance(index,str):
            if index in self.indexname2index:
                i=self.indexname2index[index]
            else:
                # pass through tkinter to get 'end' etc converted to index
                i=self.index(index)
        else:
            i=index
        return i


    def get_indexname(self,index):
        """
        Return the indexname, whether given an indexname or index
        (where index could be an int or Tkinter position e.g. 'end').

        The returned value will be None if index refers to an unnamed
        entry.
        """
        if index in self.indexname2index:
            return index
        else:
            for name,i in self.indexname2index.items():
                if self.index(index)==i:
                    return name
        return None
                

    def __init__(self, master=None, cnf={}, **kw):
        # Creates two internal indexes to track names and commands
        self.indexname2index = {}  # rename to indexnames2index or similar
        self.named_commands = {}
        T.Menu.__init__(self,master,cnf,**kw)


    def __extract_indexname(self,cnf,kw):
        # indexname will be as specified by 'indexname' in cnf or kw,
        # or else as specified by 'label' in cnf or kw.
        # 
        # indexname will be None if neither indexname nor label is
        # specified in cnf or kw.
        indexname=cnf.pop('indexname',kw.pop('indexname',None))
        if indexname is None:
            indexname = cnf.get('label',kw.get('label',None))
        return indexname

    def _update_indices(self,index,indexname,cnf,kw):
        if indexname is not None:
            self.indexname2index[indexname] = index
            # this pain is to keep the actual item, if it's a menu or a command, available to access
            self.named_commands[indexname] = cnf.get('menu',kw.get('menu',cnf.get('command',kw.get('command',None))))


    def add(self, itemType, cnf={}, **kw):
        """
        See Tkinter.Menu.add(), but 'indexname' can also be supplied.

        If supplied, indexname must be unique. If label is supplied without
        indexname, then label must be unique.
        """
        indexname = self.__extract_indexname(cnf,kw)
        assert indexname not in self.indexname2index
        T.Menu.add(self,itemType,cnf,**kw)
        self._update_indices(self.index("last") or 0,indexname,cnf,kw)
        

    def insert(self, index, itemType, cnf={}, **kw):
        """
        See Tkinter.Menu.insert(), but index can also be specified as text.
        """
        indexname = self.__extract_indexname(cnf,kw)
        assert indexname not in self.indexname2index

        # increase index of any item after insertion point
        for name,i in self.indexname2index.items():
            if i>=index:
                self.indexname2index[name]+=1

        T.Menu.insert(self,index,itemType,cnf,**kw)
        self._update_indices(index,indexname,cnf,kw)


    def __delete(self,index1):
        i1 = self.get_tkinter_index(index1)
        indexname1 = self.get_indexname(index1)

        assert (indexname1 in self.indexname2index or indexname1 is None)

        # decrease index of any item after deletion point
        for name,i in self.indexname2index.items():
            if i>i1:
                self.indexname2index[name]-=1

        self.named_commands.pop(indexname1,None)
        self.indexname2index.pop(indexname1,None)
        T.Menu.delete(self,i1,None)
        

    def delete(self, index1, index2=None):
        """
        If index2 is not specified, deletes the menu item at index1
        (an indexname or tk integer index).
        
        If index2 is specified, deletes menu items in
        range(index1,index2+1).
        """
        if index2 is not None:
            start = self.index(index1)
            end = self.index(index2)
            if start is not None and end is not None:
                for _ in range(start,end+1):
                    # __delete shifts the remaining items one position back,
                    # so repeatedly deleting the first item in the range will
                    # delete all of them
                    self.__delete(start)
        else:
            self.__delete(index1)



    ########## METHODS OVERRIDDEN FOR CONVENIENCE
    def entryconfigure(self, index, cnf=None, **kw):
        """Configure a menu item at INDEX."""
        i = self.get_tkinter_index(index)
        return T.Menu.entryconfigure(self,i,cnf,**kw)
        
    entryconfig = entryconfigure

    def invoke(self, index):
        """Invoke a menu item identified by INDEX and execute
        the associated command."""
        return T.Menu.invoke(self,self.get_tkinter_index(index))

    # other methods can be overriden if they're needed



class TaggedSlider(T.Frame):
    """
    Widget for manipulating a numeric value using either a slider or a
    text-entry box, keeping the two values in sync.

    Generates a number of Events:

    <<TagFocusOut>>  - tag loses focus
    <<TagReturn>>    - Return pressed in tag
    <<SliderSet>>    - slider is clicked/dragged
    """
    def __init__(self,master,variable,bounds=(0,1),inclusive_bounds=(True,True),
                 slider_length=100,tag_width=10,
                 tag_extra_config={},slider_extra_config={}):
        """
        On clicking or dragging the slider, the tag value is set
        to the slider's value.

        On pressing Return in or moving focus from the tag, the slider
        value is set, but also:
        
        * the range of the slider is adjusted (e.g. to fit a larger
          max value)

        * the resolution of the slider is adjusted based on the
          the value in the tag (e.g. 0.01 in the tag gives a
          resolution of 0.01), also taking into account the precision
          of the value in the tag (e.g. 0.0100 gives a resolution
          of 0.0001).
        """
        # CEBALERT: ...although respecting the precision isn't always
        # helpful because the slider can still have a limited
        # resolution anyway (from its length and the range, given the
        # size of a pixel...)
        T.Frame.__init__(self,master)

        self.variable= variable

        # CEBALERT: shouldn't this be calling set_slider_bounds()?
        self.bounds = bounds
        self.inclusive_bounds = inclusive_bounds

        self.tag = T.Entry(self,textvariable=self.variable,
                                 width=tag_width,**tag_extra_config)
        self.tag.pack(side='left')
        self.tag.bind('<Return>', self._tag_press_return)  
        self.tag.bind('<FocusOut>', self._tag_focus_out)
        self.tag.bind('<Leave>', self._tag_focus_out)

        # no variable: we control the slider ourselves
        self.slider = T.Scale(self,variable=None,
                    from_=self.bounds[0],to=self.bounds[1],
                    orient='horizontal',length=slider_length,
                    showvalue=0,**slider_extra_config)
        
        self.slider.pack(side='right',expand="yes",fill='x')
        self.slider.bind('<ButtonRelease-1>', self._slider_used)
        self.slider.bind('<B1-Motion>', self._slider_used)

        self.tag_set()


    def tag_set(self):
        """
        After entering a value into the tag, this method should be
        called to set the slider correctly.

        (Called automatically for tag's <Return> and <FocusOut>
        events.)
        """
        # Set slider resolution. This is important because
        # we want the slider to be positioned at the exact
        # tag value.
        self._try_to_set_slider_resolution()
        self._try_to_set_slider()


    def set_slider_bounds(self,lower,upper,inclusive_bounds=None):
        """
        Set new lower and upper bounds for the slider.

        If specified, inclusive_bounds should be a sequence of length
        2 specifying True or False for the lower and upper bounds.
        """
        self.bounds = (lower,upper)

        if inclusive_bounds is not None:
            self.inclusive_bounds = inclusive_bounds

        epsilon = max(self.slider['resolution'],0.00000000001)

        if self.inclusive_bounds[0] is False:
            lower+=epsilon
        if self.inclusive_bounds[1] is False:
            upper-=epsilon
        self.slider.config(from_=lower,to=upper)

    set_bounds = set_slider_bounds
        
 
    # CB: why isn't this used for [] access? What should this
    # be called? Is it configure?
    def config(self,**options):
        """
        TaggedSlider is a compound widget. In most cases, config
        options should be passed to one of the component widgets
        (i.e. the tag or the slider). For some options, however,
        we need to handle them being set on the widget as a whole;
        further, some of these should be applied to both component
        widgets, but some should just be applied to one.

        Options handled:
        * state (applied to both)
        * background, foreground (applied to tag only)
        """
        if 'state' in options:
            self.tag['state']=options['state']
            self.slider['state']=options['state']
            del options['state']
        if 'background' in options:
            self.tag['background']=options['background']
            del options['background']
        if 'foreground' in options:
            self.tag['foreground']=options['foreground']
            del options['foreground']
        if len(options)>0:
            raise NotImplementedError(
                """Only state, background, and foreground options are
                currently supported for this widget; set options on
                either the component tag or slider instead.""")

        return {} # CEBALERT: need to return same object as Tkinter would.
    

    def get(self):
        """
        Calls the tag's get() method.

        Helps to match behavior of other Tkinter Widgets.
        """
        return self.tag.get()


    # CEBALERT: three different events for max. flexibility...but
    # often a user will just want to know if the value was set. Could
    # also generate a "<<TaggedSliderSet>>" event each time, which a
    # user could just look for. Or could these events all be children
    # of a <<TaggedSliderSet>>?
    def _slider_used(self,event=None):
        self.variable.set(self.slider.get())
        self.event_generate("<<SliderSet>>")


    def _tag_press_return(self,event=None):
        self.event_generate("<<TagReturn>>")
        self.tag_set()


    def _tag_focus_out(self,event=None):
        self.event_generate("<<TagFocusOut>>")
        self.tag_set()        


    def _set_slider_resolution(self,value):
        # CEBALERT: how to find n. dp simply?
        p = decimal.Decimal(str(value)).as_tuple()[2]
        self.slider['resolution']=10**p


    def _try_to_set_slider_resolution(self):
        """
        Use the actual number in the box to set the slider's resolution,
        so that user-entered resolutions are respected (e.g. 0.1 vs 0.1000).

        If that's not possible (e.g. there's text in the box), use the
        value contained in the variable (because whatever owns the
        variable could have performed a conversion of the text -
        TkParameterized does this, for instance).

        Leaves the resolution as it was if no number is available.
        """
        try:
            # 1st choice is to get the actual number in the box:
            # allows us to respect user-entered resolution
            # (e.g. 0.010000) 
            self._set_slider_resolution(self.tag.get())
            return True
        except: # probably tclerror
            try:
                # ...but that might have been text.  2nd choice is to
                # get the value from the variable (e.g. 0.01)
                self._set_slider_resolution(self.variable.get())
                return True
            except: # probably tclerror
                return False # can't set a new resolution


    def _try_to_set_slider(self):
        """
        If the value in the box can't be converted to a float, the slider doesn't get set.
        """
        tagvar_val = self.variable.get()
        try:
            val = float(tagvar_val)
            self.set_slider_bounds(min(self.bounds[0],val),
                                   max(self.bounds[1],val))
            self.slider.set(val)
        except ValueError:
            pass


class FocusTakingButton(T.Button):
    """
    A Tkinter Button that takes the focus when the mouse <Enter>s.

    (Tkinter.Button doesn't get focus even when it's clicked,
    and only <Enter> and <Leave> events work for buttons.)
    """
    def __init__(self, master=None, cnf={}, **kw):
        T.Button.__init__(self,master=master,cnf=cnf,**kw)
        self.bind("<Enter>", lambda e=None,x=self: x.focus_set())
        #self['highlightthickness']=0


# CB: tklib has status bar and scrolled window (among other widgets);
# should try them out (although they're tk only...) because we might
# not need the scrodget pacakge.

# Might wonder why we need <<SizeRight>> event, and don't just use the
# <Configure> event for calling sizeright: Can't distinguish manual
# resize from autoresizing.
class ScrolledFrame(T.Frame):
    """
    XXXX
    
    Content to be scrolled should go in the 'content' frame.
    """

    def _getstatus(self):
        return self._status
    def _setstatus(self,s):
        self._status = s
    status = property(_getstatus,_setstatus)
    
    def __init__(self,parent,**config):
        assert 'status' not in config
        T.Frame.__init__(self,parent,**config)

        
        abovetopframe = T.Frame(self)
        topframe = T.Frame(self)
        middleframe = T.Frame(self)
        botframe = T.Frame(self)
       
        botframe.pack(side="bottom",expand="yes",fill="x")
        abovetopframe.pack(side="top",expand="yes",fill="both")
        topframe.pack(side="top")#,expand="no",fill="both")
        middleframe.pack(side="top",expand='yes',fill='x')

        self.noscroll = abovetopframe
        self.noscroll_bottom = middleframe

        self.canvas = T.Canvas(topframe)
        self.canvas.pack()
        self.canvas.configure(width=0,height=0)
        
        self.sc = Scrodget(topframe,autohide=1)
        self.sc.associate(self.canvas)
        self.sc.pack(expand=1,fill="both")
        
        self.content = T.Frame(self.canvas)
        self.content.title = lambda x: self.title(x)
        self.content.container = self
        
        self.canvas.create_window(0,0,window=self.content,anchor='nw')

        self.bind("<<SizeRight>>",self.sizeright)

        #self.status = StatusBar(botframe) 
        #if status:
        #    self.status.pack(side="bottom",fill="both",expand="yes")
            

    def sizeright(self,event=None):
        self.content.update_idletasks()
        W = self.content.winfo_width()
        H = self.content.winfo_height()        
        self.canvas.configure(scrollregion=(0, 0, W, H))
        self.canvas.configure(width=W,height=H)
        


class ScrolledWindow(T.Toplevel):

    def __init__(self,parent,**config):
        T.Toplevel.__init__(self,parent,**config)
        self.maxsize(self.winfo_screenwidth(),self.winfo_screenheight())

        self.topframe = T.Frame(self)
        # CEBALERT: specifying 20 necessary because otherwise nothing
        # requests any height for the frame. I feel there should be
        # way to have the (status) label request the right height but
        # make no request about the width.
        self.botframe = T.Frame(self,height=20)
        
        self.botframe.pack(side='bottom',expand='no',fill='x')
        self.topframe.pack(side='top',expand='yes',fill='both')
        
        self._scrolledframe = ScrolledFrame(self.topframe)
        self._scrolledframe.pack(expand=1,fill='both')
        self.content = self._scrolledframe.content
        self.noscroll = self._scrolledframe.noscroll
        self.noscroll_bottom = self._scrolledframe.noscroll_bottom

    # required? presumably should be deleted
    def sizeright(self,event=None):
        self._scrolledframe.sizeright()





class ProgressController(object):
    def __init__(self,timer=None,sim=None,progress_var=None,status=None):

        self.status=status
        self.sim=sim
        self.timer = timer #or topo.sim.timer
        self.timer.receive_info.append(self.timing_info)

        self.progress_var = progress_var or T.DoubleVar()
        # trace the variable so that at 100 we can destroy the window
        self.progress_trace_name = self.progress_var.trace_variable(
            'w',lambda name,index,mode: self._close_if_complete())


    def _close_if_complete(self):
        """
        Close the specified progress window if the value of progress_var has reached 100.
        """
        if self.progress_var.get()>=100:
            # delete the variable trace (necessary?)
            #self.progress_var.trace_vdelete('w',self.progress_trace_name)

            self._close(final_message="Time %s: Finished %s"%(self.sim.timestr(),
                                                             self.timer.func.__name__))
            

    def _close(self,final_message=None):
        self.timer.receive_info.remove(self.timing_info)
        if final_message:
            self.status.response(final_message)

    def timing_info(self,time,percent,name,duration,remaining):
        self.progress_var.set(percent)

    def set_stop(self):
        """Declare that running should be interrupted."""
        self.timer.stop=True        
        final_message = "Time %s: Interrupted %s"%(self.sim.timestr(),
                                                   self.timer.func.__name__)
        self._close(final_message)


class ProgressWindow(ProgressController,T.Frame):
    """
    Graphically displays progress information for a SomeTimer object.
    
    ** Currently expects a 0-100 (percent) value ***        
    """
    def __init__(self,parent,sim=None,timer=None,progress_var=None,
                 title=None,status=None,unpack_master_when_done=True):
        ProgressController.__init__(self,timer=timer,sim=sim,
                                    progress_var=progress_var,status=status)
        T.Frame.__init__(self,parent)

        self.balloon = Balloon(self)
        
        self._unpack_master=unpack_master_when_done


        progress_bar = Progressbar(self,variable=self.progress_var)
        progress_bar.pack(side='left')

        # CEBALERT: would like time to be displayed inside the bar,
        # but I don;t know how to do that.
        self.timeleft=T.Label(self)
        self.timeleft.pack(side='left')

        stop_button = FocusTakingButton(self,text="X",command=self.set_stop)
        stop_button.pack(side='right')#side="bottom")
        self.balloon.bind(stop_button,"""Interrupt a procedure.""")
#        Stop a running simulation.
#            
#        The simulation can be interrupted only on round integer
#        simulation times, e.g. at 3.0 or 4.0 but not 3.15.  This
#        ensures that stopping and restarting are safe for any
#        model set up to be in a consistent state at integer
#        boundaries, as the example Topographica models are.""")
            
        
    def _close(self,final_message=None):
        ProgressController._close(self,final_message)
        # such a hack
        if self._unpack_master:
            self.master.pack_forget()
            self.master.master['width']=1
        T.Frame.destroy(self)

    def timing_info(self,time,percent,name,duration,remaining):
        try:
            ProgressController.timing_info(self,time,percent,name,duration,remaining)

            Z = "%02d:%02d"%(int(remaining/60),int(remaining%60))
            self.timeleft['text']=Z

            if self.status is not None:
                self.status.response('Time: %s  Duration: %s'%(time,duration))  
                self.update()
                self.update_idletasks()
        except T.TclError:
            pass




# CEB: slightly modifed code from http://code.activestate.com/recipes/576688/

# CEBALERT: this seems better than the tooltip provided by
# tklib. Should probably use this instead of 'Balloon' everywhere. I
# need to use Tooltip rather than Balloon for the status bar, because
# Tooltip allows a function to be passed for generating the text. I
# wish tk included a useful tooltip widget by default.
from time import time
class ToolTip( T.Toplevel ):
    """
    Provides a ToolTip widget for Tkinter.
    To apply a ToolTip to any Tkinter widget, simply pass the widget to the
    ToolTip constructor
    """ 
    def __init__( self, wdgt, msg=None, msgFunc=None, delay=1, follow=True ):
        """
        Initialize the ToolTip
        
        Arguments:
          wdgt: The widget this ToolTip is assigned to
          msg:  A static string message assigned to the ToolTip
          msgFunc: A function that retrieves a string to use as the ToolTip text
          delay:   The delay in seconds before the ToolTip appears(may be float)
          follow:  If True, the ToolTip follows motion, otherwise hides
        """
        self.wdgt = wdgt
        self.parent = self.wdgt.master                                          # The parent of the ToolTip is the parent of the ToolTips widget
        T.Toplevel.__init__( self, self.parent, bg='black', padx=1, pady=1 )      # Initalise the Toplevel
        self.withdraw()                                                         # Hide initially
        self.overrideredirect( True )                                           # The ToolTip Toplevel should have no frame or title bar
        
        self.msgVar = T.StringVar()                                               # The msgVar will contain the text displayed by the ToolTip        
        if msg == None:                                                         
            pass#self.msgVar.set( 'No message provided' )
        else:
            self.msgVar.set( msg )
        self.msgFunc = msgFunc
        self.delay = delay
        self.follow = follow
        self.visible = 0
        self.lastMotion = 0
        T.Message( self, textvariable=self.msgVar, bg='#FFFFDD',
                 aspect=1000 ).grid()                                           # The test of the ToolTip is displayed in a Message widget
        self.wdgt.bind( '<Enter>', self.spawn, '+' )                            # Add bindings to the widget.  This will NOT override bindings that the widget already has
        self.wdgt.bind( '<Leave>', self.hide, '+' )
        self.wdgt.bind( '<Motion>', self.move, '+' )
        
    def spawn( self, event=None ):
        """
        Spawn the ToolTip.  This simply makes the ToolTip eligible for display.
        Usually this is caused by entering the widget
        
        Arguments:
          event: The event that called this funciton
        """
        self.visible = 1
        self.after( int( self.delay * 1000 ), self.show )                       # The after function takes a time argument in miliseconds
        
    def show( self ):
        """
        Displays the ToolTip if the time delay has been long enough
        """
        if self.visible == 1 and time() - self.lastMotion > self.delay:
            self.visible = 2
        if self.visible == 2 and self.msgVar.get()!='':
            self.deiconify()
            
    def move( self, event ):
        """
        Processes motion within the widget.
        
        Arguments:
          event: The event that called this function
        """
        self.lastMotion = time()
        if self.follow == False:                                                # If the follow flag is not set, motion within the widget will make the ToolTip dissapear
            self.withdraw()
            self.visible = 1
        self.geometry( '+%i+%i' % ( event.x_root+10, event.y_root+10 ) )        # Offset the ToolTip 10x10 pixes southwest of the pointer
        try:
            self.msgVar.set( self.msgFunc() )                                   # Try to call the message function.  Will not change the message if the message function is None or the message function fails
        except:
            pass
        self.after( int( self.delay * 1000 ), self.show )
            
    def hide( self, event=None ):
        """
        Hides the ToolTip.  Usually this is caused by leaving the widget
        
        Arguments:
          event: The event that called this function
        """
        self.visible = 0
        self.withdraw()


def bind_tooltip(widget,msg):
    kw = dict(delay=1,follow=False)
    if callable(msg):
        kw['msgFunc']=msg
    else:
        kw['msg']=msg
    ToolTip(widget,**kw)
        

class StatusBar(T.Frame):

    messageframe_pack_options = dict(side='left',expand='yes',fill='x')
    dynamicinfoframe_pack_options = dict(side='left',expand='yes',fill='x')
    progressframe_pack_options = dict(side='right')


    #####
    # CEBALERT: hacks until we're using styles.
    #
    # This won't look good across platforms. Should get defaults.
    label_background = '#d9d9d9'
    label_foreground = '#000000'
    def _wrn_fmt(self):
        self.messagelabel.config(background=self.label_background)
        self.messagelabel.config(foreground='red')

    def _err_fmt(self):
        self.messagelabel.config(background='red')
        self.messagelabel.config(foreground='white')

    def _nrm_fmt(self):
        self.messagelabel.config(background=self.label_background)
        self.messagelabel.config(foreground=self.label_foreground)
    #####


    def __init__(self,master):
        T.Frame.__init__(self, master)

        self.mstack = []
        self.msformat = []
        self.mpoint = -1
        self.pf0 = T.Frame(self)
        self.pf0.pack(side='right')
        self.progressframe=T.Frame(self.pf0)
        
        self.dynamicinfoframe=T.Frame(self)
        self.dynamicinfolabel=T.Label(self.dynamicinfoframe,anchor='w')
        self.dynamicinfolabel.pack(side='left')
        bind_tooltip(self.dynamicinfolabel,self._get_dynamicinfo)

        self.messageframe=T.Frame(self)
        self.messageclear=T.Button(self.messageframe,text="X",
                                   command=lambda *args: self.clear_message())

        self.messagefwd=T.Button(self.messageframe,text=">",
                                 command=lambda *args:self.next_message())

        self.messagebck=T.Button(self.messageframe,text="<",
                                 command=lambda *args:self.previous_message())

        bind_tooltip(self.messageclear,"Dismiss current message(s)")
        bind_tooltip(self.messagefwd,"Next message")
        bind_tooltip(self.messagebck,"Previous message")

        self.messageclear.pack(side='right')
        self.messagefwd.pack(side='right')
        self.messagebck.pack(side='right')

        self.messagelabel=T.Label(self.messageframe,anchor='w')
        self.messagelabel.pack(side='left')
        bind_tooltip(self.messagelabel,self._get_message)


        self._show_dynamicinfoframe()


    def open_progress_window(self,timer=None,sim=None):
        p = ProgressWindow(self.progressframe,sim=sim,timer=timer,status=self)
        p.pack() 
        self.progressframe.pack(self.progressframe_pack_options)       
        return p


    def _show_messageframe(self):
        self.dynamicinfoframe.pack_forget()
        self.messageframe.pack(**self.messageframe_pack_options)

        
    def _show_dynamicinfoframe(self):
        self.messageframe.pack_forget()
        self.dynamicinfoframe.pack(**self.dynamicinfoframe_pack_options)
        self.update_idletasks()

        
    def dynamicinfo(self,text):
        self.dynamicinfolabel.config(text=text)


    def response(self,text):
        self.dynamicinfo(text)

        # remove previous after()
        try:
            self.after_cancel(self.__last_after_id)
        except:
            pass
        
        self.__last_after_id = self.after(10000,lambda *args: self.clear_dynamicinfo())

    def _display_from_history(self):
        displayindex=self.mpoint+1
        self.msformat[self.mpoint]()
        if displayindex<0:
            self._display_message("%s: %s"%(displayindex,self.mstack[self.mpoint]))
        else:
            self._display_message(self.mstack[self.mpoint])
        
    
    def previous_message(self):
        self.mpoint=max(-len(self.mstack),self.mpoint-1)
        self._display_from_history()

    def next_message(self):
        self.mpoint=min(-1,self.mpoint+1)
        self._display_from_history()

    def message(self,text):
        self._nrm_fmt()
        self.mstack.append(text)
        self.msformat.append(self._nrm_fmt)
        self._display_message(text)

        
    def _display_message(self,text):
        if text!='':
            if len(self.mstack)>1:
                pass#self.mnavframe.pack(side='right')
            else:
                pass#self.mnavframe.pack_forget()
            self.messagelabel.config(text=text)
            self._show_messageframe()

            
    def warn(self,text):
        self._wrn_fmt()
        self.mstack.append(text)
        self.msformat.append(self._wrn_fmt)
        self._display_message(text)


    def error(self,text):
        self._err_fmt()
        self.mstack.append(text)
        self.msformat.append(self._err_fmt)
        self._display_message(text)
        self.bell()
#        # CEBALERT: would like to lock only the window with the error,
#        # not the whole app, but I don't know how to do that.
#        try:
#            self.grab_set()
#        except: # get tclerror if another app has grab
#            pass

    def clear_message(self):
        self.mpoint=-1
        self.mstack=[]
        self.messagelabel.config(text="")
        self._nrm_fmt()
        self._show_dynamicinfoframe()
#        try:
#            self.grab_release()
#        except:
#            pass
        
    def clear_dynamicinfo(self):
        self.dynamicinfolabel.config(text="")

    def _get_message(self):
        return self.messagelabel.config()['text'][4]
    def _get_dynamicinfo(self):
        return self.dynamicinfolabel.config()['text'][4]

        

# CEBALERT: rename
class AppWindow(ScrolledWindow):
    """
    A ScrolledWindow with extra features intended to be common to all
    windows of an application.
    
    Currently this only includes a window icon, but we intend to
    add a right-click menu and possibly more.
    """
    window_icon_path = None

    def __init__(self,parent,status=False,**config):
        ScrolledWindow.__init__(self,parent)
        self.content.title = self.title
        self.renew()
        ### Universal right-click menu
        # CB: not currently used by anything but the plotgrouppanels
        # self.context_menu = Tkinter.Menu(self, tearoff=0)
        # self.bind("<<right-click>>",self.display_context_menu)

        # status bar is currenlty inside scrolled area (a feature
        # request is to move it outside ie replace self.content with
        # just self)
        self.status = StatusBar(self.botframe) 
        if status:
            # place doesn't interfere with parent's geometry
            # (don't want status bar to cause horizontal resizing,
            # but DO want it to cause vertical resizing - the vertical
            # part doesn't work, see earlier HACKALERT by botframe)
            self.status.place(relx=0,rely=0,relwidth=1.0,height='')

    def renew(self):
        # CEBALERT: doesn't work on OS X, and is a strange color on
        # Windows.  To get a proper icon on OS X, we probably have to
        # bundle into an application package or something like that.
        # On OS X, could possibly alter the small titlebar icon with something like:
        # self.attributes("-titlepath","/Users/x/topographica/AppIcon.icns")
        self.iconbitmap('@'+self.window_icon_path)

        self.protocol("WM_DELETE_WINDOW",self.mydestroy)

    def mydestroy(self):
        ScrolledWindow.destroy(self)
        


class ListWidget(T.Frame):

    # CEBALERT: as with several of my compound widgets, need to deal
    # with **config passed to __init__, by putting through config()
    # (and so also need to add config() methods where currently
    # missing).
    def __init__(self, master, variable,cmd,**widget_options):
        T.Frame.__init__(self, master)

        if 'state' in widget_options:
            self.disabled=widget_options['state']
        else:
            self.disabled=False
            
        self.entry=T.Entry(self,textvariable=variable,state='disabled',disabledforeground='black') #CEBALERT: presumably disabledforeground won't work work with styles...
        self.entry.pack(fill='both',expand=1)

        ### Right-click menu for widgets
        # CEBALERT: I can't work out how to make the right-click event
        # bound to the widget already (by the ParametersFrame) ever
        # activate!  It must be overwritten or something by tk. So I
        # have to duplicate the right-click menu code here.
        self.entry.bind("<<right-click>>",self._right_click)
        master.option_add("*Menu.tearOff", "0") 
        self.menu = Menu(master)
        self.menu.insert_command('end',label='Properties',
            command=cmd)

    def _right_click(self, event):
        """
        Popup the right-click menu.
        """
        if self.disabled is False:
            self.menu.tk_popup(event.x_root, event.y_root)

    def config(self,**options):
        # all options are passed to the entry
        # state=disabled->no right click menu
        if 'state' in options:
            if options['state']=='disabled':
                self.disabled=True
            elif options['state']=='normal':
                self.disabled=False
        return self.entry.config(**options)



import new



# CEBALERT: dict stuff is just half implemented! does enough
# to support list subclasses
def dict_to_parameterized(class_name,parameter_values):
    # each item is just a Parameter (i.e. not specific)
    parameter_objs = dict([(name,Parameter(default=value))
                           for name,value in parameter_values.items()])

    # got to be a new class to get independent sets of parameters
    new_class = new.classobj(class_name,(Representer,),parameter_objs)
    return  new_class(parameter_values)


def list_to_parameterized(list_,class_=None):

    parameter_values = OrderedDict([('a'*i,item) for item,i in zip(list_,range(1,len(list_)+1))])

    if class_ is None:
        parameter_objs = dict([(name,Parameter(default=value))
                               for name,value in parameter_values.items()])
    else:
        parameter_objs = dict([(name,ClassSelector(class_=class_,default=value))
                               for name,value in parameter_values.items()])
        

    new_class = new.classobj('List',(ListRepresenter,),parameter_objs)
    #new_class.params('name').hidden=True
    
    inst = new_class(parameter_values,class_=class_)
    inst.list_ = list_ # that's a hack; need to get classes right
    return inst





############################################################    

def standard_parameterized_params():
    return Parameterized.params().keys()


class Representer(Parameterized):

    name = Parameter(precedence=-1) # CEBALERT
    
    def __init__(self,represented,class_):
        ## CEBALERT: when we come to represent dicts in the GUI,
        ## will have to deal with name clashes (e.g. for name parameter)
        for name in standard_parameterized_params():
            assert name not in represented
        ##
        self.class_ = class_
        self.represented = represented
        super(Representer,self).__init__(**represented)
        self.initialized=False # allow all modifications


    def my_params(self):
        param_names = self.params().keys()

        # remove any of the standard params (e.g. name) that haven't
        # been added to represented
        for name in standard_parameterized_params():
            if name not in self.represented:
                param_names.pop(param_names.index(name))

        return param_names
        

    def update(self):
        for name in self.my_params():
            self.represented[name]=getattr(self,name)

    def add(self,name):
        if self.class_ is None:
            p = Parameter(default=None)
        else:
            p = ClassSelector(class_=self.class_,default=None)
            
        self._add_parameter(name,p)
        self.represented[name]=p.default
        return name
        
    def remove(self,name):
        # CB: don't move any of this method up to parameterized
        # without considering the consequences!

        del self.represented[name]
        
        cls=type(self)
        delattr(cls,name)
        try:
            delattr(cls,'_%s__params'%cls.__name__) 
        except AttributeError:
            pass
        

class ListRepresenter(Representer):

    def update(self):
        super(ListRepresenter,self).update()

        ## grow or shrink original list if necessary
        l = len(self.list_)-len(self.represented)

        if l>0:
            for i in range(l):
                self.list_.pop()
        elif l<0:
            for i in range(-l):
                self.list_.append(None)

        if len(self.represented)==0:
            self.list_[:]=[]
            return

        for val,i in zip(self.represented.values(),range(len(self.list_))):
            self.list_[i]=val

    def add(self,name=None):
        try:
            longest = max([len(n) for n in self.my_params()])
        except ValueError:
            longest = 0
        
        if name is None:
            name = 'a'*(longest+1)
            #name = 'a'*(len(self.my_params())+1)
        assert name not in self.my_params()
        return super(ListRepresenter,self).add(name)


# Problems:
# * + button gets hidden as more rows added (unless window made
#   bigger)
#
# * window doesn't open at right width to display contents
#   list item contents
#
# * I suspect there's a bug where you can get to a situation in
#   which editing one box will result in changes to another,
#   thanks to the ridiculously and unnecessarily complex code
#   for tracking items. But I can't currently demonstrate such a
#   a bug...
class EditingParametersFrameWithApply(ParametersFrameWithApply):

    def __init__(self,master,parameterized_object=None,
                 on_set=None,on_modify=None,**params):
        super(EditingParametersFrameWithApply,self).__init__(
            master,parameterized_object,on_set,on_modify,**params)

        self.hide_param('Defaults')

        ## hack to find last row
        last_row = -1
        for n,d in self.currently_displayed_params.items():
            row = int(d['widget'].grid_info()['row'])
            last_row=max(row,last_row)

        ad=T.Button(self,text="+",command=self._add_param)
        ad.pack(side='right')

        ### CB: should use button parameter and pack_param
        self._hack=[]
        image=ImageTk.PhotoImage(ImageOps.fit(
            Image.open(resolve_path('tkgui/icons/edit_add.png')),(20,20)))
        ad['image']=image
        self._hack.append(image)
        ###

        self._apply_hooks.append(lambda *args: self.xupdate())
        self._apply_hooks.append(lambda *args: self._update_apply_status())


# CEBALERT: name this, and there's duplication with represented etc.
    def xupdate(self):
        cls = type(self._extraPO)
        
        old = {}
        for name in self.params_to_display:
            old[name]=(self._tkvars[name],
                       self.representations[name],
                       self.params_to_display[name],
                       self.currently_displayed_params[name],
                       self._extraPO.params(name))

        new_pos = {} 
        for name in self.params_to_display.keys():
            new_pos[int(self.representations[name]['widget'].grid_info()['row'])]=name

        self._extraPO.represented = OrderedDict()
        
        for name,pos in zip(sorted(self.params_to_display),range(len(self.params_to_display))):
            self._tkvars[name]=old[new_pos[pos]][0]

            # getting ridiculous. make sure old widgets are wiped from
            # the earth. who knows how many other times I should have
            # been doing this in the gui?
            for w in self.representations[name].values():
                try:
                    w.grid_remove()
                    w.destroy()
                except:
                    pass
                    
            self.representations[name]=old[new_pos[pos]][1]
            self.params_to_display[name]=old[new_pos[pos]][2]
            self.currently_displayed_params[name]=old[new_pos[pos]][3]
            type.__setattr__(cls,name,old[new_pos[pos]][4])

            # (see alert at start of method)
            self._extraPO.represented[name]=getattr(self._extraPO,name)

        ## delete cached params()
        try:
            delattr(cls,'_%s__params'%cls.__name__) 
        except AttributeError:
            pass

        self._extraPO.update()
        self.set_PO(self._extraPO) # HACK! At least extract relevant parts
        

    def _grid_param(self,parameter_name,row):
        super(EditingParametersFrameWithApply,self)._grid_param(
            parameter_name,row)
        lc = self.representations[parameter_name]['list_ctrl']
        lc.grid(column=3,row=row)


    def _make_representation(self,name):
        super(EditingParametersFrameWithApply,self)._make_representation(name)

        self.representations[name]['list_ctrl']=ListItemCtrlWidget(
            self._params_frame,
            lambda:self._up_param(name),
            lambda:self._down_param(name),
            lambda:self._del_param(name))

    def _add_param(self):
        # should refactor pack_params to get out adding of single param

        po = self._extraPO
        name = po.add()

        self._create_tkvar(po,name,po.params(name))

        self._make_representation(name)
        row = len(self.params_to_display)
        self._grid_param(name,row)

        self.params_to_display[name]=po.params(name)
        self.currently_displayed_params[name]=self.representations[name]

        self._update_apply_status()
        

    def _del_param(self,name):
        current_pos = int(self.representations[name]['widget'].grid_info()['row'])
        po = self._extraPO
        for w in self.representations[name]:
            try:
                self.representations[name][w].grid_forget()
                self.representations[name][w].destroy()
            except:
                pass
            
        del self._tkvars[name]
        del self.representations[name]
        del self.params_to_display[name]
        del self.currently_displayed_params[name]
        del self.translators[name]
        
        po.remove(name)

        # move ones below up one
        for n in self.params_to_display:
            for n2,w in self.representations[n].items():
                if hasattr(w,'grid_info'):
                    w_gi = w.grid_info()
                    if 'row' in w_gi:
                        r1 = int(w_gi['row'])
                        if r1>current_pos:
                            w_gi['row']='%s'%(r1-1)
                            w.grid(**w_gi)
                        
        self._update_apply_status()


        
    def _down_param(self,name):
        current_pos = int(self.representations[name]['widget'].grid_info()['row'])

        if current_pos==len(self.params_to_display)-1:
            return

        new_pos = current_pos+1
        current_name = name

        self.y(current_name,current_pos,new_pos)


    def y(self,current_name,current_pos,new_pos):
        #### HACK TO FIND NEW NAME BY MATCHING ROW
        new_name=None
        for n in self.representations:
            if 'row' in self.representations[n]['widget'].grid_info():
                row = int(self.representations[n]['widget'].grid_info()['row'])
                if row==new_pos:
                    new_name=n
                    break
        assert new_name is not None
        ####

        for n,w in self.representations[current_name].items():
            if hasattr(w,'grid_info'):
                g = w.grid_info()
                if 'row' in g:
                    #print "regrid",current_name,current_pos
                    g['row']='%s'%new_pos
                    w.grid(**g)

        for n,w in self.representations[new_name].items():
            if hasattr(w,'grid_info'):
                g = w.grid_info()
                if 'row' in g:
                    #print "regrid",new_name,new_pos
                    g['row']='%s'%current_pos 
                    w.grid(**g)

        self._update_apply_status()


    def _up_param(self,name):
        current_pos = int(self.representations[name]['widget'].grid_info()['row'])

        if current_pos==0:
            return

        new_pos = current_pos-1
        current_name = name

        self.y(current_name,current_pos,new_pos)

    # CEBALERT: why not in super?
    def _update_apply_status(self):
        w=self.representations['Apply']['widget']
        if self.has_unapplied_change():
            w.config(state='normal')
        else:
            w.config(state='disabled')
            
    def set_PO(self,parameterized_object):
        super(EditingParametersFrameWithApply,self).set_PO(parameterized_object)
        self.hide_param('Defaults') # CEBALERT: should just have been unpacked earlier

    def has_unapplied_change(self):
        # detect length change
        if len(self._extraPO.list_)!=len(self.params_to_display):
            return True

        # detect order change 
        names = sorted(self.params_to_display.keys())
        for i,name in zip(range(len(names)),names):
            if 'widget' not in self.representations[name] or int(self.representations[name]['widget'].grid_info()['row'])!=i:
                return True
            
        return super(EditingParametersFrameWithApply,self).has_unapplied_change()
        

    def _refresh_button(self,overwrite_error=True):
        self.set_PO(self._extraPO)
        self._update_apply_status()

    # CEBALERT: because 
    def _apply_button(self):
        self.update_parameters()
        
        for h in self._apply_hooks:
            h(self)


class ListItemCtrlWidget(T.Frame):
    def __init__(self,master,up_cmd,down_cmd,remove_cmd):
        T.Frame.__init__(self, master)

        up = T.Button(self,text="u",command=up_cmd)
        up.pack(side='left')

        down = T.Button(self,text="d",command=down_cmd)
        down.pack(side='left')

        remove = T.Button(self,text='-',command=remove_cmd)
        remove.pack(side='left')


        ### CEBALERT: should use button parameter & pack_param
        self._hack = []
        image=ImageTk.PhotoImage(ImageOps.fit(
            Image.open(resolve_path('tkgui/icons/arrow-up.png')),(20,20)))
        up['image']=image
        self._hack.append(image)

        image=ImageTk.PhotoImage(ImageOps.fit(
            Image.open(resolve_path('tkgui/icons/arrow-down-2.0.png')),(20,20)))
        down['image']=image
        self._hack.append(image)

        image=ImageTk.PhotoImage(ImageOps.fit(
            Image.open(resolve_path('tkgui/icons/edit_remove.png')),(20,20)))
        remove['image']=image
        self._hack.append(image)
        ###
    

