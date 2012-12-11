"""
The Test Pattern window allows input patterns to be previewed.
"""

## Notes:
# * need to remove audigen pgs
# * missing disparity flip hack (though see JABHACKALERT below)
# * values like pi are written over
# * need to sort the list of Pattern generators

## Needs to be upgraded to behave how we want:
### JABHACKALERT: Should use PatternPresenter (from
### topo.command.analysis), which will allow flexible support for
### making objects with different parameters in the different eyes,
### e.g. to test ocular dominance or disparity.

# CBENHANCEMENT: add 'use for learning' to install current pattern
# (saving previous ones)?

from Tkinter import Frame

import param
import paramtk as tk

import topo

from topo.base.functionfamily import PatternDrivenAnalysis
from topo.base.sheetview import SheetView
from topo.base.patterngenerator import PatternGenerator, Constant
from topo.misc.generatorsheet import GeneratorSheet
from topo.command import pattern_present
from topo.plotting.plot import make_template_plot
from topo.plotting.plotgroup import SheetPlotGroup

from plotgrouppanel import SheetPanel


# CEBALERT: this uses make_template_plot(), so how is it not a
# TemplatePlotGroup?
class TestPatternPlotGroup(SheetPlotGroup):

    def sheets(self):
        if hasattr(self,'_sheets'):
            return self._sheets
        else:
            return super(TestPatternPlotGroup,self).sheets()

    def _generate_plots(self):
        dynamic_plots = []
        for kw in [dict(sheet=sheet) for sheet in self.sheets()]:
            sheet = kw['sheet']
            new_view = SheetView((sheet.input_generator(),sheet.bounds),
                                  sheet.name,sheet.precedence,topo.sim.time())
            sheet.sheet_views['Activity']=new_view
            channels = {'Strength':'Activity','Hue':None,'Confidence':None}

            ### JCALERT! it is not good to have to pass '' here... maybe a test in plot would be better
            dynamic_plots.append(make_template_plot(channels,sheet.sheet_views,
                                                    sheet.xdensity,sheet.bounds,self.normalize,
                                                    name=''))

        return self._static_plots[:]+dynamic_plots



class TestPattern(SheetPanel,PatternDrivenAnalysis):

    sheet_type = GeneratorSheet

    dock = param.Boolean(False)

    edit_sheet = param.ObjectSelector(doc="""
        Sheet for which to edit pattern properties.""")

    plastic = param.Boolean(default=False,doc="""
        Whether to enable plasticity during presentation.""")

    duration = param.Number(default=1.0, softbounds=(0.0,10.0),doc="""
        How long to run the simulation for each presentation.""")

    Present = tk.Button(doc="""Present this pattern to the simulation.""")

    pattern_generator = param.ClassSelector(default=Constant(), class_=PatternGenerator, doc="""
        Type of pattern to present. Each type has various parameters that can be changed.""")



    def __init__(self,master,plotgroup=None,**params):
        plotgroup = plotgroup or TestPatternPlotGroup()

        super(TestPattern,self).__init__(master,plotgroup,**params)

        self.auto_refresh = True

        self.plotcommand_frame.pack_forget()
        for name in ['pre_plot_hooks','plot_hooks','Fwd','Back']:
            self.hide_param(name)

        edit_sheet_param = self.get_parameter_object('edit_sheet')
        edit_sheet_param.objects = self.plotgroup.sheets()

        self.pg_control_pane = Frame(self) #,bd=1,relief="sunken")
        self.pg_control_pane.pack(side="top",expand='yes',fill='x')

        self.params_frame = tk.ParametersFrame(
            self.pg_control_pane,
            parameterized_object=self.pattern_generator,
            on_modify=self.conditional_refresh,
            msg_handler=master.status)

        self.params_frame.hide_param('Close')
        self.params_frame.hide_param('Refresh')

        # CEB: 'new_default=True' is temporary so that the current
        # behavior is the same as before; shoudl make None the
        # default and mean 'apply to all sheets'.
        self.pack_param('edit_sheet',parent=self.pg_control_pane,on_modify=self.switch_sheet,widget_options={'new_default':True,'sort_fn_args':{'cmp':lambda x, y: cmp(-x.precedence,-y.precedence)}})
        self.pack_param('pattern_generator',parent=self.pg_control_pane,
                        on_modify=self.change_pattern_generator,side="top")

        present_frame = Frame(self)
        present_frame.pack(side='bottom')

        self.pack_param('plastic',side='bottom',parent=present_frame)
        self.params_frame.pack(side='bottom',expand='yes',fill='x')
        self.pack_param('duration',parent=present_frame,side='left')
        self.pack_param('Present',parent=present_frame,on_set=self.present_pattern,side="right")


    def setup_plotgroup(self):
        super(TestPattern,self).setup_plotgroup()

        # CB: could copy the sheets instead (deleting connections etc)
        self.plotgroup._sheets = [GeneratorSheet(name=gs.name,
                                                 nominal_bounds=gs.nominal_bounds,
                                                 nominal_density=gs.nominal_density)
                                  for gs in topo.sim.objects(GeneratorSheet).values()]
        self.plotgroup._set_name("Test Pattern")


    def switch_sheet(self):
        if self.edit_sheet is not None:
            self.pattern_generator = self.edit_sheet.input_generator
        self.change_pattern_generator()


    def change_pattern_generator(self):
        """
        Set the current PatternGenerator to the one selected and get the
        ParametersFrameWithApply to draw the relevant widgets
        """
        # CEBALERT: if pattern generator is set to None, there will be
        # an error. Need to handle None in the appropriate place
        # (presumably tk.py).
        self.params_frame.set_PO(self.pattern_generator)

        for sheet in self.plotgroup.sheets():
            if sheet==self.edit_sheet:
                sheet.set_input_generator(self.pattern_generator)

        self.conditional_refresh()


    def refresh(self):
        """
        Simply update the plots: skip all handling of history.
        """
        self.refresh_plots()


    def present_pattern(self):
        """
        Move the user created patterns into the GeneratorSheets, run for
        the specified length of time, then restore the original
        patterns.
        """
        topo.sim.run(0.0)  # ensure EPs are start()ed

        topo.sim.state_push()
        for f in self.pre_presentation_hooks: f()
        input_dict = dict([(sheet.name,sheet.input_generator) \
                           for sheet in self.plotgroup.sheets()])
        pattern_present(input_dict,self.duration,
                        plastic=self.plastic,overwrite_previous=False)
        topo.guimain.auto_refresh()
        for f in self.post_presentation_hooks: f()
        topo.sim.state_pop()

