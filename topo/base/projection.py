"""
Projection and related classes.
"""

import numpy
from numpy import array,asarray,ones,sometrue, logical_and, logical_or

from collections import OrderedDict

import param
from param.parameterized import overridable_property

from dataviews import SheetView, AttrDict
from dataviews.collector import AttrTree

from sheet import Sheet
from simulation import EPConnection
from functionfamily import TransferFn

class SheetMask(param.Parameterized):
    """
    An abstract class that defines a mask over a ProjectionSheet object.

    This class is typically used for optimization, where mask
    indicates which neurons are active and should be processed
    further. A mask can also be used for lesion experiments, to
    specify which units should be kept inactive.

    See the code for CFProjection and CFResponseFn to see how this
    class can be used to restrict the computation to only those
    neurons that the Mask lists as active.
    """

    # JPALERT: Is there anything about this class that assumes its
    # sheet is a ProjectionSheet?

    def _get_data(self):
        assert(self._sheet != None)
        return self._data
    def _set_data(self,data):
        assert(self._sheet != None)
        self._data = data

    data = overridable_property(_get_data,_set_data,doc="""
    Ensure that whenever somebody accesses the data they are not None.""")

    def _get_sheet(self):
        assert(self._sheet != None)
        return self._sheet
    def _set_sheet(self,sheet):
        self._sheet = sheet
        if(self._sheet != None): self.reset()

    sheet = overridable_property(_get_sheet,_set_sheet)

    def __init__(self,sheet=None,**params):
        super(SheetMask,self).__init__(**params)
        self.sheet = sheet

    def __and__(self,mask):
        return AndMask(self._sheet,submasks=[self,mask])
    def __or__(self,mask):
        return OrMask(self._sheet,submasks=[self,mask])

    # JABALERT: Shouldn't this just keep one matrix around and zero it out,
    # instead of allocating a new one each time?
    def reset(self):
        """Initialize mask to default value (with no neurons masked out)."""
        self.data = ones(self.sheet.shape)


    def calculate(self):
        """
        Calculate a new mask based on the activity of the sheet.

        For instance, in an algorithm like LISSOM that is based on a
        process of feedforward activation followed by lateral settling,
        the calculation is done at the beginning of each iteration after
        the feedforward activity has been calculated.

        Subclasses should override this method to compute some non-default
        mask.
        """
        pass


    # JABALERT: Not clear what the user should do with this.
    def update(self):
        """
        Update the current mask based on the current activity and a previous mask.

        Should be called only if calculate() has already been called since the last
        reset(); potentially faster to compute than redoing the entire calculate().

        Subclasses should override this method to compute some non-default
        mask.
        """
        pass


class CompositeSheetMask(SheetMask):
    """
    A SheetMask that computes its value from other SheetMasks.
    """
    __abstract =  True

    submasks = param.List(class_=SheetMask)

    def __init__(self,sheet=None,**params):
        super(CompositeSheetMask,self).__init__(sheet,**params)
        assert self.submasks, "A composite mask must have at least one submask."

    def _combine_submasks(self):
        """
        A method that combines the submasks.

        Subclasses should override this method to do their respective
        composite calculations.  The result should be stored in self.data.
        """
        raise NotImplementedError

    def _set_sheet(self,sheet):
        for m in self.submasks:
            m.sheet = sheet
        super(CompositeSheetMask,self)._set_sheet(sheet)

    def reset(self):
        for m in self.submasks:
            m.reset()
        self._combine_submasks()

    def calculate(self):
        for m in self.submasks:
            m.calculate()
        self._combine_submasks()

    def update(self):
        for m in self.submasks:
            m.update()
        self._combine_submasks()



class AndMask(CompositeSheetMask):
    """
    A composite SheetMask that computes its value as the logical AND (i.e. intersection) of its sub-masks.
    """
    def _combine_submasks(self):
        self._data = asarray(reduce(logical_and,(m.data for m in self.submasks)),dtype=int)



class OrMask(CompositeSheetMask):
    """
    A composite SheetMask that computes its value as the logical OR (i.e. union) of its sub-masks.
    """
    def _combine_submasks(self):
        self._data = asarray(reduce(logical_or,(m.data for m in self.submasks)),dtype=int)



class Projection(EPConnection):
    """
    A projection from a Sheet into a ProjectionSheet.

    Projections are required to support the activate() method, which
    will construct a matrix the same size as the target
    ProjectionSheet, from an input matrix of activity from the source
    Sheet.  Other than that, a Projection may be of any type.
    """
    __abstract=True

    strength = param.Number(default=1.0)

    src_port = param.Parameter(default='Activity')

    dest_port = param.Parameter(default='Activity')

    output_fns = param.HookList(default=[],class_=TransferFn,doc="""
        Function(s) applied to the Projection activity after it is computed.""")

    plastic = param.Boolean(default=True, doc="""
        Whether or not to update the internal state on each call.
        Allows plasticity to be turned off during analysis, and then re-enabled.""")

    activity_group = param.Parameter(default=(0.5,numpy.add), doc="""
       Grouping and precedence specifier for computing activity from
       Projections.  In a ProjectionSheet, all Projections in the
       same activity_group will be summed, and then the results from
       each group will be combined in the order of the activity_group
       using the operator specified by the activity_operator.  For
       instance, if there are two Projections with
       activity_group==(0.2,numpy.add) and two with
       activity_group==(0.6,numpy.divide), activity
       from the first two will be added together, and the result
       divided by the sum of the second two.""")

    # CEBALERT: precedence should probably be defined at some higher level
    # (and see other classes where it's defined, e.g. Sheet)
    precedence = param.Number(default=0.5)


    def __init__(self,**params):
        super(Projection,self).__init__(**params)
        self.activity = array(self.dest.activity)
        self.__saved_activity = []
        self._plasticity_setting_stack = []


    def activate(self,input_activity):
        """
        Compute an activity matrix for output, based on the specified input_activity.

        Subclasses must override this method to whatever it means to
        calculate activity in that subclass.
        """
        raise NotImplementedError


    def learn(self):
        """
        This function has to be re-implemented by sub-classes, if they wish
        to support learning.
        """
        pass


    def apply_learn_output_fns(self,active_units_mask=True):
        """
        Sub-classes can implement this function if they wish to
        perform an operation after learning has completed, such as
        normalizing weight values across different projections.

        The active_units_mask argument determines whether or not to
        apply the output_fn to non-responding units.
        """
        pass



    def override_plasticity_state(self, new_plasticity_state):
        """
        Temporarily override plasticity of medium and long term internal
        state.

        This function should be implemented by all subclasses so that
        it preserves the ability of the Projection to compute
        activity, i.e. to operate over a short time scale, while
        preventing any lasting changes to the state.

        For instance, if new_plasticity_state is False, in a
        Projection with modifiable connection weights, the values of
        those weights should temporarily be made fixed and unchanging
        after this call.  For a Projection with automatic
        normalization, homeostatic plasticity, or other features that
        depend on a history of events (rather than just the current
        item being processed), changes in those properties would be
        disabled temporarily.  Setting the plasticity state to False
        is useful during analysis operations (e.g. map measurement)
        that would otherwise change the state of the underlying
        network.

        Any process that does not have any lasting state, such as
        those affecting only the current activity level, should not
        be affected by this call.

        By default, this call simply calls override_plasticity_state()
        on the Projection's output_fn, and sets the 'plastic'
        parameter to False.
        """
        self._plasticity_setting_stack.append(self.plastic)
        self.plastic=new_plasticity_state

        for of in self.output_fns:
            if hasattr(of,'override_plasticity_state'):
                of.override_plasticity_state(new_plasticity_state)


    def restore_plasticity_state(self):
        """
        Restore previous plasticity state of medium and long term
        internal state after a override_plasticity_state call.

        This function should be implemented by all subclasses to
        remove the effect of the most recent override_plasticity_state call,
        e.g. to reenable plasticity of any type that was disabled.
        """
        self.plastic = self._plasticity_setting_stack.pop()

        for of in self.output_fns:
            if hasattr(of,'restore_plasticity_state'):
                of.restore_plasticity_state()


    def projection_view(self, timestamp=None):
        """Returns the activity in a single projection"""
        if timestamp is None:
            timestamp = self.src.simulation.time()
        sv = SheetView(self.activity.copy(), self.dest.bounds,
                         label='Activity', title='%s {label}' % self.name)
        sv.metadata=AttrDict(proj_src_name=self.src.name,
                             precedence=self.src.precedence,
                             proj_name=self.name,
                             row_precedence=self.src.row_precedence,
                             src_name=self.dest.name,
                             timestamp=timestamp)
        return sv


    def state_pop(self):
        """
        Pop the most recently pushed activity state of the stack.
        """
        self.activity = self.__saved_activity.pop()


    def state_push(self):
        """
        Push the current activity state onto the stack.
        """

        self.__saved_activity.append(array(self.activity))


    def get_projection_view(self, timestamp):
        self.warning("Deprecated, call 'projection_view' method instead.")
        return self.projection_view(timestamp)


    def n_bytes(self):
        """
        Estimate the memory bytes taken by this Projection.

        By default, counts only the activity array, but subclasses
        should implement this method to include also the bytes taken
        by weight arrays and any similar arrays, as a rough lower
        bound from which memory requirements and memory usage patterns
        can be estimated.
        """
        (rows,cols) = self.activity.shape
        return rows*cols


    def n_conns(self):
        """
        Return the size of this projection, in number of connections.

        Must be implemented by subclasses, if only to declare that no
        connections are stored.
        """
        raise NotImplementedError



class ProjectionSheet(Sheet):
    """
    A Sheet whose activity is computed using Projections from other sheets.

    A standard ProjectionSheet expects its input to be generated from
    other Sheets. Upon receiving an input event, the ProjectionSheet
    interprets the event data to be (a copy of) an activity matrix
    from another sheet.  The ProjectionSheet provides a copy of this
    matrix to each Projection from that input Sheet, asking each one
    to compute their own activity in response.  The same occurs for
    any other pending input events.

    After all events have been processed for a given time, the
    ProjectionSheet computes its own activity matrix using its
    activate() method, which by default sums all its Projections'
    activity matrices and passes the result through user-specified
    output_fns() before sending it out on the default output port.
    The activate() method can be overridden to sum some of the
    projections, multiply that by the sum of other projections, etc.,
    to model modulatory or other more complicated types of connections.
    """

    dest_ports=['Activity']

    src_ports=['Activity']

    # CEBALERT: why isn't this a parameter of Sheet?
    # Should be a MaskParameter for safety
    #mask = ClassSelectorParameter(SheetMask,default=SheetMask(),instantiate=True,doc="""
    mask = param.Parameter(default=SheetMask(),instantiate=True,doc="""
        SheetMask object for computing which units need to be computed further.
        The object should be an instance of SheetMask, and will
        compute which neurons will be considered active for the
        purposes of further processing.  The default mask effectively
        disables all masking, but subclasses can use this mask to
        implement optimizations, non-rectangular Sheet shapes,
        lesions, etc.""")

    # CEBALERT: not sure what to call this, and the default should
    # actually be False. True to match existing behavior.  Not sure
    # this parameter is necessary; clean up with NeighborhoodMask.
    # (Plus same comment as mask: why not parameter of sheet?)
    allow_skip_non_responding_units = param.Boolean(default=True,doc="""
        If true, then units that are inactive after the response
        function has been called can be skipped in subsequent
        processing. Whether or not the units will actually be skipped
        depends on the implementation of learning and learning output
        functions.""")


    def __init__(self, **params):
        super(ProjectionSheet,self).__init__(**params)
        self.new_input = False
        self.mask.sheet = self
        self.old_a = self.activity.copy()*0.0
        self.views['RFs'] = AttrTree()


    def _dest_connect(self, conn):
        """
        See EventProcessor's _dest_connect(); raises an error if conn is not
        a Projection.  Subclasses of ProjectionSheet that know how to handle
        other types of Connections should override this method.
        """
        if isinstance(conn, Projection):
            super(ProjectionSheet,self)._dest_connect(conn)
        else:
            raise TypeError('ProjectionSheets only accept Projections, not other types of connection.')


    def input_event(self,conn,data):
        """
        Accept input from some sheet.  Call .present_input() to
        compute the stimulation from that sheet.
        """
        self.verbose("Received input from %s on dest_port %s via connection %s." % (conn.src.name,str(conn.dest_port),conn.name))
        self.present_input(data,conn)
        self.new_input = True


    def _port_match(self,key,portlist):
        """
        Returns True if the given key matches any port on the given list.

        A port is considered a match if the port is == to the key,
        or if the port is a tuple whose first element is == to the key,
        or if both the key and the port are tuples whose first elements are ==.

        This approach allows connections to be grouped using tuples.
        """
        return [port for port in portlist
                if (port == key or
                    (isinstance(key,tuple)  and key[0] == port) or
                    (isinstance(port,tuple) and port[0] == key) or
                    (isinstance(key,tuple)  and isinstance(port,tuple) and port[0] == key[0]))]


    def _grouped_in_projections(self,ptype):
        """
        Return a dictionary of lists of incoming Projections, grouped by type.

        Each projection of type <ptype> is grouped according to the
        name of the port, into a single list within the dictionary.

        The entry None will contain those that are not of type
        <ptype>, while the other entries will contain a list of
        Projections, each of which has type ptype.

        Example: to obtain the lists of projections that should be
        jointly normalised together, call
        __grouped_in_projection('JointNormalize').
        """
        in_proj = OrderedDict()
        in_proj[None]=[] # Independent (ungrouped) connections

        for c in self.in_connections:
            d = c.dest_port
            if not isinstance(c,Projection):
                self.debug("Skipping non-Projection "+c.name)
            elif isinstance(d,tuple) and len(d)>2 and d[1]==ptype:
                if in_proj.get(d[2]):
                    in_proj[d[2]].append(c)
                else:
                    in_proj[d[2]]=[c]
            #elif isinstance(d,tuple):
            #    raise ValueError("Unable to determine appropriate action for dest_port: %s (connection %s)." % (d,c.name))
            else:
                in_proj[None].append(c)

        return in_proj


    def activate(self):
        """
        Collect activity from each projection, combine it to calculate
        the activity for this sheet, and send the result out.

        Subclasses may override this method to whatever it means to
        calculate activity in that subclass.
        """

        self.activity *= 0.0
        tmp_dict={}

        for proj in self.in_connections:
            if (proj.activity_group != None) | (proj.dest_port[0] != 'Activity'):
                if not tmp_dict.has_key(proj.activity_group[0]):
                    tmp_dict[proj.activity_group[0]]=[]
                tmp_dict[proj.activity_group[0]].append(proj)

        keys = tmp_dict.keys()
        keys.sort()
        for priority in keys:
            tmp_activity = self.activity.copy() * 0.0

            for proj in tmp_dict[priority]:
                tmp_activity += proj.activity
            self.activity=tmp_dict[priority][0].activity_group[1](self.activity,tmp_activity)

        if self.apply_output_fns:
            for of in self.output_fns:
                of(self.activity)

        self.send_output(src_port='Activity',data=self.activity)


    def process_current_time(self):
        """
        Called by the simulation after all the events are processed for the
        current time but before time advances.  Allows the event processor
        to send any events that must be sent before time advances to drive
        the simulation.
        """
        if self.new_input:
            self.activate()
            self.new_input = False
            if self.plastic:
                self.learn()


    def learn(self):
        """
        By default, call the learn() and apply_learn_output_fns()
        methods on every Projection to this Sheet.

        Any other type of learning can be implemented by overriding this method.
        Called from self.process_current_time() _after_ activity has
        been propagated.
        """
        for proj in self.in_connections:
            if not isinstance(proj,Projection):
                self.debug("Skipping non-Projection "+proj.name)
            else:
                proj.learn()
                proj.apply_learn_output_fns()


    def present_input(self,input_activity,conn):
        """
        Provide the given input_activity to each in_projection that has a dest_port
        equal to the specified port, asking each one to compute its activity.

        The sheet's own activity is not calculated until activate()
        is called.
        """
        conn.activate(input_activity)


    def projections(self,name=None):
        """

        Return either a named input p, or a dictionary
        {projection_name, projection} of all the in_connections for
        this ProjectionSheet.

        A minor convenience function for finding projections by name;
        the sheet's list of in_connections usually provides simpler
        access to the Projections.
        """
        if not name:
            return dict([(p.name,p) for p in self.in_connections])
        else:
            for c in self.in_connections:
                if c.name == name:
                    return c
            raise KeyError(name)


    def override_plasticity_state(self, new_plasticity_state):
        """
        Temporarily override plasticity state of medium and long term
        internal state.

        This function should be implemented by all subclasses so that
        when new_plasticity_state=False, it preserves the ability of
        the ProjectionSheet to compute activity, i.e. to operate over
        a short time scale, while preventing any lasting changes to
        the state.

        Any process that does not have any lasting state, such as
        those affecting only the current activity level, should not
        be affected by this call.

        By default, calls override_plasticity_state() on the
        ProjectionSheet's output_fns and all of its incoming
        Projections, and also enables the 'plastic' parameter for this
        ProjectionSheet.  The old value of the plastic parameter is
        saved to an internal stack to be restored by
        restore_plasticity_state().
        """
        super(ProjectionSheet,self).override_plasticity_state(new_plasticity_state)

        for of in self.output_fns:
            if hasattr(of,'override_plasticity_state'):
                of.override_plasticity_state(new_plasticity_state)

        for proj in self.in_connections:
            # Could instead check for a override_plasticity_state method
            if isinstance(proj,Projection):
                proj.override_plasticity_state(new_plasticity_state)


    def restore_plasticity_state(self):
        super(ProjectionSheet,self).restore_plasticity_state()

        for of in self.output_fns:
            if hasattr(of,'restore_plasticity_state'):
                of.restore_plasticity_state()

        for proj in self.in_connections:
            if isinstance(proj,Projection):
                proj.restore_plasticity_state()


    def state_push(self):
        """
        Subclasses Sheet state_push to also push projection activities.
        """
        super(ProjectionSheet, self).state_push()
        for p in self.projections().values(): p.state_push()


    def state_pop(self):
        """
        Subclasses Sheet state_pop to also pop projection activities.
        """
        super(ProjectionSheet, self).state_pop()
        for p in self.projections().values(): p.state_pop()


    def n_bytes(self):
        """
        Estimate the memory bytes taken by this Sheet and its Projections.

        Typically, this number will include the activity array and any
        similar arrays, plus memory taken by all incoming Projections.
        It will not usually include memory taken by the Python
        dictionary or various "housekeeping" attributes, which usually
        contribute only a small amount to the memory requirements.
        Thus this value should be considered only a rough lower bound
        from which memory requirements and memory usage patterns can
        be estimated.

        Subclasses should reimplement this method if they store a
        significant amount of data other than in the activity array
        and the projections.
        """
        return self.activity.nbytes + \
               sum([p.n_bytes() for p in self.in_connections
                    if isinstance(p,Projection)])


    def n_conns(self):
        """
        Count the total size of all incoming projections, in number of connections.
        """
        return sum([p.n_conns() for p in self.in_connections
                    if isinstance(p,Projection)])


# CEBALERT: untested
class NeighborhoodMask(SheetMask):
    """
    A SheetMask where the mask includes a neighborhood around active neurons.

    Given a radius and a threshold, considers a neuron active if at
    least one neuron in the radius is over the threshold.
    """

    threshold = param.Number(default=0.00001,bounds=(0,None),doc="""
       Threshold for considering a neuron active.
       This value should be small to avoid discarding significantly active
       neurons.""")

    radius = param.Number(default=0.05,bounds=(0,None),doc="""
       Radius in Sheet coordinates around active neurons to consider
       neighbors active as well.  Using a larger radius ensures that
       the calculation will be unaffected by the mask, but it will
       reduce any computational benefit from the mask.""")


    def __init__(self,sheet,**params):
        super(NeighborhoodMask,self).__init__(sheet,**params)


    def calculate(self):
        rows,cols = self.data.shape

        # JAHACKALERT: Not sure whether this is OK. Another way to do
        # this would be to ask for the sheet coordinates of each unit
        # inside the loop.

        # transforms the sheet bounds with bounds2slice() and then
        # uses this to cut out the activity window
        ignore1,matradius = self.sheet.sheet2matrixidx(self.radius,0)
        ignore2,x = self.sheet.sheet2matrixidx(0,0)
        matradius = abs(matradius-x)
        for r in xrange(rows):
            for c in xrange(cols):
                rr = max(0,r-matradius)
                cc = max(0,c-matradius)
                neighbourhood = self.sheet.activity[rr:r+matradius+1,cc:c+matradius+1].ravel()
                self.data[r][c] = sometrue(neighbourhood>self.threshold)
