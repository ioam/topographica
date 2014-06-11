"""
A class for grabbing frames from the camera.
In order to grab frames, you need to install Opencv, and python-opencv
(Python bindings for the computer vision library).

This class was tested with Opencv 2.0.0 and Ubuntu 10.04 LTS.
"""

import ImageOps
from imagen.image import GenericImage
import param

try:
    import opencv
    from opencv import highgui

except ImportError:
    param.Parameterized().warning("opencvcamera.py classes will not be usable; python-opencv is not available.")


class CameraImage(GenericImage):

    def __init__ (self,**params):
        super(CameraImage,self).__init__(**params)
        self._image=None
        self._camera = highgui.cvCreateCameraCapture(0)


    def _get_image(self,params):
        #while 1:

        ### HACK to work around opencv problem
        for i in range(5):
            highgui.cvQueryFrame(self._camera)
        ###

        im = highgui.cvQueryFrame(self._camera)
        #im = opencv.cvGetMat(im)
        im = opencv.adaptors.Ipl2PIL(im)
            # Figure out what is happening!
        #im = copy.copy(im)
        self._image = ImageOps.grayscale(im)
        return self._image
