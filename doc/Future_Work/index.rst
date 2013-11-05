***********
Future Work
***********



Topographica is under very active development, but there are always
more features that we have not yet been able to implement or bugs
that we have not been able to address. These will be listed in our
GitHub `Issues`_ list, or or in the issues for a specific
`subproject`_ if appropriate. Feel free to add suggestions of your
own to those lists, or to `tackle one of the existing problems
listed`_ if you need that feature for your work. In particular, we are
always happy to receive your (well-written) 
`pull requests! <https://github.com/ioam/topographica/pulls>`_
Other general, ongoing tasks include:

ALERTs
======

There are a large number of relatively small problems noted in the
source code for the simulator; these are marked with comments
containing the string ALERT. These comments help clarify how the
code should look when it is fully polished, and act as our to-do
list. They also help prevent poor programming style from being
propagated to other parts of the code before we have a chance to
correct it. We are slowly working to correct these issues.

Improve documentation
=====================

The reference manual is generated automatically from the source
code, and needs significant attention to ensure that it is readable
and consistent. For instance, not all parameters are documented yet,
but all will need to be.

More testing code
=================

Topographica has a fairly complete test library, but there are still
classes and functions without corresponding tests. Eventually, there
should be tests for everything.

Pycheck/pylint
==============

Topographica code is automatically checked using pyflakes, 
but more stringent tests can be performed by the pycheck and
pylint programs. It would be very useful to fix any suspicious items
reported by those programs, and to disable the remaining warnings.
That way, new code could be automatically checked with those
programs and the warnings would be likely to be meaningful. (Right
now, the real issues detected by those programs are buried in a sea
of spurious warnings.)

More non-visual modalities
==========================

Much of the neural-specific code in Topographica was designed with
visual areas in mind, but it is written generally so that it applies
to any topographically organized region. Examples are provided for
somatosensory inputs (e.g. rodent whisker barrels), auditory inputs,
and motor outputs (for controlling eye movements) that show how to
work with those modalities, but additional contributions for other
types of sensory inputs or motor outputs would be very welcome from
Topographica users with experience in these domains.

More library components
=======================

Topographica currently includes examples of each type of library
component, such as Sheets, Projections, TransferFns,
ResponseFunctions, LearningFunctions, and PatternGenerators.
However, many other types are used in the literature, and as these
are implemented in Topographica they will be added to the library.
Again, user contributions are very welcome!

More example models
===================

Topographica currently includes a number of example models, mostly
from the visual system but also from somatosensory, auditory, and
motor areas. As additional models are implemented, they will be
added as examples and starting points. Again, user contributions are
very welcome!

.. _Issues: https://github.com/ioam/topographica/issues
.. _subproject: https://github.com/ioam
.. _tackle one of the existing problems listed: ../Developer_Manual/index.html#joining
