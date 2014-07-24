"""
Sheet classes.

A Sheet is a two-dimensional arrangement of processing units,
typically modeling a neural region or a subset of cells in a neural
region.  Any new Sheet classes added to this directory will
automatically become available for any model.
"""

# Imported here so that all Sheets will be in the same package
from topo.base.sheet import Sheet
from topo.base.projection import ProjectionSheet  # pyflakes:ignore (API import)
from topo.base.cf import CFSheet
from topo.base.generatorsheet import GeneratorSheet
from topo.base.generatorsheet import ChannelGeneratorSheet # pyflakes:ignore (API import)

# Imported here for ease of access by users
from topo.base.boundingregion import BoundingBox  # pyflakes:ignore (API import)
from topo.base.sheet import activity_type  # pyflakes:ignore (API import)

import numpy

import topo

import param

from topo.base.cf import CFIter
from topo.base.projection import Projection
from topo.base.simulation import FunctionEvent, PeriodicEventSequence, EPConnectionEvent


class ActivityCopy(Sheet):
    """
    Copies incoming Activity patterns to its activity matrix and output port.

    Trivial Sheet class that is useful primarily as a placeholder for
    data that is computed elsewhere but that you want to appear as a
    Sheet, e.g. when wrapping an external simulation.
    """

    dest_ports=['Activity']
    src_ports=['Activity']

    def input_event(self,conn,data):
        self.input_data=data

    def process_current_time(self):
        if hasattr(self, 'input_data'):
            self.activity*=0
            self.activity+=self.input_data
            self.send_output(src_port='Activity',data=self.activity)
            del self.input_data



class SequenceGeneratorSheet(GeneratorSheet):
    """
    Sheet that generates a timed sequence of patterns.

    This sheet will repeatedly generate the input_sequence, with the
    given onsets.  The sequence is repeated every self.period time
    units.  If the total length of the sequence is longer than
    self.period, a warning is issued and the sequence repeats
    immediately after completion.
    """

    input_sequence = param.List(default=[],
          doc="""The sequence of patterns to generate.  Must be a list of
          (onset,generator) tuples. An empty list defaults to the
          single tuple: (0,self.input_generator), resulting in
          identical behavior to an ordinary GeneratorSheet.""")


    def __init__(self,**params):
        super(SequenceGeneratorSheet,self).__init__(**params)
        if not self.input_sequence:
            self.input_sequence = [(0,self.input_generator)]

    def start(self):
        assert self.simulation

        event_seq = []
        for delay,gen in self.input_sequence:
            event_seq.append(FunctionEvent(self.simulation.convert_to_time_type(delay),self.set_input_generator,gen))
            event_seq.append(FunctionEvent(0,self.generate))
        now = self.simulation.time()
        self.event = PeriodicEventSequence(now+self.simulation.convert_to_time_type(self.phase),self.simulation.convert_to_time_type(self.period),event_seq)
        self.simulation.enqueue_event(self.event)


def compute_joint_norm_totals(projlist,active_units_mask=True):
    """
    Compute norm_total for each CF in each projection from a group to
    be normalized jointly.
    """
    # Assumes that all Projections in the list have the same r,c size
    assert len(projlist)>=1
    iterator = CFIter(projlist[0],active_units_mask=active_units_mask)

    for junk,i in iterator():
        sums = [p.flatcfs[i].norm_total for p in projlist]
        joint_sum = numpy.add.reduce(sums)
        for p in projlist:
            p.flatcfs[i].norm_total=joint_sum


class JointNormalizingCFSheet(CFSheet):
    """
    A type of CFSheet extended to support joint sum-based normalization.

    For L1 normalization, joint normalization means normalizing the
    sum of (the absolute values of) all weights in a set of
    corresponding CFs in different Projections, rather than only
    considering weights in the same CF.

    This class provides a mechanism for grouping Projections (see
    _port_match and _grouped_in_projections) and a learn() function
    that computes the joint sums.  Joint normalization also requires
    having ConnectionField store and return a norm_total for each
    neuron, and having an TransferFn that will respect this norm_total
    rather than the strict total of the ConnectionField's weights.  At
    present, CFPOF_DivisiveNormalizeL1 and
    CFPOF_DivisiveNormalizeL1_opt do use norm_total; others can be
    extended to do something similar if necessary.

    To enable joint normalization, you can declare that all the
    incoming connections that should be normalized together each
    have a dest_port of:

    dest_port=('Activity','JointNormalize', 'AfferentGroup1'),

    Then all those that have this dest_port will be normalized
    together, as long as an appropriate TransferFn is being used.
    """

    joint_norm_fn = param.Callable(default=compute_joint_norm_totals,doc="""
        Function to use to compute the norm_total for each CF in each
        projection from a group to be normalized jointly.""")

    # JABALERT: Should check that whenever a connection is added to a
    # group, it has the same no of cfs as the existing connections.
    def start(self):
        self._normalize_weights(active_units_mask=False)


    # CEBALERT: rename active_units_mask and default to False
    def _normalize_weights(self,active_units_mask=True):
        """
        Apply the weights_output_fns for every group of Projections.

        If active_units_mask is True, only active units will have
        their weights normalized.
        """
        for key,projlist in self._grouped_in_projections('JointNormalize').items():
            if key == None:
                normtype='Individually'
            else:
                normtype='Jointly'
                self.joint_norm_fn(projlist,active_units_mask)

            self.debug(normtype + " normalizing:")

            for p in projlist:
                p.apply_learn_output_fns(active_units_mask=active_units_mask)
                self.debug('  ',p.name)


    def learn(self):
        """
        Call the learn() method on every Projection to the Sheet, and
        call the output functions (jointly if necessary).
        """
        # Ask all projections to learn independently
        for proj in self.in_connections:
            if not isinstance(proj,Projection):
                self.debug("Skipping non-Projection "+proj.name)
            else:
                proj.learn()

        # Apply output function in groups determined by dest_port
        self._normalize_weights()



class JointNormalizingCFSheet_Continuous(JointNormalizingCFSheet):
    """
    CFSheet that runs continuously, with no 'resting' periods between pattern presentations.

    Note that learning occurs only when the time is a whole number.
    """
    def process_current_time(self):
        if self.new_input:
           self.new_input = False
           if(float(topo.sim.time()) % 1.0 == 0.0):
               #self.activate()
               if (self.plastic):
                   self.learn()
           #else:
           self.activate()



class SettlingCFSheet(JointNormalizingCFSheet):
    """
    A JointNormalizingCFSheet implementing the idea of settling.

    Breaks continuous time up into discrete iterations, each
    consisting of a series of activations, up to a fixed number of
    settling steps.  Settling is controlled by the tsettle parameter;
    once that number of settling steps has been reached, an external
    input is required before the sheet will activate again.

    See the LISSOM algorithm (Sirosh and Miikkulainen, Biological
    Cybernetics 71:66-78, 1994) for one example of its usage.
    """

    strict_tsettle = param.Parameter(default = None,doc="""
        If non-None, delay sending output until activation_count reaches this value.""")

    mask_init_time=param.Integer(default=5,bounds=(0,None),doc="""
        Determines when a new mask is initialized in each new iteration.

        The mask is reset whenever new input comes in.  Once the
        activation_count (see tsettle) reaches mask_init_time, the mask
        is initialized to reflect the current activity profile.""")

    tsettle=param.Integer(default=8,bounds=(0,None),doc="""
        Number of times to activate the SettlingCFSheet sheet for each external input event.

        A counter is incremented each time an input is received from any
        source, and once the counter reaches tsettle, the last activation
        step is skipped so that there will not be any further recurrent
        activation.  The next external (i.e., afferent or feedback)
        event will then start the counter over again.""")

    continuous_learning = param.Boolean(default=False, doc="""
        Whether to modify the weights after every settling step.
        If false, waits until settling is completed before doing learning.""")

    precedence = param.Number(0.6)

    post_initialization_weights_output_fns = param.HookList([],doc="""
        If not empty, weights output_fns that will replace the
        existing ones after an initial normalization step.""")

    beginning_of_iteration = param.HookList(default=[],instantiate=False,doc="""
        List of callables to be executed at the beginning of each iteration.""")

    end_of_iteration = param.HookList(default=[],instantiate=False,doc="""
        List of callables to be executed at the end of each iteration.""")


    def __init__(self,**params):
        super(SettlingCFSheet,self).__init__(**params)
        self.__counter_stack=[]
        self.activation_count = 0
        self.new_iteration = True


    def start(self):
        self._normalize_weights(active_units_mask=False)
        if len(self.post_initialization_weights_output_fns)>0:
            for proj in self.in_connections:
                if not isinstance(proj,Projection):
                    self.debug("Skipping non-Projection ")
                else:
                    proj.weights_output_fns=self.post_initialization_weights_output_fns


    def input_event(self,conn,data):
        # On a new afferent input, clear the activity
        if self.new_iteration:
            for f in self.beginning_of_iteration: f()
            self.new_iteration = False
            self.activity *= 0.0
            for proj in self.in_connections:
                proj.activity *= 0.0
            self.mask.reset()
        super(SettlingCFSheet,self).input_event(conn,data)


    ### JABALERT!  There should be some sort of warning when
    ### tsettle times the input delay is larger than the input period.
    ### Right now it seems to do strange things in that case (does it
    ### settle at all after the first iteration?), but of course that
    ### is arguably an error condition anyway (and should thus be
    ### flagged).
    # CEBALERT: there is at least one bug in here for tsettle==0: see
    # CB/JAB email "LISSOM tsettle question", 2010/03/22.
    def process_current_time(self):
        """
        Pass the accumulated stimulation through self.output_fns and
        send it out on the default output port.
        """
        if self.new_input:
            self.new_input = False

            if self.activation_count == self.mask_init_time:
                self.mask.calculate()

            if self.tsettle == 0:
                # Special case: behave just like a CFSheet
                self.activate()
                self.learn()

            elif self.activation_count == self.tsettle:
                # Once we have been activated the required number of times
                # (determined by tsettle), reset various counters, learn
                # if appropriate, and avoid further activation until an
                # external event arrives.
                for f in self.end_of_iteration: f()

                self.activation_count = 0
                self.new_iteration = True # used by input_event when it is called
                if (self.plastic and not self.continuous_learning):
                    self.learn()
            else:
                self.activate()
                self.activation_count += 1
                if (self.plastic and self.continuous_learning):
                   self.learn()


    # print the weights of a unit
    def printwts(self,x,y):
        for proj in self.in_connections:
            print proj.name, x, y
            print proj.cfs[x,y].weights


    def state_push(self,**args):
        super(SettlingCFSheet,self).state_push(**args)
        self.__counter_stack.append((self.activation_count,self.new_iteration))


    def state_pop(self,**args):
        super(SettlingCFSheet,self).state_pop(**args)
        self.activation_count,self.new_iteration=self.__counter_stack.pop()

    def send_output(self,src_port=None,data=None):
        """Send some data out to all connections on the given src_port."""

        out_conns_on_src_port = [conn for conn in self.out_connections
                                 if self._port_match(conn.src_port,[src_port])]

        for conn in out_conns_on_src_port:
            if self.strict_tsettle != None:
               if self.activation_count < self.strict_tsettle:
                   if len(conn.dest_port)>2 and conn.dest_port[2] == 'Afferent':
                       continue
            self.verbose("Sending output on src_port %s via connection %s to %s" %
                         (str(src_port), conn.name, conn.dest.name))
            e=EPConnectionEvent(self.simulation.convert_to_time_type(conn.delay)+self.simulation.time(),conn,data)
            self.simulation.enqueue_event(e)




_public = list(set([_k for _k,_v in locals().items() if isinstance(_v,type) and issubclass(_v,Sheet)]))
_public += [
    "compute_joint_norm_totals",
    "BoundingBox",
    "activity_type",
]

# Automatically discover all .py files in this directory.
import os,fnmatch
__all__ = _public + [f.split('.py')[0] for f in os.listdir(__path__[0]) if fnmatch.fnmatch(f,'[!._]*.py')]
del f,os,fnmatch

# By default, avoid loading modules that rely on external libraries
# that might not be present on this system.
__all__.remove('ptztracker')
