#!/bin/tcsh

echo HOST:"\t"$HOST

echo PARAMS:"\t"$1"\t"$2"\t"$3"\t"$4

echo VERSION:"\t"`git describe --tags`

echo Loading Topographica ant quitting:

time ../../topographica -c quit

echo ----------------------------------

echo Loading Topographica + setting up $1 using $2 cortex density + running 0 iterations \(gpu=$4\):

time ../../topographica -p cortex_density=$2 -p gpu=$4 $1 -c "topo.sim.run(0)"

echo ----------------------------------

echo Loading Topographica + setting up $1 using $2 cortex density + running $3 iterations \(gpu=$4\):

time ../../topographica -p cortex_density=$2 -p gpu=$4 $1 -c "topo.sim.run($3)"

echo ----------------------------------
