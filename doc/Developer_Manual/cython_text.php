<H1>Cython</H1>

<P>This is draft documentation! Needs checking and editing, at
least.

<p><a target="_top" href="http://www.cython.org/">Cython</a> language is very close
to the Python language, but Cython
additionally supports calling C functions and declaring C types on
variables and class attributes. This allows the compiler to generate
very efficient C code from Cython code. Cython is based on the
well-known Pyrex, but supports more cutting edge functionality and
optimizations. We shall demonstrate how a significant performance
boost can be achieved by using some basic code optimization using
Cython. </p>

<p>Our test case scenario is converting a 768 by 576 pixels image from
RGB (red, green, blue) color space to HSV (hue, saturation, value),
while making sure that the results remain correct (by converting the
RGB-&gt;HSV result back to RGB, and comparing the initial and final
values), which is <span style="font-weight: bold;">always</span> very
important when doing optimizations - you first <strong>must</strong>
have a test written to ensure the output is still correct, and that
test should be run every time you do any changes to the code. Color
space
conversion functions are taken directly from
<a target="_top" href="http://docs.python.org/library/colorsys.html"><code>colorsys</code></a>
Python module (which can usually be found in
/usr/lib/python2.X/colorsys.py).</p>

<p>The baseline code is as follows:

<pre>
##############################
# color_conversion.py
##############################

import Image
import numpy
import colorfns

imagepath = 'images/mcgill/foliage_b/01.png'
red,green,blue = Image.open(imagepath).split()
R = numpy.array(red, dtype=numpy.float32)/255.0
G = numpy.array(green, dtype=numpy.float32)/255.0
B = numpy.array(blue, dtype=numpy.float32)/255.0

## test rgb_to_hsv
def test():
    h,s,v = colorfns.rgb_to_hsv_array(R,G,B)

</pre>


<pre>
##############################
# colorfns.py
##############################

import numpy
import param

# Copied from Python's colorsys module
def rgb_to_hsv(r, g, b):
    maxc = max(r, g, b)
    minc = min(r, g, b)
    v = maxc
    if minc == maxc: return 0.0, 0.0, v
    s = (maxc-minc) / maxc
    rc = (maxc-r) / (maxc-minc)
    gc = (maxc-g) / (maxc-minc)
    bc = (maxc-b) / (maxc-minc)
    if r == maxc: h = bc-gc
    elif g == maxc: h = 2.0+rc-bc
    else: h = 4.0+gc-rc
    h = (h/6.0) % 1.0
    return h, s, v
   
# naive array version
def rgb_to_hsv_array(r,g,b):
    rows,cols = r.shape
    h=numpy.zeros((rows,cols), dtype=float)
    v=numpy.zeros((rows,cols), dtype=float)
    s=numpy.zeros((rows,cols), dtype=float)
    for i in range(rows):
        for j in range(cols):
            h[i,j],s[i,j],v[i,j]=rgb_to_hsv(r[i,j],g[i,j],b[i,j])
    return h,s,v
</pre>

<h4>Timing</h4>

To
time your functions with Python, you need to import <code>timeit</code>,
and use
its <code>Timer("function_to_be_timed()", "import required_function")</code>
object to get the running time. In our case, the following lines are
added at the bottom of <span style="font-style: italic;">color_conversion.py</span>:<br>

<pre>
...
import timeit

t = timeit.Timer("test()",&nbsp; "from __main__ import test")
print min(t.repeat(repeat=10,&nbsp; number=1)),&nbsp; " sec/pass"&nbsp; # report the lowset time out of 10 runs
</pre>

Using <code>timeit</code> Python module
we measure running time of the baseline code to
be 8.62 sec/pass, which will be our reference performance.<br>
<h4>Importing Cython modules<br>
</h4>
<p>First of all, in order to use Cython code, we need to make it
compile first. The key point here is that lines: <br>
</p>
<pre>import pyximport<br>pyximport.install()</pre>
<p><span style="font-weight: bold;">must</span> come before using any
of the Cython code. This can be achieved in a number of ways. In case
you are using Topographica, the most convenient way would be to add
these two lines to your <span style="font-style: italic;">.topographicarc</span>
file. Adding them to the top of <span style="font-style: italic;">PATH_TO_TOPOGRAPHICA/topographica</span>
file would also do the job, although this would not be as flexible as
the first option (e.g. if you re-build Topographica from the source
often). On the other hand, if you only want to test a small portion of
the code (e.g. one script), a possible approach would be to write a
'substitute' script (named
<span style="font-style: italic;">colorfns.py</span>, in this case),
which would use <code>pyximport</code> module to
compile our Cython code:</p>
<pre>import pyximport<br>pyximport.install()<br>from colorfns_cython import * <br></pre>
<p>Cython also must know which modules are written using its features,
which is done by using <span style="font-weight: bold;">.pyx</span>
file extensions. In the 'substitute script' case, <code>colorfns_cython</code>
would be the <span style="font-style: italic;">colorfns_cython</span><span
 style="font-weight: bold; font-style: italic;">.pyx</span> file (<b>not
.py</b>) which contains our Cython code. To run the
Cython code, we would use <span style="font-style: italic;">colorfns.py</span>
to import all the functions from&nbsp;<span style="font-style: italic;">colorfns_cython.pyx</span>
which would then enable us to call them as normal Python
functions. Timing the unmodified code, as imported by the script above,
gives the running time of 7.60 sec/pass, so the result is already
starting to improve.<br>
</p>
<h2>Python code conversion to Cython</h2>
<h4>Typing arguments<br>
</h4>
The rule of thumb, when doing Python -&gt; Cython conversion, is to let
Cython know what type of an object (<code>int</code>, <code>float</code>,
numpy.ndarray etc.) we are dealing with (this is called typing).
Inside functions, this is done using <code>cdef</code> statements,
while function arguments are typed without using <code>cdef</code>.
Let us start by typing function arguments for&nbsp;<code></code><code>rgb_to_hsv()</code>,
and <code>rgb_to_hsv_array()</code>.
We
know
that
arguments for <code></code><code>rgb_to_hsv()</code>
are of type <code>numpy.float32</code>, because we initialized R, G,
and B as:
<pre>    
R = numpy.array(R,dtype=numpy.float32)  ## dtype = numpy.float32 is used
G = numpy.array(G,dtype=numpy.float32)
B = numpy.array(B,dtype=numpy.float32)
</pre>

<p>Therefore, arguments for <code>rgb_to_hsv(r, g,
b)</code> are typed
as <code>rgb_to_hsv(numpy.float32_t h, numpy.float32_t s,
numpy.float32_t v)</code>, where <code>numpy.float32_t</code> is the
type identifier for single precision floating point number (equivalents
exist for all types supported by numpy e.g. numpy.float64_t for double,
numpy.int32_t for int etc.). For Cython to know these types, numpy must
be imported using <code>cimport</code> statement, which we include
among all the other imports on the top of <span
 style="font-style: italic;">colorfns.py</span>. Function<code></code> <code>rgb_to_hsv_array()</code>
is expecting numpy arrays as
their arguments, so the same conversion procedure as for <code>rgb_to_hsv()</code><code></code>
is applied, except for this time
arguments have the type numpy.ndarray: <code>rgb_to_hsv_array(r,
g,
b)</code> becomes <code>rgb_to_hsv_array(numpy.ndarray r,
numpy.ndarray g, numpy.ndarray b)</code>. For convenience, we can use <code>ctypedef
numpy.float32_t
float_t</code> statement to save some time on typing,
and improved readability. So far, our changes in the code look like
(showing only the modified lines):</p>
<pre>...<b><br>cimport numpy<br></b>...<b><br>ctypedef numpy.float32_t float_t</b><br>...<br>def rgb_to_hsv(<b>float_t</b> r, <b>float_t</b> g, <b>float_t</b> b):<br>...<br>...<br>def rgb_to_hsv_array(<b>numpy.ndarray</b> r, <b>numpy.ndarray</b> g, <b>numpy.ndarray</b> b):<br>...<br></pre>
<p><code>Timeit</code> reports running time of this code to be 1.50
sec/pass - already ~5.7 times faster than the original Python code<span
 style="font-weight: bold;"><br>
Note:</span> such optimization might reduce the types that a function
can accept, therefore it is advised to do type checking if you are not
certain about what arguments might be passed.<br>
</p>

<h4>
<p>Typing array contents</p>
</h4>
<h4></h4>

<p>Even though we typed arguments for <code>rgb_to_hsv_array()</code>,
arrays are still accessed using
Python operations. To access the data at C speed, we need to type the
contents of every <code>numpy.ndarray</code> by specifying what that
particular array holds, and what are the dimensions of it. The syntax
for such statement is <code>numpy.ndarray<b>[type,ndim=n]</b></code>,
where <code>type</code> is the type identifier for the contents, and <code>n</code>
is the number
of dimensions of that array. Having said that, we use the <code>numpy.ndarray[type,ndim=n]</code>
notation to get:</p>
<pre>...<br>def rgb_to_hsv_array(numpy.ndarray<b>[numpy.float32_t, ndim=2]</b> r, numpy.ndarray<b>[numpy.float32_t, ndim=2]</b> g, numpy.ndarray<b>[float_t, ndim=2]</b> b):<br>...<br></pre>
<p>Again, <code>timeit</code> reports a further improvement: 1.43
sec/pass. <br>
</p>

<h4>
<p>Typing variables</p>
</h4>
<h4></h4>

<p>Next, we do typing inside the<span style="font-family: monospace;"></span><code></code>
<code>rgb_to_hsv()</code> function.
As
it
was
mentioned before, typing inside functions is done using <code>cdef
type
variable_name</code> statements, where, again, <code>type</code>
is the type identifier, and <code>variable_name</code> is... You
guessed it - the name of the variable to be typed. The important thing
to remember here, is that <b>all</b> interacting variables inside
the function need to be typed, failing to do so will result in
significant drop in performance (Cython then tries to use any untyped
variables as Python objects). Variable typing results in:</p>
<pre>def rgb_to_hsv(float_t r, float_t g, float_t b):<br>    <b>cdef float</b> maxc = max(r, g, b)<br>    <b>cdef float</b> minc = min(r, g, b)<br>    <b>cdef float</b> v = maxc<br>    if minc == maxc: return 0.0, 0.0, v<br>    <b>cdef float</b> s = (maxc-minc) / maxc<br>    <b>cdef float</b> rc = (maxc-r) / (maxc-minc)<br>    <b>cdef float</b> gc = (maxc-g) / (maxc-minc)<br>    <b>cdef float</b> bc = (maxc-b) / (maxc-minc)<br>    <b>cdef float</b> h<br>    if r == maxc: h = bc-gc<br>    elif g == maxc: h = 2.0+rc-bc<br>    ...<br></pre>
<p><code>Timeit</code> shows 1.11 sec/pass. So far, so good. Let us now
type variables in <code>rgb_to_hsv_array()</code>:</p>
<pre>def rgb_to_hsv_array(numpy.ndarray[float_t, ndim=2] r, numpy.ndarray[float_t, ndim=2] g, numpy.ndarray[float_t, ndim=2] b):<br>    ...<br>    <b>cdef numpy.ndarray[float_t, ndim=2]</b> h = numpy.zeros(shape,dtype=numpy.float32)<br>    <b>cdef numpy.ndarray[float_t, ndim=2]</b> v = numpy.zeros(shape,dtype=numpy.float32)<br>    <b>cdef numpy.ndarray[float_t, ndim=2]</b> s = numpy.zeros(shape,dtype=numpy.float32)<br>    <b>cdef int i,j</b>  # counter variables are very important!<br>    ...<br></pre>
<p>What does <code>timeit</code> think about this? 0.48 sec/pass - 18
times faster!<br>
</p>

<h4>
<p>Removing built-in Python functions</p>
</h4>
<h4></h4>

<p>So far we have taken only the basic, and most trivial steps in
optimizing Cython code. Any further performance improvements
require some investigation. <code>cProfile</code> module comes in
handy in such situations (see Profiling Cython section below for
details). Profiling the existing code reveals that <code>rgb_to_hsv()</code>
is rather slow,
because it uses <code>min()</code> and <code>max()</code> that are
built-in Python functions, which means that we are going back to
'Python speed' whenever we call them (442368 times, to be exact). One
possible improvement here,
is to use <code>cdef</code> to declare some functions that will be
in-lined for us. The syntax for inline functions is <code>cdef inline
return_type function_name()</code>. An example in our case, would be
writing <code>float_max()</code> and <code>float_min()</code>, that
take three floats as their arguments, and return the biggest/smallest
value out of three respectively:</p>

<pre>cdef inline float_t float_max(float_t a, float_t b, float_t c):<br>    if (a &gt; b) and (a &gt; c): return a<br>    elif b &gt; c:return b<br>    else:return c<br><br>cdef inline float_t float_min(float_t a, float_t b, float_t c):<br>    if (a &lt; b) and (a &lt; c):return a<br>    elif b &lt; c:return b<br>    else:return c<br></pre>
we need to modify <code>rgb_to_hsv()</code> to use our Cython
functions instead of Python ones:
<pre>def rgb_to_hsv(float_t r, float_t g, float_t b):<br>    cdef float maxc = <b>float_max</b>(r, g, b)<br>    cdef float minc = <b>float_min</b>(r, g, b)<br>    ...<br></pre>
<p><code>Timeit</code> reports 0.16 sec/pass, which is 54 times faster
than the original Python code.<br>
</p>

<h4>
<p>Profiling Cython<br>
</p>
</h4>
In order
to profile Cython code, we must use compiler directive <code># cython:
profile=True</code> at the top of <span style="font-style: italic;">colorfns_cython.pyx</span>
file:<br>
<br>
<code><span style="font-weight: bold;"># cython: profile=True</span><br>
import numpy<br>
import param<br>
cimport numpy<br>
<br>
# copied from Python's colorsys module<br>
def rgb_to_hsv(r, g, b):<br>
...</code><br>
<br>
Afterwards, cProfile can be used as for any ordinary Python code
profiling. In this case, we can modify the <span
 style="font-style: italic;">color_conversion.py</span> script to be:<br>
<code><br>
...<br>
import pyximport<br>
pyximport.install()<br>
<span style="font-weight: bold;">import cProfile, pstats</span><span
 style="font-weight: bold;"></span><br style="font-weight: bold;">
<br style="font-weight: bold;">
<span style="font-weight: bold;">cProfile.runctx("test()", globals(),
locals(), "Profile.prof")</span><br style="font-weight: bold;">
<span style="font-weight: bold;">s = pstats.Stats("Profile.prof")</span><br
 style="font-weight: bold;">
<span style="font-weight: bold;">s.strip_dirs().sort_stats("time").print_stats()</span></code><br>
<br>
As an alternative to cProfile, you could also use any other tool that
profiles C code e.g. <a target="_top" href="http://valgrind.org/">Valgrind</a>.<br>

<h2>Recap and conclusion<br>
</h2>
1) We started off by changing the file extension from .py
into .pyx, and used <code>pyximport</code>
to compile it.<br>
2) Next, we typed the arguments for two of our functions: <code></code><code>rgb_to_hsv()</code>,<code></code>
and <code>rgb_to_hsv_array()</code>.<br>
3) We typed the contents of each <code>numpy.ndarray</code> passed as
an argument, by using the <code>numpy.ndarray[type,ndim=n]</code>
notation.<br>
4) Types were declared inside <code></code><code>rgb_to_hsv()</code>,
using
<code>cdef type variable_name</code>.<br>
5) Types were declared inside<code></code> <code>rgb_to_hsv_array()</code>.<br>
6) We in-lined <code>float_max()</code> and <code>float_min()</code>
to be used instead of <code>max()</code> and <code>min()</code>,
which are built-in Python functions (avoid using them if possible!).<br>
<p>The final result of these steps is execution type drop from 8.67s to
0.16s, which is more than a x50 speedup:</p>
<p><img style="width: 681px; height: 273px;" src="rt.png"
 alt="Running time decrease at each step"> </p>
<p>In this short Cython guide, we discussed only the basic principles
of using Cython to improve the performance of your code. Many more
topics were left untouched, and can be found in
<a target="_top" href="http://docs.cython.org/">Cython documentation</a>. Nevertheless,
we hope that this guide will give an idea on how to
start using Cython for (pretty much effortless) performance boosting of
your own code.<br>
</p>

