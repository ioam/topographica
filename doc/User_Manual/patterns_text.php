<H1>Generating patterns</H1>

<P>Topographica provides comprehensive support for creating
two-dimensional patterns of various sorts.  These patterns can be used
for generating training or testing inputs, generating initial or fixed
weight patterns, neighborhood kernels, or any similar application.
Pattern support is provided by the
<A HREF="../Reference_Manual/imagen-module.html">ImaGen</A> package,
which was developed alongside Topographica but is completely
independent and usable for any simulator.

<H2>Simple patterns</H2>

<P>The basic types of patterns supported by Topographica include:

<center>
<img src="images/patterntypes_small.png" width="598" height="209">
</center>

<P>These patterns are created using objects of type
<?php classref('topo.base.patterngenerator','PatternGenerator')?>,
which is an object that will return a 2D pattern 
when it is called as a function.  For instance, the Gaussian
PatternGenerator will return Gaussian-shaped patterns:

<pre>
$ topographica -g
Topographica&gt; from topo import pattern
Topographica&gt; pg=pattern.Gaussian(xdensity=60,ydensity=60,size=0.3,aspect_ratio=1.0)
Topographica&gt; 
Topographica&gt; matrixplot(pg())
Topographica&gt; matrixplot(pg(size=0.5))
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
of the parameters are set to Dynamic values.  For instance, a Gaussian
input pattern can be specified to have a random orientation and (x,y)
location:

<pre>
$ topographica -g
Topographica&gt; from topo import pattern, numbergen
Topographica&gt; input_pattern = pattern.Gaussian(size=0.08, aspect_ratio=4,
                 xdensity=60,ydensity=60,
                 x=numbergen.UniformRandom(lbound=-0.5,ubound=0.5,seed=12),
                 y=numbergen.UniformRandom(lbound=-0.5,ubound=0.5,seed=34),
                 orientation=numbergen.UniformRandom(lbound=-pi,ubound=pi,seed=56))
Topographica&gt; matrixplot(input_pattern())
Topographica&gt; matrixplot(input_pattern())
</pre>

<center>
<img src="images/or_gaussian_1.png" width="169" height="159"><img src="images/or_gaussian_2.png" width="169" height="159">
</center>

<P>There are many other types of patterns available already defined in
the <A HREF="../Reference_Manual/topo.pattern-module.html">
topo/pattern</A> directory, and adding new patterns is
straightforward.  Just create a new class inheriting from
PatternGenerator or one of its subclasses, make sure it is loaded
before you start the GUI, and it will then show up in the Test Pattern
window of the GUI automatically, and can be used in scripts the same
way.

<H2>Composite patterns</H2>

<P>Often, rather than writing a new PatternGenerator class, you can
combine existing PatternGenerators to make a new pattern.  To do this,
Topographica provides the special Composite PatternGenerator, which
accepts a list of other PatternGenerators and an operator for
combining them.  For instance, you can make connection weights be
random but with a Gaussian falloff in strength by setting:

<pre>
CFProjection.weights_generator=pattern.Composite(
    generators=[pattern.random.UniformRandom(),
                pattern.Gaussian(aspect_ratio=1.0,size=0.2)],
    operator=numpy.multiply)
</pre>

<center>
<!-- <img src="images/gaussianrandomweights.png" width=640 height=432> -->
<img src="images/gaussianrandomweights_dense.png" width="396" height="368">
</center>

<P>More complex patterns can be created by combining multiple Composite PatternGenerators:

<pre>
$ topographica -g
Topographica&gt; from topo import pattern
Topographica&gt; import numpy
Topographica&gt; surroundsine   = pattern.SineGrating(frequency=8.0,orientation=0.25*pi,
Topographica&gt;                                      phase=3*pi/2)
Topographica&gt; centersine     = pattern.SineGrating(frequency=8.0,orientation=0.60*pi)
Topographica&gt; centerdisk     = pattern.Disk(aspect_ratio=1.0, size=0.35, smoothing=0.005)
Topographica&gt; surrounddisk   = pattern.Disk(aspect_ratio=1.0, size=0.90, smoothing=0.005)
Topographica&gt; surroundring   = pattern.Composite(generators=[surrounddisk,centerdisk],
Topographica&gt;                                    operator=numpy.subtract)
Topographica&gt; center         = pattern.Composite(generators=[centersine,centerdisk],
Topographica&gt;                                    operator=numpy.multiply)
Topographica&gt; surround       = pattern.Composite(generators=[surroundsine,surroundring],
Topographica&gt;                                    operator=numpy.multiply)
Topographica&gt; centersurround = pattern.Composite(generators=[center,surround],
Topographica&gt;                                    operator=numpy.add,
Topographica&gt;                                    xdensity=160,ydensity=160)
Topographica&gt; matrixplot(centersurround())
</pre>

<center>
<img src="images/centersurround.png" width="384" height="384">
</center>

<P>Once created, even very complex composite patterns can be scaled,
rotated, and placed together as a unit:

<pre>
$ topographica -g
Topographica&gt; from topo import pattern
Topographica&gt; import numpy
Topographica&gt; pattern.Disk.smoothing=0.005
Topographica&gt; lefteye    = pattern.Disk(    aspect_ratio=0.7, x=0.04, y=0.10, size=0.08, scale=1.00)
Topographica&gt; leftpupil  = pattern.Disk(    aspect_ratio=1.0, x=0.03, y=0.08, size=0.04, scale=-1.6)
Topographica&gt; righteye   = pattern.Disk(    aspect_ratio=0.7, x=0.04, y=-0.1, size=0.08, scale=1.00)
Topographica&gt; rightpupil = pattern.Disk(    aspect_ratio=1.0, x=0.03, y=-0.08,size=0.04, scale=-1.6)
Topographica&gt; nose       = pattern.Gaussian(aspect_ratio=0.8, x=-0.1, y=0.00, size=0.04, scale=-0.5)
Topographica&gt; mouth      = pattern.Gaussian(aspect_ratio=0.8, x=-0.2, y=0.00, size=0.06, scale=-0.8)
Topographica&gt; head       = pattern.Disk(    aspect_ratio=1.5, x=-0.02,y=0.00, size=0.40, scale=0.70)
Topographica&gt; pg=pattern.Composite(generators=[lefteye,leftpupil,righteye,rightpupil,nose,mouth,head],
Topographica&gt;                      operator=numpy.add,xdensity=160,ydensity=160)
Topographica&gt; matrixplot(pg(orientation=pi/1.8, x=0.2, y=0.1, offset=0.5, size=0.75))
</pre>

<center>
<img src="images/face.png" width="310" height="299">
</center>

<P>A wide variety of operators are provided for combining the patterns; see the
<A HREF="../Reference_Manual/topo.pattern.Composite-class.html#operator">
Composite parameter <code>operator</code></A> for more details.


<H2>Selector patterns</H2>

<P>Instead of combining the patterns, it can also be useful to choose
one from a set of different patterns, such as choosing randomly from a
database of natural images.  This can be done with the Selector
PatternGenerator.  As a contrived example, weights can be choosen at
random from a set of four different pattern generators:

<pre>
CFProjection.weights_generator=pattern.Selector(generators=[
    pattern.Gaussian(orientation=numbergen.UniformRandom(lbound=-pi,ubound=pi,seed=99)),
    pattern.Gaussian(aspect_ratio=1.0,
                     x=numbergen.UniformRandom(lbound=-0.2,ubound=0.2,seed=12),
                     y=numbergen.UniformRandom(lbound=-0.2,ubound=0.2,seed=34)),
    pattern.Rectangle(orientation=numbergen.UniformRandom(lbound=-pi,ubound=pi,seed=99),
                      size=0.3),
    pattern.Disk(size=0.2)])
</pre>

<center>
<img src="images/fourclassweights.png" width="390" height="371">
</center>

