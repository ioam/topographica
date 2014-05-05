"""
Functional GUI tests: run_basic() and run_detailed().
"""

import copy

from numpy import array
from numpy.testing import assert_array_equal


import topo

import topo.tests.functionaltest as ft
from topo.tests.utils import assert_array_not_equal

from nose.tools import nottest

def run_basic():
    """Check that the windows all open ok (i.e. is GUI functioning?)."""
    _initialize()

    s = 'Simulation'
    p = 'Plots'

    menu_paths = [ (s,'Test Pattern'),
                   (s,'Model Editor'),
                   (p,'Activity'),
                   (p,'Connection Fields'),
                   (p,'Projection'),
                   (p,'Projection Activity'),
                   (p,'Preference Maps','Orientation Preference'),
                   (p,'Tuning Curves','Orientation Tuning') ]

    return ft.run([_menu_item_fn(*x) for x in menu_paths],"Running basic GUI tests...")



def run_detailed():
    """Test that more complex GUI actions are working."""
    _initialize()
    tests = [test_cf_coords,test_test_pattern,
             test_projection,test_orientation_tuning] # and so on...
    return ft.run(tests,"Running detailed GUI tests...")



######################################################################
# DETAILED TESTS
######################################################################
@nottest
def test_cf_coords():
    """Check that ConnectionFields window opens with specified coords."""
    cf = topo.guimain['Plots']['Connection Fields'](x=0.125,y=0.250)
    assert cf.x==0.125
    assert cf.y==0.250

@nottest
def test_test_pattern():
    """Check that test pattern window is working."""
    tp = topo.guimain['Simulation']['Test Pattern']()
    act = topo.guimain['Plots']['Activity']()

    tp.gui_set_param('edit_sheet','GS')

    ## Test for state_push bug (simulation not run() before Present pressed)
    assert len(topo.sim.eps_to_start)>0, "test must be run before simulation is run()"
    from topo.pattern import Gaussian
    from topo import numbergen
    topo.sim['GS'].set_input_generator(Gaussian(x=numbergen.UniformRandom()))
    tp.Present()
    topo.sim.run(1)
    act1 = copy.deepcopy(topo.sim['GS'].activity)
    topo.sim.run(2)
    assert_array_not_equal(topo.sim['GS'].activity,act1,"GeneratorSheet no longer generating patterns")
    ##

    tp.gui_set_param('pattern_generator','TwoRectangles')
    from topo.pattern import TwoRectangles
    assert isinstance(tp.pattern_generator,TwoRectangles), "Pattern generator did not change."

    preview = _get_named_plot('GS',tp.plotgroup.plots).view_dict.get('Strength',{})['Activity'].last.data
    two_rectangles = array([[0.,1],[1.,0.]])
    assert_array_equal(preview,two_rectangles,"Incorrect pattern in preview plot.")


    tp.Present()
    gs_view = _get_named_plot('GS',act.plotgroup.plots).view_dict.get('Strength',{})['Activity']
    assert gs_view.metadata.src_name=='GS'
    gs_plot_array = gs_view.last.data
    assert_array_equal(gs_plot_array,two_rectangles,"Incorrect pattern in activity plot after Present.")


    tp.params_frame.gui_set_param('scale',0.5)
    preview = _get_named_plot('GS',tp.plotgroup.plots).view_dict.get('Strength',{})['Activity'].last.data
    assert_array_equal(preview,0.5*two_rectangles,"Changing pattern parameters did not update preview.")


    ### Defaults button

    # first change several more parameters
    initial_preview = tp.plotgroup.plots[0].view_dict.get('Strength',{})['Activity'].last.data

    new_param_values = [#('output_fns','Sigmoid'),
                        ('scale','2')]

    for name,value in new_param_values:
        tp.params_frame.gui_set_param(name,value)

    changed_preview = _get_named_plot('GS',tp.plotgroup.plots).view_dict.get('Strength',{})['Activity'].last.data
    # and check the preview did change
    try:
        assert_array_equal(changed_preview,initial_preview)
    except AssertionError:
        pass
    else:
        raise AssertionError("Test pattern didn't change.")

    # test that preview display is correct
    tp.params_frame.Defaults()
    preview = _get_named_plot('GS',tp.plotgroup.plots).view_dict.get('Strength',{})['Activity'].last.data
    assert_array_equal(preview,two_rectangles,"Defaults button failed to revert params to default values.")

    # CB: still need to test duration, learning, etc


@nottest
def test_projection():
    """Check the Projection window."""

    p = topo.guimain['Plots']['Projection']()
    p.gui_set_param('sheet','S')
    p.gui_set_param('projection','GSToS')

    p.gui_set_param('sheet','S2')
    p.gui_set_param('projection','GS2ToS2')
    p.gui_set_param('projection','GSToS2')

@nottest
def test_orientation_tuning():
    """Check that orientation tuning plot works."""

    p = topo.guimain['Plots']['Tuning Curves']['Orientation Tuning']()
    from topo.command.analysis import measure_or_tuning
    p.pre_plot_hooks = [measure_or_tuning.instance(num_phase=1,num_orientation=1,contrasts=[30])]
    p.Refresh()


######################################################################
# UTILITY FUNCTIONS
######################################################################

# make these particular tests simpler

def _initialize():
    """Make a simple simulation."""
    from topo.base.simulation import Simulation
    from topo.base.cf import CFSheet,CFProjection
    from topo.sheet import GeneratorSheet

    sim=Simulation(register=True,name="test pattern tester")
    sim['GS']=GeneratorSheet(nominal_density=2)
    sim['GS2']=GeneratorSheet(nominal_density=2)
    sim['S'] = CFSheet(nominal_density=2)
    sim['S2'] = CFSheet(nominal_density=2)
    sim.connect('GS','S',connection_type=CFProjection,delay=0.05)
    sim.connect('GS','S2',connection_type=CFProjection,delay=0.05)
    sim.connect('GS2','S2',connection_type=CFProjection,delay=0.05)


def _menu_item_fn(*clicks):
    """Return a wrapper round topo.guimain[click1][click2]...[clickN], with __doc__ set
    to the menu path."""
    menu_path = 'topo.guimain'

    for click in clicks:
        menu_path+='["%s"]'%click

    menu_item = eval(menu_path)

    def test_menu_item():
        menu_item()

    test_menu_item.__doc__ = "%s"%menu_path[12::]

    return test_menu_item



def _get_named_plot(name,plots):

    for plot in plots:
        if plot.plot_src_name==name:
            return plot

    assert False

