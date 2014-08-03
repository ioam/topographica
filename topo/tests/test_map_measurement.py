"""
Functions to test that map measurements haven't changed.

Use generate() to save data, and test() to check that the data is
unchanged in a later version. Results from generate() are already
checked into svn, so intentional changes to map measurement mean new
data must be generated and committed. E.g.

# ...deliberate change to orientation map measurement...
$ ./topographica -c 'default_density=8' examples/lissom_oo_or.ty -c \
  'topo.sim.run(100)' -c \
  'from topo.tests.test_map_measurement import *' -c \
  'generate(["Orientation Preference"])'
# now commit the resulting data file to the svn repository


plotgroups_to_test is a list of PlotGroups for which these
test functions are expected to be useful.
"""

import pickle

import numpy

from param import resolve_path

from dataviews.collector import AttrTree

from topo.command.analysis import *
from topo.command.pylabplot import *
from topo.plotting.plotgroup import plotgroups
from topo.misc.util import unit_value

from nose.tools import nottest



# CEBALERT: change to be the all-in-one model eventually, and
# uncomment all ocular/disparity/direction groups below.
sim_name = 'lissom_oo_or'

# CEB: tests should store params of commands
# so we don't have to update data if someone
# e.g. edits a default value.

plotgroups_to_test = [
    # Several plotgroups are commented out because I was only thinking
    # about map measurement that results in sheet_views stored for V1.
    # (All could be included if the functions below were to be
    # extended to handle sheets other than V1, etc.)
    #'Activity',
    #'Connection Fields',
    #'Projection',
    #'Projection Activity',
    #'RF Projection',
    #'RF Projection (noise)',

    'Position Preference',
    # 'Center of Gravity',
    # 'Orientation and Ocular Preference',
    # 'Orientation and Direction Preference',
    # 'Orientation, Ocular and Direction Preference',
    'Orientation Preference',
    #'Ocular Preference',
    'Spatial Frequency Preference',
    #'PhaseDisparity Preference',
    'Orientation Tuning Fullfield',
    'Orientation Tuning',
    'Size Tuning',
    'Contrast Response',
    #'Retinotopy',  commented out because measurement is unstable
    #'Direction Preference',
    'Corner OR Preference'
    ]


def _reset_views(sheet):
    if hasattr(sheet.views,'Maps'):
        sheet.views.Maps = AttrTree()
    if hasattr(sheet.views,'Curves'):
        sheet.views.Curves = AttrTree()


def generate(plotgroup_names):
    assert topo.sim.name==sim_name
    assert topo.sim['V1'].nominal_density==8
    assert topo.sim.time()==100

    for name in plotgroup_names:
        print "* Generating data for plotgroups['%s']"%name

        views = {}
        sheet = topo.sim['V1']

        _reset_views(sheet)

        plotgroups[name]._exec_pre_plot_hooks()

        sheets_views = views[sheet.name] = {}

        if hasattr(sheet.views,'maps'):
            sheets_views['sheet_views'] = sheet.views.Maps
        if hasattr(sheet.views,'curves'):
            sheets_views['curves'] = sheet.views.Curves

        filename = normalize_path('tests/%s_t%s_%s.data'%(sim_name,topo.sim.timestr(),
                                                          name.replace(' ','_')))
        print "Saving results to %s" % (filename)
        f = open(filename,'wb')
        pickle.dump((topo.version,views),f)
        f.close()

def checkclose(label,version,x,y):
    errors=[]
    topo_version = "v{0}.{1}.{2} {3}".format(*version) if type(version) == tuple else version
    if not numpy.allclose(x,y,rtol=1e-05,atol=1e-07):
        print "...%s array is no longer close to the %s version:\n%s\n---\n%s" % (label,topo_version,x,y)
        errors=[label]
    else:
        print '...%s array is unchanged since data was generated (%s)' % (label,topo_version)
    return errors


@nottest
def test(plotgroup_names):
    import topo
    assert topo.sim.name==sim_name
    assert topo.sim['V1'].nominal_density==8
    assert topo.sim.time()==100

    failing_tests=[]
    for name in plotgroup_names:
        print "\n* Testing plotgroups['%s']:"%name

        sheet = topo.sim['V1']
        _reset_views(sheet)
        plotgroups[name]._exec_pre_plot_hooks()

        filename = resolve_path('tests/data_maptests/%s_t%s_%s.data'%(sim_name,topo.sim.timestr(),
                                                          name.replace(' ','_')))
        print "Reading previous results from %s" % (filename)
        f = open(filename,'r')

        try:
            topo_version,previous_views = pickle.load(f)
        ########################################
        except AttributeError:
            # PRALERT: Code to allow loading of old data files after
            # boundingregion was moved to dataviews.
            import sys
            from dataviews.sheetviews import boundingregion
            sys.modules['imagen.boundingregion'] = boundingregion


            # CEBALERT: code here just to support old data file. Should
            # generate a new one so it's no longer necessary.

            from topo.misc.legacy import preprocess_state

            import topo.base.boundingregion

            def _boundingregion_not_parameterized(instance,state):
                for a in ['initialized', '_name_param_value', 'nopickle']:
                    if a in state:
                        del state[a]

            preprocess_state(topo.base.boundingregion.BoundingRegion,
                             _boundingregion_not_parameterized)

            f.seek(0)
            topo_version,previous_views = pickle.load(f)
        ########################################

        f.close()

        if 'sheet_views' in previous_views[sheet.name]:
            previous_sheet_views = previous_views[sheet.name]['sheet_views']
            for view_name in previous_sheet_views:
                failing_tests += checkclose(sheet.name + " " + view_name,topo_version,
                                            sheet.views.Maps[view_name].last.data,
                                            previous_sheet_views[view_name].view()[0])

        if 'curve_dict' in previous_views[sheet.name]:
            previous_curve_dicts = previous_views[sheet.name]['curve_dict']
            # CB: need to cleanup var names e.g. val
            time, duration = (topo.sim.time(), 1.0)
            for curve_name in previous_curve_dicts:
                for other_param in previous_curve_dicts[curve_name]:
                    other_param_val = unit_value(other_param)[-1]
                    for val in previous_curve_dicts[curve_name][other_param]:
                        new_curves = sheet.views.Curves[curve_name.capitalize()+"Tuning"]
                        new = new_curves[time, duration, other_param_val-0.01:other_param_val+0.01, val].values()[0].data
                        old = previous_curve_dicts[curve_name][other_param][val].view()[0]
                        failing_tests += checkclose("%s %s %s %s" %(sheet.name,curve_name,other_param,val),
                                                    topo_version, new, old)

    if failing_tests != []: raise AssertionError, "Failed map tests: %s" % (failing_tests)
