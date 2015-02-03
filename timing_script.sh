#!/bin/tcsh

echo Loading Topographica ant quitting:

time ./topographica -c quit

echo ----------------------------------

echo Loading Topographica + setting up gcal_oo_or.ty using $1 cortex density + running 0 iterations \(gpu=$3\):

time ./topographica -p cortex_density=$1 -p gpu=$3 examples/gcal_oo_or.ty -c "topo.sim.run(0)"

echo ----------------------------------

echo Loading Topographica + setting up gcal_oo_or.ty using $1 cortex density + running 1 iteration \(gpu=$3\):

time ./topographica -p cortex_density=$1 -p gpu=$3 examples/gcal_oo_or.ty -c "topo.sim.run(1)"

echo ----------------------------------

echo Loading Topographica + setting up gcal_oo_or.ty using $1 cortex density + running $2 iterations \(gpu=$3\):

time ./topographica -p cortex_density=$1 -p gpu=$3 examples/gcal_oo_or.ty -c "topo.sim.run($2)"

echo ----------------------------------
