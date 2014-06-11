### Check fixedpoint works for simulation time
import topo
from topo.misc.fixedpoint import FixedPoint

def fixedpoint_time_type(x, precision=4):
    "A fixedpoint time type of given precision"
    return FixedPoint(x, precision)

original_type = topo.sim.time.time_type
topo.sim.initialized=False
assert topo.sim.time(0.0,time_type = fixedpoint_time_type) == FixedPoint('0.0000', 4)
z = FixedPoint(0.999,4)
z-=topo.sim.convert_to_time_type(0.0004)
assert z == FixedPoint('0.9986', 4)
topo.sim.time(0.0, time_type = original_type)
topo.sim.intialized=True
