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
from topo.misc.generatorsheet import GeneratorSheet

# Imported here for ease of access by users
from topo.base.boundingregion import BoundingBox  # pyflakes:ignore (API import)
from topo.base.sheet import activity_type  # pyflakes:ignore (API import)

import numpy

import topo

import param

from topo.base.cf import CFIter
from topo.base.projection import Projection
from topo.base.simulation import FunctionEvent, PeriodicEventSequence


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
        for key,projlist in self._grouped_in_projections('JointNormalize'):
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



_public = list(set([_k for _k,_v in locals().items() if isinstance(_v,type) and issubclass(_v,Sheet)]))
_public += [
    "compute_joint_norm_totals",
    "BoundingBox",
    "ProjectionSheet",
    "activity_type",
]

# Automatically discover all .py files in this directory.
import os,fnmatch
__all__ = _public + [f.split('.py')[0] for f in os.listdir(__path__[0]) if fnmatch.fnmatch(f,'[!._]*.py')]
del f,os,fnmatch

# By default, avoid loading modules that rely on external libraries
# that might not be present on this system.
__all__.remove('ptztracker')
