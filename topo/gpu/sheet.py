import param
import numpy as np

from topo.sheet import SettlingCFSheet
from topo.base.cf import CFSheet

import pycuda.gpuarray as gpuarray
import pycuda.driver as cuda
import pycuda.autoinit
import scikits.cuda.cusparse as cusparse

cusparse.init()



def compute_sparse_gpu_joint_norm_totals(projlist,active_units_mask=True):
    assert len(projlist)>=1
    
    joint_sum = gpuarray.zeros((projlist[0].weights_gpu.shape[0], ), np.float32)
    for p in projlist:
        if not p.has_norm_total:
            p.norm_total_gpu = p.weights_gpu.mv(p.norm_ones_gpu, autosync=True)
            p.has_norm_total = True
        joint_sum += p.norm_total_gpu
    for p in projlist:
        p.norm_total_gpu = joint_sum.copy()


class GPUSettlingCFSheet(SettlingCFSheet):
    """
    A SettlingCFSheet that makes it possible to calculate projection activities and learning in concurrent GPU streams.
    This is done by placing barriers before the 'activate' and 'learn' methods of the sheet that synchronize GPU streams.

    Otherwise, behaves exactly the same as SettlingCFSheet.
    """

    joint_norm_fn = param.Callable(default=compute_sparse_gpu_joint_norm_totals,doc="""
        Function to use to compute the norm_total for each CF in each
        gpu projection from a group to be normalized jointly.""")


    def __init__(self, **params):
        super(GPUSettlingCFSheet, self).__init__(**params)


    def process_current_time(self):
        """
        Pass the accumulated stimulation through self.output_fns and
        send it out on the default output port.

        We need to synchronize before processing the projection activities or their weights,
        since they might be still running on the GPU.
        """
        if self.new_input:
            self.new_input = False

            if self.activation_count == self.mask_init_time:
                cuda.Context.synchronize()
                self.mask.calculate()

            if self.tsettle == 0:
                # Special case: behave just like a CFSheet
                cuda.Context.synchronize()
                self.activate()
                self.learn()

            elif self.activation_count == self.tsettle:
                # Once we have been activated the required number of times
                # (determined by tsettle), reset various counters, learn
                # if appropriate, and avoid further activation until an
                # external event arrives.
                for f in self.end_of_iteration: f()

                self.activation_count = 0
                self.new_iteration = True # used by input_event when it is called
                if (self.plastic and not self.continuous_learning):
                    self.learn()
            else:                
                cuda.Context.synchronize()
                self.activate()
                self.activation_count += 1
                if (self.plastic and self.continuous_learning):
                   self.learn()


class GPUCFSheet(CFSheet):

    def __init__(self, **params):
        super(GPUCFSheet, self).__init__(**params)

    def process_current_time(self):
        """
        Called by the simulation after all the events are processed for the
        current time but before time advances.  Allows the event processor
        to send any events that must be sent before time advances to drive
        the simulation.
        
        GPUCFSheet is meant to be used with GPU projections that are called
        asynchronously and might not have computed the activation. Therefore, we synchronize.
        """
        if self.new_input:
            cuda.Context.synchronize()    
            self.activate()
            self.new_input = False
            if self.plastic:
                self.learn()        
