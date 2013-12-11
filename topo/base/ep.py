"""
EventProcessor classes.

An EventProcessor is an object that the Simulation is aware of, and can
accept simulation Events. EventProcessors can also generate Events, and
will presumably do some computation as well.  Most EventProcessors
will be in other more specific packages, such as topo.sheet; those
here are the remaining uncategorized EventProcessors.  Any new
EventProcessors classes added to this directory will automatically
become available for any model.
"""

import param

from simulation import EventProcessor,EPConnectionEvent


class PulseGenerator(EventProcessor):
    """
    A simple pulse generator node.

    Produces pulses (scalars) of a fixed amplitude at a fixed
    frequency and phase.  Period and phase are in units of simulation
    time.
    """

    dest_ports=None # Allows connections to come in on any port

    amplitude = param.Number(1.0,doc="The size of the pulse to generate.")

    period    = param.Number(1.0,bounds=(0.0,None),doc=
        "The period with which to repeat the pulse. Must be greater than zero.")

    phase     = param.Number(0.0,doc=
        "The time after starting the simulation to wait before sending the first pulse.")

    def input_event(self,conn,data):
        """On input from self, generate output. Ignore all other inputs."""
        self.verbose("Received event from ",conn.src,'on port',conn.dest_port,'with data',data)
        self.send_output(data=self.amplitude)

    def start(self):
        conn=self.simulation.connect(self.name,self.name,delay=self.period)
        e=EPConnectionEvent(self.simulation.time()+self.simulation.convert_to_time_type(self.phase), conn)
        self.simulation.enqueue_event(e)
        EventProcessor.start(self)


class ThresholdUnit(EventProcessor):
    """
    A simple pulse-accumulator threshold node.  Accumulates incoming
    pulses.  When the accumulated value rises above threshold, it
    generates a pulse of a given amplitude and resets the accumulator
    to zero.
    """

    dest_ports=None # Allows connections to come in on any port

    threshold     = param.Number(default=1.0,doc="The threshold at which to fire.")
    initial_accum = param.Number(default=0.0,doc="The initial accumulator value.")
    amplitude     = param.Number(default=1.0,doc="The size of the pulse to generate.")

    def __init__(self,**params):
        EventProcessor.__init__(self,**params)
        self.accum = self.initial_accum

    def input_event(self,conn,data):
        if conn.dest_port == 'input':
            self.accum += data
            self.verbose("Received ",data,"; accumulator now",self.accum)
            if self.accum > self.threshold:
                self.send_output(data=self.amplitude)
                self.accum = 0
                self.verbose(`self` + ' firing, amplitude = ' + `self.amplitude`)


class SumUnit(EventProcessor):
    """A simple unit that outputs the running sum of input received thus far."""

    dest_ports=None # Allows connections to come in on any port

    def __init__(self,**params):
        super(SumUnit,self).__init__(**params)
        self.value = 0.0

    def input_event(self,conn,data):
        self.value += data
        self.debug("received",data,"from",conn.src,"value =",self.value)

    def process_current_time(self):
        self.debug("process_current_time called, time =",self.simulation.time(),"value =",self.value)
        if self.value:
            self.debug("Sending output:",self.value)
            self.send_output(data=self.value)
            self.value = 0.0

__all__ = list(set(k for k,v in locals().items()
                    if isinstance(v, type)
                    and issubclass(v, EventProcessor)
                    and v is not EventProcessor
                    and not v.__name__.startswith('_')))
