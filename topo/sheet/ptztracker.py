"""
This class finds the brightest pixel of the image, returns it in white and
other in black.
This class also gives instructions to move the camera.

$Id$
"""
__version__ = "$Revision$"



import param
from topo.base.sheet import Sheet
from topo.misc.ptz import PTZ
from topo.base.arrayutil import array_argmax


class BrightPixelTracker(Sheet):
    """
    Given an incoming Activity pattern, find the brightest pixel and
    output an activity pattern where all but this pixel is set to zero.
    Also controls a pan/tilt/zoom camera, instructing it to move so that
    the brightest pixel will be in the center of the sheet.
    """

    dest_ports=['Activity']
    src_ports=['Activity']

    ratio = param.Number(default=1.33,doc=
        "Ratio depends of the resolution of the camera, here 640x480.")

    fov_x = param.Number(default=76,doc=
        "Field of view along x in degrees, depends of the camera.")

    fov_y = param.Number(default=57,doc=
        """
        Field of view along y in degrees. It is calculate with the resolution
        of the camera, and its field of view. It also depends of the bounds used,
        here the size_normalization used is "fit_shortest". So Sheet coordinates
        along y for camera's image are between -0.5 and 0.5.     
        The original calculation is fov_y=fov_x*0.5*2/ratio.
        """)

    ptz = param.ClassSelector(PTZ,default=PTZ(),doc="""
        An instance of ptzcamera.PTZ to be controlled.""")

    # Max Ranges (determined with uvcdynctrl -v -c)
    maxrange_x = param.Number(default=4480, doc=
        """Maximum position of the camera along x.""")

    maxrange_y = param.Number(default=1920, doc=
        """Maximum position of the camera along y.""")   

    #Coordinates in degrees
    y_deg = 0
    x_deg = 0
    #Coordinates in degrees for uvcdynctrl(unit=1/64th of a degree)
    y_deg_uvc = 0
    x_deg_uvc = 0
    #Coordinates of the brightest pixel
    coor = (0,0)
    #Current postitions along x and y
    curr_y=0
    curr_x=0

    def input_event(self,conn,data):
        self.input_data=data

    def process_current_time(self):
        if hasattr(self, 'input_data'):
            self.activity*=0
            self.activity+=self.input_data

            #Find the brightest pixel of the image, put it in white and other pixels in black
            maximum=array_argmax(self.activity)
            self.activity*=0
            self.activity[maximum]+=1

            self.send_output(src_port='Activity',data=self.activity)
            del self.input_data


            #Find sheet's coordinates of the brightest pixel
            self.coor=self.matrixidx2sheet(*maximum)

            self.y_deg=self.coor[1]*(self.fov_y/2)/0.5
            self.x_deg=self.coor[0]*(self.fov_x/2)/(self.ratio/2)
            
            # The unit of uvcdynctrl is 1/64th of a degree
            ## HACK problem with the scaling. so divide by 2.
            ##it doesn't come from the fov or resolution maybe from somewhere with the coordinates
            self.y_deg_uvc=self.y_deg*64/2
            self.x_deg_uvc=self.x_deg*64/2
           
            self.message("Coordinates of the birghtest pixel: (%f,%f)" % (self.coor[0],self.coor[1]))
            self.verbose("Current position of the camera (%f,%f) along the two directions of the camera" % (self.curr_x,self.curr_y))
            self.verbose("Movements in degrees of uvcdynctrl (%f,%f)" % (self.x_deg_uvc,self.y_deg_uvc))

            #Use class PTZ in order to move the camera with uvcdynctrl
            # Max Ranges (determined with uvcdynctrl -v -c)
            if ((self.curr_y+self.y_deg_uvc<self.maxrange_y) and (self.curr_y+self.y_deg_uvc>-self.maxrange_y)):
                self.curr_y+=self.y_deg_uvc
                self.ptz.tilt(self.y_deg_uvc)
            else:
                self.message("The camera can't move further along y")
                
            if ((self.curr_x+self.x_deg_uvc<self.maxrange_x) and (self.curr_x+self.x_deg_uvc>-self.maxrange_x)):
                self.curr_x+=self.x_deg_uvc
                self.ptz.pan(self.x_deg_uvc)
            else:
                self.message("The camera can't move further along x")


