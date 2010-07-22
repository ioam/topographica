This directory contains example Topographica simulation scripts,
including the following simple ones:

  tiny.ty              - Short, simple, fast example
  hierarchical.ty      - Example of connecting multiple maps
  lissom_oo_or.ty      - LISSOM orientation map with ON/OFF channels
  som_retinotopy.ty    - SOM retinotopy map


Additionally, several other examples are also included:

  goodhill_network90.ty        - 2D ocular dominance elastic net model 

  gcal.ty                      - Orientation map with gain 
                                 control and homesotatic plasticity

  leaky_lissom_or.ty           - LISSOM with spiking neurons

  lissom.ty                    - LISSOM with orientation, direction, 
                                 ocular dominance, disparity, spatial 
                                 frequency, and color preference maps

  lissom_fsa.ty                - LISSOM-based face-selective-area 
                                 simulation

  lissom_or.ty                 - LISSOM orientation map with no ON/OFF 
                                 channels

  lissom_or_movie.ty           - Shows how to create an activity movie

  lissom_whisker_barrels.ty    - LISSOM whisker barrel cortex simulation

  obermayer_pnas90.ty          - SOM orientation map

  sullivan_neurocomputing04.ty - A temporal trace and SOM-based model 
                                 of complex cell development


Other scripts may also be included, but these are likely to be works
in progress, incomplete, or otherwise not particularly useful.  Once a
script has become useful, it should be placed into the above list (and
topographica/Makefile altered to ensure that it is not removed from
public distributions).
