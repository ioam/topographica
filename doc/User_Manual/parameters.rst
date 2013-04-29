**********
Parameters
**********

The behavior of most of the objects making up a Topographica
simulation can be controlled by variables called Parameters. A
`Parameter`_ is a special type of Python attribute extended to have
features such as type and range checking, dynamically generated
values, documentation strings, default values, etc., each of which
is inherited from parent classes if not specified in a subclass.
Parameter support is provided by the `param`_ package, which was
developed alongside Topographica but is completely independent and
usable for any Python project.

Objects that can contain Parameters are called `Parameterized`_
objects. For instance, Sheets, Projections, and PatternGenerators
are all Parameterized. The Parameters of a Sheet include its
``nominal_density`` and ``nominal_bounds``, and the Parameters of a
PatternGenerator include its ``scale`` and ``offset``.

Basic usage
-----------

For the most part, Parameters can be used just like Python
attributes. For instance, consider ``G=topo.pattern.Gaussian()``.
This is a two-dimensional Gaussian pattern generator, which has the
Parameters ``scale``, ``offset``, ``x``, ``y``, ``size``,
``aspect_ratio``, and ``orientation``. (To see this list, you can
select Gaussian in a Test Pattern window, or type
``G.params().keys()`` at a Topographica command prompt.) From a
Topographica command prompt, you can type ``G.scale`` to see its
scale (e.g. 1.0), and e.g. ``G.scale=0.8`` to set it. Alternatively,
you can set the value via the ``scale`` widget in a Test Pattern
window.

The biggest difference from a standard Python attribute is visible
when one tries to set a Parameter to a value that is not allowed.
For instance, you can try to enter ``-1`` in the ``aspect_ratio``
box, or type ``G.aspect_ratio=-0.5`` at the command prompt, but in
either case you should get a ValueError. Similarly, trying to set it
to anything but a number (e.g. ``G.aspect_ratio="big"``) should
produce an error. These errors are detected because the
``aspect_ratio`` has been declared as a ``Number`` Parameter with
bounds '(0,None)' (i.e. a minimum value of 0.0, and no maximum
value).

To provide reasonable checking for parameters of different types, a
large number of `other Parameter types`_ are provided besides
`Number`_, such as `Integer`_, `Filename`_, `Enumeration`_, and
`Boolean`_. Each of these types can be declared to be constant, in
which case the value cannot be changed after the Parameterized
object that owns the Parameter has been created. Some classes, such
as `Number`_, allow the parameter values to be generated from a
sequence or random distribution, such as for generating random input
patterns; in this case the random number will be updated at most
once for each unique value of simulation time.

Parameters also typically have a ``doc`` string, which is a brief
explanation of what the Parameter does (as for function and class
docstrings in Python). Some Parameter types or instances can be
declared to have ``softbounds``, which are used to suggest the sizes
of GUI sliders for the object, and ``precedence``, which determines
the sorting order for the Parameter in the GUI or in lists. A large
number of Parameter types are provided, and more can be added
easily.

Inheritance and class Parameters
--------------------------------

Parameterized objects inherit Parameter values from their parent
classes, allowing Parameterized objects to use default values for
most Parameters. This is designed to work just as Python attribute
inheritance normally works, but also inheriting any documentation,
bounds, etc. associated with the Parameter, even when the default
value is overridden. For instance, the Gaussian PatternGenerator
parameters ``x`` and ``y`` are not actually specified in the
Gaussian class, but are inherited from the base class,
PatternGenerator. If the value for x or y is set on the Gaussian
object ``G`` (as in ``G.x=0.5``) or the Gaussian class itself (by
typing ``Gaussian.x=0.5`` or ``x=0.5`` in the source code for the
Gaussian class), the values will overwrite the defaults, yet the
same documentation and bounds will still apply.

Note that there is an important difference between setting the
Parameter on the class and on the object. If we do ``G.x=0.5``, only
object G will be affected. If we do ``Gaussian.x=0.5``, all future
objects of type Gaussian will have a default x value of 0.5.
Moreover, all *existing* objects of type Gaussian will also get the
new x value of 0.5, unless the user has previously set the value of
x on that object explicitly. That is, setting a Parameter at the
class level typically affects all existing and future objects from
that class, unless the object has overriden the value for that
Parameter. To affect only one object, set the value on that object
by itself.

In certain cases, it can be confusing to have objects inherit from a
single shared class Parameter. For instance, constant parameters are
expected to keep the same value even if the class Parameter is later
changed. Also, mutable Parameter objects, i.e. values that have
internal state (such as lists, arrays, or class instances) can have
very confusing behavior if they are shared between Parameterized
objects, because changes to one Parameterized object's value can
affect all the others. In both of these cases (constants and
Parameters whose values may be mutable objects) the Parameter is
typically set to ``instantiate=True``, which forces every
Parameterized object owning that Parameter to instantiate its own
private, independent copy when the Parameterized object is created.
This avoids much confusion, but does prevent existing objects from
being controlled as a group by changing the class Parameters.

Inheritance examples
--------------------

The following examples should clarify how Parameter values are
inherited and instantiated. In Python, attributes (including but not
limited to Parameters) declared at the class level are shared by all
instances of that class, unless an instance overwrites the attribute
with its own copy of the variable. For example:

::

  class Example(object):
    a = 10

Here ``a`` is a class attribute, because it is declared at the class
level (outside of any method like ``__init__``). Creating two
instances of Example demonstrates that the value ``a`` is shared
between the instances:

::

  Topographica> example1 = Example()
  Topographica> example2 = Example()
  Topographica> example1.a
  10
  Topographica> example2.a
  10
  Topographica> Example.a=7
  Topographica> example1.a
  7
  Topographica> example2.a
  7

Note that setting the class attribute on the Example class changed
the value held in both instances. For an Example instance to have
its own, independent copy of the variable, it is necessary to set
the variable directly on the instance:

::

  Topographica> example2.a=19
  Topographica> Example.a=40
  Topographica> example1.a
  40
  Topographica> example2.a
  19

Because instances share the object held in the class attribute, any
changes to attributes of the object will show up in all the
instances. The same general rules apply to Parameters declared at
the class level:

::

  import param

  class ExampleP(param.Parameterized):
    a = param.Parameter(default=10)

::

  Topographica> example1 = ExampleP()
  Topographica> example1.a
  10
  Topographica> ExampleP.a = 40
  Topographica> example1.a
  40

However, if a specific Parameter value is passed in when creating
the object, there will be a separate and independent copy containing
that value:

::

  Topographica> e1 = ExampleP(a=8)
  Topographica> e1.a
  8
  Topographica> ExampleP.a = 12
  Topographica> e1.a
  8

The author of a class can also force this behavior even when no
value is supplied by declaring ``a`` with
``a = Parameter(default=10,instantiate=True)``. As mentioned above,
this is useful when the Parameter will hold a mutable object, when
sharing between instances would lead to confusion.

For instance, consider a Parameter whose value is the learning
function ``Oja``, which itself has the Parameter ``alpha``. A user
might want to declare that all ``CFSheet``\ s should have a single
output function, ``Oja``, by setting ``CFSheet.learning_fn=Oja()``.
Without ``instantiate=True``, instances of the class ``CFSheet``
would share a single ``Oja`` object. A user with a number of
``CFSheet``\ s might be surprised to find that setting ``alpha`` on
one particular ``CFSheet``'s learning\_fn would change it on them
all.

To avoid this confusion, the author of ``CFSheet`` can declare that
the learning\_fn Parameter always be instantiated:

::

  learning_fn = Parameter(default=Oja(),instantiate=True)

In this case, each instance of CFSheet will have its own instance of
Oja, independent of other ``CFSheet``\ s' ``Oja()`` instances. In
fact, learning\_fn parameters (like others taking mutable objects)
are typically declared not as Parameter but as `ClassSelector`_,
which sets ``instantiate=True`` automatically. Thus in most cases
users can use Parameters without worrying about the details of
inheritance and instantiation, but the details have been included
here because the behavior in unusual cases may be surprising.

.. _Parameter: ../Reference_Manual/param.parameterized.Parameter-class.html
.. _param: ../Reference_Manual/param-module.html
.. _Parameterized: ../Reference_Manual/param.parameterized.Parameterized-class.html
.. _other Parameter types: ../Reference_Manual/param-module.html
.. _Number: ../Reference_Manual/param.Number-class.html
.. _Integer: ../Reference_Manual/param.Integer-class.html
.. _Filename: ../Reference_Manual/param.Filename-class.html
.. _Enumeration: ../Reference_Manual/param.Enumeration-class.html
.. _Boolean: ../Reference_Manual/param.Boolean-class.html
.. _ClassSelector: ../Reference_Manual/param.ClassSelector-class.html
