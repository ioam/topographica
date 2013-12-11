"""
A class for controlling pan/tilt and pan/tilt reset of a camera.
In order to move the camera, you need to install UVCDYNCTRL,
it is a Logitech software for webcam.

This class was tested with uvcdynctrl and Ubuntu 10.04 LTS.
"""



from param import Parameterized
import subprocess

UVCDYNCTRLEXEC='/usr/bin/uvcdynctrl'

# Max Ranges (determined with uvcdynctrl -v -c):
# Tilt = -1920 to 1920
# Pan  = -4480 to 4480

def disp(args):
    print " ".join(args)


class PTZ(Parameterized):

    ## Define the init script to initialize the application
    def __init__(self,**params):
        super(PTZ,self).__init__(**params)
	self.reset()

    #Functions for control Pan/tilt
    def tilt(self,value):
        control = "Tilt (relative)"
        disp([UVCDYNCTRLEXEC, "-s", control, "--", str(value)])
        subprocess.call([UVCDYNCTRLEXEC, "-s", control, "--", str(-value)])

    def pan(self, value):
        control = "Pan (relative)"
        disp([UVCDYNCTRLEXEC, "-s", control, "--", str(value)])
        subprocess.call([UVCDYNCTRLEXEC, "-s", control, "--", str(-value)])

    def reset(self):
        value = "3"
        control = "Pan Reset"
        disp([UVCDYNCTRLEXEC, "-s", control, value])
        subprocess.call([UVCDYNCTRLEXEC, "-s", control, value])
        control = "Tilt Reset"
        disp([UVCDYNCTRLEXEC, "-s", control, value])
        subprocess.call([UVCDYNCTRLEXEC, "-s", control, value])
        control = "Pan/tilt Reset"
        disp([UVCDYNCTRLEXEC, "-s", control, value])
        subprocess.call([UVCDYNCTRLEXEC, "-s", control, value])
