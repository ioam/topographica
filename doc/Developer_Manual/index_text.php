<P>This manual gives guidelines for developers working on the source
code for the Topographica simulator. Users will not usually need to
refer to this material, unless they plan to submit significant blocks
of code to the project (which is, of course, strongly <a href="#joining">encouraged</a>!).

<P>Before starting, you will need to install a version-controlled
copy of Topographica. Please see our
developer <A HREF="installation.html">installation instructions</A>
for how to do this.

<P>By default, all the text in this manual refers to program code
written in the Python language. There are also some bits of C/C++ code
in the simulator, which use different conventions.


<P><DL COMPACT>
<P><DT><A href="coding.html"><strong>General guidelines</strong></A></DT>
<DD>General info on writing Python, plus Topographica-specific
conventions such as guidelines for naming, comments, documentation,
parameters, units, and external imports.

<P><DT><A href="ood.html"><strong>Object-oriented design</strong></A></DT>
<DD>How to design well-structured code</DD>

<P><DT><A href="imports.html"><strong>Importing files and packages</strong></A></DT>
<DD>How to import Topographica and external code</DD>

<P><DT><A href="alerts.html"><strong>ALERTs</strong></A></DT>
<DD>How to flag incorrect or confusing code or documentation</DD>

<P><DT><A href="gui.html"><strong>GUI programming</strong></A></DT>
<DD>How to add functionality to the GUI</DD>

<P><DT><A href="optimization.html"><strong>Performance optimization</strong></A></DT>
<DD>When (and when not!) to optimize for performance, and how to do it</DD>

<P><DT><A href="memuse.html"><strong>Memory usage</strong></A></DT>
<DD>How to measure memory usage and reduce it</DD>

<P><DT><A href="revisioncontrol.html"><strong>Revision control</strong></A></DT>
<DD>How we keep track of changes to the code and other files</DD>

<P><DT><A href="refactoring.html"><strong>Refactoring/testing tips</strong></A></DT>
<DD>Tips for improving existing code by refactoring</DD>

<P><DT><A href="testing.html"><strong>Test suite</strong></A></DT>
<DD>Rationale behind unit tests; should eventually include information
about how to set up tests</DD>

<P><DT><A href="releases.html"><strong>Releases</strong></A></DT>
<DD>How to make a new public release of Topographica</DD>

<P><DT><A name="joining"><strong>Joining</strong></A></DT> <DD>Anyone
interested in Topographica is welcome to join as a Topographica
developer to get read/write access, so that your changes can become
part of the main distribution.  Just sign up for a free account at <A
HREF="http://sourceforge.net/"> SourceForge.net</A>, then email <A
HREF="mailto:&#106&#98&#101&#100&#110&#97&#114&#64&#105&#110&#102&#46&#101&#100&#46&#97&#99&#46&#117&#107?subject=Request%20to%20be%20a%20Topographica%20developer">Jim</a>
your username and what you want to do, and he'll tell you how to
proceed from there. Alternatively, if you want to use Git, you can
immediately <A HREF="../Downloads/git.html">create your own git
repository</A>.  It is also possible to <A
href="../Downloads/bzr.html">get your own Bazaar branch</A> from
Topographica's Bazaar mirror of the SVN repository, but we do not
necessarily provide any support for this.  </DD> </DL>
