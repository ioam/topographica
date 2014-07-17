"""
GeneratorSheet: a sheet with a pattern generator.
"""


import param
from topo.base.sheet import Sheet
from topo.base.patterngenerator import PatternGenerator,Constant
from topo.base.simulation import FunctionEvent, PeriodicEventSequence

import numpy as np


# JLALERT: This sheet should have override_plasticity_state/restore_plasticity_state
# functions that call override_plasticity_state/restore_plasticty_state on the
# sheet output_fn and input_generator output_fn.
class GeneratorSheet(Sheet):
    """
    Sheet for generating a series of 2D patterns.

    Typically generates the patterns by choosing parameters from a
    random distribution, but can use any mechanism.
    """

    src_ports=['Activity']

    period = param.Number(default=1,bounds=(0,None), inclusive_bounds=(False, True), constant=True, doc=
        "Delay (in Simulation time) between generating new input patterns.")

    phase  = param.Number(default=0.05,doc=
        """
        Delay after the start of the Simulation (at time zero) before
        generating an input pattern.  For a clocked, feedforward simulation,
        one would typically want to use a small nonzero phase and use delays less
        than the user-visible step size (typically 1.0), so that inputs are
        generated and processed before this step is complete.
        """)

    input_generator = param.ClassSelector(PatternGenerator,default=Constant(),
        doc="""Specifies a particular PatternGenerator type to use when creating patterns.""")


    def __init__(self,**params):
        super(GeneratorSheet,self).__init__(**params)
        self.input_generator_stack = []
        self.set_input_generator(self.input_generator)


    def set_input_generator(self,new_ig,push_existing=False):
        """
        Set the input_generator, overwriting the existing one by default.

        If push_existing is false, the existing input_generator is
        discarded permanently.  Otherwise, the existing one is put
        onto a stack, and can later be restored by calling
        pop_input_generator.
        """

        if push_existing:
            self.push_input_generator()

        # CEBALERT: replaces any bounds specified for the
        # PatternGenerator with this sheet's own bounds. When
        # PatternGenerators can draw patterns into supplied
        # boundingboxes, should remove this.
        new_ig.set_matrix_dimensions(self.bounds, self.xdensity, self.ydensity)
        self.input_generator = new_ig


    def push_input_generator(self):
        """Push the current input_generator onto a stack for future retrieval."""
        self.input_generator_stack.append(self.input_generator)

        # CEBALERT: would be better to reorganize code so that
        # push_input_generator must be supplied with a new generator.
        # CEBALERT: presumably we can remove this import.
        from topo.base.patterngenerator import Constant
        self.set_input_generator(Constant())


    def pop_input_generator(self):
        """
        Discard the current input_generator, and retrieve the previous one from the stack.

        Warns if no input_generator is available on the stack.
        """
        if len(self.input_generator_stack) >= 1:
            self.set_input_generator(self.input_generator_stack.pop())
        else:
            self.warning('There is no previous input generator to restore.')

    def generate(self):
        """
        Generate the output and send it out the Activity port.
        """
        self.verbose("Generating a new pattern")

        try:
            ac = self.input_generator()
        except StopIteration:
            # Note that a generator may raise an exception StopIteration if it runs out of patterns.
            # Example is if the patterns are files that are loaded sequentially and are not re-used (e.g. the constructors
            # are  discarded to save memory).
            self.warning('Pattern generator {0} returned None. Unable to generate Activity pattern.'.format(self.input_generator.name))
        else:
            self.activity[:] = ac

            if self.apply_output_fns:
                for of in self.output_fns:
                    of(self.activity)
            self.send_output(src_port='Activity',data=self.activity)


    def start(self):
        assert self.simulation

        if self.period > 0:
            # if it has a positive period, then schedule a repeating event to trigger it
            e=FunctionEvent(0,self.generate)
            now = self.simulation.time()
            self.simulation.enqueue_event(PeriodicEventSequence(now+self.simulation.convert_to_time_type(self.phase),self.simulation.convert_to_time_type(self.period),[e]))

    def input_event(self,conn,data):
        raise NotImplementedError




class ChannelGeneratorSheet(GeneratorSheet):
    """
    A GeneratorSheet that handles input patterns with multiple simultaneous channels.

    Accepts either a single-channel or an NChannel input_generator.  If the
    input_generator stores separate channel patterns, it
    is used as-is; if other (single-channel) PatternGenerators are used, the Class behaves
    like a normal GeneratorSheet.

    When a pattern is generated, the average of the channels is sent out on the Activity port as 
    usual for a GeneratorSheet, and channel activities are sent out on the Activity0,
    Activity1, ..., ActivityN-1 ports.  Thus this class can be used
    just like GeneratorSheet, but with optional color channels available, too.


    If the input_generator is NChannel, this GeneratorSheet will handle the separate channels and 
    create the specific output ports. If the input_generator is single-channel (eg, a monochrome image)
    then this GeneratorSheet will behave as a normal non-NChannel GeneratorSheet.
    """

    constant_mean_total_channels_output = param.Number(default=None,doc="""
        If set, it enforces the average of the mean channel values to be fixed. Eg,
        M = ( activity0+activity1+...+activity(N-1) ).mean() / N = constant_mean_total_channels_output""")

    channel_output_fns = param.Dict(default={},doc="""
        Dictionary with arrays of channel-specific output functions: eg, {0:[fnc1, fnc2],3:[fnc3]}.
        The dictionary isn't required to specify every channel, but rather only those required.""")


    def __init__(self,**params):
        # We need to setup our datastructures before calling super.init, as that will automatically
        # call set_input_generator
        self._channel_data = []
        super(ChannelGeneratorSheet,self).__init__(**params)


    def set_input_generator(self,new_ig,push_existing=False):
        """If single-channel generators are used, the Class reverts to a simple GeneratorSheet behavior.
           If NChannel inputs are used, it will update the number of channels of the ChannelGeneratorSheet
           to match those of the input. If the number of channels doesn't change, there's no need to reset."""

        num_channels = new_ig.num_channels()

        if( num_channels>1 ):
            if( num_channels != len(self._channel_data) ):
                self.src_ports = ['Activity']
                self._channel_data = []

                for i in range(num_channels):
                    # TODO: in order to add support for generic naming of Activity ports, it's necessary
                    #       to implement a .get_channel_names method.  Calling .channels() and inspecting
                    #       the returned dictionary in fact could change the state of the input generator.
                    self.src_ports.append( 'Activity'+str(i) )
                    self._channel_data.append(self.activity.copy())

        else: # monochrome
            # Reset channels to match single-channel inputs.
            self.src_ports = ['Activity']
            self._channel_data = []

        super(ChannelGeneratorSheet,self).set_input_generator(new_ig,push_existing=push_existing)

        
    def generate(self):
        """
        Works as in the superclass, but also generates NChannel output and sends
        it out on the Activity0, Activity1, ..., ActivityN ports.
        """

        try:
            channels_dict = self.input_generator.channels()
        except StopIteration:
            # Note that a generator may raise an exception StopIteration if it runs out of patterns.
            # Example is if the patterns are files that are loaded sequentially and are not re-used (e.g. the constructors
            # are  discarded to save memory).
            self.warning('Pattern generator {0} returned None. Unable to generate Activity pattern.'.format(self.input_generator.name))
        else:
            self.activity[:] = channels_dict.items()[0][1]

            if self.apply_output_fns:
                for of in self.output_fns:
                    of(self.activity)
            self.send_output(src_port='Activity',data=self.activity)



            ## These loops are safe: if the pattern doesn't provide further channels, self._channel_data = []
            for i in range(len(self._channel_data)):
                self._channel_data[i][:] = channels_dict.items()[i+1][1]


            if self.apply_output_fns:
                ## Default output_fns are applied to all channels
                for f in self.output_fns:
                    for i in range(len(self._channel_data)):
                        f( self._channel_data[i] )

               # Channel specific output functions, defined as a dictionary {chn_number:[functions]}
                for i in range(len(self._channel_data)):
                    if(i in self.channel_output_fns):
                        for f in self.channel_output_fns[i]:
                            f( self._channel_data[i] )


            if self.constant_mean_total_channels_output is not None:
                M = sum(act for act in self._channel_data).mean()/len(self._channel_data)
                if M>0:
                    p = self.constant_mean_total_channels_output/M
                    for act in self._channel_data:
                        act *= p
                        np.minimum(act,1.0,act)


            for i in range(len(self._channel_data)):
                self.send_output(src_port=self.src_ports[i+1], data=self._channel_data[i])




