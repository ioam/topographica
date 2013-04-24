"""
Specific support for the LISSOM algorithm.
"""

import param
import topo

from topo.sheet import SettlingCFSheet
from topo.transferfn import PiecewiseLinear

# Legacy declaration for backwards compatibility
class LISSOM(SettlingCFSheet):
    output_fns = param.HookList(default=[PiecewiseLinear(lower_bound=0.1,upper_bound=0.65)])


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
    "schedule_events",
]
