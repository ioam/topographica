"""
LISSOM and related sheet classes.
"""

from numpy import zeros,ones
import copy

import param

import topo

from topo.base.projection import Projection
from topo.base.sheet import activity_type
from topo.base.simulation import EPConnectionEvent
from topo.transferfn import PiecewiseLinear
from topo.sheet import JointNormalizingCFSheet


class LISSOM(JointNormalizingCFSheet):
    """
    A Sheet class implementing the LISSOM algorithm
    (Sirosh and Miikkulainen, Biological Cybernetics 71:66-78, 1994).

    A LISSOM sheet is a JointNormalizingCFSheet slightly modified to
    enforce a fixed number of settling steps.  Settling is controlled
    by the tsettle parameter; once that number of settling steps has
    been reached, an external input is required before the sheet will
    activate again.
    """

    strict_tsettle = param.Parameter(default = None,doc="""
        If non-None, delay sending output until activation_count reaches this value.""")

    mask_init_time=param.Integer(default=5,bounds=(0,None),doc="""
        Determines when a new mask is initialized in each new iteration.

        The mask is reset whenever new input comes in.  Once the
        activation_count (see tsettle) reaches mask_init_time, the mask
        is initialized to reflect the current activity profile.""")

    tsettle=param.Integer(default=8,bounds=(0,None),doc="""
        Number of times to activate the LISSOM sheet for each external input event.

        A counter is incremented each time an input is received from any
        source, and once the counter reaches tsettle, the last activation
        step is skipped so that there will not be any further recurrent
        activation.  The next external (i.e., afferent or feedback)
        event will then start the counter over again.""")

    continuous_learning = param.Boolean(default=False, doc="""
        Whether to modify the weights after every settling step.
        If false, waits until settling is completed before doing learning.""")

    output_fns = param.HookList(default=[PiecewiseLinear(lower_bound=0.1,upper_bound=0.65)])

    precedence = param.Number(0.6)

    post_initialization_weights_output_fns = param.HookList([],doc="""
        If not empty, weights output_fns that will replace the
        existing ones after an initial normalization step.""")

    beginning_of_iteration = param.HookList(default=[],instantiate=False,doc="""
        List of callables to be executed at the beginning of each iteration.""")

    end_of_iteration = param.HookList(default=[],instantiate=False,doc="""
        List of callables to be executed at the end of each iteration.""")


    def __init__(self,**params):
        super(LISSOM,self).__init__(**params)
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
        super(LISSOM,self).input_event(conn,data)


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
        super(LISSOM,self).state_push(**args)
        self.__counter_stack.append((self.activation_count,self.new_iteration))


    def state_pop(self,**args):
        super(LISSOM,self).state_pop(**args)
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


class JointScaling(LISSOM):
    """
    LISSOM sheet extended to allow joint auto-scaling of Afferent input projections.

    An exponentially weighted average is used to calculate the average
    joint activity across all jointly-normalized afferent projections.
    This average is then used to calculate a scaling factor for the
    current afferent activity and for the afferent learning rate.

    The target average activity for the afferent projections depends
    on the statistics of the input; if units are activated more often
    (e.g. the number of Gaussian patterns on the retina during each
    iteration is increased) the target average activity should be
    larger in order to maintain a constant average response to similar
    inputs in V1. The target activity for learning rate scaling does
    not need to change, because the learning rate should be scaled
    regardless of what causes the change in average activity.
    """
    # ALERT: Should probably be extended to jointly scale different
    # groups of projections. Currently only works for the joint
    # scaling of projections named "Afferent", grouped together by
    # JointNormalize in dest_port.

    target = param.Number(default=0.045, doc="""
        Target average activity for jointly scaled projections.""")

    # JABALERT: I cannot parse the docstring; is it an activity or a learning rate?
    target_lr = param.Number(default=0.045, doc="""
        Target average activity for jointly scaled projections.

        Used for calculating a learning rate scaling factor.""")

    smoothing = param.Number(default=0.999, doc="""
        Influence of previous activity, relative to current, for computing the average.""")

    apply_scaling = param.Boolean(default=True, doc="""Whether to apply the scaling factors.""")

    precedence = param.Number(0.65)


    def __init__(self,**params):
        super(JointScaling,self).__init__(**params)
        self.x_avg=None
        self.sf=None
        self.lr_sf=None
        self.scaled_x_avg=None
        self.__current_state_stack=[]

    def calculate_joint_sf(self, joint_total):
        """
        Calculate current scaling factors based on the target and previous average joint activities.

        Keeps track of the scaled average for debugging. Could be
        overridden by a subclass to calculate the factors differently.
        """

        if self.plastic:
            self.sf *=0.0
            self.lr_sf *=0.0
            self.sf += self.target/self.x_avg
            self.lr_sf += self.target_lr/self.x_avg
            self.x_avg = (1.0-self.smoothing)*joint_total + self.smoothing*self.x_avg
            self.scaled_x_avg = (1.0-self.smoothing)*joint_total*self.sf + self.smoothing*self.scaled_x_avg


    def do_joint_scaling(self):
        """
        Scale jointly normalized projections together.

        Assumes that the projections to be jointly scaled are those
        that are being jointly normalized.  Calculates the joint total
        of the grouped projections, and uses this to calculate the
        scaling factor.
        """
        joint_total = zeros(self.shape, activity_type)

        for key,projlist in self._grouped_in_projections('JointNormalize'):
            if key is not None:
                if key =='Afferent':
                    for proj in projlist:
                        joint_total += proj.activity
                    self.calculate_joint_sf(joint_total)
                    if self.apply_scaling:
                        for proj in projlist:
                            proj.activity *= self.sf
                            if hasattr(proj.learning_fn,'learning_rate_scaling_factor'):
                                proj.learning_fn.update_scaling_factor(self.lr_sf)
                            else:
                                raise ValueError("Projections to be joint scaled must have a learning_fn that supports scaling, such as CFPLF_PluginScaled")

                else:
                    raise ValueError("Only Afferent scaling currently supported")


    def activate(self):
        """
        Compute appropriate scaling factors, apply them, and collect resulting activity.

        Scaling factors are first computed for each set of jointly
        normalized projections, and the resulting activity patterns
        are then scaled.  Then the activity is collected from each
        projection, combined to calculate the activity for this sheet,
        and the result is sent out.
        """

        self.activity *= 0.0

        if self.x_avg is None:
            self.x_avg=self.target*ones(self.shape, activity_type)
        if self.scaled_x_avg is None:
            self.scaled_x_avg=self.target*ones(self.shape, activity_type)
        if self.sf is None:
            self.sf=ones(self.shape, activity_type)
        if self.lr_sf is None:
            self.lr_sf=ones(self.shape, activity_type)

        #Afferent projections are only activated once at the beginning of each iteration
        #therefore we only scale the projection activity and learning rate once.
        if self.activation_count == 0:
            self.do_joint_scaling()

        for proj in self.in_connections:
            self.activity += proj.activity

        if self.apply_output_fns:
            for of in self.output_fns:
                of(self.activity)

        self.send_output(src_port='Activity',data=self.activity)


    def state_push(self,**args):
        super(JointScaling,self).state_push(**args)
        self.__current_state_stack.append((copy.copy(self.x_avg),copy.copy(self.scaled_x_avg),
                                           copy.copy(self.sf), copy.copy(self.lr_sf)))


    def state_pop(self,**args):
        super(JointScaling,self).state_pop(**args)
        self.x_avg,self.scaled_x_avg, self.sf, self.lr_sf=self.__current_state_stack.pop()



def schedule_events(sheet_str="topo.sim['V1']",st=0.5,aff_name="Afferent",
                    ids=1.0,ars=1.0,increase_inhibition=False):
    """
    Convenience function for scheduling a default set of events
    typically used with a LISSOM sheet.  The parameters used
    are the defaults from Miikkulainen, Bednar, Choe, and Sirosh
    (2005), Computational Maps in the Visual Cortex, Springer.

    Note that Miikulainen 2005 specifies only one output_fn for the
    LISSOM sheet; where these scheduled actions operate on an
    output_fn, they do so only on the first output_fn in the sheet's
    list of output_fns.

    Installs afferent learning rate changes for any projection whose
    name contains the keyword specified by aff_name (typically
    "Afferent").

    The st argument determines the timescale relative to a
    20000-iteration simulation, and results in the default
    10000-iteration simulation for the default st=0.5.

    The ids argument specifies the input density scale, i.e. how much
    input there is at each iteration, on average, relative to the
    default.  The ars argument specifies how much to scale the
    afferent learning rate, if necessary.

    If increase_inhibition is true, gradually increases the strength
    of the inhibitory connection, typically used for natural image
    simulations.
    """

    # Allow sheet.BoundingBox calls (below) after reloading a snapshot
    topo.sim.startup_commands.append("from topo import sheet")

    # Lateral excitatory bounds changes
    # Convenience variable: excitatory projection
    LE=sheet_str+".projections()['LateralExcitatory']"

    topo.sim.schedule_command(  200*st,LE+'.change_bounds(sheet.BoundingBox(radius=0.06250))')
    topo.sim.schedule_command(  500*st,LE+'.change_bounds(sheet.BoundingBox(radius=0.04375))')
    topo.sim.schedule_command( 1000*st,LE+'.change_bounds(sheet.BoundingBox(radius=0.03500))')
    topo.sim.schedule_command( 2000*st,LE+'.change_bounds(sheet.BoundingBox(radius=0.02800))')
    topo.sim.schedule_command( 3000*st,LE+'.change_bounds(sheet.BoundingBox(radius=0.02240))')
    topo.sim.schedule_command( 4000*st,LE+'.change_bounds(sheet.BoundingBox(radius=0.01344))')
    topo.sim.schedule_command( 5000*st,LE+'.change_bounds(sheet.BoundingBox(radius=0.00806))')
    topo.sim.schedule_command( 6500*st,LE+'.change_bounds(sheet.BoundingBox(radius=0.00484))')
    topo.sim.schedule_command( 8000*st,LE+'.change_bounds(sheet.BoundingBox(radius=0.00290))')
    topo.sim.schedule_command(20000*st,LE+'.change_bounds(sheet.BoundingBox(radius=0.00174))')

    # Lateral excitatory learning rate changes
    idss=("" if ids==1 else "/%3.1f"%ids)
    estr='%s.learning_rate=%%s%s*%s.n_units'%(LE,idss,LE)

    topo.sim.schedule_command(  200*st,estr%'0.12168')
    topo.sim.schedule_command(  500*st,estr%'0.06084')
    topo.sim.schedule_command( 1000*st,estr%'0.06084')
    topo.sim.schedule_command( 2000*st,estr%'0.06084')
    topo.sim.schedule_command( 3000*st,estr%'0.06084')
    topo.sim.schedule_command( 4000*st,estr%'0.06084')
    topo.sim.schedule_command( 5000*st,estr%'0.06084')
    topo.sim.schedule_command( 6500*st,estr%'0.06084')
    topo.sim.schedule_command( 8000*st,estr%'0.06084')
    topo.sim.schedule_command(20000*st,estr%'0.06084')

    ### Lateral inhibitory learning rate and strength changes
    if increase_inhibition:
        LI=sheet_str+".projections()['LateralInhibitory']"
        istr='%s.learning_rate=%%s%s'%(LI,idss)

        topo.sim.schedule_command( 1000*st,istr%'1.80873/5.0*2.0')
        topo.sim.schedule_command( 2000*st,istr%'1.80873/5.0*3.0')
        topo.sim.schedule_command( 5000*st,istr%'1.80873/5.0*5.0')

        topo.sim.schedule_command( 1000*st,LI+'.strength=-2.2')
        topo.sim.schedule_command( 2000*st,LI+'.strength=-2.6')


    # Afferent learning rate changes (for every Projection named Afferent)
    sheet_=eval(sheet_str)
    projs = [pn for pn in sheet_.projections().keys() if pn.count(aff_name)]
    num_aff=len(projs)
    arss="" if ars==1.0 else "*%3.1f"%ars
    for pn in projs:
        ps="%s.projections()['%s'].learning_rate=%%s%s%s" % \
            (sheet_str,pn,idss if num_aff==1 else "%s/%d"%(idss,num_aff),arss)
        topo.sim.schedule_command(  500*st,ps%('0.6850'))
        topo.sim.schedule_command( 2000*st,ps%('0.5480'))
        topo.sim.schedule_command( 4000*st,ps%('0.4110'))
        topo.sim.schedule_command(20000*st,ps%('0.2055'))

    # Activation function threshold changes
    bstr = sheet_str+'.output_fns[0].lower_bound=%5.3f;'+\
           sheet_str+'.output_fns[0].upper_bound=%5.3f'
    lbi=sheet_.output_fns[0].lower_bound
    ubi=sheet_.output_fns[0].upper_bound

    topo.sim.schedule_command(  200*st,bstr%(lbi+0.01,ubi+0.01))
    topo.sim.schedule_command(  500*st,bstr%(lbi+0.02,ubi+0.02))
    topo.sim.schedule_command( 1000*st,bstr%(lbi+0.05,ubi+0.03))
    topo.sim.schedule_command( 2000*st,bstr%(lbi+0.08,ubi+0.05))
    topo.sim.schedule_command( 3000*st,bstr%(lbi+0.10,ubi+0.08))
    topo.sim.schedule_command( 4000*st,bstr%(lbi+0.10,ubi+0.11))
    topo.sim.schedule_command( 5000*st,bstr%(lbi+0.11,ubi+0.14))
    topo.sim.schedule_command( 6500*st,bstr%(lbi+0.12,ubi+0.17))
    topo.sim.schedule_command( 8000*st,bstr%(lbi+0.13,ubi+0.20))
    topo.sim.schedule_command(20000*st,bstr%(lbi+0.14,ubi+0.23))

    # Just to get more progress reports
    topo.sim.schedule_command(12000*st,'pass')
    topo.sim.schedule_command(16000*st,'pass')

    # Settling steps changes
    topo.sim.schedule_command( 2000*st,sheet_str+'.tsettle=10')
    topo.sim.schedule_command( 5000*st,sheet_str+'.tsettle=11')
    topo.sim.schedule_command( 6500*st,sheet_str+'.tsettle=12')
    topo.sim.schedule_command( 8000*st,sheet_str+'.tsettle=13')


__all__ = [
    "LISSOM",
    "JointScaling",
    "schedule_events",
]
