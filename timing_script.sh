#!/bin/tcsh

echo Loading Topographica ant quitting:

time ./topographica -c quit

echo ----------------------------------

echo Loading Topographica + setting up gcal_oo_or.ty using $1 cortex density + running 0 iterations:

time ./topographica -p cortex_density=$1 -p gpu=False examples/gcal_oo_or.ty -c "topo.sim.run(0)"

echo ----------------------------------

echo Loading Topographica + setting up gcal_oo_or.ty using $1 cortex density + running 1 iteration:

time ./topographica -p cortex_density=$1 -p gpu=False examples/gcal_oo_or.ty -c "topo.sim.run(1)"

echo ----------------------------------

echo Loading Topographica + setting up gcal_oo_or.ty using $1 cortex density + running $2 iterations:

time ./topographica -p cortex_density=$1 -p gpu=False examples/gcal_oo_or.ty -c "topo.sim.run($2)"

echo ----------------------------------

echo Loading Topographica + setting up gcal_oo_or.ty using $1 cortex density and GPU + running 0 iterations:

time ./topographica -p cortex_density=$1 -p gpu=True examples/gcal_oo_or.ty -c "topo.sim.run(0)"

echo ----------------------------------

echo Loading Topographica + setting up gcal_oo_or.ty using $1 cortex density and GPU + running 1 iteration:

time ./topographica -p cortex_density=$1 -p gpu=True examples/gcal_oo_or.ty -c "topo.sim.run(1)"

echo ----------------------------------

echo Loading Topographica + setting up gcal_oo_or.ty using $1 cortex density and GPU + running $2 iterations:

time ./topographica -p cortex_density=$1 -p gpu=True examples/gcal_oo_or.ty -c "topo.sim.run($2)"

echo ----------------------------------
