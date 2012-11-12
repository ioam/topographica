<!-- -*-html-helper-*- mode -- (Hint for Emacs)-->

<H1>Parameters</H1>

<P>The behavior of most of the objects making up a Topographica
simulation can be controlled by variables called Parameters. A 
<?php classref('param.parameterized','Parameter')?> 
is a special type of Python attribute extended to have
features such as type and range checking, dynamically generated
values, documentation strings, default values, etc., each of which
is inherited from parent classes if not specified in a subclass.
Parameter support is provided by the
<A HREF="../Reference_Manual/param-module.html">param</A> package,
which was developed alongside Topographica but is completely
independent and usable for any Python project.

<P>Objects that can contain Parameters are called
<?php classref('param.parameterized','Parameterized')?> objects.
For instance, Sheets, Projections, and
PatternGenerators are all Parameterized.  The Parameters of a
Sheet include its <code>nominal_density</code> and <code>nominal_bounds</code>, and
the Parameters of a PatternGenerator include its <code>scale</code> and
<code>offset</code>.

<H2>Basic usage</H2>

<P>For the most part, Parameters can be used just like Python
attributes.  For instance, consider
<code>G=topo.pattern.Gaussian()</code>.  This is a
two-dimensional Gaussian pattern generator, which has the Parameters
<code>scale</code>, <code>offset</code>, <code>x</code>,
<code>y</code>, <code>size</code>, <code>aspect_ratio</code>, and
<code>orientation</code>.  (To see this list, you can select Gaussian
in a Test Pattern window, or type 
<code>G.params().keys()</code> at a Topographica command
prompt.)  From a Topographica command prompt, you can type
<code>G.scale</code> to see its scale (e.g. 1.0), and e.g.
<code>G.scale=0.8</code> to set it.  Alternatively, you can set the
value via the <code>scale</code> widget in a Test Pattern window.

<P>The biggest difference from a standard Python attribute is visible
when one tries to set a Parameter to a value that is not allowed.  For
instance, you can try to enter <code>-1</code> in the
<code>aspect_ratio</code> box, or type <code>G.aspect_ratio=-0.5</code>
at the command prompt, but in either case you should get a ValueError.
Similarly, trying to set it to anything but a number
(e.g. <code>G.aspect_ratio="big"</code>) should produce an error.
These errors are detected because the <code>aspect_ratio</code> has
been declared as a <code>Number</code> Parameter with bounds
'(0,None)' (i.e. a minimum value of 0.0, and no maximum value). 

<P>To provide reasonable checking for parameters of different types, a large number of
<A HREF="../Reference_Manual/param-module.html">other
Parameter types</A> are provided besides
<?php classref('param','Number')?>,
such as
<?php classref('param','Integer')?>,
<?php classref('param','Filename')?>,
<?php classref('param','Enumeration')?>,
and
<?php classref('param','Boolean')?>.
Each of these types can be declared to be constant, in which case the
value cannot be changed after the Parameterized object that owns the
Parameter has been created.  Some classes, such as
<?php classref('param','Number')?>,
allow the parameter values to be generated from a sequence or random
distribution, such as for generating random input patterns; in this
case the random number will be updated at most once for each unique
value of simulation time.  <!-- Explain more? -->

<P>Parameters also typically have a <code>doc</code> string, which is
a brief explanation of what the Parameter does (as for function and
class docstrings in Python).  Some Parameter types or instances can
be declared to have <code>softbounds</code>, which are used to
suggest the sizes of GUI sliders for the object, and
<code>precedence</code>, which determines the sorting order for the
Parameter in the GUI or in lists.  A large number of Parameter types
are provided, and more can be added easily.


<H2>Inheritance and class Parameters</H2>

<P>Parameterized objects inherit Parameter values from
their parent classes, allowing Parameterized objects to use default
values for most Parameters.  This is designed to work just as Python
attribute inheritance normally works, but also inheriting any
documentation, bounds, etc. associated with the Parameter, even when
the default value is overridden.  For instance, the Gaussian
PatternGenerator parameters <code>x</code> and <code>y</code> are not
actually specified in the Gaussian class, but are inherited from the
base class, PatternGenerator.  If the value for x or y is set on the
Gaussian object <code>G</code> (as in <code>G.x=0.5</code>) or the
Gaussian class itself (by typing <code>Gaussian.x=0.5</code> or
<code>x=0.5</code> in the source code for the Gaussian class), the
values will overwrite the defaults, yet the same documentation and
bounds will still apply.

<P>Note that there is an important difference between setting the
Parameter on the class and on the object.  If we do
<code>G.x=0.5</code>, only object G will be affected. If we do
<code>Gaussian.x=0.5</code>, all future objects of type Gaussian will
have a default x value of 0.5.  Moreover, all <i>existing</i> objects
of type Gaussian will also get the new x value of 0.5, unless the user
has previously set the value of x on that object explicitly.  That is,
setting a Parameter at the class level typically affects all existing
and future objects from that class, unless the object has overriden
the value for that Parameter.  To affect only one object, set the
value on that object by itself.

<P>In certain cases, it can be confusing to have objects inherit from
a single shared class Parameter.  For instance, constant parameters
are expected to keep the same value even if the class Parameter is
later changed.  Also, mutable Parameter objects, i.e. values that have
internal state (such as lists, arrays, or class instances) can have
very confusing behavior if they are shared between Parameterized
objects, because changes to one Parameterized object's value can
affect all the others.  In both of these cases (constants and
Parameters whose values may be mutable objects) the Parameter is
typically set to <code>instantiate=True</code>, which forces every
Parameterized object owning that Parameter to instantiate its own
private, independent copy when the Parameterized object is created.
This avoids much confusion, but does prevent existing objects from
being controlled as a group by changing the class Parameters.


<H2>Inheritance examples</H2>

The following examples should clarify how Parameter values are
inherited and instantiated.  In Python, attributes (including but not
limited to Parameters) declared at the class level are shared by all
instances of that class, unless an instance overwrites the attribute
with its own copy of the variable. For example:

<pre>
class Example(object):
    a = 10
</pre>

Here <code>a</code> is a class attribute, because it is declared at
the class level (outside of any method like <code>__init__</code>).
Creating two instances of Example demonstrates that the value
<code>a</code> is shared between the instances:

<pre>
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
</pre>

Note that setting the class attribute on the Example class changed the
value held in both instances. For an Example instance to have its own,
independent copy of the variable, it is necessary to set the variable
directly on the instance:

<pre>
Topographica> example2.a=19
Topographica> Example.a=40
Topographica> example1.a
40
Topographica> example2.a
19
</pre>

Because instances share the object held in the class attribute, any
changes to attributes of the object will show up in all the instances.
The same general rules apply to Parameters declared at the class
level:

<pre>
import param

class ExampleP(param.Parameterized):
    a = param.Parameter(default=10)
</pre>

<pre>
Topographica> example1 = ExampleP()
Topographica> example1.a
10
Topographica> ExampleP.a = 40
Topographica> example1.a
40
</pre>

However, if a specific Parameter value is passed in when creating the
object, there will be a separate and independent copy containing that
value:

<pre>
Topographica> e1 = ExampleP(a=8)
Topographica> e1.a
8
Topographica> ExampleP.a = 12
Topographica> e1.a
8
</pre>

The author of a class can also force this behavior even when no value
is supplied by declaring <code>a</code> with <code>a =
Parameter(default=10,instantiate=True)</code>.  As mentioned above,
this is useful when the Parameter will hold a mutable object, when
sharing between instances would lead to confusion.

<P>For instance, consider a Parameter whose value is the learning 
function <code>Oja</code>, which itself has the Parameter
<code>alpha</code>. A user might
want to declare that all <code>CFSheet</code>s should have 
a single output function, <code>Oja</code>, by
setting <code>CFSheet.learning_fn=Oja()</code>.  Without
<code>instantiate=True</code>, instances of the class
<code>CFSheet</code> would share a single <code>Oja</code>
object. A user with a number of <code>CFSheet</code>s might be
surprised to find that setting <code>alpha</code> on one
particular <code>CFSheet</code>'s learning_fn would change it on them all.

<P>To avoid this confusion, the author of <code>CFSheet</code> can
declare that the learning_fn Parameter always be instantiated:

<pre>
learning_fn = Parameter(default=Oja(),instantiate=True)
</pre>

In this case, each instance of CFSheet will have its own instance of
Oja, independent of other <code>CFSheet</code>s' <code>Oja()</code>
instances.  In fact, learning_fn parameters (like others taking
mutable objects) are typically declared not as Parameter but as <?php
classref('param','ClassSelector')?>, which sets
<code>instantiate=True</code> automatically.  Thus in most cases users
can use Parameters without worrying about the details of inheritance
and instantiation, but the details have been included here because the
behavior in unusual cases may be surprising.
