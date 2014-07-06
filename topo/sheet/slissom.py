"""
The SLISSOM class.
"""

from math import exp

import numpy as np
import param

from topo.command.pylabplot import vectorplot, matrixplot

from topo.sheet import SettlingCFSheet
from topo.transferfn import PiecewiseLinear




activity_type = np.float32

class SLISSOM(SettlingCFSheet):
    """
    A Sheet class implementing the SLISSOM algorithm
    (Choe and Miikkulainen, Neurocomputing 21:139-157, 1998).

    A SLISSOM sheet is a SettlingCFSheet sheet extended to include spiking
    neurons using dynamic synapses.
    """

    # configurable parameters
    threshold = param.Number(default=0.3,bounds=(0,None), doc="Baseline threshold")

    threshold_decay_rate = param.Number(default=0.01,bounds=(0,None),
        doc="Dynamic threshold decay rate")

    absolute_refractory = param.Number(default=1.0,bounds=(0,None),
        doc="Absolute refractory period")

    dynamic_threshold_init = param.Number(default=2.0,bounds=(0,None),
        doc="Initial value for dynamic threshold when spike occurs")

    spike_amplitude = param.Number(default=1.0,bounds=(0,None),
        doc="Amplitude of spike at the moment of spiking")

    reset_on_new_iteration = param.Boolean(default=False,
        doc="Reset activity and projection activity when new iteration starts")

    noise_rate = param.Number(default=0.0,bounds=(0,1.0),
        doc="Noise added to the on-going activity")

    output_fns = param.HookList(default=[PiecewiseLinear(lower_bound=0.1,upper_bound=0.65)])

    # logging facility for debugging
    trace_coords = param.List(default=[],
        doc="List of coord(s) of membrane potential(s) to track over time")

    trace_n = param.Number(default=400,bounds=(1,None),
        doc="Number of steps to track neuron's membrane potential")

    # matrices and vectors for internal use
    dynamic_threshold = None
    spike = None
    spike_history= None
    membrane_potential = None
    membrane_potential_trace = None
    trace_count = 0

    def __init__(self,**params):
        """
        SLISSOM-specific init, where dynamic threshold stuff
        gets initialized.
        """
        super(SLISSOM,self).__init__(**params)
        self.dynamic_threshold = \
            np.zeros(self.activity.shape).astype(activity_type)
        self.spike = np.zeros(self.activity.shape)
        self.spike_history = np.zeros(self.activity.shape)
        self.membrane_potential = \
            np.zeros(self.activity.shape).astype(activity_type)

        num_traces = len(self.trace_coords)
        self.membrane_potential_trace = \
            np.zeros((num_traces,self.trace_n)).astype(activity_type)

    def activate(self):
        """
        For now, this is the same as the parent's activate(), plus
        fixed+dynamic thresholding. Overloading was necessary to
        avoid self.send_output() being invoked before thresholding.
        This function also updates and maintains internal values such as
        membrane_potential, spike, etc.
        """
        self.activity *= 0.0

        for proj in self.in_connections:
            self.activity += proj.activity

        if self.apply_output_fns:
            for of in self.output_fns:
                of(self.activity)

        # Add noise, based on the noise_rate.
        if self.noise_rate > 0.0:
            self.activity = self.activity * (1.0-self.noise_rate) \
                + np.random.random(self.activity.shape) * self.noise_rate

        # Thresholding: baseline + dynamic threshold + absolute refractory
        # period
        rows,cols = self.activity.shape

        for r in xrange(rows):
            for c in xrange(cols):

                thresh = self.threshold + self.dynamic_threshold[r,c]

                # Calculate membrane potential
                self.membrane_potential[r,c] = self.activity[r,c] - thresh

                if (self.activity[r,c] > thresh and self.spike_history[r,c]<=0):
                    self.activity[r,c] = self.spike_amplitude
                    self.dynamic_threshold[r,c] = self.dynamic_threshold_init
                    # set absolute refractory period for "next" timestep
                    # (hence the "-1")
                    self.spike_history[r,c] = self.absolute_refractory-1.0
                else:
                    self.activity[r,c] = 0.0
                    self.dynamic_threshold[r,c] = self.dynamic_threshold[r,c] * exp(-(self.threshold_decay_rate))
                    self.spike_history[r,c] -= 1.0

                # Append spike to the membrane potential
                self.membrane_potential[r,c] += self.activity[r,c]

        self._update_trace()
        self.send_output(src_port='Activity',data=self.activity)

    def input_event(self,conn,data):
        """
        SLISSOM-specific input_event handeling:
        On a new afferent input, DO NOT clear the activity matrix unless
        reset_on_new_iteration is True.
        """
        if self.new_iteration and self.reset_on_new_iteration:
            self.new_iteration = False
            self.activity *= 0.0
            for proj in self.in_connections:
                proj.activity *= 0.0
            self.mask.reset()
        super(SettlingCFSheet,self).input_event(conn,data)

    def plot_trace(self):
        """
        Plot membrane potential trace of the unit designated by the
        trace_coords list. This plot has trace_n data points.
        """
        trace_offset=0
        for trace in self.membrane_potential_trace:
            vectorplot(trace+trace_offset,style="b-")
            vectorplot(trace+trace_offset,style="rx")
            trace_offset += 3

    def vectorplot_trace(self):
        """
        Plot membrane potential trace of the unit designated by the
        trace_coords list. This plot has trace_n data points.
        This method simply calls plot_trace().
        """
        self.plot_trace()

    def matrixplot_trace(self):
        """
        Matrixplot membrane potential trace of the unit designated by the
        trace_coords list.
        """
        matrixplot(self.membrane_potential_trace,aspect=40)

    def _update_trace(self):
        """
        Update membrane potential trace for sheet coordinate (x,y).
        """

        trace_id=0

        for coord in self.trace_coords:
            (trace_r, trace_c) = self.sheet2matrix(coord[0],coord[1])
            self.membrane_potential_trace[trace_id][self.trace_count]=\
                 self.membrane_potential[trace_r,trace_c]
            trace_id += 1

        self.trace_count = (self.trace_count+1)%self.trace_n


__all__ = [
    "SLISSOM",
]
