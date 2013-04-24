"""
Sheets first developed for the LISSOM algorithm, but now
used in various other classes.
"""

from numpy import zeros,ones
import copy

import param

import topo

from topo.base.sheet import activity_type
from topo.sheet import SettlingCFSheet

# Legacy declaration for backwards compatibility
LISSOM=SettlingCFSheet

class JointScaling(SettlingCFSheet):
    """
    SettlingCFSheet sheet extended to allow joint auto-scaling of Afferent input projections.

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

    target_lr = param.Number(default=0.045, doc="""
        Target learning rate for jointly scaled projections.

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
    typically used with a LISSOM model sheet.  The parameters used
    are the defaults from Miikkulainen, Bednar, Choe, and Sirosh
    (2005), Computational Maps in the Visual Cortex, Springer.

    Note that Miikulainen 2005 specifies only one output_fn for the
    LISSOM model sheet; where these scheduled actions operate on an
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
    "JointScaling",
    "schedule_events",
]
