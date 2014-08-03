"""
The GUI model editor.

Tools:   for the editor menu bar
Objects: that can be manipulated in the canvas
Window:  window and canvas

Originally written by Alan Lindsay.
"""

from inspect import getdoc
import math

from Tkinter import Button, Label, Frame, TOP, LEFT, RIGHT, BOTTOM, E, LAST, FIRST, OptionMenu, StringVar,Canvas,X,GROOVE,RAISED,Checkbutton,Menu,Scrollbar, YES,Y,END,BOTH
from tkFileDialog import asksaveasfilename


import param
from param import parameterized,normalize_path
import paramtk as tk
from paramtk.tilewrapper import Combobox

import topo
from topo.command.analysis import update_activity
from topo.misc.util import shortclassname
from topo.base.simulation import EventProcessor

# Make sure at least some sheets or projections are available to
# choose from; rest will be available if some other module imports *
# from sheet and projection
from topo.base.sheet import Sheet
from topo.base.projection import Projection
from topo.base.cf import CFProjection


###########################################################################
## WINDOW
###########################################################################

# These can be customized, e.g. in .topographicarc; they should probably be parameters
# somewhere.
canvas_width = 1200
scaling_factor = topo.sim.item_scale
enlarging_factor = 1.25

canvas_region = (0, 0, canvas_width, canvas_width)
"""Size of the canvas, as a bounding box (xl yl xh yh)."""


class EditorCanvas(Canvas):

    """
    EditorCanvas extends the Tk Canvas class.
    There are 3 modes that determine the effect of mouse events in the Canvas
    A Canvas can accept new objects, move objects and make connections
    between them. The intended use of this class is as the main
    canvas in a Topographica model-editing GUI.
    """

    def __init__(self, root = None, width = 600, height = 600):
        Canvas.__init__(self, root, width = width, height = height,bg='white')
        # bg = "white", bd = 2, relief = SUNKEN)
        self.panel = Frame(root)
        self.panel.pack(side = TOP, fill = X)
        # Top bar of the canvas, allowing changes in size, display and to force refresh.
        Button(self.panel,text="Refresh", command=self.refresh).pack(side=LEFT)
        Button(self.panel,text="Reduce", command=self.reduce_scale).pack(side=LEFT)
        Button(self.panel,text="Enlarge", command=self.enlarge_scale).pack(side=LEFT)
        self.auto_refresh = False
        self.console = topo.guimain
        self.auto_refresh_checkbutton = Checkbutton(self.panel,text="Auto-refresh",
                                                    command=self.toggle_auto_refresh)
        self.auto_refresh_checkbutton.pack(side=LEFT)

        self.normalize_checkbutton = Checkbutton(self.panel, text="Normalize",
                                                    command=self.toggle_normalize)
        self.normalize_checkbutton.pack(side=LEFT)
        if EditorSheet.normalize == True:
            self.normalize_checkbutton.select()

        self.node_labels_checkbutton = Checkbutton(self.panel, text="Node labels",
                                                    command=self.toggle_node_labels)
        self.node_labels_checkbutton.pack(side=LEFT)
        if EditorNode.show_label == True:
            self.node_labels_checkbutton.select()

        self.connection_labels_checkbutton = Checkbutton(self.panel, text="Connection labels",
                                                    command=self.toggle_connection_labels)
        self.connection_labels_checkbutton.pack(side=LEFT)
        if EditorConnection.show_label == True:
            self.connection_labels_checkbutton.select()

        # retain the current focus in the canvas
        self.scaling_factor = topo.sim.item_scale#scaling_factor
        self.current_object = None
        self.current_connection = None
        self.focus = None
        # list holding references to all the objects in the canvas
        self.object_list = []
        # set the initial mode.
        self.display_mode = 'video'
        self.mode = "ARROW"
        self.MAX_VIEWS = 5
        # get the topo simulation
        self.simulation = topo.sim

        # create the menu widget used as a popup on objects and connections
        self.option_add("*Menu.tearOff", "0")
        self.item_menu = Menu(self)
        self.view = Menu(self.item_menu)
        # add property, toggle activity drawn on sheets, object draw ordering and delete entries to the menu.
        self.item_menu.insert_command(END, label = 'Properties',
            command = lambda: self.show_properties(self.focus))
        self.item_menu.add_cascade(label = 'Change View', menu = self.view, underline = 0)
        self.item_menu.insert_command(END, label = 'Move Forward',
            command = lambda: self.move_forward(self.focus))
        self.item_menu.insert_command(END, label = 'Move to Front',
            command = lambda: self.move_to_front(self.focus))
        self.item_menu.insert_command(END, label = 'Move to Back',
            command = lambda: self.move_to_back(self.focus))
        self.item_menu.insert_command(END, label = 'Delete',
            command = lambda: self.delete_focus(self.focus))
        # the indexes of the menu items that are for objects only
        self.object_indices = [2,3,4]

        self.canvas_menu = Menu(self)
        self.sheet_options = Menu(self.canvas_menu)
        mode_options = Menu(self.canvas_menu)
        self.canvas_menu.add_command(label = 'Export as PostScript image', command = self.save_snapshot)
        self.canvas_menu.add_cascade(label = 'Select Mode', menu = mode_options)
        mode_options.add_command(label = 'Video', command = lambda: self.set_display_mode('video'))
        mode_options.add_command(label = 'Normal', command = lambda: self.set_display_mode('normal'))
        mode_options.add_command(label = 'Printing', command = lambda:
            self.set_display_mode('printing'))
        self.canvas_menu.add_cascade(label = 'Sheet options', menu = self.sheet_options, underline = 0)
        self.sheet_options.add_command(label = 'Toggle Density Grid', command =
            self.toggle_object_density)
        self.sheet_options.add_command(label = 'Toggle Activity', command = self.toggle_object_activity)

        # bind key_press events in canvas.
        self.bind('<KeyPress>', self.key_press)
        # bind the possible left button events to the canvas.
        self.bind('<Button-1>', self.left_click)
        self.bind('<B1-Motion>', self.left_click_drag)
        self.bind('<Double-1>', self.left_double_click)
        self.bind('<ButtonRelease-1>', self.left_release)
        # bind the possible right button events to the canvas.
        self.bind('<<right-click>>', self.right_click)
        # because right-click opens menu, a release event can only be flagged by the menu.
        self.item_menu.bind('<<right-click-release>>', self.right_release)

        # add scroll bar; horizontal and vertical
        self.config(scrollregion = canvas_region)
        vertical_scrollbar = Scrollbar(root)
        horizontal_scrollbar = Scrollbar(root, orient = 'horizontal')
        vertical_scrollbar.config(command = self.yview)
        horizontal_scrollbar.config(command = self.xview)
        self.config(yscrollcommand=vertical_scrollbar.set)
        self.config(xscrollcommand=horizontal_scrollbar.set)
        vertical_scrollbar.pack(side = RIGHT, fill = Y)
        horizontal_scrollbar.pack(side = BOTTOM, fill = X)

    def key_press(self, event):
        "What happens when a key is pressed."
        self.change_mode(event.char)


    #   Left mouse button event handlers

    def left_click(self, event):
        "What is to happen if the left button is pressed."

        x,y = self.canvasx(event.x), self.canvasy(event.y)
        {"ARROW" : self.init_move,           # case Arrow mode
         "MAKE" : self.none,                 # case Make mode
         "CONNECTION" : self.init_connection # case Connection mode.
        }[self.mode](x,y)                    # select function depending on mode

    def left_click_drag(self, event):
        "What is to happen if the mouse is dragged while the left button is pressed."

        x,y = self.canvasx(event.x), self.canvasy(event.y)
        {"ARROW" : self.update_move,              # case Arrow mode
         "MAKE" : self.none,                   # case Make mode
         "CONNECTION" : self.update_connection # case Connection mode.
        }[self.mode](x,y)                      # select function depending on mode

    def left_release(self, event):
        "What is to happen when the left mouse button is released."

        x,y = self.canvasx(event.x), self.canvasy(event.y)
        {"ARROW" : self.end_move,            # case Arrow mode
         "MAKE" : self.create_object,        # case Make mode
         "CONNECTION" : self.end_connection  # case Connection mode.
        }[self.mode](x,y)                    # select function depending on mode

    def left_double_click(self, event):
        """
        What is to happen if the left button is double clicked.
        The same for all modes - show the properties for the clicked item.
        Gets object or connection at this point and gives it the focus.
        """
        focus = self.get_xy(event.x, event.y)
        if (focus != None):
            focus.set_focus(True)
        # show the object or connection's properties.
        self.show_properties(focus)


    #   Right mouse button event handlers

    def right_click(self, event):
        "What is to happen if the right button is pressed."
        self.show_hang_list(event)

    def right_release(self, event):
        "What is to happen when the right mouse button is released (bound to the menu)."
        if (self.focus != None) : # remove focus.
            self.focus.set_focus(False)


    #   Mode Methods

    def change_mode(self, char):
        "Changes the mode of the canvas, i.e., what mouse events will do."

        if not char in ('c', 'm', 'a') : return
        # remove the focus from the previous toolbar item
        {"ARROW" : self.arrow_tool.set_focus,     # arrow toolbar item
         "MAKE" : self.object_tool.set_focus,        # object toolbar item
         "CONNECTION" : self.connection_tool.set_focus # connection toolbar item
        }[self.mode](False)                  # select function depending on mode

        # determine the new mode and corresponding toolbar item.
        if (char == 'c'):
            mode = "CONNECTION"
            bar = self.connection_tool
        elif (char == 'm'):
            mode = "MAKE"
            bar = self.object_tool
        elif (char == 'a'):
            mode = "ARROW"
            bar = self.arrow_tool
        # set the focus of the toolbar item of the new mode and retain the note the new mode.
        bar.set_focus(True)
        self.mode = mode


    #   Panel methods

    def refresh(self):
        for obj in self.object_list:
            obj.set_focus(True)
            obj.set_focus(False)
        for obj in self.object_list:
            connection_list = obj.from_connections[:]
            connection_list.reverse()
            for con in connection_list:
                con.move()

    def enlarge_scale(self):
        self.scaling_factor *= enlarging_factor
        self.refresh()

    def reduce_scale(self):
        self.scaling_factor /= enlarging_factor
        self.refresh()

    def toggle_auto_refresh(self):
        self.auto_refresh = not self.auto_refresh
        if self.auto_refresh:
            self.console.auto_refresh_panels.append(self)
        else:
            self.console.auto_refresh_panels.remove(self)

    def toggle_normalize(self):
        EditorSheet.normalize = not EditorSheet.normalize
        self.refresh()

    def toggle_node_labels(self):
        EditorNode.show_label = not EditorNode.show_label
        self.refresh()

    def toggle_connection_labels(self):
        EditorConnection.show_label = not EditorConnection.show_label
        self.refresh()



    #   Object moving methods
    #
    # If an object is left clicked in the canvas, these methods allow
    # it to be repositioned in the canvas.

    def init_move(self, x, y):
        "Determine if click was on an object."

        self.current_object = self.get_object_xy(x, y)
        if (self.current_object != None) :
            # if it was, give it the focus
            self.current_object.set_focus(True)

    def update_move(self, x, y):
        "If dragging an object, refresh its position"

        if (self.current_object != None):
            self.current_object.move(x, y)

    def end_move(self, x, y):
        "If dropping an object, remove focus and refresh."

        if (self.current_object != None):
            self.current_object.set_focus(False)
            self.current_object.move(x, y)
        # redraw all the objects in the canavas and dereference
        self.redraw_objects()
        self.current_object = None

    #   Connection methods
    #
    # these methods allow a connection to be made between two objects in the canvas

    def init_connection(self, x, y):
        "Determine if click was on an object, and retain if so."

        current_object = self.get_object_xy(x, y)
        if (current_object == None) : # if not change to ARROW mode
            self.change_mode('a')
        else :  # if on an object, create a connection and give it the focus
            self.current_connection = self.connection_tool.new_cover(current_object)
            self.current_connection.set_focus(True)

    def update_connection(self, x, y):
        "Update connection's position."
        self.current_connection.update_position((x, y))

    def end_connection(self, x, y):
        "Determine if the connection has been dropped on an object."

        obj = self.get_object_xy(x, y)
        if (obj != None) : # if an object, connect the objects and remove focus
            if (self.current_connection != None):
                connected = self.connection_tool.create_connection(self.current_connection, obj)
                if connected:
                    self.current_connection.set_focus(False)
        else : # if not an object, remove the connection
            connected=False
            if (self.current_connection != None):
                self.current_connection.remove()
        if connected:
            self.redraw_objects()
        # dereference
        self.current_connection = None

    def get_connection_xy(self, x, y):
        "Return connection at given x, y (None if no connection)."

        for obj in self.object_list:
            connection_list = obj.from_connections[:]
            connection_list.reverse()
            for con in connection_list:
                if (con.in_bounds(x, y)):
                    return con
        return None

    #   Object Methods

    def create_object(self, x, y) :
        "Create a new object."
        self.add_object(self.object_tool.create_node(x, y))

    def add_object(self, obj) :
        "Add a new object to the Canvas."

        self.object_list = [obj] + self.object_list

    def add_object_to_back(self, obj) :
        "Add a new object to the Canvas at back of the list."

        self.object_list =  self.object_list + [obj]

    def remove_object(self, obj) :
        "Remove an object from the canvas."

        for i in range(len(self.object_list)) :
            if (obj == self.object_list[i]) : break
        else : return # object was not found
        del self.object_list[i]
        return i

    def toggle_object_density(self):
        if EditorSheet.show_density:
            EditorSheet.show_density = False
        else:
            EditorSheet.show_density = True
        self.refresh()

    def toggle_object_activity(self):
        if EditorSheet.view == 'activity':
            EditorSheet.view = 'normal'
        else:
            EditorSheet.view = 'activity'
        self.refresh()

    def get_object_xy(self, x, y) :
        "Return object at given x, y (or None if no object)."

        # search through the bounds of each object in the canvas.
        # returns the first (nearest to front) object, None if no object at x,y
        for obj in self.object_list:
            if (obj.in_bounds(x, y)):
                break
        else : return None
        return obj


    def show_properties(self, focus):
        "Show properties of an object or connection, and remove the focus."

        if (focus != None):
            focus.show_properties()
            focus.set_focus(False)

    def delete_focus(self, focus):
        "Tell a connection or object to delete itself."

        if (focus == None) :
            pass
        else:
            focus.remove()
            self.redraw_objects()

    #   Object Order Methods
    #
    # These methods ensure the ordering in the canvas window is held
    # and allows manipulation of the order.

    def redraw_objects(self, index = None):
        """
        Redraw all the objects in the canvas.

        If non-None, the index specifies that only the objects below
        that index need drawing.
        """

        if (index == None or index < 0) : index = len(self.object_list)
        for i in range(index ,0, -1):
            self.object_list[i-1].draw()

    def move_to_front(self, obj):
        index = self.remove_object(obj)
        self.add_object(obj)
        self.redraw_objects(index)

    def move_forward(self, obj):
        for i in range(len(self.object_list)) : # find object index in list
            if (obj == self.object_list[i]) : break
        else : return # object was not found
        # swap this object for the one higher in the canvas and redraw
        a = self.object_list[(i-1) : (i+1)]
        a.reverse()
        self.object_list[(i-1):(i+1)] = a
        self.redraw_objects(i+1)

    def move_to_back(self, obj):
        self.remove_object(obj)
        self.add_object_to_back(obj)
        self.redraw_objects()

    #   Hang List Methods
    #
    # If there is an object or connection at the right clicked point,
    # a popup menu is displayed, allowing for modifications to the
    # particular obj/con.

    def show_hang_list(self, event):

        # change to ARROW mode and get x, y mouse coords
        self.change_mode('a')
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        # get connection at this point
        focus = self.get_connection_xy(x, y)
        for i in range(self.MAX_VIEWS) : # max number of views
            self.view.delete(END)
        if (focus == None):
            # if no connection, checks bounds of objects
            focus = self.get_object_xy(x, y)
            # fill in menu items that are just for objects
            for i in self.object_indices:
                self.item_menu.entryconfig(i, foreground = 'Black', activeforeground = 'Black')
        else:
            # gray out menu items that are just for objects
            for i in self.object_indices:
                self.item_menu.entryconfig(i,foreground = 'Gray', activeforeground = 'Gray')
        if (focus != None):
            for (label, function) in focus.viewing_choices:
                self.view.add_command(label = label, command = function)
            # give the connection or object the focus
            focus.set_focus(True)
            self.focus = focus
            # create the popup menu at current mouse coord
            self.item_menu.tk_popup(event.x_root, event.y_root)
        else:
            self.canvas_menu.tk_popup(event.x_root, event.y_root)

    #   Utility methods

    def save_snapshot(self):
        POSTSCRIPT_FILETYPES = [('Encapsulated PostScript images','*.eps'),
                                ('PostScript images','*.ps'),('All files','*')]
        snapshot_name = asksaveasfilename(filetypes=POSTSCRIPT_FILETYPES,
                                          initialdir=normalize_path(),
                                          initialfile=topo.sim.basename()+".ps")

        if snapshot_name:
            self.postscript(file=snapshot_name)

    def set_display_mode(self, mode):
        self.display_mode = mode
        for obj in self.object_list:
            obj.set_mode(mode)

    def set_tool_bars(self, arrow_tool, connection_tool, object_tool):
        # reference to the toolbar items, a tool is notified when the canvas is changed
        # to the mode corresponding to it.
        self.arrow_tool = arrow_tool
        # connection tool supplies 'connection' objects that can draw themselves in the canvas
        self.connection_tool = connection_tool
        # object tool supplies 'object' objects that can draw themselves in the canvas
        self.object_tool = object_tool
        # initialise mode
        self.change_mode('a')

    # does nothing
    def none(self, x, y) : pass

    def get_xy(self, x, y):
        "Returns the connection or object at this x, y position or None if there is not one."

        # check for a connection
        focus = self.get_connection_xy(x, y)
        if (focus == None):
            # if no connection, check bounds of objects
            focus = self.get_object_xy(x, y)
        return focus # return the first found or None




# JABALERT: I made this into parameterized.Parameterized to make self.warning work,
# but it should be changed to a PlotGroupPanel eventually
class ModelEditor(parameterized.Parameterized):
    """
    This class constructs the main editor window. It uses a instance
    of GUICanvas as the main editing canvas and inserts the
    three-option toolbar in a Frame along the left side of the window.
    """

    def __init__(self,master,**params):
        parameterized.Parameterized.__init__(self,**params)

        # create editor window and set title
        root = tk.AppWindow(master)
        root.title("Model Editor")

        canvas_frame = Frame(root,bg = 'white')
        canvas_frame.pack(side='right',fill = BOTH, expand = YES)

        toolbar_frame = Frame(root, bg = 'light grey', bd = 2)
        toolbar_frame.pack(side=LEFT,fill=Y)

        self.canvas = EditorCanvas(canvas_frame)
        self.canvas.pack(fill = BOTH, expand = YES)


        # object/node = sheet

        parameters_tool = ParametersTool(toolbar_frame)
        arrow_tool=ArrowTool(self.canvas,toolbar_frame,parameters_tool)
        object_tool=NodeTool(self.canvas,toolbar_frame,parameters_tool)
        connection_tool=ConnectionTool(self.canvas,toolbar_frame,parameters_tool)

        arrow_tool.pack(side='top')
        object_tool.pack(side='top')
        connection_tool.pack(side='top')
        parameters_tool.pack(side='top')


        # give the canvas a reference to the toolbars
        self.canvas.set_tool_bars(arrow_tool, connection_tool, object_tool)

        # give the canvas focus and import any objects and connections already in the simulation
        self.canvas.focus_set()


        # Grid layout defaults
        self.xstart = 100
        self.ystart = 100
        self.next_x = self.xstart+100
        self.next_y = self.ystart
        self.xstep = 150
        self.ystep = 150

        self.import_model()

    def import_model(self):
        # get a list of all the objects in the simulation
        sim = self.canvas.simulation
        node_dictionary = sim.objects(EventProcessor)
        node_list = node_dictionary.values()

        # create the editor covers for the nodes
        for node in node_list:
            # if the sheet has x,y coords, use them
            if (hasattr(node,'layout_location') and node.layout_location!=(-1,-1)):
                x, y = node.layout_location
            # if not generate new coords on a grid layout
            # Could use dot/graphviz to place the objects nicely
            else:
                x, y = self.next_x , self.next_y
                self.next_y += self.ystep
                if self.next_y > canvas_region[3]:
                    self.next_y  = self.ystart
                    self.next_x += self.xstep
                if self.next_x > canvas_region[2]:
                    self.next_x = self.xstart + 15
                    self.next_y = self.ystart + 15

            # Could handle more EventProcessor subclasses here
            if isinstance(node,Sheet):
                editor_node = EditorSheet(self.canvas, node, (x, y), node.name)
            else:
                editor_node = EditorEP(self.canvas, node, (x, y), node.name)

            node.layout_location=(x,y)
            self.canvas.add_object(editor_node)

        # create the editor covers for the connections

        for editor_node in self.canvas.object_list:
            for con in editor_node.simobj.out_connections:
                # Could handle more EditorConnection subclasses here
                if isinstance(con,CFProjection):
                    editor_connection = EditorProjection("", self.canvas, editor_node)
                else:
                    editor_connection = EditorEPConnection("", self.canvas, editor_node)

                # find the EditorNode that the proj connects to
                for dest in self.canvas.object_list:
                    if (dest.simobj == con.dest):
                        # connect the connection to the destination node
                        editor_connection.connect(dest, con)
                        break
                else:
                    self.warning("The model editor cannot draw connection", con.name,
                                 "because", con.dest.name, "is not drawn in the editor.")



        self.canvas.redraw_objects()























###########################################################################
## TOOLS
###########################################################################

class ArrowTool(Frame):
    """
    ArrowTool is a selectable frame containing an arrow icon and a label. It is a
    toolbar item in a ModelEditor that allows the user to change the GUICanvas to
    'ARROW' mode.
    """

    def __init__(self, canvas,  parent = None, parambar = None):
        Frame.__init__(self, parent,bg = 'light grey', bd = 4, relief = RAISED)
        self.canvas = canvas # hold canvas reference
        self.parameter_tool = parambar # To display class properties and name
        # label sets canvas mode
        self.title_label = Label(self, text="Move:", bg ='light grey')
        self.title_label.bind('<Button-1>', self.change_mode)
        self.title_label.pack()
        self.doc = 'Use the arrow tool to select and\nmove objects in the canvas around'
        # arrow icon
        self.icon = Canvas(self, width = 35, height = 30,bg = 'light grey')
        self.icon.create_polygon(10,0, 10,22, 16,17, 22,29, 33,22, 25,13, 33,8,
            fill = 'black', outline = 'white')
        self.icon.pack()
        self.icon.bind('<Button-1>', self.change_mode) # icon sets canvas mode
        # pack in toolbar at top and fill out in X direction; click changes canvas mode
        self.pack(side = TOP, fill = X)
        self.bind('<Button-1>', self.change_mode)


    def change_mode(self, event):
        self.canvas.change_mode('a') # (ARROW)

    def set_focus(self, focus):
        "Change the background highlight to reflect whether this toolbar item is selected."

        if (focus):
             col = 'dark grey'; relief = GROOVE
             if not(self.parameter_tool == None):
                 self.parameter_tool.set_focus('Arrow', None, self.doc)
        else:
            col = 'light grey'; relief = RAISED

        # ALERT
        self.config(bg = col, relief = relief)
        self.title_label.config(bg = col)
        self.icon.config(bg = col)



# hack to sort by precedence
# (won't need when modeleditor is plotgroup)
def names_sorted_by_precedence(classes):
    classes.sort(lambda x, y: cmp(-x.precedence,-y.precedence))
    return [class_.__name__ for class_ in classes]


class NodeTool(Frame):
    """
    NodeTool extends Frame. It is expected to be included in a topographica
    model development GUI and functions as a self populating Node tool.
    The available Sheet types are supplied to be selected from. This Tool supplies
    a suitable Editor cover for a node and creates the corresponding topo object.
    """
    # hack: we can do this properly when converting to a plotgrouppanel
    default_sheet = 'CFSheet'

    def __init__(self, canvas,  parent = None, parambar = None):

        Frame.__init__(self, parent,bg = 'light grey', bd = 4, relief = RAISED)
        self.canvas = canvas # hold canvas reference.
        self.parameter_tool = parambar # To display class properties and name
        # bind clicks, pack in toolbar at top and fill out in X direction
        self.bind('<Button-1>', self.change_mode)
        self.pack(side = TOP, fill = X)
        # label sets canvas mode

        # CebAlerT: make these 'move' 'add sheet of type' things etc
        # look like buttons again, or -better - clean up the whole
        # interface!

        self.title_label = Label(self, text="Add sheet of type:",bg ='light grey')
        self.title_label.bind('<Button-1>', self.change_mode)
        self.title_label.pack()
        self.doc = 'Use the sheet tool to click a\nsheet object into the canvas.'
        # gets list of all the available sheets.
        self.sheet_list = param.concrete_descendents(Sheet)

        sheet_list = names_sorted_by_precedence(self.sheet_list.values())

        ## menu with list of available sheets
        self.option_var = StringVar()
        self.option_var.set(self.default_sheet)
        self.current_option = self.option_var.get()

        self.option_menu = Combobox(self,textvariable=self.option_var,
                                    values=sheet_list,state='readonly')
        self.option_menu.pack()
        self.option_menu.bind('<Button-1>', self.change_mode)

        self.option_var.trace_variable('w',self.set_option)





    #   Focus Methods

    def change_mode(self, option):
        self.canvas.change_mode('m') # ('MAKE')

    def set_focus(self, focus):
        "Change the background highlight to reflect whether this toolbar item is selected."

        if (focus):
            col = 'dark grey'; relief = GROOVE
            if not(self.parameter_tool == None):
                current_option = self.sheet_list[self.current_option]
                name = str(current_option).split('.')[-1][:-2]
                self.parameter_tool.set_focus(name, current_option, self.doc)
        else:
            col = 'light grey'; relief = RAISED

        # ALERT
        self.config(bg = col, relief = relief)
        self.title_label.config(bg = col)
        #self.option_menu.config(bg = col)


    #   Node Methods

    def create_node(self, x, y):
        if self.parameter_tool.focus:
            self.parameter_tool.update_parameters()
        # get the current selection and create the new topo object

        # CEBALERT: because Parameterized overwrites the name
        # unless it's passed in params when the object is created, I
        # pass the class name (set by ParametersFrameWithApply) here.
        # Same goes for projections. (i.e. Allow people to set the name
        # for a new sheet or projection.)
        name=self.sheet_list[self.current_option].name
        # Instead, should have a popup that asks for the name.

        if name:
            simobj = self.sheet_list[self.current_option](name=name)
        else:
            simobj = self.sheet_list[self.current_option]()

        sim = self.canvas.simulation # get the current simulation
        sim[simobj.name] = simobj
        # create the cover for the simobj and return it.
        return EditorSheet(self.canvas, simobj, (x, y), simobj.name)


    #   Util Methods

    def set_option(self,*args):
        """ """
        self.current_option = self.option_var.get()
        self.change_mode(None)




# JABHACKALERT: Currently only searches for topo.projection (connections have not been implemented yet).
class ConnectionTool(Frame):
    """
    ConnectionTool extends Frame. It is expected to be included in a topographica
    model development GUI and functions as a self populating Connection toolbar.
    The available Connection types are listed and the user can select one.
    When a connection is formed between two nodes a topo.projection of the
    specified type is instantiated and a reference to it is stored in it's Editor
    cover. Allows user to change the EditorCanvas mode to 'CONNECTION' mode.
    """

    def __init__(self, canvas, parent = None, parambar = None):
        # super constructor call.
        Frame.__init__(self, parent, bg = 'light grey', bd = 4, relief = RAISED)
        self.canvas = canvas # hold canvas reference.
        self.parameter_tool = parambar # To display class properties and name
        # bind clicks, pack in toolbar at top and fill out in X direction
        self.bind('<Button-1>', self.change_mode)
        self.pack(side = TOP, fill = X)
        # label sets canvas mode
        self.title_label = Label(self, text="Add projection of type:",bg ='light grey')
        self.title_label.bind('<Button-1>', self.change_mode)
        self.title_label.pack()
        self.doc = 'Use the connection tool to\ndrag connections between objects'
        # gets list of all the available projections.
        self.proj_list = param.concrete_descendents(Projection)
        proj_list = names_sorted_by_precedence(self.proj_list.values())


        ## menu with list of available projections
        self.option_var = StringVar()
        self.option_var.set(proj_list[0])
        self.current_option = self.option_var.get()

        self.option_menu = Combobox(self,textvariable=self.option_var,
                                    values=proj_list,state='readonly')

        self.option_menu.pack()
        self.option_menu.bind("<Button-1>",self.change_mode)

        self.option_var.trace_variable('w',self.set_option)



    #   Canvas Topo Linking Methods

    def new_cover(self, from_node):
        """
        Create an EditorProjection and return it.

        If there is more than one representation for connections/
        projections, the returned object will depend on the current
        selection.
        """
        return EditorProjection("", self.canvas, from_node)

    def create_connection(self, editor_connection, node):
        "Connects the editor connection and the topo simulation connection."

        if self.parameter_tool.focus:
            self.parameter_tool.update_parameters()
        sim = self.canvas.simulation
        from_node = editor_connection.from_node.simobj
        to_node = node.simobj
        con_type = self.proj_list[self.current_option]
        con_name = con_type.name
        # CEBHACKALERT: see alert about sheet name

        # CEBHACKALERT: should probably catch a specific error?
        try:
            if con_name is not None:
                con = sim.connect(from_node.name,to_node.name,connection_type=con_type,name=con_name)
            else:
                con = sim.connect(from_node.name,to_node.name,connection_type=con_type)
        except Exception, e:
            param.Parameterized().warning("Unable to connect these sheets with the given "+ self.current_option + " (" + str(e) +").")
            editor_connection.remove()
            return False

        editor_connection.connect(node, con)
        return True


    def set_option(self,*args):
        """ """
        self.current_option = self.option_var.get()
        self.change_mode(None)


    #   Focus Methods

    def change_mode(self, option):
        self.canvas.change_mode('c') # ('CONNECTION')

    def set_focus(self, focus):
        "Change the background highlight to reflect whether this toolbar item is selected."

        if (focus):
            col = 'dark grey'; relief = GROOVE
            if not(self.parameter_tool == None):
                current_option = self.proj_list[self.current_option]
                name = str(current_option).split('.')[-1][:-2]
                self.parameter_tool.set_focus(name, current_option, self.doc)
        else:
            col = 'light grey'; relief = RAISED

        # ALERT
        self.config(bg = col, relief = relief)
        self.title_label.config(bg = col)
        #self.option_menu.config(bg = col)


class ParametersTool(Frame):

    def __init__(self, parent = None):

        # CEBALERT: need to tidy up the title, positioning, etc.
        Frame.__init__(self, parent)
        self.focus = None
        # label
        self.title_label = Label(self)
        self.title_label.pack(side = TOP)
        self.doc_label = Label(self, font = ("Times", 12))
        self.doc_label.pack(side = TOP)

        # CEBALERT: will the users think they have to press 'apply' rather than just clicking
        # on the canvas to get the new object?
        self.parameter_frame = tk.ParametersFrameWithApply(self)#,buttons_to_remove=['Close','Defaults'])
        self.parameter_frame.hide_param('Close')
        self.parameter_frame.hide_param('Defaults')
        self.parameter_frame.pack(side=BOTTOM)

    def update_parameters(self):
        self.parameter_frame.update_parameters()


    def set_focus(self, name, focus_class, doc = ''):

        self.focus = name

        self.title_label.config(text = name)
        self.doc_label.config(text = doc)

        if focus_class:
            self.parameter_frame.set_PO(focus_class)



###########################################################################
## OBJECTS
###########################################################################

# CEBALERT: should be a Parameterized
class EditorObject(object):
    """
    Anything that can be added and manipulated in an EditorCanvas. Every EditorCanvas
    has a corresponding Topo object associated with it. An instance of this class can
    have the focus.
    """
    FROM = 0
    TO = 1

    def __init__(self, name, canvas,**params):
        self.canvas = canvas # retains a reference to the canvas
        self.name = name # set the name of the sheet
        self.focus = False # this does not have the focus
        self.viewing_choices = []
        self.label=None

    def draw(self):
        "Draw the object at the current x, y position."
        pass

    def objdoc(self):
        """Documentation string for this object."""
        ### JABALERT: Should be expanded to allow a per-object description,
        ### and should be bound to the actual editor object as well.
        return self.name + " is of type " + \
               shortclassname(self.simobj) + \
               ":\n\n" + str(getdoc(self.simobj))

    def show_properties(self):
        "Show parameters frame for object."

        parameter_window = tk.AppWindow(topo.guimain,status=True)
        #status=tk.StatusBar(parameter_window)
        #status.pack(side="bottom",fill='x',expand='yes')

        parameter_window.title(self.name)
        balloon = tk.Balloon(parameter_window)

#        import __main__;__main__.__dict__['AAA'] = parameter_window
        title = Label(parameter_window, text = self.name)
        title.pack(side = TOP)
        self.parameter_frame = tk.ParametersFrameWithApply(
            parameter_window,
            msg_handler=parameter_window.status)
        parameter_window.sizeright()

        balloon.bind(title,self.objdoc())
        self.parameter_window = parameter_window

    def update_parameters(self):
        self.parameter_frame.update_parameters()

    def okay_parameters(self, parameter_window):
        self.update_parameters()
        parameter_window.destroy()

    def set_focus(self, focus) : # set focus
        self.focus = focus

    def move(self):
        "Update position of object and redraw."
        pass

    def remove(self):
        "Remove this object from the canvas and from the Topographica simulation."
        pass

    def in_bounds(self, x, y) :
        "Return true if x,y lies within this gui object's boundary."
        pass



class EditorNode(EditorObject):
    """
    An EditorNode is used to cover any topographica node, presently this can only be a sheet.
    It is a sub class of EditorObject and supplies the methods required by any node to be used
    in a EditorCanvas. Extending classes will supply a draw method and other type specific
    attributes.
    """
    show_label= param.Boolean(default=True,
        doc="Whether to show a textual label for this object")

    def __init__(self, canvas, simobj, pos, name):
        EditorObject.__init__(self, name, canvas)
        self.from_connections = [] # connections from this node
        self.to_connections = [] # connections to this node
        self.x = pos[0] # set the x and y coords of the center of this node
        self.y = pos[1]
        self.mode = canvas.display_mode
        self.simobj = simobj

    #   Connection methods

    def attach_connection(self, con, from_to):
        if (from_to == self.FROM):
            if (con.from_node == con.to_node):
                self.from_connections = [con] + self.from_connections
            else:
                self.from_connections = self.from_connections + [con]
        else:
            if (con.from_node == con.to_node):
                self.to_connections = [con] + self.to_connections
            else:
                self.to_connections = self.to_connections + [con]

    def remove_connection(self, con, from_to) : # remove a connection to or from this node
        if (from_to):
            l = len(self.to_connections)
            for i in range(l):
                if (con == self.to_connections[i]) : break
            else : return
            del self.to_connections[i]
        else:
            l = len(self.from_connections)
            for i in range(l):
                if (con == self.from_connections[i]) : break
            else : return
            del self.from_connections[i]


    #   Util methods

    def get_pos(self):
        return (self.x, self.y) # return center point of node

    def show_properties(self):
        EditorObject.show_properties(self)
        self.parameter_frame.set_PO(self.simobj)
        Label(self.parameter_window, text = '\n\nConnections').pack(side = TOP)
        connections = list(set(self.to_connections).union(set(self.from_connections)))
        connection_list = [con.name for con in connections]

        self.connection_var = StringVar()
        self.connection_var.set(connection_list[0])

        connection_menu = OptionMenu(self.parameter_window,self.connection_var,*connection_list)

        self.connection_var.trace_variable('w',self.view_connection_parameters)

        connection_menu.pack(side = TOP)

    def view_connection_parameters(self, *args):
        con_sel = self.connection_var.get()
        for con in self.to_connections + self.from_connections:
            if con.name == con_sel:
                break
        else :
            return
        con.show_properties()



# JABALERT: Should probably combine this with EditorNode
class EditorEP(EditorNode):
    """
    Represents any topo EventProcessor as a small, fixed-size oval by default.
    """

    def __init__(self, canvas, simobj, pos, name):
        EditorNode.__init__(self, canvas, simobj, pos, name)
        simobj.layout_location = (self.x,self.y) # store the ed coords in the topo sheet
        self.set_bounds()

        self.set_colours()
        col = self.colour[1]
        self.init_draw(col, False) # create a new parallelogram
        self.currentCol = col
        self.gradient = 1

    #   Draw methods

    def set_focus(self, focus):
        for id in self.id:
            self.canvas.delete(id)
        self.canvas.delete(self.label) # remove label
        EditorNode.set_focus(self, focus) # call to super's set focus
        col = self.colour[not focus]
        self.init_draw(col, focus) # create new one with correct colour
        self.currentCol = col
        self.draw()

    def select_view(self, view_choice):
        self.view = view_choice
        self.set_focus(False)
        self.canvas.redraw_objects()

    def set_colours(self):
        colour = {'video':('dark red','black'),
                  'normal':('slate blue', 'lavender'),
                  'printing':('grey','white')}
        self.colour = colour[self.mode] # colours for drawing this node on the canvas

    def init_draw(self, colour, focus):
        if focus : label_colour = colour
        else : label_colour = 'black'
        h, w = 0.5*self.height, 0.5*self.width

        x, y = self.x, self.y
        x1,y1 = (x-w,y-h)
        x2,y2 = (x+w,y+h)

        self.id = [self.canvas.create_oval(x1,y1,x2,y2,fill=colour,outline="black")]
        dX = w + 5
        if (self.show_label):
            self.label = self.canvas.create_text(x - dX, y, anchor = E, fill = label_colour, text = self.name)

    def dec_to_hex_str(self, val, length):
        # expects a normalised value and maps it to a hex value of the given length
        max_val = pow(16, length) - 1
        fmt = '%%0%dx'%length
        return fmt % (val*max_val)

    def draw(self, x = 0, y = 0):
        # move the parallelogram and label by the given x, y coords (default redraw)
        if not(x == y == 0):
            for id in self.id:
                self.canvas.move(id, x, y)
            if (self.show_label):
                self.canvas.move(self.label, x, y)
        for id in self.id:
            self.canvas.tag_raise(id)
        if (self.show_label):
            self.canvas.tag_raise(self.label)
        # redraw the connections
        for con in self.to_connections :
            if (con.from_node == con.to_node):
                con.move()
        for con in self.to_connections:
            if (not(con.from_node == con.to_node)):
                con.move()
        for con in self.from_connections:
            if (not(con.from_node == con.to_node)):
                con.move()


    #   Update methods

    def remove(self):
        l = len(self.from_connections) # remove all the connections from and to this sheet
        for index in range(l):
            self.from_connections[0].remove()
        l = len(self.to_connections)
        for index in range(l):
            self.to_connections[0].remove()
        for id in self.id:
            self.canvas.delete(id)
        self.canvas.delete(self.label)
        self.canvas.remove_object(self) # remove from canvas' object list
        del topo.sim[self.simobj.name] # actually delete the sheet

    def move(self, x, y):
        # the connections position is updated
        old = self.x, self.y
        self.x = x
        self.y = y
        self.simobj.layout_location = (self.x,self.y) # update topo sheet position
        self.draw(self.x - old[0], self.y - old[1])


    #   Connection methods

    def remove_connection(self, con, from_to):
        EditorNode.remove_connection(self, con, from_to)
        if from_to:
            node = con.from_node
        else:
            node = con.to_node
        index = con.draw_index
        # Decrease the indexes of the connections between the same nodes and with a higher index.
        for connection in self.from_connections:
            if (node == connection.to_node and connection.draw_index >= index):
                connection.decrement_draw_index()
            if connection.to_node == connection.from_node : return
        for connection in self.to_connections :
            if (node == connection.from_node and connection.draw_index >= index):
                connection.decrement_draw_index()

    def get_connection_count(self, node):
        count = 0
        for con in self.from_connections:
            if (con.to_node == node):
                count += 1
        for con in self.to_connections:
            if (con.from_node == node):
                count += 1
        if node == self : count /= 2
        return count


    #   Util methods

    def in_bounds(self, pos_x, pos_y):
        return ((pos_x> self.x-self.width)  and (pos_x<= self.x+self.width) and
                (pos_y> self.y-self.height) and (pos_y<= self.y+self.height))


    def set_bounds(self):
        # Default representation: fixed-size node
        self.width=15
        self.height=self.width*0.7


    def set_mode(self, mode):
        self.mode = mode
        self.set_colours()

        for id in self.id:
            self.canvas.delete(id)
        self.canvas.delete(self.label) # remove label
        self.init_draw(self.colour[not self.focus], self.focus)
        for con in self.to_connections:
            con.set_mode(mode)
        for con in self.from_connections:
            con.draw()




class EditorSheet(EditorEP):
    """
    Represents any topo sheet. It is a subclass of EditorEP and fills in the
    methods that are not defined. It is represented by a Parallelogram in its
    Canvas. The colours used for drawing can be set. Uses bounding box to
    determine if x, y coord is within its boundary.
    """
    normalize = param.Boolean(default=False)
    show_density = param.Boolean(default=False)
    view = param.ObjectSelector(default='activity',objects=['normal','activity'])

    def __init__(self, canvas, simobj, pos, name):
        # Should call EditorEP's constructor instead
        EditorNode.__init__(self, canvas, simobj, pos, name)
        simobj.layout_location = (self.x,self.y) # store the ed coords in the topo sheet
        self.element_count = self.matrix_element_count()
        self.set_bounds()

        self.set_colours()
        col = self.colour[1]
        self.init_draw(col, False) # create a new parallelogram
        self.currentCol = col
        self.gradient = 1
        self.viewing_choices = [('Normal', lambda: self.select_view('normal')),
                                ('Activity', lambda: self.select_view('activity'))]


    #   Draw methods

    def set_focus(self, focus):
        for id in self.id:
            self.canvas.delete(id)
        self.canvas.delete(self.label) # remove label
        EditorNode.set_focus(self, focus) # call to super's set focus
        col = self.colour[not focus]
        self.init_draw(col, focus) # create new one with correct colour
        self.currentCol = col
        self.draw()

    def init_draw(self, colour, focus):
        self.id = []
        if focus : label_colour = colour
        else : label_colour = 'black'
        factor = self.canvas.scaling_factor
        h, w = 0.5 * self.height * factor, 0.5 * self.width *factor
        if not(self.focus):
            if self.view == 'activity':
                colour = ''
                x, y = self.x - w + h, self.y - h
                # AL, the idea will be to allow any available plots to be shown on the sheet.
                # eg m = self.simobj.sheet_views['OrientationPreference'].view()[0]
                update_activity()
                m = self.simobj.views.Maps['ActivityBuffer'].last.data
                if self.normalize == True:
                    m = self.normalize_plot(m)
                matrix_width, matrix_height = self.element_count
                dX, dY = (w * 2)/ matrix_width, (h * 2) / matrix_height
                for i in range(matrix_height):
                    for j in range(matrix_width):
                        a = i * dY
                        x1, y1 = x - a + (j * dX), y + a
                        x2, y2 = x1 - dY, y1 + dY
                        x3, x4 = x2 + dX, x1 + dX
                        point = m[i,j]
                        if point < 0 : point = 0.0
                        if point > 1 : point = 1.0
                        col = '#' + (self.dec_to_hex_str(point, 3)) * 3
                        self.id = self.id + [self.canvas.create_polygon
                           (x1, y1, x2, y2, x3, y2, x4, y1, fill = col, outline = col)]
        x, y = self.x, self.y
        x1,y1 = (x - w - h, y + h)
        x2,y2 = (x - w + h, y - h)
        x3,y3 = x2 + (w * 2), y2
        x4,y4 = x1 + (w * 2), y1
        self.id = self.id + [self.canvas.create_polygon(x1, y1, x2, y2, x3, y3, x4, y4,
            fill = colour , outline = "black")]
        dX = w + 5
        if (self.show_label):
            self.label = self.canvas.create_text(x - dX, y, anchor = E, fill = label_colour, text = self.name)
        # adds a density grid over the sheet
        if self.show_density:
            x, y = self.x - w + h, self.y - h
            matrix_width, matrix_height = self.element_count
            dX, dY = (w * 2)/ matrix_width, (h * 2) / matrix_height
            for i in range(matrix_height + 1):
                x1 = x - (i * dY)
                x2 = x1 + (w * 2)
                y1 = y + (i * dY)
                self.id = self.id + [self.canvas.create_line(x1, y1, x2, y1, fill = 'slate blue')]
            for j in range(matrix_width + 1):
                x1 = x + (j * dX)
                x2 = x1 - (h * 2)
                y1 = y
                y2 = y1 + (h * 2)
                self.id = self.id + [self.canvas.create_line(x1, y1, x2, y2, fill = 'slate blue')]

    def normalize_plot(self,a):
        """
        Normalize an array s.
        In case of a constant array, ones is returned for value greater than zero,
        and zeros in case of value inferior or equal to zero.
        """
        # AL is it possible to use the normalize method in plot?
        import numpy as np
        a_offset = a-min(a.ravel())
        max_a_offset = max(a_offset.ravel())
        if max_a_offset>0:
             a = np.divide(a_offset,float(max_a_offset))
        else:
             if min(a.ravel())<=0:
                  a=np.zeros(a.shape, dtype=np.float)
             else:
                  a=np.ones(a.shape, dtype=np.float)
        return a

    #   Util methods

    def in_bounds(self, pos_x, pos_y) : # returns true if point lies in a bounding box
        # if the coord is pressed within the parallelogram representation this
        # returns true.
        # Get the parallelogram points and centers them around the given point
        x = self.x - pos_x; y = self.y - pos_y
        w = 0.5 * self.width * self.canvas.scaling_factor
        h = 0.5 * self.height * self.canvas.scaling_factor
        A = (x - w - h, y + h)
        B = (x - w + h, y - h)
        C = B[0] + (2 * w), B[1]
        D = A[0] + (2 * w), A[1]
        # calculate the line constants
        # As the gradient of the lines is 1 the calculation is simple.
        a_AB = A[1] + A[0]
        a_CD = C[1] + C[0]
        # The points are centered around the given coord, finding the
        # intersects with line y = 0 and ensuring that the left line
        # lies on the negative side of the point and the right line
        # lies on the positive side of the point determines that the
        # point is within the parallelogram.
        if ((D[1] >= 0) and (B[1] <= 0) and (a_AB <= 0) and (a_CD >= 0)):
            return True
        return False


    def matrix_element_count(self):
        # returns the length and width of the matrix that holds this sheet's plot values
        l,b,r,t = self.simobj.bounds.aarect().lbrt()
        density = self.simobj.xdensity
        return int(density * (r - l)), int(density * (t - b))

    def set_bounds(self):
        # Use the default sheet bounds as to set the "normal" size
        # of SheetObject in the GUI, so simulations using very large
        # sheets still look normal.
        dl,db,dr,dt = self.simobj.__class__.nominal_bounds.aarect().lbrt()
        width_fact = 120.0 / (dr - dl)
        height_fact = 60.0 / (dt - db)
        l,b,r,t = self.simobj.bounds.aarect().lbrt()
        self.width = width_fact * (r - l) * self.canvas.scaling_factor
        self.height = height_fact * (t - b) * self.canvas.scaling_factor




class EditorConnection(EditorObject):

    """
    A connection formed between 2 EditorNodes on a EditorCanvas. A EditorConnection is used
    to cover any topographica connection (connection / projection), and extending
    classes will supply a draw method and other type specific attributes.
    """

    show_label= param.Boolean(default=True,
        doc="Whether to show a textual label for this object")

    def __init__(self, name, canvas, from_node):
        EditorObject.__init__(self, name, canvas)
        self.from_node = from_node # initial node selected
        self.to_node = None # updated when the user selects the second node - self.connect(..)
        # temporary point, for when the to connection node is undefined
        self.to_position = from_node.get_pos()
        self.mode = canvas.display_mode


    #   Draw methods

    def set_focus(self, focus) : # give this connection the focus
        EditorObject.set_focus(self, focus)
        self.draw()


    #   Update methods

    def move(self):
        # if one of the nodes connected by this connection move, then move by redrawing
        self.draw()

    def update_position(self, pos) : # update the temporary point
        self.to_position = pos
        self.draw()

    def connect(self, to_node, con) : # pass the node this connection is to
        self.simobj = con
        if (self.name == ""):
            self.name = con.name
        self.to_node = to_node # store a reference to the node this is connected to
        self.to_position = None
        self.from_node.attach_connection(self, self.FROM) # tell the sheets that they are connected.
        self.to_node.attach_connection(self, self.TO)

    def remove(self):
        # CEBALERT: there's no code here to handle GUI object
        # removal (though the EditorProjection subclass does have GUI
        # removal code, so presumably projections do get removed from
        # the screen. But I'm confused about what is treated as a
        # connection, and what as a projection in the model editor).
        if hasattr(self,'simobj'):
            self.simobj.remove()


    #   Util methods

    def show_properties(self):
        EditorObject.show_properties(self)
        self.parameter_frame.set_PO(self.simobj)


# JABALERT: Should probably combine this with EditorConnection
class EditorEPConnection(EditorConnection):
    """
    Represents any topo EPConnection using a line with an arrow head in the middle.
    """

    def __init__(self, name, canvas, from_node):
        EditorConnection.__init__(self, name, canvas, from_node)
        # if more than one connection between nodes,
        # this will reflect how to draw this connection
        self.draw_index = 0
        self.deviation = 0
        self.gradient = (1,1)
        self.id = (None,None)
        self.balloon = tk.Balloon(canvas)
        self.set_colours()
        self.view = 'line'
        self.draw_fn = self.draw_line
        self.viewing_choices = [('Line', lambda: self.select_view('line'))]
        self.update_factor()

    #   Draw methods

    def select_view(self, view_choice):
        self.view = view_choice
        self.move()
        self.set_focus(False)

    def set_colours(self):
        colours = {'video' : ('dark red', 'blue', 'yellow'),
                   'normal': ('dark red', 'blue', 'yellow'),
                   'printing': ('grey', 'black', 'black')}
        self.colour = colours[self.mode]

    def draw(self):
        # determine if connected to a second node, and find the correct from_position
        for id in self.id : # remove the old connection
            self.canvas.delete(id)
        self.canvas.delete(self.label)
        from_position = self.from_node.get_pos() # get the center points of the two nodes
        if (self.to_node == None) :  # if not connected yet, use temporary point.
            to_position = self.to_position
        else:
            to_position = self.to_node.get_pos()

        self.draw_fn(from_position, to_position)

    def draw_line(self,from_position, to_position):
        # set the colour to be used depending on whether connection has the focus.
        if (self.focus) :
            text_col = col = self.colour[0]
        else:
            text_col = 'black'
            col = self.colour[1]
        middle = self.get_middle(from_position, to_position)
        factor = self.canvas.scaling_factor
        if (to_position == from_position) : # connection to and from the same node
            deviation = self.draw_index * 15 * factor
            x1 = to_position[0] - ((20 * factor) + deviation)
            y2 = to_position[1]
            x2 = x1 + (40 * factor) + (2 * deviation)
            y1 = y2 - ((30 * factor) + deviation)
            midX = self.get_middle((x1,0),(x2,0))[0]
            # create oval and an arrow head.
            self.id = (self.canvas.create_oval(x1, y1, x2, y2, outline = col),
            self.canvas.create_line(midX, y1, midX+1, y1, arrow = FIRST, fill = col))
            # draw name label beside arrow head
            if (self.show_label):
                self.label = self.canvas.create_text(middle[0] -
                    (20 + len(self.name)*3), middle[1] - (30 + deviation) , text = self.name)
        else :
            # create a line between the nodes - use 2 to make arrow in center.
            dev = self.deviation
            from_pos = from_position[0] + self.deviation, from_position[1]
            mid = middle[0] + 0.5 * dev, middle[1]
            self.id = (self.canvas.create_line(from_pos, mid , arrow = LAST, fill = col),
                    self.canvas.create_line(mid, to_position, fill = col))
            # draw name label
            dX = 20 * factor
            dY = self.draw_index * 20 * factor
            if (self.show_label):
                self.label = self.canvas.create_text(middle[0] - dX,
                    middle[1] - dY, fill = text_col, text = self.name, anchor = E)


    #   Update methods
    def remove(self):
        if (self.to_node != None) : # if a connection had been made then remove it from the 'to' node
            self.to_node.remove_connection(self, self.TO)
            self.from_node.remove_connection(self, self.FROM) # and remove from 'from' node
        for id in self.id : # remove the representation from the canvas
            self.canvas.delete(id)
        self.canvas.delete(self.label)

        # CEBALERT: see earlier alert about EditorObject not inheriting from object.
        EditorConnection.remove(self) #super(EditorProjection,self).remove()


    def move(self):
        # if one of the nodes connected by this connection move, then move by redrawing
        self.gradient = self.calculate_gradient()
        self.update_factor()
        self.draw()

    def decrement_draw_index(self):
        self.draw_index -= 1
        if self.to_node == self.from_node:
            self.update_factor()
        else:
            self.connect_to_coord((self.from_node.width / 2) - 10)

    def connect(self, to_node, con):
        EditorConnection.connect(self, to_node, con)
        self.draw_index = self.from_node.get_connection_count(to_node)-1
        if (self.from_node == to_node):
            self.update_factor()
        else:
            self.connect_to_coord((self.from_node.width / 2) - 10)
        self.gradient = self.calculate_gradient()
        self.radius = self.get_radius()

    #   Util methods

    def get_middle(self, pos1, pos2) : # returns the middle of two points
        return (pos1[0] + (pos2[0] - pos1[0])*0.5, pos1[1] + (pos2[1] - pos1[1])*0.5)

    def get_radius(self):
        """Not implemented in this class"""
        return (0,0)

    def update_factor(self):
        pass

    def connect_to_coord(self, width):
        n = self.draw_index
        sign = math.pow(-1, n)
        self.deviation = sign * width + (-sign) * math.pow(0.5, math.ceil(0.5 * (n))) * width

    # returns the gradients of the two lines making the opening 'v' part of the receptive field.
    # this depends on the draw_index, as it determines where the projection's representation begins.
    def calculate_gradient(self):
        """Not implemented in this class"""
        return (1,1)

    def in_bounds(self, x, y) : # returns true if point lies in a bounding box
        factor = self.canvas.scaling_factor
        # If connections are represented as lines
        # currently uses an extent around the arrow head.
        to_position = self.to_node.get_pos()
        from_position = self.from_node.get_pos()
        if (self.to_node == self.from_node):
            dev = self.draw_index * 15 * factor
            middle = (to_position[0], to_position[1] - ((30 * factor) + dev))
        else:
            dev = self.deviation * 0.5
            middle = self.get_middle(from_position, to_position)
        if ((x < middle[0] + 10 + dev) & (x > middle[0] - 10 + dev) & (y < middle[1] + 10) & (y > middle[1] - 10)):
            return True
        return False

    def set_mode(self, mode):
        self.mode = mode
        self.set_colours()
        self.draw()



class EditorProjection(EditorEPConnection):
    """
    Represents any topo CFProjection. It is a subclass of EditorEPConnection and fills
    in the methods that are not defined. Can be represented by a representation of a
    projection's receptive field or by a line with an arrow head in the middle;
    lateral projections are represented by a dotted ellipse around the center.
    Can determine if x,y coord is within the triangular receptive field or within an
    area around the arrow head. The same can be determined for a lateral projection
    ellipse.
    """

    def __init__(self, name, canvas, from_node, receptive_field = True):
        EditorEPConnection.__init__(self, name, canvas, from_node)
        # if more than one connection between nodes,
        # this will reflect how to draw this connection
        self.normal_radius = 15
        self.radius = self.get_radius()
        self.receptive_field = receptive_field
        self.view = 'radius'
        self.viewing_choices = [('Field Radius', lambda: self.select_view('radius')),
                                ('Line', lambda: self.select_view('line')),
                                ('Fixed Size', lambda: self.select_view('normal'))]


    #   Draw methods

    def draw(self):
        self.draw_fn = \
        {'normal' : self.draw_normal,
         'line' :   self.draw_line,
         'radius' : self.draw_radius
        }[self.view]
        EditorEPConnection.draw(self)


    def draw_radius(self, from_position, to_position):
         # set the colour to be used depending on whether connection has the focus.
        if (self.focus) :
            text_col = col = self.colour[0]
            lateral_colour = self.from_node.colour[0]
        else:
            text_col = 'black'
            col = self.colour[1]
            lateral_colour = ''
        # midpoint of line
        middle = self.get_middle(from_position, to_position)
        if (to_position == from_position) : # connection to and from the same node
            a, b = self.get_radius()
            x1 = to_position[0] - a
            y1 = to_position[1] + b
            x2 = to_position[0] + a
            y2 = to_position[1] - b
            self.id = (self.canvas.create_oval(x1, y1, x2, y2, fill = lateral_colour,
                dash = (2,2), outline = self.colour[2], width = 2), None)

# CEBALERT: as far as I know, this balloon binding never worked.
#            self.balloon.tagbind(self.canvas, self.id[0], self.name)

        else :  # connection between distinct nodes
            x1, y1 = to_position
            x2, y2 = from_position
            # this is for cases when the radius changes size.
            radius_x, radius_y = self.get_radius()
            self.id = (self.canvas.create_line(x1, y1, x2 - radius_x, y2, fill = col),
                self.canvas.create_line(x1, y1, x2 + radius_x, y2, fill = col),
                self.canvas.create_oval(x2 - radius_x, y2 - radius_y,
                    x2 + radius_x, y2 + radius_y, outline = col))
            # draw name label
            dX = 20
            dY = self.draw_index * 20
            if (self.show_label):
                self.label = self.canvas.create_text(middle[0] - dX,
                    middle[1] - dY, fill = text_col, text = self.name, anchor = E)


    def draw_normal(self, from_position, to_position):
        # set the colour to be used depending on whether connection has the focus.
        if (self.focus) :
            text_col = col = self.colour[0]
            lateral_colour = self.from_node.colour[0]
        else:
            text_col = 'black'
            col = self.colour[1]
            lateral_colour = ''
        # midpoint of line
        middle = self.get_middle(from_position, to_position)
        if (to_position == from_position) : # connection to and from the same node
            a, b = self.factor
            x1 = to_position[0] - a
            y1 = to_position[1] + b
            x2 = to_position[0] + a
            y2 = to_position[1] - b
            self.id = (self.canvas.create_oval(x1, y1, x2, y2, fill = lateral_colour,
                dash = (2,2), outline = self.colour[2], width = 2), None)

#            self.balloon.tagbind(self.canvas, self.id[0], self.name)

        else :  # connection between distinct nodes
            x1, y1 = to_position
            x2, y2 = from_position
            x2 += self.deviation
            radius = self.normal_radius
            self.id = (self.canvas.create_line(x1, y1, x2 - radius, y2, fill = col),
                self.canvas.create_line(x1, y1, x2 + radius, y2, fill = col),
                self.canvas.create_oval(x2 - radius, y2 - (0.5 * radius),
                x2 + radius, y2 + (0.5 * radius), outline = col))
            # draw name label
            dX = 20
            dY = self.draw_index * 20
            if (self.show_label):
                self.label = self.canvas.create_text(middle[0] - dX,
                    middle[1] - dY, fill = text_col, text = self.name, anchor = E)


    #   Util methods

    def get_radius(self):
        factor = self.canvas.scaling_factor
        if self.to_node == None:
            return (factor * self.normal_radius, factor * self.normal_radius *
                self.from_node.height / self.from_node.width)
        node = self.from_node
        node_bounds = node.simobj.bounds.aarect().lbrt()

        try:
            bounds = self.simobj.bounds_template.lbrt()
        except AttributeError:
            return (factor * self.normal_radius, factor * self.normal_radius *
                self.from_node.height / self.from_node.width)
        radius_x = factor * (node.width / 2) * (bounds[2] - bounds[0]) / (node_bounds[2] - node_bounds[0])
        radius_y = radius_x * node.height / node.width
        return radius_x, radius_y

    # returns the size of the semimajor and semiminor axis of the ellipse representing
    # the draw_index-th lateral projection.
    def get_factor(self):
        factor = self.canvas.scaling_factor
        w = factor * self.from_node.width; h = factor * self.from_node.height
        a = 20; n = (w / 2) - 10; b = (n - a)
        major = a + (b * (1 - pow(0.8, self.draw_index)))
        a = 20 * h / w; n = (h / 2) - 10; b = (n - a)
        minor = a + (b * (1 - pow(0.8, self.draw_index)))
        return major, minor

    def update_factor(self):
        self.factor = self.get_factor()

    # returns the gradients of the two lines making the opening 'v' part of the receptive field.
    # this depends on the draw_index, as it determines where the projection's representation begins.
    def calculate_gradient(self):
        factor = self.canvas.scaling_factor
        if self.view == 'radius':
            A = self.to_node.get_pos()
            T = self.from_node.get_pos()
            B = (T[0] - self.radius[0], T[1])
            C = (T[0] + self.radius[0], T[1])
        else:
            A = self.to_node.get_pos()
            T = (self.from_node.get_pos()[0] + self.deviation ,self.from_node.get_pos()[1])
            B = (T[0] - (factor * self.normal_radius), T[1])
            C = (T[0] + (factor * self.normal_radius), T[1])
        den_BA = (A[0] - B[0])
        if not(den_BA == 0):
            m_BA = (A[1] - B[1]) / den_BA
        else :
            m_BA = 99999 # AL - this should be a big number
        den_CA = (A[0] - C[0])
        if not(den_CA == 0):
            m_CA = (A[1] - C[1]) / den_CA
        else :
            m_CA = 99999 # AL - this should be a big number
        return (m_BA, m_CA)

    def in_bounds(self, x, y) : # returns true if point lies in a bounding box
        factor = self.canvas.scaling_factor
        if self.view == 'line':
            return EditorEPConnection.in_bounds(self,x,y)
        else:
            # returns true if x, y lie inside the oval representing this lateral projection
            if (self.to_node == None or self.to_node == self.from_node):
                if self.view == 'radius':
                    a, b = self.get_radius()
                else:
                    a, b = self.factor
                x, y = x - self.to_node.get_pos()[0], y - self.to_node.get_pos()[1]
                if (x > a or x < -a):
                    return False
                pY = math.sqrt(pow(b,2) * (1 - (pow(x,2)/pow(a,2))))
                if (y > pY or y < -pY):
                    return False
                return True
            # returns true if x, y lie inside the triangular receptive
            # field representing this projection get the points of the
            # triangular receptive field, centered around the x, y
            # point given
            to_position = self.to_node.get_pos()
            from_position = self.from_node.get_pos()
            if self.view == 'radius':
                A = (to_position[0] - x, to_position[1] - y)
                T = (from_position[0] + (self.deviation * factor) - x, from_position[1] - y)
                B = (T[0] - self.radius[0], T[1])
                #C = (T[0] + self.radius[0], T[1])
            else:
                A = (to_position[0] - x, to_position[1] - y)
                T = (from_position[0] + (self.deviation * factor) - x, from_position[1] - y)
                B = (T[0] - (self.normal_radius * factor), T[1])
                #C = (T[0] + (self.normal_radius * factor), T[1])
            # if the y coords lie outwith the boundaries, return false
            if (((A[1] < B[1]) and (B[1] < 0 or A[1] > 0)) or
                ((A[1] >= B[1]) and (B[1] > 0 or A[1] < 0))):
                return False
            # calculate the constant for the lines of the triangle
            a_BA = A[1] - (self.gradient[0] * A[0])
            a_CA = A[1] - (self.gradient[1] * A[0])
            # The points are centered around the given coord, finding
            # the intersects with line y = 0 and ensuring that the
            # left line lies on the negative side of the point and the
            # right line lies on the positive side of the point
            # determines that the point is within the triangle.
            if (((0 - a_CA) / self.gradient[1] >= 0) and ((0 - a_BA) / self.gradient[0] <= 0)):
                return True
            return False
