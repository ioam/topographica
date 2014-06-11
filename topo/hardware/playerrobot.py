"""
High-level interface to the Player client libraries.

The Player client libraries allow Python code to communicate with
hardware devices such as robots, cameras, and range sensors.

This is a temporary home for this file until it finds a permanent home
(maybe in the PlayerStage project or in PLASTK?)
"""


import time,array

from threading import RLock, Thread
from Queue import Queue

from operator import eq,ne
from math import pi

# Since this module ships with Topographica only as a sample and is not
# intended to be run, the following SkipTest statement was included to allow
# nose to handle this module (when looking for doctests) without raising an
# import error. If the file is moved elsewhere -- or run on its own, 
# assuming the PlayerStage package has been installed -- the below code should
# be reworked to either import the package directly, or handle the import error
# differently. For more information on how nose works, see topo/tests/README.

try:
    import playerc
    SKIP = False
except ImportError:
    SKIP = True

# JPALERT: Because of the global interpreter lock in Python, using
# Python threads (via the 'thread' or 'threading' modules does not
# necessarily provide low-latency polling of the player process.  In
# particular, long-running native functions (e.g. C/C++ foreign
# functions) will not be pre-empted, so the polling loop won't
# get a timeslice until they complete.  A better solution, especially
# on multicore machines, is true preemptive multiprocessing.  The
# 'processing' module should provide that, but it doesn't yet work
# properly on MacOS, and I haven't tested it yet on linux.  God knows
# what will happen on Windows.

def use_processing():
    """
    Configure the module to use the processing library for asynchronous
    process support. Use of the processing library requires the use of
    queues for communication with robot devices.
    """
    import processing
    global RLock, Thread, Queue
    RLock = processing.RLock  # pyflakes:ignore (optional alternative)
    Thread = processing.Process  # pyflakes:ignore (optional alternative)
    Queue = processing.Queue  # pyflakes:ignore (optional alternative)

def use_threading():
    """
    Configure the module to use the threading library for asynchronous
    process support. (the default)
    """
    import threading
    global RLock, Thread, Queue
    RLock = threading.RLock  # pyflakes:ignore (optional alternative)
    Thread = threading.Thread  # pyflakes:ignore (optional alternative)
    Queue = Queue.Queue  # pyflakes:ignore (optional alternative)

# JPALERT This is a HACK for the CVS version of Player, this value
# should be defined in the playerc module:
if not SKIP:
    playerc.PLAYERC_OPEN_MODE = 1


class PlayerException(Exception):
    pass


def player_fn(error_op=ne,error_val=0):
    """
    Player function decorator.  Adds error checking.

    Takes an operator and a value, and compares the result
    of the function call with the value using the operator.
    If the result is true, a PlayerException is raised.  The
    default error condition is error_op = ne, error_value = 0,
    which raises an exception if fn(*args) != 0.
    """
    def wrap(fn):
        def new_fn(*args):
            if error_op(fn(*args),error_val):
                raise PlayerException(playerc.playerc_error_str())
        return new_fn
    return wrap


def synchronized(lock):
    """
    Simple synchronization decorator.

    Takes an existing lock and synchronizes a function or
    method on that lock.  Code taken from the Python Wiki
    PythonDecoratorLibrary:

    http://wiki.python.org/moin/PythonDecoratorLibrary
    """
    def wrap(f):
        def newFunction(*args, **kw):
            lock.acquire()
            try:
                return f(*args, **kw)
            finally:
                lock.release()
        return newFunction
    return wrap


def synched_method(f):
    """
    Synchronized method decorator.

    Like synchronized() decorator, except synched_method assumes
    that the first argument of the function is an instance containing
    a Lock object, and this lock is used for synchronization.
    """
    def newFunction(self,*args,**kw):
        self._lock.acquire()
        try:
            return f(self,*args, **kw)
        finally:
            self._lock.release()
    return newFunction



class PlayerObject(object):
    """
    A generic threadsafe wrapper for client and proxy objects
    from the playerc library.

    PlayerObject wrappers are constructed automatically by PlayerRobot
    objects.  Each PlayerObject instance wraps a playerc device proxy
    or client object, and publishes a thread-safe version of each of
    proxy's methods, that is synchronized with the PlayerRobot
    instance's run-loop thread, and that catches playerc error
    conditions and raises them as PlayerExceptions.  The original
    playerc proxy object is available via the attribute .proxy.
    Specialized subclasses of PlayerObject can have additional
    interfaces for getting device state or setting commands specific
    to that device.

    Developer note: the PlayerObject base class __init__ method
    automatically wraps each method on the proxy that (a) doesn't
    begin with '__' and (b) is not already in dir(self).  This way,
    subclasses can override the wrapping process by defining their own
    wrappers *before* the base class __init__ method is called.
    """
    def __init__(self,proxy,lock):

        self._lock = lock
        self.proxy = proxy
        for name in dir(proxy):
            attr = getattr(proxy,name)
            if name not in dir(self) and name[:2] != '__' and callable(attr):
                setattr(self,name,synchronized(lock)(player_fn()(attr)))

        self.cmd_queue = Queue()

    def process_queues(self):
        while not self.cmd_queue.empty():
            name,args = self.cmd_queue.get()
            try:
                print "Doing command:",name,args
                getattr(self,name)(*args)
            finally:
                self.cmd_queue.task_done()


class PlayerClient(PlayerObject):
    """
    Player object wrapper for playerc.client objects.
    """
    def __init__(self,proxy,lock):

        # Override the wrapper on playerc.client.read, because
        # it returns None for errors, instead of returning 0 for
        # "no error."
        self.read = synchronized(lock)(player_fn(eq,None)(proxy.read))
        super(PlayerClient,self).__init__(proxy,lock)

    def process_queues(self):
        pass


class PlayerDevice(PlayerObject):
    """
    Generic Player device object.

    Overrides the default proxy .subscribe method so that the mode defaults
    to PLAYERC_OPEN_MODE.
    """

    @synched_method
    @player_fn()
    def subscribe(self, mode=None):
        mode = playerc.PLAYERC_OPEN_MODE if None else mode
        return self.proxy.subscribe(mode)



class PTZDevice(PlayerDevice):
    """
    Player Pan/Tilt/Zoom (PTZ) device.

    Adds the following to the original proxy interface:

    state = The tuple (pan,tilt,zoom) indicating the current state of
    the PTZ device.

    state_deg = Same as state, but returns values in  degrees instead
    of radians

    set_deg() and set_ws_deg() methods.  Same as .set() and .set_ws(),
    using degrees instead of radians.
    """
    def get_state(self):
        return self.proxy.pan, self.proxy.tilt, self.proxy.zoom
    state = property(get_state)

    def get_state_deg(self):
        return self.proxy.pan*180/pi, \
               self.proxy.tilt*180/pi, \
               self.proxy.zoom*180/pi
    state_deg = property(get_state_deg)

    def set_deg(self,pan,tilt,zoom):
        self.set(pan*pi/180, tilt*pi/180, zoom*pi/180)

    def set_ws_deg(self,pan,tilt,zoom,pan_speed,tilt_speed):
        self.set_ws(pan*pi/180, tilt*pi/180, zoom*pi/180,pan_speed*pi/180,tilt_speed*pi/180)



class CameraDevice(PlayerDevice):
    """
    A Player camera device.

    The synchronized method get_image grabs an uncompressed snapshot,
    along with the additional formatting information needed to make an
    image.
    """

    def __init__(self,proxy,lock):
        self.decompress = synchronized(lock)(player_fn(ne,None)(proxy.decompress))
        super(CameraDevice,self).__init__(proxy,lock)
        self.image_queue = Queue()

    def process_queues(self):
        im = self.image
        # check to make sure it's really an image
        if im[1] > 0:
            self.image_queue.put(im)
        super(CameraDevice,self).process_queues()


#    @synched_method
    def get_image(self):
        """
        Returns the tuple:
          (format,width,height,bpp,fdiv,data)
        Where data is a copy of the uncompressed image data.
        """
        if self.proxy.compression:
            self.decompress()
        im_array = array.array('B')
        im_array.fromstring(self.proxy.image[:self.proxy.image_count])
        return self.proxy.format, \
               self.proxy.width,  \
               self.proxy.height, \
               self.proxy.bpp,    \
               self.proxy.fdiv,   \
               im_array

    image = property(get_image)



##################
# DEVICE TABLE
#
# This table contains the mapping from device type names
# to specialized device object types.  Types not indexed in this table
# should default to type PlayerDevice.

device_table = {'ptz'     :PTZDevice,
                'camera'  :CameraDevice,
                }



class PlayerRobot(object):
    """
    Player Robot interface.

    A PlayerRobot instance encapsulates an interface to a Player
    robot. It creates and manages a playerc.client object and a set of
    device proxies wrapped in PlayerDevice objects.  In addition, it
    maintains a run-loop in a separate thread that calls the client's
    .read() method at regular intervals.  The devices are published
    through standard interfaces on the PlayerRobot instance, and their
    methods and properties are synchronized with the run thread
    through a mutex.

    Example:

      # set up a robot object with position, laser, and camera objects
      robot = PlayerRobot(host='myrobot.mydomain.edu',port=6665,
                          devices = [('position2d',0),
                                     ('laser',0),
                                     ('camera',1)])

      # start the run thread, devices will be subscribed
      # automatically.
      robot.start()

      # start the robot turning at 30 deg/sec
      robot.position2d[0].set_cmd_vel(0, 0, 30*pi/180)

      # wait for a while
      time.sleep(5.0)

      # all stop
      robot.position2d[0].set_cmd_vel(0,0,0)

      # shut down the robot's thread, unsubscribing all devices and
      # disconnecting the client
      robot.stop()
    """

    def __init__(self,host='localhost',port=6665,speed=20,
                 devices=[]):

        self._thread = None
        self._running = False
        self._lock = RLock()
        self.speed = speed

        self._client = PlayerClient(playerc.playerc_client(None,host,port),self._lock)

        self._queues_running = False
        self._devices = []
        for devname,devnum in devices:
            self.add_device(devname,devnum=devnum)

    def start(self):
        assert self._thread is None
        self._thread = Thread(target=self.run_loop,name="PlayerRobot Run Loop")
        self._thread.setDaemon(True)
        self._thread.start()

    def stop(self):
        self._running = False
        self._thread.join()
        self._thread = None

    def run_loop(self):
        self._client.connect()
        self._running = True
        self.subscribe_all()
        try:
            while self._running:
                self._client.read()
                if self._queues_running:
                    self.process_queues()
                time.sleep(1.0/self.speed)
        finally:
            self.unsubscribe_all()
            self._client.disconnect()

    def run_queues(self,run_state):
        """
        When using queues for communication with devices, this method
        toggles queue processing.  It is often useful to turn off
        queue processing, e.g. when a client does not plan on using queued
        data for a while.
        """
        self._queues_running = run_state

    def process_queues(self):
        for d in self._devices:
            d.process_queues()

    def subscribe_all(self):
        for dev in self._devices:
            dev.subscribe()

    def unsubscribe_all(self):
        for dev in self._devices:
            dev.unsubscribe()

    def add_device(self,devname,devnum=0):
        if devname not in dir(self):
            setattr(self,devname,{})

        proxy_constr =  getattr(playerc,'playerc_'+devname)
        devtype = device_table.get(devname,PlayerDevice)

        try:
            self._lock.acquire()
            dev = devtype(proxy_constr(self._client.proxy,devnum),self._lock)
        finally:
            self._lock.release()

        self._devices.append(dev)
        getattr(self,devname)[devnum] = dev
        if self._running:
            dev.subscribe()
