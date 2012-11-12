<P>This manual gives guidelines for developers working on the source
code for the Topographica simulator. Users will not usually need to
refer to this material, unless they plan to submit significant blocks
of code to the project (which is, of course, strongly <a target="_top" href="#joining">encouraged</a>!).

<P>By default, all the text in this manual refers to program code
written in the Python language. There are also some bits of C/C++ code
in the simulator, which use different conventions.

<P><em>Note that Topographica's documentation may change between
releases, so developers should usually be reading either their locally
built copy of the documentation, or the online <A
HREF="http://buildbot.topographica.org/doc/Developer_Manual/index.html">
nightly documentation build</A>. The documentation at topographica.org
applies to the previous release, so may be out of date with respect to
the current version of Topographica in Git.</em>

<P><DL COMPACT>

<P><DT><A href="installation.html"><strong>Installation instructions</strong></A></DT>
<DD>Before starting, you will need a version-controlled copy of Topographica.

<P><DT><A href="revisioncontrol.html"><strong>Revision control</strong></A></DT>
<DD>How we keep track of changes to the code and other files</DD>

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
HREF="http://github.com/">GitHub.com</A>, then email <A
HREF="mailto:&#106&#98&#101&#100&#110&#97&#114&#64&#105&#110&#102&#46&#101&#100&#46&#97&#99&#46&#117&#107?subject=Request%20to%20be%20a%20Topographica%20developer">Jim</a>
your username and what you want to do, and he'll tell you how to
proceed from there. Alternatively, you can start immediately by
cloning Topographica, developing your feature, and 
<A HREF="git.html#pullrequest">submitting it as a public pull request</A> only
once it's done.
</DD>
</DL>
