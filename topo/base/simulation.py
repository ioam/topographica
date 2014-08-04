"""
A general-purpose Simulation class for discrete events.

The Simulation object is the central object of a simulation.  It
handles the simulation clock time and maintains communication between
the components of the simulation.

A simulation is structured as a directed graph of event-processing
nodes called EventProcessors (EPs).  EventProcessors generate
data-carrying Events, which are routed through the graph to other
EventProcessors via delayed connections.  Most objects in the
simulation will be a subclass of EventProcessor, customized to provide
some specific behavior.

There are different subclasses of Event, each doing different types of
computation, and each can contain any arbitrary Python data.  A
simulation begins by giving each EventProcessor an opportunity to send
any initial events.  It then proceeds by processing and delivering
events to EventProcessors in time order.  After all events for the
current time are processed, the simulation gives each EventProcessor a
chance to do any final computation, after which simulation time skips
to the time of the earliest event remaining in the queue.


PORTS

All connections between EPs are tagged with a source port and a
destination port.  Ports are internal addresses that EPs can use to
distinguish between inputs and outputs.  A port specifier can be any
hashable Python object.  If not specified, the input and output ports
for a connection default to None.

src_ports distinguish different types of output that an EP may
produce. When sending output, the EP must call self.send_output()
separately for each port.  dest_ports distinguish different types of
input an EP may receive and process.  The EP is free to interpret the
input port designation on an incoming event in any way it chooses.

An example dest_port might be for an EP that receives 'ordinary'
neural activity on the default port, and receives a separate
modulatory signal that influences learning.  The originator of the
modulatory signal might have a connection to the EP with dest_port =
'Modulation'.  Multiple ports can be grouped by a dest EP by assuming
a convention that the keys are tuples,
e.g. ('JointNormalize','Group1'), ('JointNormalize','Group2').

An example src_port use might be an EP that sends different events to
itself than it sends out to other EPs.  In this case the self
connections might have src_port = 'Recurrent', and probably also a
special dest_port.
"""

import param

from copy import copy, deepcopy
import time
import bisect

from topo.misc.attrdict import AttrDict

#: Default path to the current simulation, from main
#: Only to be used by script_repr(), to allow it to generate
#: a runnable script
_simulation_path="topo.sim"




class EventProcessor(param.Parameterized):
    """
    Base class for EventProcessors, i.e. objects that can accept and
    handle events.  This base class handles the basic mechanics of
    connections and sending events, and stores both incoming and outgoing
    connections.

    The dest_ports attribute specifies which dest_ports are supported
    by this class; subclasses can augment or change this list if they
    wish.  The special value dest_ports=None means to accept
    connections to any dest_port, while dest_ports=[None,'Trigger']
    means that only connections to port None or port 'Trigger' are
    accepted.

    Similarly, the src_ports attribute specifies which src_ports will
    be given output by this class.
    """
    __abstract = True

    dest_ports=[None]

    src_ports=[None]


    def __init__(self,**params):
        """
        Create an EventProcessor.

        Note that just creating an EventProcessor does not mean it is
        part of the simulation (i.e. it is not in the simulation's list
        of EventProcessors, and it will not have its start() method called).
        To add an EventProcessor e to a simulation s, simply do
        s['name_of_e']=e. At this point, e's 'name' attribute will be set
        to 'name_of_e'.
        """
        super(EventProcessor,self).__init__(**params)

        # A subclass could use another data stucture to optimize operations
        # specific to itself, if it also overrides _dest_connect().
        self.in_connections = []
        self.out_connections = []

        self.simulation = None

    def _port_match(self,key,portlist):
        """
        Returns True if the given key matches any port on the given list.

        In the default implementation, a port is considered a match if
        the port is == to the key, but subclasses of EventProcessor can
        override this to allow weaker forms of matching.
        """
        return key in portlist

    # if extra parameters are required for an EP subclass, a
    # dictionary could be added to Simulation.connect() to hold
    # them, and passed on here
    def _src_connect(self,conn):
        """
        Add the specified connection to the list of outgoing connections.
        Should only be called from Simulation.connect().
        """

        if self.src_ports and not self._port_match(conn.src_port,self.src_ports):
            raise ValueError("%s is not on the list of ports provided for outgoing connections for %s: %s." %
                             (str(conn.src_port), self.__class__, str(self.src_ports)))

        # CB: outgoing connection must be uniquely named among others
        # going to the same destination.
        for existing_connection in self.out_connections:
            if existing_connection.name==conn.name and existing_connection.dest==conn.dest:
                raise ValueError('A connection out of an EventProcessor must have a unique name among connections to a particular destination; "%s" out of %s into %s already exists'%(conn.name,conn.dest,self.name))

        # CB: alternative: outgoing connection must have a unique name
##         for existing_connection in self.out_connections:
##             if existing_connection.name==conn.name:
##                 raise ValueError('A connection out of an EventProcessor must have a unique name; "%s" out of %s already exists'%(conn.name,self.name))

        self.out_connections.append(conn)


    def _dest_connect(self,conn):
        """
        Add the specified connection to the list of incoming connections.
        Should only be called from Simulation.connect().
        """

        if self.dest_ports and not self._port_match(conn.dest_port,self.dest_ports):
            raise ValueError("%s is not on the list of ports allowed for incoming connections for %s: %s." %
                             (str(conn.dest_port), self.__class__, str(self.dest_ports)))

        for existing_connection in self.in_connections:
            if existing_connection.name == conn.name:
                raise ValueError('A connection into an EventProcessor must have a unique name; "%s" into %s already exists'%(conn.name,self.name))

        self.in_connections.append(conn)


    def __dir__(self):
        """
        Extend dir() to include in_connections of an EventProcessor.
        Useful for software that examines the list of possible
        in_connections, such as tab completion in IPython.
        """
        default_dir = dir(type(self)) + list(self.__dict__)
        return sorted(set(default_dir + [conn.name for conn in self.in_connections]))


    def __getattr__(self, name):
        """
        Provide a simpler attribute-like syntax for accessing the
        in_connections of an EventProcessor (e.g. obj.conn, for
        in_connection "conn" of EventProcessor obj).
        """
        for conn in self.in_connections:
            if conn.name == name: return conn
        raise AttributeError


    def start(self):
        """
        Called by the simulation when the EventProcessor is added to
        the simulation.

        If an EventProcessor needs to have any code run when it is
        added to the simulation, the code can be put into this method
        in the subclass.
        """
        pass

    ### JABALERT: Should change send_output to accept a list of src_ports, not a single src_port.
    def send_output(self,src_port=None,data=None):
        """
        Send some data out to all connections on the given src_port.
        The data is deepcopied before it is sent out, to ensure that
        future changes to the data are not reflected in events from
        the past.
        """

        out_conns_on_src_port = [conn for conn in self.out_connections
                                 if self._port_match(conn.src_port,[src_port])]

        data=deepcopy(data)
        for conn in out_conns_on_src_port:
            #self.verbose("Sending output on src_port %s via connection %s to %s" % (str(src_port), conn.name, conn.dest.name))
            e=EPConnectionEvent(self.simulation.convert_to_time_type(conn.delay)+self.simulation.time(),conn,data,deep_copy=False)
            self.simulation.enqueue_event(e)


    def input_event(self,conn,data):
        """
        Called by the simulation when an EPConnectionEvent is delivered;
        the EventProcessor should process the data somehow.
        """
        raise NotImplementedError


    def process_current_time(self):
        """
        Called by the simulation before advancing the simulation
        time.  Allows the event processor to do any computation that
        requires that all events for this time have been delivered.
        Computations performed in this method should not generate any
        events with a zero time delay, or else causality could be
        violated. (By default, does nothing.)
        """
        pass

    def script_repr(self,imports=[],prefix="    "):
        """Generate a runnable command for creating this EventProcessor."""
        return _simulation_path+"['"+self.name+"']="+\
        super(EventProcessor,self).script_repr(imports=imports,prefix=prefix)




class EventProcessorParameter(param.Parameter):
    """Parameter whose value can be any EventProcessor instance."""

    def __init__(self,default=EventProcessor(),**params):
        super(EventProcessorParameter,self).__init__(default=default,**params)

    def __set__(self,obj,val):
        if not isinstance(val,EventProcessor):
            raise ValueError("Parameter must be an EventProcessor.")
        else:
            super(EventProcessorParameter,self).__set__(obj,val)


from param import parameterized

class EPConnection(param.Parameterized):
    """
    EPConnection stores basic information for a connection between
    two EventProcessors.
    """

## JPALERT: This type-checking is redundant, since
##     Simulation.connect() only allows the user to create connections
##     between existing simulation objects, which must be EPs.  Type
##     checking here means that it is impossible to ever instantiate
##     an EPConnection in any situation (including debugging) w/o
##     making src and dest be EPs.  However, there is nothing I can
##     find that requires that the src or dest be EPs.  While some
##     *subclasses* of EPConnection (such as Projection) do require
##     that their src and dest support the interfaces of some
##     *subclasses* of EventProcessor (e.g. Sheet.activity), there is
##     no reason that those objects have to be EPs, per se.  IMO,
##     excessive type checking removes much of the power of using a
##     dynamic language like Python.

##     src = EventProcessorParameter(default=None,constant=True,precedence=0.10,doc=
##        """The EventProcessor from which messages originate.""")

##     dest = EventProcessorParameter(default=None,constant=True,precedence=0.11,doc=
##        """The EventProcessor to which messages are delivered.""")

    src = param.Parameter(default=None,constant=True,precedence=0.10,doc=
       """The EventProcessor from which messages originate.""")

    dest = param.Parameter(default=None,constant=True,precedence=0.11,doc=
       """The EventProcessor to which messages are delivered.""")

    src_port = param.Parameter(default=None,precedence=0.20,doc=
       """
       Identifier that can be used to distinguish different types of outgoing connections.

       EventProcessors that generate only a single type of
       outgoing event will typically use a src_port of None.  However,
       if multiple types of communication are meaningful, the
       EventProcessor can accept other values for src_port.  It is up
       to the src EventProcessor to deliver appropriate data to each
       port, and to declare what will be sent over that port.
       """)

    dest_port = param.Parameter(default=None,precedence=0.21,doc=
       """
       Identifier that can be used to distinguish different types of incoming connections.

       EventProcessors that accept only a single type of incoming
       event will typically use a src_port of None.  However, if
       multiple types of communication are meaningful, the
       EventProcessor can accept other values for dest_port.  It is up
       to the dest EventProcessor to process the data appropriately
       for each port, and to define what is expected to be sent to
       that port.
       """)

    # Should the lower bound be exclusive?
    delay = param.Number(default=0.05,bounds=(0,None),doc="""
       Simulation time between generation of an Event by the src and delivery to the dest.
       Should normally be nonzero, to represent a causal with a well-defined ordering
       of events.""")

    private = param.Boolean(default=False,doc=
       """Set to true if this connection is for internal use only, not to be manipulated by a user.""")


    # CEBALERT: should be reimplemented. It's difficult to understand,
    # and contains the same code twice. But it does work.
    def remove(self):
        """
        Remove this connection from its src's list of out_connections and its
        dest's list of in_connections.
        """
        # remove from EPs that have this as in_connection
        i = 0
        to_del = []
        for in_conn in self.dest.in_connections:
            if in_conn is self:
                to_del.append(i)
            i+=1

        for i in to_del:
            del self.dest.in_connections[i]

        # remove from EPs that have this as out_connection
        i = 0
        to_del = []
        for out_conn in self.src.out_connections:
            if out_conn is self:
                to_del.append(i)
            i+=1

        for i in to_del:
            del self.src.out_connections[i]


    def script_repr(self,imports=[],prefix="    "):
        """Generate a runnable command for creating this connection."""

        if self.private:
            return ""

        settings=[]
        for name,val in self.get_param_values():
            try: # There may be a better way to figure out which parameters specify classes
                if issubclass(val,object):
                    rep=val.__name__
                    # Generate import statement
                    cls = val.__name__
                    mod = val.__module__
                    imports.append("from %s import %s" % (mod,cls))
            except TypeError:
                if name=="src" or name=="dest":
                    rep=None
                else:
                    rep = parameterized.script_repr(val,imports,prefix,settings)

            if rep is not None:
                settings.append('%s=%s' % (name,rep))

        # add import statement
        cls = self.__class__.__name__
        mod = self.__module__
        imports.append("from %s import %s" % (mod,cls))

        return _simulation_path+".connect('"+self.src.name+"','"+self.dest.name+ \
               "',connection_type="+self.__class__.__name__+ \
               ",\n"+prefix+(",\n"+prefix).join(settings) + ")"


# CB: event is not a Parameterized because of a (small) performance hit.
class Event(object):
    """Hierarchy of classes for storing simulation events of various types."""

    def __init__(self,time):
        self.time = time

    def __call__(self,sim):
        """
        Cause some computation to be performed, deliver a message, etc.,
        as appropriate for each subtype of Event.  Should be passed the
        simulation object, to allow access to .time() etc.
        """
        raise NotImplementedError

    def __cmp__(self,ev):
        """
        Implements event comparison by time, allowing sorting,
        and queue maintenance  using bisect module or minheap
        implementations, if needed.

        NOTE: identity comparisons should always be done using the
        'is' operator, not '=='.
        """
        if self.time > ev.time:
            return 1
        elif self.time < ev.time:
            return -1
        else:
            return 0


class EPConnectionEvent(Event):
    """
    An Event for delivery to an EPConnection.

    Provides access to a data field, which can be used for anything
    the src wants to provide, and a link to the connection over which
    it has arrived, so that the dest can determine what to do with the
    data.

    By default, the data is deepcopied before being added to this
    instance for safety (e.g. so that future changes to data
    structures do not affect messages arriving from the past).
    However, if you can ensure that the copying is not
    necessary (e.g. if you deepcoy before sending a set of
    identical messages), then you can pass deep_copy=False
    to avoid the copy.
    """

    def __init__(self,time,conn,data=None,deep_copy=True):
        super(EPConnectionEvent,self).__init__(time)
        assert isinstance(conn,EPConnection)
        self.data = deepcopy(data) if deep_copy else data
        self.conn = conn

    def __call__(self,sim):
        self.conn.dest.input_event(self.conn,self.data)

    def __repr__(self):
        return "EPConnectionEvent(time="+`self.time`+",conn="+`self.conn`+")"


class CommandEvent(Event):
    """An Event consisting of a command string to execute."""

    def __init__(self,time,command_string):
        """
        Add the event to the simulation.

        Raises an exception if the command_string contains a syntax
        error.
        """
        self.command_string = command_string
        self.__test()
        super(CommandEvent,self).__init__(time)

    def __repr__(self):
        return "CommandEvent(time="+`self.time`+", command_string='"+self.command_string+"')"


    def script_repr(self,imports=[],prefix="    "):
        """Generate a runnable command for creating this CommandEvent."""
        return _simulation_path+'.schedule_command('\
               +`self.time`+',"'+self.command_string+'")'


    def __call__(self,sim):
        """
        exec's the command_string in __main__.__dict__.

        Be sure that any required items will be present in
        __main__.__dict__; in particular, consider what will be present
        after the network is saved and restored. For instance, results of
        scripts you have run, or imports they make---all currently
        available in __main__.__dict__---will not be saved with the
        network.
        """
        # Presumably here to avoid importing __main__ into the rest of the file
        import __main__

        param.Parameterized(name='CommandEvent').message("Running command %s" \
                                                         % (self.command_string))
        try:
            exec self.command_string in __main__.__dict__
        except:
            print "Error in scheduled command:"
            raise

    def __test(self):
        """
        Check for SyntaxErrors in the command.
        """
        try:
            compile(self.command_string,"CommandString","single")
        except SyntaxError:
            print "Error in scheduled command:"
            raise


class FunctionEvent(Event):
    """
    Event that executes a given function function(*args,**kw).
    """
    def __init__(self,time,fn,*args,**kw):
        super(FunctionEvent,self).__init__(time)
        self.fn = fn
        self.args = args
        self.kw = kw

    def __call__(self,sim):
        self.fn(*self.args,**self.kw)

    def __repr__(self):
        return 'FunctionEvent(%s,%s,*%s,**%s)' % (`self.time`,`self.fn`,`self.args`,`self.kw`)

class EventSequence(Event):
    """
    Event that contains a sequence of other events to be scheduled and
    executed.

    The .time attributes of the events in the sequence are interpreted
    as offsets relative to the start time of the sequence itself.
    """
    def __init__(self,time,sequence):
        super(EventSequence,self).__init__(time)
        self.sequence = sequence

    def __call__(self,sim):

        # Enqueue all the events in the sequence, offsetting their
        # times from the current time
        sched_time = sim.time()
        for ev in self.sequence:
            new_ev = copy(ev)
            sched_time += ev.time
            new_ev.time = sched_time
            sim.enqueue_event(new_ev)

    def __repr__(self):
        return 'EventSequence(%s,%s)' % (`self.time`,`self.sequence`)



class PeriodicEventSequence(EventSequence):
    """
    An EventSequence that reschedules itself periodically

    Takes a period argument that determines how often the sequence
    will be scheduled.   If the length of the sequence is longer than
    the period, then the length of the sequence will be used as the period.
    """
    ## JPHACKALERT: This should really be refactored into a
    ## PeriodicEvent class that periodically executes a single event,
    ## then the user can construct a periodic sequence using a
    ## combination of PeriodicEvent and EventSequence.  This would
    ## change the behavior if the sequence length is longer than the
    ## period, but I'm not sure how important that is, and it might
    ## actually be useful the other way.


    def __init__(self,time,period,sequence):
        super(PeriodicEventSequence,self).__init__(time,sequence)
        self.period = period

    def __call__(self,sim):
        super(PeriodicEventSequence,self).__call__(sim)

        # Find the timed length of the sequence
        seq_length = sum(e.time for e in self.sequence)

        if seq_length < self.period:
            # If the sequence is shorter than the period, then reschedule
            # the sequence to occur again after the period
            self.time += self.period
        else:
            # If the sequence is longer than the period, then
            # reschedule to start after the sequence ends.
            self.time += seq_length
        sim.enqueue_event(self)

    def __repr__(self):
        return 'PeriodicEventSequence(%s,%s,%s)' % (`self.time`,`self.period`,`self.sequence`)


# CB: code that previously existed in various places now collected
# together. The original timing code was not properly tested, and the
# current code has not been tested either: needs writing cleanly and
# testing. This whole class is pretty difficult to follow.
#
### JP: Is it possible that some or all of this can be more cleanly
### implemented using PeriodicEvents?

from math import floor
class SomeTimer(param.Parameterized):
    """
    Provides a countdown timer for functions that run repeatedly.

    There are two distinct ways to use the timer.

    The first, via call_and_time(), is for calling some function every
    specified number of steps for a specified duration. Currently
    call_and_time() is used for timing calls to simulation.run() every
    1.0 steps for 100 iterations. See the Simulation class for an
    example of using the timer in this way.

    The second, via call_fixed_num_times(), is for calling some
    function repeatedly a specified number of times. A case to use
    call_fixed_num_times() would be timing pattern presentations,
    where the number of times the pattern_presenter will be called is
    known in advance. Additionally, this method allows a list of
    arguments to be passed to the function (in this case, the
    permutation for each call).
    """
    # * parameters to control formatting?
    # * the parameter types for some of the following could be more specific
    step = param.Parameter(default=2,doc=
        """Only relevant with call_and_time(), not call_fixed_num_times().

           Each iteration, func is called as func(step).

           For example, step=1 with func set to topo.sim.time would cause
           the simulation time to advance once per iteration.

           The default value (None) gives 50 iterations for any value of simulation_duration
           passed to call_and_time(simulation_duration).""")

    estimate_interval = param.Number(default=50,doc=
        """Interval in simulation time between estimates.""")

    func = param.Parameter(default=None,instantiate=True,doc=
        """Function to be timed.""")

##     func_args = Parameter(default=None,instantiate=True,doc=
##         """Arguments passed to func at time of calling.""")

    simulation_time_fn = param.Parameter(default=None,instantiate=True,doc=
        """Function that returns the simulation time.""")

    real_time_fn = param.Parameter(default=time.time,instantiate=True,doc=
        """Function that returns the wallclock time.""")

    receive_info = param.Parameter(default=[],instantiate=True,doc=
        """List of objects that will receive timing information.
        Each must have a timing_info() method.""")

    stop = param.Boolean(default=False,doc=
        """If set to True, execution of func (and timing) will cease at the end of
        the current iteration.""")


    def __pass_out_info(self,time,percent,name,duration,remaining):
        [thing(time,percent,name,duration,remaining) for thing in self.receive_info]

    # CB: this used to say how long the operation took (in wallclock time)

    def __measure(self,fduration,step,arg_list=None):

        if not arg_list:
            # no list of arguments means not being called set number of times
            fixed_num_calls = False
        else:
            fixed_num_calls = True

        iters  = int(floor(fduration/step))

        recenttimes=[]

        if not fixed_num_calls: arg_list=[step]*iters

        simulation_starttime = self.simulation_time_fn()

        self.stop = False
        for i in xrange(iters):
            recenttimes.append(self.real_time_fn())
            length = len(recenttimes)

            if (length>self.estimate_interval):
                recenttimes.pop(0)
                length-=1

            self.func(arg_list[i])

            percent = 100.0*i/iters
            estimate = (iters-i)*(recenttimes[-1]-recenttimes[0])/length
            self.__pass_out_info(time=self.simulation_time_fn(),
                                 percent=percent,
                                 name=self.func.__name__,
                                 duration=fduration,
                                 remaining=estimate)

            ## JABALERT: Needs to be fixed to avoid calling topo from base/
            ## HACK refresh windows for camera in simulation time
            import topo
            if hasattr(topo, 'guimain'):
                topo.guimain.refresh_activity_windows()
            ##

            if self.stop: break


        if not self.stop:
            if not fixed_num_calls:
                # ensure specified duration has been respected, since code above might not
                # complete specified duration (integer number of iterations)
                leftover = fduration+simulation_starttime-self.simulation_time_fn()
                if leftover>0: self.func(leftover)
            percent = 100
        self.__pass_out_info(time=self.simulation_time_fn(),
                             percent=percent,
                             name=self.func.__name__,
                             duration=fduration,
                             remaining=0)



    def call_fixed_num_times(self,args_for_iterations):
        """
        Call self.func(args_for_iterations[i]) for all i in args_for_iterations.
        """
        self.__measure(len(args_for_iterations),1.0,arg_list=args_for_iterations)


    def call_and_time(self,fduration):
        """
        Call self.func(self.step or fduration/50.0) for fduration.
        """
        # default to 50 steps unless someone set otherwise
        step = self.step or fduration/50.0
        self.__measure(fduration,step)


    def update_timer(self,name,current_presentation,total_presentations):
        if current_presentation == 0:
            self.recenttimes=[]

        if current_presentation == total_presentations-1:
            percent = 100
            estimate = 0
        else:
            self.recenttimes.append(self.real_time_fn())

            length = len(self.recenttimes)

            if (length>self.estimate_interval):
                self.recenttimes.pop(0)
                length-=1

            try:
                percent = 100.0*current_presentation/total_presentations
            except:
                percent = 100
            estimate = (total_presentations-current_presentation)* \
                (self.recenttimes[-1]-self.recenttimes[0])/length

        self.__pass_out_info(time=current_presentation,
                             percent=percent,
                             name=name,
                             duration=total_presentations,
                             remaining=estimate)



# CEBALERT: This singleton-producing mechanism is pretty complicated,
# and it would be great if someone could simplify it. Getting all of
# the behavior we want for e.g. Simulation is tricky, but there are
# tests for it. Note that:
# (1) There should only ever be one single Simulation instance for
#     which register is True. Creating, copying, and unpickling
#     need to take this into account.
# (2) A Simulation instance for which register is False should
#     behave the same as any normal Python object.
#
# For how to use, see topo.base.simulation.Simulation or
# topo.misc.commandline.GlobalParams.
class OptionalSingleton(object):

    _inst = None

    def __new__(cls,singleton):
        """
        Return the single instance stored in _inst if singleton is
        True; otherwise, return a new instance.
        """
        if singleton:
            if cls is not type(cls._inst):
                cls._inst = object.__new__(cls)
                cls._inst._singleton = True
            return cls._inst
        else:
            new_inst = object.__new__(cls)
            new_inst._singleton = False
            return new_inst

    def __getnewargs__(self):
        return (self._singleton,)

    def __copy__(self):
        # An OptionalSingleton(singleton=False) instance is copied, while the
        # OptionalSingleton(singleton=True) instance is not copied.
        if self._singleton:
            return self
        else:
            # Ideally we'd just call "object.__copy__", but apparently
            # there's no such method.

            # CB: I *think* this is how to do a copy. Any better
            # ideas?  Python's copy.copy() function calls an object's
            # __reduce__ method and then reconstructs the object from
            # that using copy._reconstruct().
            new_obj = self.__class__(self._singleton)
            new_obj.__dict__ = copy(self.__dict__)
            return new_obj

    def __deepcopy__(self,m):
        if self._singleton:
            return self
        else:
            new_obj = self.__class__(self._singleton)
            new_obj.__dict__ = deepcopy(self.__dict__,m)
            return new_obj

    # CB: I might have bound __copy__ (& __deepcopy__) just to the
    # Simulation(singleton=True) instance to avoid the Simulation
    # class having a __copy__ method at all, but copy() only checks
    # the *class* for the existence of __copy__.



# Simulation stores its events in a linear-time priority queue (i.e., a
# sorted list.) For efficiency, e.g. for spiking neuron simulations,
# we'll probably need to replace the linear priority queue with a more
# efficient one.  Jeff has an O(log N) minheap implementation, but
# there are likely to be many others to select from.
#
class Simulation(param.Parameterized,OptionalSingleton):
    """
    A simulation class that uses a simple sorted event list (instead of
    e.g. a sched.scheduler object) to manage events and dispatching.

    Simulation is a singleton: there is only one instance of
    Simulation, no matter how many times it is instantiated.
    """

    register = param.Boolean(default=True,constant=True,doc="""
        Whether or not to register this Simulation. If True, this
        Simulation (when created explicitly or when unpickled)
        will replace any existing registered Simulation (if one exists).
        Thus only one Simulation with register=True can exist at
        any one time, which makes it simpler to handle defining
        and reloading a series of simulations without polluting the
        memory space with unused simulations.""")

    startup_commands = param.Parameter(instantiate=True,default=[],doc="""
        List of string commands that will be exec'd in
        __main__.__dict__ (i.e. as if they were entered at the
        command prompt) every time this simulation is unpickled
        (and will be executed before the simulation is itself
        unpickled).

        For example, allows items to be imported before
        scheduled_commands are run.
        """)

    time = param.Callable(default=param.Dynamic.time_fn, doc="""
        The time object is a callable that can be set, incremented and
        decremented with a chosen numeric type as necessary.
        """)

    time_printing_format = param.String("%(_time)09.2f",doc="""
        Format string to be used when the simulation time must be
        formatted as a string, e.g. for display or for basename().
        When the string is evaluated, the time will be available as
        the attribute '_time'.
        """)

    basename_format = param.String("%(name)s_%(timestr)s",doc="""
        Format string to be used by the basename() function.
        When the string is evaluated, the formatted time from
        time_printing_format will be available as the attribute
        'timestr'.
        """)

    eps_to_start = []

    name = param.Parameter(constant=False)

    forever = param.Infinity()

    ### Simulation(register=True) is a singleton
    #
    #
    # There is only ever one instance of Simulation(register=True).
    # This instance is stored in the '_inst' attribute; when __new__
    # is called and register is True, this instance is created if it
    # doesn't already exist, and returned otherwise. copying or
    # deepcopying this instance returns the instance.
    #
    # For a Simulation with register False, calling __new__ results in
    # a new object as usual for Python objects. copying and
    # deepcopying returns a new Simulation with a copy or deepcopy
    # (respectively) of the original Simulation's __dict__.
    #
    # See OptionalSingleton for more information.
    def __new__(cls,*args,**kw):

        # simulate behavior of a parameter for register
        if 'register' in kw:
            register = kw['register']
        # this elif shouldn't be required, but is needed for
        # unpickling: OptionalSingleton's __getnewargs__ is called
        # with register as the first argument (I don't know how else
        # to set register on unpickling).
        elif len(args)==1:
            register = args[0]
        else:
            register = cls.register

        n = OptionalSingleton.__new__(cls,register)

        # CEBALERT: without removing references to the Sheets from
        # from instances of Slice, those instances of Slice and the
        # Sheets they refer to are never garbage collected.
        #
        # This temporary implementation of cleanup code explicitly
        # removes references to Sheets from Slice instances for
        # typical simulations.
        #
        # 1: Better than having cleanup code here would be to make a
        # change to Slice, so that a Slice either doesn't have a
        # reference to a Sheet, or doesn't hold onto that reference.
        #
        # 2: Some cleanup code will always be required here in
        # Simulation.__new__: As well as removing references to Sheets
        # from Slices, it is also necessary to remove references to
        # sheets from Simulation's lists of EPs - otherwise the sheets
        # are not garbage collected and memory usage will go up every
        # time a new Simulation is created. This cleanup must be in
        # Simulation.__new__ so that it runs whenever a simulation is
        # created or unpickled (it can't be done e.g. in
        # load_snapshot).
        #
        # 3: this particular implementation assumes the only instances
        # of Slice are in ConnectionFields, which is true for our
        # simulations. (This won't matter when the slice cleanup
        # becomes unnecessary.)
        if hasattr(n,'_cleanup'):
            n._cleanup()
        # if we don't collect() here (exactly here - not in _cleanup,
        # and not later), gc seems to lose track of some objects and
        # there is still a (smaller) memory increase with every call
        # to load_snapshot()
        import gc
        gc.collect()

        return n

    # CEBALERT: see gc alert in __new__()
    def _cleanup(self):
        # will always be required: in case eps haven't been started
        # so are still in the list
        if hasattr(self,'eps_to_start'):
            self.eps_to_start[:]=[]

        if hasattr(self,'_event_processors'):
            for name,EP in self._event_processors.items():
                for c in EP.in_connections:
                    if hasattr(c,'_cleanup'):
                        c._cleanup()
                # will always be required
                self._event_processors[name]=None
                # (check when cleaning up existing mechanism for
                # adding sheets e.g. sim['x']=sheet could first set
                # sim['x'] to None if there is already a sheet with
                # name x...)


    # CEBALERT: if we're keeping this, should have a better name
    def convert_to_time_type(self,time):
        """
        Convert the supplied time to the Simulation's time_type.
        """
        return (self.forever if time == self.forever else self.time.time_type(time))

    # Note that __init__ can still be called after the
    # Simulation(register=True) instance has been created. E.g. with
    # Simulation.register is True,
    #   Simulation(name='A'); Simulation(name='B')
    #
    # would leave the single Simulation(register=True) instance with
    # name=='B'. This is because, as is usual in Python, __new__
    # creates an instance of a class, while __init__ is subsequently
    # given that instance (to initialize).


    def __init__(self, *args,**params):
        """
        Initialize a Simulation instance.
        """
        param.Parameterized.__init__(self, **params)

        self.time(val=0.0)
        self.views = AttrDict()
        self._event_processors = {}

        self._instantiated_model = False
        self.model = None

        if self.register:
            # Indicate that no specific name has been set
            self.name=params.get('name')
            # Set up debugging messages to include the simulator time
            param.parameterized.dbprint_prefix= \
               (lambda: "Time: "+self.timestr()+" ")

        self.events = [] # CB: consider collections.deque? (PEP 290)
        self._events_stack = []
        self.eps_to_start = []
        self.item_scale=1.0 # this variable determines the size of each item in a diagram

        # CB (this comment applies to SomeTimer!): make this a
        # parameter for documentation? Otherwise nobody will know
        # about being able to adjust step.
        #
        # we set step to 2 so that by default timing doesn't slow simulation too much. but
        # e.g. leaving it as None would result in info at 2% increments of requested run duration,
        # no matter what duration (0.005 or 5, etc).
        self.timer = SomeTimer(func=self.run,
                               simulation_time_fn=self.time)


    def __getitem__(self,item_name):
        """
        Return item_name if it exists as an EventProcessor in
        the Simulation. See objects().
        """
        if not isinstance(item_name,str):
            raise TypeError("Expected string (objects in the Simulation are indexed by name); %s is a %s"%(item_name,type(item_name)))
        try:
            return self.objects()[item_name]
        except KeyError:
            raise AttributeError("Simulation doesn't contain '"+item_name+"'.")


    # CEBALERT: should this at least give a warning when an existing
    # EP is replaced?
    def __setitem__(self,ep_name,ep):
        """
        Add ep to the simulation, setting its name to ep_name.
        ep must be an EventProcessor.

        If ep_name already exists in the simulation, ep overwrites
        the original object (as for a dictionary).

        Note: EventProcessors do not necessarily have to be added to
        the simulation to be used, but otherwise they will not receive the
        start() message.  Adding a node to the simulation also sets the
        backlink node.simulation, so that the node can enqueue events
        and read the simulation time.
        """
        if not isinstance(ep_name,str):
            raise TypeError("Expected string for item name (EPs in the Simulation are indexed by name).")

        if not isinstance(ep,EventProcessor):
            raise TypeError("Expected EventProcessor: objects in the Simulation must be EPs.")

        if ep in self._event_processors.values():
            self.warning("EventProcessor "+str(ep)+" () already exists in the simulation and will not be added.")
        else:
            ep.initialized=False
            ep.name=ep_name
            ep.initialized=True
            # deletes and overwrites any existing EP with the same name,
            # silently, as if a dictionary
            if ep.name in self._event_processors: del self[ep.name]

            self._event_processors[ep_name] = ep
            ep.simulation = self
            self.eps_to_start.append(ep)

            if hasattr(ep,'views'):
                self.views[ep_name] = ep.views


    def __delitem__(self,ep_name):
        """
        Dictionary-style deletion of EPs from the simulation; see __delete_ep().

        Deletes EP from simulation, plus connections that come into it and
        connections that go out of it.
        """
        if not isinstance(ep_name,str):
            raise TypeError("Expected string for item name (EPs in the Simulation are indexed by name).")

        self.__delete_ep(ep_name)


    def __delete_ep(self,ep_name):
        """
        Remove the specified EventProcessor from the simulation, plus
        delete connections that come into it and connections that go from it.

        (Used by 'del sim[ep_name]' (as for a dictionary) to delete
        an event processor from the simulation.)
        """
        ep = self[ep_name]

        # remove from simulation list of eps
        del self._event_processors[ep_name]

        # remove out_conections that go to this ep
        for conn in ep.in_connections:
            conn.remove()

        # remove in_connections that come from this ep
        for conn in ep.out_connections:
            conn.remove()

    def __iter__(self):
        for obj in self.objects(): yield obj


    def __dir__(self):
        """
        Extend dir() to include simulation objects as well.  Useful
        for software that examines the list of possible objects, such
        as tab completion in IPython.
        """
        default_dir = dir(type(self)) + list(self.__dict__)
        return sorted(set(default_dir + self.objects().keys()))


    def __getattr__(self, name):
        """
        Provide a simpler attribute-like syntax for accessing objects
        within a Simulation (e.g. sim.obj1, for an EventProcessor
        "obj1" in sim).
        """
        if name=='_event_processors':
            raise AttributeError

        try:
            return self.objects()[name]
        except:
            raise AttributeError


    def timestr(self,specified_time=None):
        """
        Returns the specified time (or the current time, if none
        specified) formatted using time.time_printing_format, which allows
        users to control how much precision, etc. is used for time
        displays.
        """
        # CEBALERT: I doubt this gets all attributes. Does it get
        # properties (not that there are any right now)?
        all_vars = dict(self.get_param_values())
        all_vars.update(self.__dict__)
        if specified_time is not None:
            all_vars['_time']=specified_time
        elif self.time is not None:
            all_vars['_time'] = self.time()
        else:
            raise Exception('No time object available.')

        timestr = self.time_printing_format % all_vars
        return timestr


    @property
    def timestr_prop(self):
        """
        A property that simply returns self.timestr(); useful for setting the
        interactive command-line prompt.
        """
        return self.timestr()


    def basename(self):
        """
        Return a string suitable for labeling an object created
        by the current simulation at the current time.  By default
        this is simply the name of the simulation + " " +
        the result from evaluating the time_printing_format parameter.
        """
        all_vars = dict(self.get_param_values())
        all_vars.update(self.__dict__)
        all_vars['timestr']=self.timestr()

        return self.basename_format % all_vars



    # Change current run() to _run(), and current run_and_time() to run()?

    # CEBALERT: need to simplify duration/until code. Hiding 'until' option
    # until it's fixed (presumably nobody's using it).
    def run_and_time(self, duration=forever):

        if duration==self.forever:
            # CEBALERT: timing code not setup to handle indefinite durations
            # (e.g. 'self.forever')
            self.run(duration)
            return
        else:
            self.timer.call_and_time(duration)


    def __call__(self, *args, **kwargs):
        """
        Load the model specified by topo.sim.model by calling the
        model object. The model will only be called if self.model not
        None and if the model has not already instantiated.

        All positional and keyword arguments are passed through to the
        call used to initialize the model.
        """
        if self.model is None:  return
        elif not callable(self.model):
            raise Exception("Model object %r is not callable" % self.model)
        elif not self._instantiated_model:
            self._instantiated_model = True
            self.model(*args, **kwargs)


    def run(self, duration=forever, until=forever):
        """
        Process simulation events for the specified duration or until the
        specified time.

        Arguments:

          duration = length of simulation time to run. Default: run
          indefinitely while there are still events in the
          event_queue.

          until = maximum simulation time to simulate. Default: run
          indefinitely while there are still events in the event
          queue.

        If both duration and until are used, the one that is reached first will apply.


        Note that duration and until should be specified in a format suitable for
        conversion (coercion?) into the Simulation's _time_type.
        """

        if not self._instantiated_model and self.model: self()
        elif not self.objects():
            self.message("No model specified to the Simulation instance.")
            return

        # CEBALERT: calls to topo.sim.run() within topo should use a
        # string to specify the time rather than a float (since float
        # is not compatible with all number types).

        duration = self.convert_to_time_type(duration)

        # Use the until value of self.time if not explicitly specified
        until = self.convert_to_time_type(until)
        # Initialize any EPs that haven't been started yet
        #
        # Anything that manipulates the event stack in some way
        # (e.g. calls state_push() *must* ensure that this code has
        # been executed first (i.e. the code must call topo.sim.run(0)
        # before doing anything).  (Currently applies to
        # pattern_present(), Test Pattern's Present button, and
        # save_input_generators, but future code may need such calls
        # as well.)
        for e in self.eps_to_start:
            e.start()

        self.eps_to_start=[]

        stop_time = min(self.time() + duration, until)
        # Use time.until if it is between the current time and stop_time.
        # This ensures self.time.until act only as a 'soft' limit
        if (self.time() < self.time.until <= stop_time):
            stop_time = self.time.until
        # Stops time going backward if until less than current time.
        stop_time = self.time() if stop_time < self.time() else stop_time

        did_event = False

        while self.events and (stop_time == self.forever or self.time() <= stop_time):
            # Loop while there are events and it's not time to stop.

            if self.events[0].time < self.time():
                # Warn and then discard events scheduled *before* the current time
                self.warning('Discarding stale (unprocessed) event',repr(self.events[0]))
                self.events.pop(0)

            elif self.events[0].time > self.time():
                # Before moving on to the next time, do any processing
                # necessary for the current time.  This is necessary only
                # if some event has been delivered at the current time.

                if did_event:
                    did_event = False
                    #self.debug("Time to sleep; next event time: %s",self.timestr(self.events[0].time))
                    for ep in self._event_processors.values():
                        ep.process_current_time()

                # Set the time to the frontmost event.  Bear in mind
                # that the front event may have been changed by the
                # .process_current_time() calls.
                if self.events[0].time > self.time():
                    self.sleep(self.events[0].time - self.time())

            else:
                # Pop and call the event at the head of the queue.
                event = self.events.pop(0)
                self.debug(lambda:"Delivering %s"%(event))
                event(self)
                did_event=True

        # The time needs updating if the events have not done it.
        #if self.events and self.events[0].time >= stop_time:

        if stop_time != self.forever:
            self.time(stop_time)

    def sleep(self,delay):
        """
        Advance the simulator time by the specified amount.
        By default simply increments the _time value, but subclasses can
        override this method as they wish, e.g. to wait for an
        external real time clock to advance first.
        """
        time = self.time
        time += delay

    def enqueue_event(self,event):
        """
        Enqueue an Event at an absolute simulation clock time.
        """
        assert isinstance(event,Event)

        if not self.events or event >= self.events[-1]:
            # The new event goes at the end of the event queue if there
            # isn't a queue right now, or if it's later than the last
            # event's time.
            self.events.append(event)
        elif event < self.events[0]:
            # If it's earlier than the first item it goes at the beginning.
            self.events.insert(0,event)
        else:
            # Otherwise, it's inserted at the appropriate
            # position somewhere inside the event queue.
            # New events are enqueued after (right of) existing
            # events with the same time, i.e. 'simultaneous' events
            # are executed FIFO.
            bisect.insort_right(self.events,event)

    def schedule_command(self,time,command_string):
        """
        Add a command to execute in __main__.__dict__ at the
        specified time.

        The command should be a string.
        """
        event = CommandEvent(time=self.convert_to_time_type(time),command_string=command_string)
        self.enqueue_event(event)


    def state_push(self):
        """
        Save a copy of the current state of the simulation for later restoration.

        The saved copy includes all the events on the simulator stack
        (saved using event_push()).  Each EventProcessor is also asked
        to save its own state.  This operation is useful for testing
        something while being able to roll back to the original state.
        """
        if self.eps_to_start != []:
            self.run(0.0)
        self.event_push()
        for ep in self._event_processors.values():
            ep.state_push()

        param.Parameterized.state_push(self)


    def state_pop(self):
        """
        Pop the most recently saved state off the stack.

        See state_push() for more details.
        """
        self.event_pop()
        for ep in self._event_processors.values():
            ep.state_pop()

        param.Parameterized.state_pop(self)


    def event_push(self):
        """
        Save a copy of the events queue for later restoration.

        Same as state_push(), but does not ask EventProcessors to save
        their state.
        """
        # CBALERT: does it make more sense to put the original events onto the
        # stack, and replace self.events with the copies? Not sure this makes
        # any practical difference currently.
        self._events_stack.append((self.time(),[copy(event) for event in self.events]))


    def event_pop(self):
        """
        Pop the most recently saved events queue off the stack.

        Same as state_pop(), but does not restore EventProcessors' state.
        """
        time, self.events = self._events_stack.pop()
        self.time(time)


    def event_clear(self,event_type=EPConnectionEvent):
        """
        Clear out all scheduled events of the specified type.

        For instance, with event_type=EPConnectionEvent, this function can be used to ensure
        that no pending EPConnectionEvents will remain on the queue during some analysis
        or measurement operation.  One will usually want to do a state_push before using this
        function, then clear out the events that should be deleted, do the measurement or
        analysis, and then do state_pop to restore the original state.
        """
        events_temp = []
        for e in self.events:
            if not isinstance(e,event_type):
                events_temp = events_temp + [e]
        self.events = events_temp



    # Could just process src and dest in conn_params.
    # Also could accept the connection already created, rather than
    # creating one.
    def connect(self,src,dest,connection_type=EPConnection,**conn_params):
        """
        Connect the src EventProcessor to the dest EventProcessor.

        The src and dest should be string names of existing EPs.
        Returns the connection that was created.  If the connection
        hasn't been given a name, it defaults to 'srcTodest'.
        """

        if 'name' not in conn_params:
            # Might want to have a way of altering the name if this one's
            # already in use. At the moment, an error is raised (correctly).
            conn_params['name'] = src+'To'+dest

        # Looks up src and dest in our dictionary of objects
        conn = connection_type(src=self[src],dest=self[dest],**conn_params)
        self[src]._src_connect(conn)
        self[dest]._dest_connect(conn)
        return conn


    def objects(self,baseclass=EventProcessor):
        """
        Return a dictionary of simulation objects having the specified
        base class.  All simulation objects have a base class of
        EventProcessor, and so the baseclass must be either
        EventProcessor or one of its subclasses.

        If there is a simulator called s, you can type e.g.
        s.objects().keys() to see a list of the names of all objects.
        """
        return dict([(ep_name,ep)
                     for (ep_name,ep) in self._event_processors.items()
                     if isinstance(ep,baseclass)])


    def connections(self):
        """Return a list of all unique connections to or from any object."""
        # The return value cannot be a dictionary like objects(),
        # because connection names are not guaranteed to be unique
        connlists =[o.in_connections + o.out_connections
                    for o in self.objects().values()]
        # Flatten one level
        conns=[]
        for cl in connlists:
            for c in cl:
                conns.append(c)
        return [c for c in set(conns)]


    def script_repr(self,imports=[],prefix="    "):
        """
        Return a nearly runnable script recreating this simulation.

        Needs some work to make the result truly runnable.

        Only scheduled commands that have not yet been executed are
        included, because executed commands are not kept around.
        """
        objs  = [o.script_repr(imports=imports) for o in
                 sorted(self.objects().values(), cmp=lambda x, y: cmp(x.name,y.name))]

        # CBENHANCEMENT: could allow user to plug in a sorting
        # function.  E.g. might want to compare conns based on name
        # then dest then src if lots of conns share the same name (so
        # the order is always the same).
        conns = [o.script_repr(imports=imports) for o in
                 sorted(self.connections(),      cmp=lambda x, y: cmp(x.name,y.name))]

        cmds  = [o.script_repr(imports=imports) for o in
                 sorted(sorted([e for e in self.events if isinstance(e,CommandEvent)],
                               cmp=lambda x, y: cmp(x.command_string,y.command_string)),
                        cmp=lambda x, y: cmp(x.time,y.time))]

        # CEBALERT: hack to support importing the time type since the
        # scheduled actions will have times printed using the
        # time_type.
        imports.append("from %s import %s"%(self.time.time_type.__module__,self.time.time_type.__name__))

        imps  = sorted(set(imports))

        vals  = [_simulation_path + "." + p + "=" + repr(getattr(self,p)) for p in
                 ["name","startup_commands"]
                 if getattr(self,p)]

        return "\n\n# Imports:\n\n"                +     '\n'.join(imps)  + \
               "\n\n\n"                            +   '\n\n'.join(vals)  + \
               '\n\n\n\n# Objects:\n\n'            + '\n\n\n'.join(objs)  + \
               '\n\n\n\n# Connections:\n\n'        + '\n\n\n'.join(conns) + \
               '\n\n\n\n# Scheduled commands:\n\n' +     '\n'.join(cmds)


    # Convenience function for use in graphical editors of the simulation
    def grid_layout(self,objgrid,xstart=100,xstep=150,ystart=100,ystep=150,item_scale=1.0):
        """
        Set the layout_location of simulation objects in a grid pattern.

        Takes a list of lists of simulation objects, or names of
        simulation objects, and positions them with layout_locations
        left-to-right, top-to-bottom, starting at (xstart,ystart) and
        advancing by xstep and ystep.

        The object None can be placed in the grid to skip a grid space.
        """

        self.item_scale=item_scale

        y = ystart
        for row in objgrid:
            x = xstart
            for obj in row:
                if obj:
                    if isinstance(obj,str):
                        self[obj].layout_location = x,y
                    else:
                        obj.layout_location = x,y
                x += xstep
            y += ystep



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
        self.time += delay



