"""
Panels for displaying tuning curves.

Uses a PlotGroup to generate the pylab plots
which are currently displayed separately from the gui.
"""

import topo

from topo.base.projection import ProjectionSheet

from plotgrouppanel import PlotGroupPanel


## CEBALERT: same as for featurecurveplotgroup: shares code with templateplotgrouppanel
# Should be changed to inherit from UnitPGPanel, or whatever is created to handle the PlotGroup
# hierarchy.
class FeatureCurvePanel(PlotGroupPanel):

    # CEBHACKALERT: to which types of sheet is this plotgroup supposed to be applicable?
    sheet_type = ProjectionSheet

    @classmethod
    def valid_context(cls):
        if topo.sim.objects(cls.sheet_type).items():
            return True
        else:
            return False


    def __init__(self,master,plotgroup,**params):
	PlotGroupPanel.__init__(self,master,plotgroup,**params)

        self.pack_param("sheet",parent=self.control_frame_3,
            on_modify=self.sheet_change,side='left',expand=1,
            widget_options={'new_default':True,
                            'sort_fn_args':{'cmp':lambda x, y: cmp(-x.precedence,-y.precedence)}})

        self.pack_param("x",parent=self.control_frame_4)
        self.pack_param("y",parent=self.control_frame_4)

        # remove currently irrelevant widgets (plots are drawn in a separate window by pylab)
        # CEBNOTE: when plots are in this window, remove this line.
        for name in ['Enlarge','Reduce','Back','Fwd']: self.hide_param(name)

        self.auto_refresh= False
        if self.plotgroup.plot_immediately:
            self.refresh()

        self.sheet_change()



    def sheet_change(self):
        s = self.sheet
        l,b,r,t = s.bounds.lbrt()

        x = self.get_parameter_object('x')
        y = self.get_parameter_object('y')

        x.bounds=(l,r)
        y.bounds=(b,t)

        self.x = 0.0
        self.y = 0.0

        if 'x' and 'y' in self.representations:
            w1,w2=self.representations['x']['widget'],self.representations['y']['widget']
            w1.set_bounds(*x.bounds)
            w2.set_bounds(*y.bounds)

            w1.tag_set();w2.tag_set()



    def setup_plotgroup(self):
        super(FeatureCurvePanel,self).setup_plotgroup()
        self.populate_sheet_param()


    def populate_sheet_param(self):
        sheets = topo.sim.objects(self.sheet_type).values()
        self.plotgroup.params()['sheet'].objects = sheets
        self.plotgroup.sheet = sheets[0] # CB: necessary?

    def _plot_title(self):
        return self.plotgroup.name+' at time ' + topo.sim.timestr(self.plotgroup.time)


    def display_labels(self):
        """Plots are displayed in new windows, so do not add any labels."""
        pass







