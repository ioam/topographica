#!/bin/tcsh

echo HOST:"\t"$HOST

echo PARAMS:"\t"$1"\t"$2"\t"$3

echo VERSION:"\t"`git describe --tags`

echo Loading Topographica ant quitting:

time ./topographica -c quit

echo ----------------------------------

echo Loading Topographica + setting up gcal_oo_or.ty using $1 cortex density + running 0 iterations \(gpu=$3\):

time ./topographica -p cortex_density=$1 -p gpu=$3 examples/gcal_oo_or.ty -c "topo.sim.run(0)"

echo ----------------------------------

echo Loading Topographica + setting up gcal_oo_or.ty using $1 cortex density + running $2 iterations \(gpu=$3\):

time ./topographica -p cortex_density=$1 -p gpu=$3 examples/gcal_oo_or.ty -c "topo.sim.run($2)"

echo ----------------------------------
