"""
Classes for using robotic or other hardware using Topographica.

This module contains several classes for constructing robotics
interfaces to Topographica simulations.  It includes modules that read
input from or send output to robot devices, and a (quasi) real-time
simulation object that attempts to maintain a correspondence between
simulation time and real time.

This module requires the PlayerStage robot interface system (from
playerstage.sourceforge.net), and the playerrobot module for
high-level communications with Player robots.
"""

import Image
import ImageOps
from math import pi,cos,sin

import param
from topo.base.simulation import EventProcessor
from topo.pattern.image import GenericImage

from playerrobot import CameraDevice, PTZDevice


class CameraImage(GenericImage):
    """
    An image pattern generator that gets its image from a Player
    camera device.
    """

    camera = param.ClassSelector(CameraDevice,default=None,doc="""
       An instance of playerrobot.CameraDevice to be used
       to generate images.""")

    def __init__(self,**params):
        super(CameraImage,self).__init__(**params)
        self._image = None

    def _get_image(self,params):
        self._decode_image(*self.camera.image)
        return True

    def _decode_image(self,fmt,w,h,bpp,fdiv,data):
        if fmt==1:
            self._image = Image.new('L',(w,h))
            self._image.fromstring(data,'raw')
        else:
            # JPALERT: if not grayscale, then assume color.  This
            # should be expanded for other modes.
            rgb_im = Image.new('RGB',(w,h))
            rgb_im.fromstring(data,'raw')
            self._image = ImageOps.grayscale(rgb_im)



class CameraImageQueued(CameraImage):
    """
    A version of CameraImage that gets the image from the camera's image queue,
    rather than directly from the camera object.  Using queues is
    necessary when running the playerrobot in a separate process
    without shared memory.  When getting an image, this pattern
    generator will fetch every image in the image queue and use the
    most recent as the current pattern.
    """

    def _get_image(self,params):

        im_spec = None

        if self._image is None:
            # if we don't have an image then block until we get one
            im_spec = self.camera.image_queue.get()
            self.camera.image_queue.task_done()

        # Make sure we clear the image queue and get the most recent image.
        while not self.camera.image_queue.empty():
            im_spec = self.camera.image_queue.get_nowait()
            self.camera.image_queue.task_done()

        if im_spec:
            # If we got a new image from the queue, then
            # construct a PIL image from it.
            self._decode_image(*im_spec)
            return True
        else:
            return False


class PTZ(EventProcessor):
    """
    Pan/Tilt/Zoom control.

    This event processor takes input events on its 'Saccade' input
    port in the form of (amplitude,direction) saccade commands (as
    produced by the topo.sheet.saccade.SaccadeController class) and
    appropriately servoes the attached PTZ object.  There is not
    currently any dynamic zoom control, though the static zoom level
    can be set as a parameter.
    """

    ptz = param.ClassSelector(PTZDevice,default=None,doc="""
       An instance of playerrobot.PTZDevice to be controlled.""")

    zoom = param.Number(default=120,bounds=(0,None),doc="""
       Desired FOV width in degrees.""")

    speed = param.Number(default=200,bounds=(0,None),doc="""
       Desired max pan/tilt speed in deg/sec.""")

    invert_amplitude = param.Boolean(default=False,doc="""
       Invert the sense of the amplitude signal, in order to get the
       appropriate ipsi-/contralateral sense of saccades.""")

    dest_ports = ["Saccade"]
    src_ports = ["State"]

    def start(self):
        pass
    def input_event(self,conn,data):
        if conn.dest_port == "Saccade":
            # the data should be (amplitude,direction)
            amplitude,direction = data
            self.shift(amplitude,direction)

    def shift(self,amplitude,direction):

        self.debug("Executing shift, amplitude=%.2f, direction=%.2f"%(amplitude,direction))
        if self.invert_amplitude:
            amplitude *= -1

        # if the amplitude is negative, invert the direction, so up is still up.
        if amplitude < 0:
            direction *= -1
        angle = direction * pi/180

        pan,tilt,zoom = self.ptz.state_deg
        pan += amplitude * cos(angle)
        tilt += amplitude * sin(angle)

        self.ptz.set_ws_deg(pan,tilt,self.zoom,self.speed,self.speed)
        ## self.ptz.cmd_queue.put_nowait(('set_ws_deg',
        ##                                (pan,tilt,self.zoom,self.speed,self.speed)))






