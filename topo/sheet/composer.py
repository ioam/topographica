"""
A Sheet class for composing activity from different sheets into a
single activity matrix.  Primarily a simple example of how to make
a sheet class, but can also be useful.
"""
import numpy as np

from topo.base.sheet import Sheet
from topo.misc.util import Struct, NxN

class Composer(Sheet):
    """
    A Sheet that combines the activity of 2 or more other sheets into
    a single activity matrix.  When connecting a sheet to a composer,
    you can specify the location at which that sheet's input will be
    mapped into the composer by adding the 'origin' argument to the
    connect() call e.g.:

    sim.connect(input_sheet.name,composer.name,delay=1, origin=(0.25,0.25))

    will cause (0,0) on input sheet's activity to map to (0.25,0.25)
    on composer's activity.

    """

    dest_ports=None # Allows connections to come in on any port

    def __init__(self,**params):
        super(Composer,self).__init__(**params)
        self.inputs = {}
        self.__dirty = False

    def port_configure(self,port,**config):
        """
        Configure a specific input port.

        origin = (default (0,0)) The offset in the output matrix where
        this port's input should be placed.
        """
        if not port in self.ports:
            self.ports[port] = {}

        for k,v in config.items():
            self.ports[port][k] = v

    def _dest_connect(self,proj,origin=(0,0)):
        super(Composer,self)._dest_connect(proj)
        self.inputs[(proj.src.name,proj.src_port)] = Struct(origin=origin)

    def process_current_time(self):
        if self.__dirty:
            self.send_output(data=self.activity)
            self.activity = np.zeros(self.activity.shape)+0.0
            self.__dirty=False

    def input_event(self,conn,data):

        self.verbose("Received %s input from %s." % (NxN(data.shape),conn.src))

        self.__dirty = True

        in_rows, in_cols = data.shape

        # compute the correct position of the input in the buffer
        start_row,start_col = self.sheet2matrixidx(*self.inputs[(conn.src.name,conn.src_port)].origin)
        row_adj,col_adj = conn.src.sheet2matrixidx(0,0)

        self.debug("origin (row,col) = "+`(start_row,start_col)`)
        self.debug("adjust (row,col) = "+`(row_adj,col_adj)`)

        start_row -= row_adj
        start_col -= col_adj

        # the maximum bounds
        max_row,max_col = self.activity.shape

        self.debug("max_row = %d, max_col = %d" % (max_row,max_col))
        self.debug("in_rows = %d, in_cols = %d" % (in_rows,in_cols))

        end_row = start_row+in_rows
        end_col = start_col+in_cols

        # if the input goes outside the activity, clip it
        left_clip = -min(start_col,0)
        top_clip  = -min(start_row,0)
        right_clip = max(end_col,max_col) - max_col
        bottom_clip = max(end_row,max_row) - max_row

        start_col += left_clip
        start_row += top_clip
        end_col -= right_clip
        end_row -= bottom_clip

        self.debug("start_row = %d,start_col = %d" % (start_row,start_col))
        self.debug("end_row = %d,end_col = %d" % (end_row,end_col))
        self.debug("left_clip = %d" % left_clip)
        self.debug("right_clip = %d" % right_clip)
        self.debug("top_clip = %d" % top_clip)
        self.debug("bottom_clip = %d" % bottom_clip)
        self.debug("activity shape = %s" % NxN(self.activity.shape))

        self.activity[start_row:end_row, start_col:end_col] += data[top_clip:in_rows-bottom_clip,
                                                                      left_clip:in_cols-right_clip]


__all__ = [
    "Composer",
]
