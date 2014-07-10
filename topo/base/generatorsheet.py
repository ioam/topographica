"""
GeneratorSheet: a sheet with a pattern generator.
"""


import param
from topo.base.sheet import Sheet
from topo.base.patterngenerator import PatternGenerator,Constant
from topo.base.simulation import FunctionEvent, PeriodicEventSequence

from topo.base.arrayutil import clip_upper


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




class NChannelGeneratorSheet(GeneratorSheet):
    """
    A GeneratorSheet that handles NChannel images.

    Accepts either a single-channel or an NChannel input_generator.  If the
    input_generator stores separate channel patterns, it
    is used as-is; other (monochrome) PatternGenerators are first
    wrapped using ExtendToNChannel to create the NChannel patterns.

    When a pattern is generated, a monochrome version (the average of the channels) is sent out on
    the Activity port as usual for a GeneratorSheet, and channel activities are sent out on the Activity0,
    Activity1, ..., ActivityN-1 ports.  Thus this class can be used
    just like GeneratorSheet, but with optional color channels available, too.


    If the input_generator is NChannel, this GeneratorSheet will handle the separate channels and create the specific output ports. If the input_generator is "monochrome" (ie, not NChannel) then this GeneratorSheet will behave as a normal non-NChannel (monochrome) GeneratorSheet.
    """

    src_ports = ['Activity'] # __init__ sets the other channels as required ['Activity','Activity0','Activity1',...,'ActivityN']

    constant_mean_total_retina_output = param.Number(default=None,doc="""
                         If set, the sheet will rescale its activity to achieve the target 
                         total activity average""")

    channel_output_fns = param.Dict(default={},doc="""
                         Dictionary with arrays of channel-specific output functions:
                         eg, {0:[fnc1, fnc2],3:[fnc3]}""")

    channel_data = []

    def __init__(self,**params):
        super(NChannelGeneratorSheet,self).__init__(**params)


    def set_input_generator(self,new_ig,push_existing=False):
        """Wrap new_ig in ExtendToNChannel if necessary."""

        if hasattr(new_ig,'channel_data'):
            self.src_ports = ['Activity']
            self.channel_data = []

            for i in range(len(new_ig.channel_data)):
                self.src_ports.append( 'Activity'+str(i) )
                self.channel_data.append(self.activity.copy())

        else: # monochrome
            print "WARNING: Using non-NChannel input generator with NChannelGeneratorSheet. This will behave like a simple (single-channel) GeneratorSheet."
            self.src_ports = ['Activity']
            self.channel_data = []

        super(NChannelGeneratorSheet,self).set_input_generator(new_ig,push_existing=push_existing)

        
    def generate(self):
        """
        Works as in the superclass, but also generates RGB output and sends
        it out on the Activity0, Activity1, ..., ActivityN ports.
        """

        super(NChannelGeneratorSheet,self).generate()

        # self.input_generator supports channel_data
        if( hasattr(self.input_generator, 'channel_data') ):
            for i in range(len(self.channel_data)):
                self.channel_data[i][:] = self.input_generator.channel_data[i]

        
        # SPG: whatch out for previous code by CB that might exploit the old system
        # old -- HACKATTACK: abuse of output_fns list to allow one OF to be
        # old -- applied repeatedly to each channel, or one OF per channel!
        # old -- Also note does not apply OF to activity!
        if self.apply_output_fns:
            ## Default output_fns are applied to all channels
            for f in self.output_fns:
                for i in range(len(self.channel_data)):
                    f( self.channel_data[i] )

                # Channel specific output functions, defined as a dictionary {chn_number:[functions]}
                for i in range(len(self.channel_data)):
                    if(i in self.channel_output_fns):
                        for f in self.channel_output_fns[i]:
                            f( self.channel_data[i] )


        if self.constant_mean_total_retina_output is not None:
            M = sum(act for act in self.channel_data).mean()/len(self.channel_data)
            if M>0:
                p = self.constant_mean_total_retina_output/M
                for act in self.channel_data:
                    act *= p
                    # CEBALERT: hidden away OF
                    clip_upper(act,1.0)


        for i in range(len(self.channel_data)):
            self.send_output(src_port=self.src_ports[i+1], data=self.channel_data[i])






