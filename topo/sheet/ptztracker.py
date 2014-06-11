"""
This class finds the brightest pixel of the image, returns it in white and
other in black.
This class also gives instructions to move the camera.
"""

import numpy as np
from PIL import  Image

import param
from topo.base.sheet import Sheet
from topo.hardware.ptz import PTZ
from topo.base.arrayutil import array_argmax


try:
    import opencv

except ImportError:
    param.Parameterized().warning("ptztracker.py classes will not be usable; python-opencv is not available.")


class PtzTracker(Sheet):
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

    ptz = param.ClassSelector(PTZ,default=None,doc="""
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

    def __init__(self, **params):
        # Set here to avoid having it one instantiated by default
        if self.ptz==None: self.ptz=PTZ()

    def input_event(self,conn,data):
        self.input_data=data

    def determine_next_position(self,img):
        """
        Determine the next location to move in the specified image, using whatever
        criterion is appropriate for this class.  Returns a tuple of (pos,bbox),
        where pos is the (row,column) coordinate of the next position, and bbox
        is a bounding box around that coordinate, with whatever size is appropriate
        for this class.  Returns None if no appropriate location can be found.
        """
        raise NotImplementedError


    def draw_boxes(self,input_data,bboxmin,bboxmax):
        """
        Draws three boxes arond the returned location.
        """
        opencv.cvRectangle(self.input_data, opencv.cvPoint(np.int(bboxmin[0]),np.int(bboxmin[1])),opencv.cvPoint(np.int(bboxmax[0])
            ,np.int(bboxmax[1])),0,1)
        opencv.cvRectangle(self.input_data, opencv.cvPoint(np.int(bboxmin[0])-1,np.int(bboxmin[1])-1),opencv.cvPoint(np.int(bboxmax[0])
            +1,np.int(bboxmax[1])+1),0,1)
        opencv.cvRectangle(self.input_data, opencv.cvPoint(np.int(bboxmin[0])-2,np.int(bboxmin[1])-2),opencv.cvPoint(np.int(bboxmax[0])
            +2,np.int(bboxmax[1])+2),1,1)


    def move_camera(self,pos, bboxmin, bbboxmax,brightpixel):
        """
        Move the camera to centre the returned location.
        """
        #Determinate the centre of the returned location
        if (self.brightpixel==True):
            self.pos=pos
        else:
            self.pos=(((self.bboxmax[0]+self.bboxmin[0])/2,(self.bboxmax[1]+self.bboxmin[1])/2))

        #Find sheet coordinates of the specified position
        self.coor=self.matrixidx2sheet(*self.pos)

        self.y_deg=self.coor[1]*(self.fov_y/2)/0.5
        self.x_deg=self.coor[0]*(self.fov_x/2)/(self.ratio/2)

        # The unit of uvcdynctrl is 1/64th of a degree
        ## HACK problem with the scaling. so divide by 2.
        ##it doesn't come from the fov or resolution maybe from somewhere with the coordinates
        self.y_deg_uvc=self.y_deg*64/2
        self.x_deg_uvc=self.x_deg*64/2

        self.message("Coordinates of the new position: (%f,%f)" % (self.coor[0],self.coor[1]))
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


    def process_current_time(self):
        if hasattr(self, 'input_data'):

            #Find the brightest pixel of the image, put it in white and other pixels in black
            result=self.determine_next_position(self.input_data)
            self.activity*=0

            if result: # Draw a box around the returned location
                self.pos,self.bboxmin,self.bboxmax,self.brightpixel=result
                self.draw_boxes(self.input_data,self.bboxmin,self.bboxmax)

            self.activity+=self.input_data
            self.send_output(src_port='Activity',data=self.activity)
            del self.input_data

            if not result:
                return # Else move camera

            self.move_camera(self.pos,self.bboxmin,self.bboxmax,self.brightpixel)



class BrightPixelTracker(PtzTracker):
    """
    This class is used to define the position of the brightest pixel
    in the image.
    """

    def determine_next_position(self,img):
        self.maximum=array_argmax(img)

        #Coordinates for the box around the brightest pixel
        self.coormin_bbox=(self.maximum[1]-1,self.maximum[0]-1)
        self.coormax_bbox=(self.maximum[1]+1,self.maximum[0]+1)
        self.brightpixel=True
        return(self.maximum,self.coormin_bbox,self.coormax_bbox,self.brightpixel)



class FaceTracker(PtzTracker):
    """
    This class is used to detect face in the image and draws a
    rectangle around each detected face.
    """

    def determine_next_position(self,image):

        self.image=image
        self.im=array2image(image)
        self.ipl_im = opencv.adaptors.PIL2Ipl(self.im)
        self.storage = opencv.cvCreateMemStorage(0)
        opencv.cvClearMemStorage(self.storage)
        self.cascade = opencv('/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml',opencv.cvSize(1,1))
        self.faces = opencv.cvHaarDetectObjects(self.ipl_im, self.cascade, self.storage, 1.2, 2,opencv.CV_HAAR_DO_CANNY_PRUNING, opencv.cvSize(50,50))

        if self.faces.total < 1:
            return None

        for f in self.faces:
            print "face detected: %s" %f
            #row and column are inverted in Opencv
            self.pos=(f.y,f.x)
            self.coormin_bbox=(self.pos[0],self.pos[1])
            self.coormax_bbox=(self.pos[0]+f.width,self.pos[1]+f.height)
            self.brightpixel=False
            return (self.pos,self.coormin_bbox,self.coormax_bbox,self.brightpixel)



#Convert an array into PIL image
def array2image(arr):
    arr = arr*255.0
    arr=np.floor(arr)#arr=arr.round()
    arr=arr.astype(np.uint8)
    return Image.fromarray(arr)


__all__ = [
    "PtzTracker",
    "BrightPixelTracker",
    "FaceTracker",
]
