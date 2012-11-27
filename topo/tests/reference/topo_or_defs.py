### import to _or_ reference simulations


def half_odd_array(r):
    """Return r that ends in .5"""
    int_width = int(2*r)
    # force odd width
    if int_width%2==0:
        int_width+=1
    new_r = int_width/2.0
    assert new_r-0.5==int(new_r)
    return new_r


def initialize_variables(BaseRN,BaseN):

    ############################################################
    # Variables that can be overridden & written into param file

    # force radii to end in .5, giving odd weights matrices with
    # exactly 2xradius=matrix_width

    # (could instead maybe set topographica's autosize_mask to false
    # and set the mask sizes with the exact radii...)
    rf_radius=half_odd_array(max(1.5,BaseRN/4.0+0.5))
    inh_rad=half_odd_array(max(2.5,BaseN/4.0-1.0))
    exc_rad=half_odd_array(max(2.5,BaseN/10.0))
    ############################################################


    rf_radius_scale=6.5/rf_radius
    min_exc_rad=half_odd_array(max(1.5,BaseN/44.0))

    area_scale=1.0
    #num_eyes=1

    gammaexc=0.9
    gammainh=0.9

    delta_i=0.1
    beta_i=delta_i+0.55

    randomness = 0.0

    xsigma=7.0/rf_radius_scale
    ysigma=1.5/rf_radius_scale
    scale_input=1.0

    retina_edge_buffer=rf_radius-0.5+(randomness*BaseRN*area_scale/2)
    RN=BaseRN*area_scale+2*retina_edge_buffer

    # should be divided by n_aff_inputs
    acs=6.5*6.5/rf_radius/rf_radius

    ecs=19.5*19.5/exc_rad/exc_rad
    ics=47.5*47.5/inh_rad/inh_rad
    alpha_input=0.007*acs
    alpha_exc=0.002*ecs
    alpha_inh=0.00025*ics

    tsettle=9
    ############################################################


    return locals()


def add_scheduled_outputfn_changes(sim):
    ### delta/beta changes
    #
    sim.schedule_command(  199, 'topo.sim["Primary"].output_fns[0].lower_bound=delta_i+0.01; topo.sim["Primary"].output_fns[0].upper_bound=beta_i+0.01')
    sim.schedule_command(  499, 'topo.sim["Primary"].output_fns[0].lower_bound=delta_i+0.02; topo.sim["Primary"].output_fns[0].upper_bound=beta_i+0.02')
    sim.schedule_command(  999, 'topo.sim["Primary"].output_fns[0].lower_bound=delta_i+0.05; topo.sim["Primary"].output_fns[0].upper_bound=beta_i+0.03')
    sim.schedule_command( 1999, 'topo.sim["Primary"].output_fns[0].lower_bound=delta_i+0.08; topo.sim["Primary"].output_fns[0].upper_bound=beta_i+0.05')
    sim.schedule_command( 2999, 'topo.sim["Primary"].output_fns[0].lower_bound=delta_i+0.10; topo.sim["Primary"].output_fns[0].upper_bound=beta_i+0.08')
    sim.schedule_command( 3999,                                                    'topo.sim["Primary"].output_fns[0].upper_bound=beta_i+0.11')
    sim.schedule_command( 4999, 'topo.sim["Primary"].output_fns[0].lower_bound=delta_i+0.11; topo.sim["Primary"].output_fns[0].upper_bound=beta_i+0.14')
    sim.schedule_command( 6499, 'topo.sim["Primary"].output_fns[0].lower_bound=delta_i+0.12; topo.sim["Primary"].output_fns[0].upper_bound=beta_i+0.17')
    sim.schedule_command( 7999, 'topo.sim["Primary"].output_fns[0].lower_bound=delta_i+0.13; topo.sim["Primary"].output_fns[0].upper_bound=beta_i+0.20')
    sim.schedule_command(19999, 'topo.sim["Primary"].output_fns[0].lower_bound=delta_i+0.14; topo.sim["Primary"].output_fns[0].upper_bound=beta_i+0.23')

def add_scheduled_tsettle_changes(sim):
    #tsettle changes
    sim.schedule_command( 1999, 'topo.sim["Primary"].tsettle=10')
    sim.schedule_command( 4999, 'topo.sim["Primary"].tsettle=11')
    sim.schedule_command( 6499, 'topo.sim["Primary"].tsettle=12')
    sim.schedule_command( 7999, 'topo.sim["Primary"].tsettle=13')


def add_scheduled_exc_bounds_changes(sim):
    ### Excitatory bounds changes
    #
    # The learning rate is adjusted too because the number of units
    # changes and ecs changes (even if the learning rate is going to
    # be adjusted anyway at this time)

    # Turn off mask autosizing; not sure how it manages to work
    # for creation (i.e. only doesn't match after resizing) - is
    # that a fluke of the initial radii, or does c++ lissom do
    # something different when resizing vs creating, or what?
##     LE = sim['Primary'].projections('LateralExcitatory')
##     LE.initialized=False;LE.autosize_mask=False;LE.initialized=True
##     change_bounds = "LE.cf_shape.size=2.0*round(max(exc_rad,min_exc_rad))/BaseN;LE.change_bounds(BoundingBox(radius=exc_rad/BaseN,min_radius=min_exc_rad/BaseN));LE.learning_rate=alpha_exc*LE.n_units()"


    change_bounds = "LE.change_bounds(BoundingBox(radius=half_odd_array(exc_rad)/BaseN,min_radius=min_exc_rad/BaseN));LE.learning_rate=alpha_exc*LE.n_units"
##     times = [199,499,999,1999,2999,3999,4999,6499,7999,19999]
    e =     [0.6,0.7,0.8, 0.8, 0.8, 0.6, 0.6, 0.6, 0.6,  0.6]

##     for t,i in zip(times,range(times)):
##         sim.schedule_command(t,'exc_rad=half_odd_array(exc_rad*%s);%s'%(e[i],change_bounds))

    sim.schedule_command(199,'exc_rad=exc_rad*%s; %s'%(e[0],change_bounds))
    sim.schedule_command(499,'exc_rad=exc_rad*%s; %s'%(e[1],change_bounds))
    sim.schedule_command(999,'exc_rad=exc_rad*%s; %s'%(e[2],change_bounds))
    sim.schedule_command(1999,'exc_rad=exc_rad*%s; %s'%(e[3],change_bounds))
    sim.schedule_command(2999,'exc_rad=exc_rad*%s; %s'%(e[4],change_bounds))
    sim.schedule_command(3999,'exc_rad=exc_rad*%s; %s'%(e[5],change_bounds))
    sim.schedule_command(4999,'exc_rad=exc_rad*%s; %s'%(e[6],change_bounds))
    sim.schedule_command(6499,'exc_rad=exc_rad*%s; %s'%(e[7],change_bounds))
    sim.schedule_command(7999,'exc_rad=exc_rad*%s; %s'%(e[8],change_bounds))
    sim.schedule_command(19999,'exc_rad=exc_rad*%s; %s'%(e[9],change_bounds))


def add_scheduled_exc_Lrate_changes(sim):
    ### Excitatory learning rate changes
    #
    sim.schedule_command(499,'alpha_exc=0.001*ecs; LE.learning_rate=alpha_exc*LE.n_units')


def add_scheduled_aff_Lrate_changes(sim,pname="Af"):
    ### Afferent learning rate changes
    #
    sim.schedule_command(499,  'alpha_input=0.0050*acs; %s.learning_rate=alpha_input*%s.n_units'%(pname,pname))
    sim.schedule_command(1999, 'alpha_input=0.0040*acs; %s.learning_rate=alpha_input*%s.n_units'%(pname,pname))
    sim.schedule_command(3999, 'alpha_input=0.0030*acs; %s.learning_rate=alpha_input*%s.n_units'%(pname,pname))
    sim.schedule_command(19999,'alpha_input=0.0015*acs; %s.learning_rate=alpha_input*%s.n_units'%(pname,pname))







