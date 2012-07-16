<H1>ImaGen</H1>

<P>The ImaGen package provides comprehensive support for creating
resolution-independent one and two-dimensional spatial pattern
distributions.  ImaGen consists of a large library of primarily
two-dimensional patterns, including mathematical functions, geometric
primitives, images read from files, and many ways to combine or select
from any other patterns.  These patterns can be used in any Python
program that needs configurable patterns or a series of patterns, with
only a small amount of user-level code to specify or use each pattern.

<P>For instance, various machine vision, neural network, or
computational neuroscience programs require a series of input patterns
or network-configuration patterns, but do not need to know any of the
details of how these patterns are generated.  ImaGen can easily
provide such patterns, often without needing any modification to the
target code, as long as it can accept a Numpy array.

<H2>Coordinate systems</H2>

In each of the examples below, the parameters are given in what ImaGen
calls Sheet coordinates, which are independent of the resolution of
the rendered matrix.  This feature allows the patterns to be
resolution indepdenent (as in a vector drawing program).  See
<A HREF="coords.html">ImaGen spatial coordinate systems</A> for more
details.

<H2>Simple patterns</H2>

<P>The basic types of patterns supported by ImaGen include:

<center>
<img src="images/patterntypes_small.png" width="598" height="209">
</center>

<P>These patterns are created using objects of type
<?php classref('imagen.patterngenerator','PatternGenerator')?>,
which is an object that will return a 2D pattern 
when it is called as a function.  For instance, the Gaussian
PatternGenerator will return Gaussian-shaped patterns:

<pre>
$ ipython -pylab
&gt;&gt;&gt; import imagen
&gt;&gt;&gt; pg=imagen.Gaussian(xdensity=60,ydensity=60,size=0.3,aspect_ratio=1.0)
&gt;&gt;&gt;
&gt;&gt;&gt; imshow(pg(),cmap=cm.gray,interpolation='nearest')
&gt;&gt;&gt; imshow(pg(size=0.5),cmap=cm.gray,interpolation='nearest')
</pre>

<center>
<img src="images/gaussian_0.3.png" width="174" height="165"><img src="images/gaussian_0.5.png" width="174" height="165">
</center>

<P>As you can see, the parameters of a PatternGenerator can be set up
when you create the object, or they can be supplied when you generate
the pattern.  Any parameter not supplied in either location inherits
the default value set for it in that PatternGenerator class.

<P>The reason for the name PatternGenerator is that the objects can
each actually return an infinite number of different patterns, if any
of the parameters are set to Dynamic values, using the included
<A HREF="../Reference_Manual/numbergen-module.html">
numbergen</A> directory.  For instance, a Gaussian
input pattern can be specified to have a random orientation and (x,y)
location:

<pre>
$ ipython -pylab
&gt;&gt;&gt; import imagen, numbergen
&gt;&gt;&gt; input_pattern = imagen.Gaussian(size=0.08, aspect_ratio=4,
                 xdensity=60,ydensity=60,
                 x=numbergen.UniformRandom(lbound=-0.5,ubound=0.5,seed=12),
                 y=numbergen.UniformRandom(lbound=-0.5,ubound=0.5,seed=34),
                 orientation=numbergen.UniformRandom(lbound=-pi,ubound=pi,seed=56))
&gt;&gt;&gt; imshow(input_pattern(),cmap=cm.gray,interpolation='nearest')
&gt;&gt;&gt; imshow(input_pattern(),cmap=cm.gray,interpolation='nearest')
</pre>

<center>
<img src="images/or_gaussian_1.png" width="169" height="159"><img src="images/or_gaussian_2.png" width="169" height="159">
</center>

<P>There are many other types of patterns available already defined in
the <A HREF="../Reference_Manual/imagen-module.html">
imagen</A> directory, and adding new patterns is
straightforward.  Just create a new class inheriting from
PatternGenerator or one of its subclasses, make sure it is loaded
before you start the GUI, and you can then use it just like the
existing patterns.


<H2>Composite patterns</H2>

<P>Often, rather than writing a new PatternGenerator class, you can
combine existing PatternGenerators to make a new pattern.  To do this,
ImaGen provides the special Composite PatternGenerator, which
accepts a list of other PatternGenerators and an operator for
combining them.  As a fairly complex example:

<pre>
$ ipython -pylab
&gt;&gt;&gt; import imagen
&gt;&gt;&gt; import numpy
&gt;&gt;&gt; surroundsine   = imagen.SineGrating(frequency=8.0,orientation=0.25*pi,
&gt;&gt;&gt;                                      phase=3*pi/2)
&gt;&gt;&gt; centersine     = imagen.SineGrating(frequency=8.0,orientation=0.60*pi)
&gt;&gt;&gt; centerdisk     = imagen.Disk(aspect_ratio=1.0, size=0.35, smoothing=0.005)
&gt;&gt;&gt; surrounddisk   = imagen.Disk(aspect_ratio=1.0, size=0.90, smoothing=0.005)
&gt;&gt;&gt; surroundring   = imagen.Composite(generators=[surrounddisk,centerdisk],
&gt;&gt;&gt;                                    operator=numpy.subtract)
&gt;&gt;&gt; center         = imagen.Composite(generators=[centersine,centerdisk],
&gt;&gt;&gt;                                    operator=numpy.multiply)
&gt;&gt;&gt; surround       = imagen.Composite(generators=[surroundsine,surroundring],
&gt;&gt;&gt;                                    operator=numpy.multiply)
&gt;&gt;&gt; centersurround = imagen.Composite(generators=[center,surround],
&gt;&gt;&gt;                                    operator=numpy.add,
&gt;&gt;&gt;                                    xdensity=160,ydensity=160)
&gt;&gt;&gt; imshow(centersurround(),cmap=cm.gray,interpolation='nearest')
</pre>

<center>
<img src="images/centersurround.png" width="384" height="384">
</center>

<P>Once created, any Composite pattern can be scaled, rotated, and
placed together as a unit:

<pre>
$ ipython -pylab
&gt;&gt;&gt; import numpy, imagen
&gt;&gt;&gt; imagen.Disk.smoothing=0.005
&gt;&gt;&gt; lefteye    = imagen.Disk(    aspect_ratio=0.7, x=0.04, y=0.10, size=0.08, scale=1.00)
&gt;&gt;&gt; leftpupil  = imagen.Disk(    aspect_ratio=1.0, x=0.03, y=0.08, size=0.04, scale=-1.6)
&gt;&gt;&gt; righteye   = imagen.Disk(    aspect_ratio=0.7, x=0.04, y=-0.1, size=0.08, scale=1.00)
&gt;&gt;&gt; rightpupil = imagen.Disk(    aspect_ratio=1.0, x=0.03, y=-0.08,size=0.04, scale=-1.6)
&gt;&gt;&gt; nose       = imagen.Gaussian(aspect_ratio=0.8, x=-0.1, y=0.00, size=0.04, scale=-0.5)
&gt;&gt;&gt; mouth      = imagen.Gaussian(aspect_ratio=0.8, x=-0.2, y=0.00, size=0.06, scale=-0.8)
&gt;&gt;&gt; head       = imagen.Disk(    aspect_ratio=1.5, x=-0.02,y=0.00, size=0.40, scale=0.70)
&gt;&gt;&gt; pg=imagen.Composite(generators=[lefteye,leftpupil,righteye,rightpupil,nose,mouth,head],
&gt;&gt;&gt;                      operator=numpy.add,xdensity=160,ydensity=160)
&gt;&gt;&gt; imshow(pg(orientation=pi/1.8, x=0.2, y=0.1, offset=0.5, size=0.75),cmap=cm.gray,interpolation='nearest')
</pre>

<center>
<img src="images/face.png" width="310" height="299">
</center>

<P>A wide variety of operators are provided for combining the patterns; see the
<A HREF="../Reference_Manual/imagen.Composite-class.html#operator">
Composite parameter <code>operator</code></A> for more details.


<H2>Selector patterns</H2>

<P>Instead of combining the patterns, it can also be useful to choose
one from a set of different patterns, such as choosing randomly from a
database of natural images.  This can be done with the Selector
PatternGenerator.  Here's an example of choosing 100 samples from a
Selector that chooses a random pattern from a set of four different
pattern generators:

<pre>
 pg=imagen.Selector(generators=[
    imagen.Gaussian(orientation=numbergen.UniformRandom(lbound=-pi,ubound=pi,seed=99)),
    imagen.Gaussian(aspect_ratio=1.0,
                     x=numbergen.UniformRandom(lbound=-0.2,ubound=0.2,seed=12),
                     y=numbergen.UniformRandom(lbound=-0.2,ubound=0.2,seed=34)),
    imagen.Rectangle(orientation=numbergen.UniformRandom(lbound=-pi,ubound=pi,seed=99),
                      size=0.3),
    imagen.Disk(size=0.2)])
</pre>

<center>
<img src="images/fourclassweights.png" width="390" height="371">
</center>




