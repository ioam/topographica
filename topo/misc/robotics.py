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

$Id$
"""
__version__ = '$Revision$'


import time
import Image,ImageOps
from math import pi,cos,sin

import param

from topo.base.simulation import Simulation,EventProcessor
from topo.pattern.image import GenericImage

from playerrobot import CameraDevice,PTZDevice


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



class RealTimeSimulation(Simulation):
    """
    A (quasi) real-time simulation object.

    This subclass of Simulation attempts to maintain a correspondence
    between simulation time and real time, as defined by the timescale
    parameter.  Real time simulation instances still maintain a
    nominal, discrete simulation time that determines the order of
    event delivery.

    At the beginning of each simulation time epoch, the simulation
    marks the actual wall clock time.  After event delivery for that
    epoch has ended, the simulation calculates the amount of
    computation time used for event processing, and executes a real
    sleep for the remainder of the epoch.  If the computation time for
    the epoch exceeded the real time, a warning is issued and
    processing proceeds immediately to the next simulation time epoch.


    RUN HOOKS

    The simulation includes as parameters two lists of functions/callables,
    run_start_hooks and run_stop_hooks, that will be called
    immediately before and after event processing during a call to
    .run().  This allows, for example, starting and stopping of
    real-time devices that might use resources while the simulation is
    not running.
    """
    
    timescale = param.Number(default=1.0,bounds=(0,None),doc="""
       The desired real length of one simulation time unit, in milliseconds.""")

    run_start_hooks = param.HookList(default=[],doc="""
       A list of callable objects to be called on entry to .run(),
       before any events are processed.""")
    
    
    run_stop_hooks = param.HookList(default=[],doc="""
       A list of callable objects to be called on exit from .run()
       after all events are processed.""") 

    def __init__(self,**params):
        super(RealTimeSimulation,self).__init__(**params)
        self._real_timestamp = 0.0
        
    def run(self,*args,**kw):
        for h in self.run_start_hooks:
            h()
        self._real_timestamp = self.real_time()
        super(RealTimeSimulation,self).run(*args,**kw)
        for h in self.run_stop_hooks:
            h()

    def real_time(self):
        return time.time() * 1000
    
    def sleep(self,delay):
        """
        Sleep for the number of real milliseconds seconds corresponding to the
        given delay, subtracting off the amount of time elapsed since the
        last sleep.
        """
        sleep_ms = delay*self.timescale-(self.real_time()-self._real_timestamp)

        if sleep_ms < 0:
            self.warning("Realtime fault. Sleep delay of %f requires realtime sleep of %.2f ms."
                         %(delay,sleep_ms))
        else:
            self.debug("sleeping. delay =",delay,"real delay =",sleep_ms,"ms.")
            time.sleep(sleep_ms/1000.0)
        self._real_timestamp = self.real_time()
        self._time += delay
    
        
