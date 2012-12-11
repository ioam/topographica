"""
GeneratorSheet: a sheet with a pattern generator.
"""
__version__='$Revision: 7629 $'


import param
from topo.base.sheet import Sheet
from topo.base.patterngenerator import PatternGenerator,Constant
from topo.base.simulation import FunctionEvent, PeriodicEventSequence


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

        # JABALERT: What does the [:] achieve here?  Copying the
        # values, instead of the pointer to the array?  Is that
        # guaranteed?
        self.activity[:] = self.input_generator()

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
