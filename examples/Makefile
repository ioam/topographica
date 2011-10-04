# $Id$
#
# Commands for running the example files
#
# JPALERT: Should consider rewriting this in Python so that it can run
# easily under Windows as well.
# CEBALERT: and how does this relate to topo/misc/genexamples.py?

all_quick: hierarchical som_retinotopy lissom_oo_or
all_long: lissom_oo_or_10000.typ gcal_10000.typ som_retinotopy_40000.typ lissom_or_10000.typ lissom_fsa_10000.typ
saved-examples: lissom_oo_or_10000.typ

# Allow extra arguments to be passed to the Topographica command line
TOPOCMD= -a

# Define typical commands used in the examples
SNAPSHOT = -c "save_snapshot"

OR_ANALYSIS = -c "measure_or_pref(); measure_cog()"
#measure_or_tuning_fullfield(); \
#measure_position_pref(); \

RETINOTOPY_ANALYSIS = -c "measure_position_pref(); measure_cog()"

tests: test_running

# Trivial test to make sure that everything at least loads; will have some errors if images are not present
test_loading:	
	bash -c 'for file in *.ty ; do echo "Loading $${file}..." ; ../topographica -c default_density=2 $${file} ; done'

# Trivial test to make sure that everything at least loads; will have some errors if images are not present
test_running:	
	bash -c 'for file in *.ty ; do echo "Running $${file}..." ; ../topographica -c default_density=2 $${file} -c "topo.sim.run(1)"; done'


# Perform simple tests that the examples at least run; should be
# replaced by more extensive tests.
hierarchical:
	cd .. ; ./topographica -c "default_density=4" examples/hierarchical.ty -c "topo.sim.run(1)"

lissom_or:
	cd .. ; ./topographica -c "default_density=4" examples/lissom_or.ty -c "topo.sim.run(1)"

lissom_oo_or:
	cd .. ; ./topographica -c "default_density=4" examples/lissom_oo_or.ty -c "topo.sim.run(1)"

som_retinotopy:
	cd .. ; ./topographica -c "default_density=4" examples/som_retinotopy.ty -c "topo.sim.run(1)"


# Generate saved examples of complete simulations
lissom_oo_or_10000.typ: lissom_oo_or.ty ../topo/*/*.py
	../topographica ${TOPOCMD} lissom_oo_or.ty -c "topo.sim.run(10000)" ${OR_ANALYSIS} ${SNAPSHOT}"('$@')"


gcal_10000.typ: gcal.ty ../topo/*/*.py
	../topographica ${TOPOCMD} gcal.ty -c "topo.sim.run(10000)" ${OR_ANALYSIS} ${SNAPSHOT}"('$@')"


lissom_or_10000.typ: lissom_or.ty ../topo/*/*.py
	../topographica ${TOPOCMD} lissom_or.ty -c "topo.sim.run(10000)" ${OR_ANALYSIS} ${SNAPSHOT}"('$@')"


lissom_fsa_10000.typ: lissom_fsa.ty ../topo/*/*.py
	../topographica ${TOPOCMD} lissom_fsa.ty -c "topo.sim.run(10000)" ${SNAPSHOT}"('$@')"


obermayer_pnas90_30000.typ: obermayer_pnas90.ty ../topo/*/*.py
	../topographica ${TOPOCMD} obermayer_pnas90.ty -c "topo.sim.run(30000)" ${OR_ANALYSIS} ${SNAPSHOT}"('$@')"


goodhill_network90_1000.typ: goodhill_network90.ty ../topo/*/*.py
	../topographica ${TOPOCMD} goodhill_network90.ty -c "topo.sim.run(1000)" ${SNAPSHOT}"('$@')"


som_retinotopy_40000.typ: som_retinotopy.ty ../topo/*/*.py
	../topographica ${TOPOCMD} som_retinotopy.ty -c "topo.sim.run(40000)" ${RETINOTOPY_ANALYSIS} ${SNAPSHOT}"('$@')"

# Paths handled a bit differently because lissom_whisker_barrels.ty refers to examples/
lissom_whisker_barrels_20000.typ: lissom_whisker_barrels.ty ../topo/*/*.py
	cd .. ; ./topographica ${TOPOCMD} examples/lissom_whisker_barrels.ty -c "topo.sim.run(20000)" ${SNAPSHOT}"('$@')"
	mv lissom_whisker_barrels_20000.typ examples/



