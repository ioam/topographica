**********************************
Coding Guidelines for Topographica
**********************************

This section covers general issues of how to write code to be
included in Topographica. It includes `general info on writing in
Python`_ and `Python-specific conventions`_, plus
Topographica-specific conventions such as `guidelines for naming`_,
`comments, documentation`_, `parameters`_, `numerical units`_, and
`file extensions`_.

.. _python:

Coding in Python
----------------

If you are familiar with other programming languages, but not
Python, the best place to start is to run the Python tutorial on the
`docs.python.org`_ web site. On the first pass, don't try to
memorize anything, just try to get a feel for the overall syntax and
workings of Python. Then try looking at the Topographica code. After
working with Topographica a while, it is then a good idea to revisit
the Python tutorial and go over it in more detail, trying to figure
everything out and remember it now that the basic concepts are
there.

For those with experience with functional programming languages like
ML, Haskell, Scheme, or Lisp, you will be pleased to find features
such as map, apply, reduce, filter, zip, and list comprehensions.
For those who aren't familiar with any of those, it is very
important to study the "Functional Programming Tools" and "List
Comprehensions" sections of the tutorial, because we often use those
features to write concise functions that may be hard to understand
at first glance. Lisp programmers should probably check out `Python
for Lisp Programmers`_ for details of differences.

For those with experience in Java or C++, a good (opinionated)
introduction is `Python is not Java`_, and the `Python and Java
Side-by-side comparison`_ may also be useful. For those without
prior experience in any programming language, you are probably
really a user, not a Topographica developer ``:-)``, but feel free
to get started by learning Python.

.. _conventions:

General conventions
-------------------

By default, the project uses the standard set of `Python coding
conventions`_ written by Guido van Rossum, Python's author.

These need not be followed to the letter; they simply help resolve
differences between Topographica authors if there are disagreements.

One particular guideline of these that Jim does not always follow is
that he likes to use lines much longer than 80 characters, e.g. for
a string. Other differences are listed elsewhere in this file, such
as in the `revision control`_ section.

To keep things simple and consistent, we try to use what seems to be
the most common Python names for the following concepts (as opposed
to those from C++ or Java):

method
 (not 'member function' or 'virtual function')
subclass
 (although 'derived class' is also ok)
superclass
 (although 'base class' is also ok)

Typically, classes are named with InitialCapitalLetters, functions,
methods, attributes, and parameters are
lower\_case\_with\_underscores, and filenames are
lowercasewithnounderscores.py.

For whitespace, the convention is to use no more than one blank line
within a function or method, two blank lines between methods, and
three between classes. The goal is to have the code making up a
function or method group visually into a single unit, and then to
have all methods and data in one class group visually into a higher
level unit. See the files in topo/base/ for examples.

All variable names, documentation, and comments should be in
English, using American spelling for consistency.

.. _naming:

Using consistent names
----------------------

Where there are already classes defined, please use the existing
names when writing new code, documentation, variable names, user
messages, window names, and comments. (Or else change all of the old
ones to match your new version!) For instance, Topographica is based
on Sheets, so everything should call a Sheet a Sheet, not a Region,
Area, or Layer.

In particular, when writing user interface code, think about what
you are letting the user plot or manipulate, and ask whether that's
one of the concepts for which we have (laboriously!) worked out a
specific term. Examples of acceptable, well-defined terms:

::

  Sheet
  Unit
  ConnectionField
  Projection
  ProjectionSheet
  CFSheet
  GeneratorSheet
  Image
  UnitView
  Event
  EventProcessor
  Activity

Examples of confusing, ambiguous terms to be avoided:

region
 (Sheets only sometimes correspond to neural regions like V1)
area
 (Same problem as Region)
map
 (Used in too many different senses)
layer
 (Biology and neural-network people use it very differently)
activation
 (Implies a specific stimulus, which is not always true)
receptive field
 (Only valid if plotted with reference to the external world)

As discussed elsewhere under `general principles of object-oriented
design`_, such undefined terms can be used in examples that bring in
concepts from the world outside of Topographica, but they are not
appropriate for variable or class names, documentation, or comments
making up the Topographica simulator itself.

.. _communication:

Communication: code, documentation, and comments
------------------------------------------------

Writing Python code is similar to writing anything else: to do it
well, you need to keep your intended audience in mind. There are
three different audiences for the different types of material in a
Python source file, and thus the guidelines for each category are
different:

Program code: Communicating with the computer and the human reader
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Program code tells the computer what to do, and needs to be written
so that it is obvious to a human being what the computer is being
told to do. This means using class, variable, function, and function
argument names that say exactly what they are, and favoring short,
clear bits of code rather than long, convoluted logic. For instance,
any function longer than about a screenful should be broken up into
more meaningful chunks that a human can understand.

Docstrings: Communicating with the user
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Every file, class, function, and Parameter should have an
appropriate docstring that says what that object does. The first
line of the docstring should be a brief summary that fits into 80
columns. If there are additional lines, there should be an
intervening blank line, followed by this more detailed discussion.
For functions, the summary line should use the imperative voice, as
in ``"""Return the sum of all arguments."""``. Such
documentation is collected automatically for the online help and for
the Reference manual, and must be written from the user's
perspective. I.e., the docstring must say how someone calling this
function, class, etc. can use it, rather than having details about
how it was implemented or its implementation history. These strings
are used to create the reference manual, and are thus extremely
important.

If you want to include structured text in your docstrings such as
italics, bold, bulleted or numbered lists, hyperlinks, etc., please
use the `ReStructuredText`_ format. That way the strings will be
interpreted correctly when we generate the reference manual.

Comments: Communicating with the human reader
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Comments (lines starting with #) are not processed by the computer,
and are not visible to the user. Thus comments should consist of
things that you want to be visible to someone reading the file to
really understand how something is implemented. Usually such a
person will either be (a) trying to fix a bug, or (b) trying to add
a new feature. Thus the comments should be focused on what is needed
for such readers. Please do not add redundant comments that simply
describe what each statement does; the code itself documents that
already. Redundant comments add more work for the reader, because
they are usually out of date, and not necessarily accurate. Instead,
please use comments for things that are not obvious, such as the
reason a particular approach was chosen, descriptions of things that
would be nice to add but haven't been done yet, high-level
explanations of a long section of low-level code, etc. Do not
include information relevant to the user; such things go into
docstrings.

To summarize, please use code, docstrings, and comments
appropriately. Any bit of information you add to a file should go
into the correct one of those three categories, and all files should
be written to be usable by all three of the different intended
audiences.

Parameters and bounds
---------------------

When writing user-visible classes, attributes that are meant to be
user-modifiable should be of class Parameter, so that they will be
visible in the various user interfaces.

Parameters should have the narrowest type and tightest bounds that
would be meaningful. For instance, a parameter that can be either
true or false should be of type param.Boolean, while one that can
only have a value from 0 to 0.5 should be of type param.Number with
a hard bound of 0 to 0.5. Using the right types and bounds greatly
simplifies life for the programmer, who can reason about the code
knowing the full allowable range of the parameter, and for the user,
who can tell what values make sense to use.

For Parameters that might show up in a GUI, soft bounds should also
be included wherever appropriate. These bounds set the range of
sliders, etc., and are a suggested range for the Parameter. If there
are hard bounds at both ends, soft bounds are not usually needed,
but can be useful if the reasonable range of the Parameter is much
smaller than the legal range.

Parameters should each be documented with an appropriate docstring
passed to the constructor. The documentation should be written from
the user perspective, not the programmer's, because it will appear
in various online and other forms of user documentation.

.. _units:

Numerical units in the user interface
-------------------------------------

All quantities visible to the user, such as GUI labels, parameters,
etc. must be in appropriate units that are independent of simulation
or implementation details. For instance, all coordinates and
subregions of Sheets must be in Sheet coordinates, not e.g. exposing
the row and column in the underlying matrix. Similarly, unit
specifiers should be in Sheet coordinates, selecting the nearest
appropriate unit, not row and column.

Appropriate units for most parameters can be determined by
considering the `continuous plane underlying the discrete units
forming the model sheet`_, and the `continuous logical timeline
behind the discrete timesteps in the model`_. Some parameters should
be expressed in terms of lengths in that plane, some in terms of
areas, and some in terms of volumes, rather than numbers of units,
etc. Others are expressed in terms of lengths of time, rather than
number of time steps. More information is available in `Bednar et
al, Neuroinformatics, 2004`_. There is usually only one correct
answer for how to specify a particular parameter, so please discuss
it with all, or at least with Jim, before picking a unit
arbitrarily.

.. _fileextensions:

User-level and simulator code file extensions
---------------------------------------------

By convention, we use a file extension of .py for the Python code
making up the simulator, in the ``topo/`` subdirectory. Models and
other user-level code such as scripts and examples should use an
extension of .ty, indicating that it is a file for use with
Topographica. (Many of the .py files are general purpose, and could
be used with any Python program, but the .ty files typically require
all or most of Topographica.)

All .ty files should use only the publicly available classes and
functions in ``topo/``, i.e. they should respect the
(as-yet-only-loosely-defined) Topographica API.

Typically, files organized around one main class will be named with
the lowercase version of that main class. E.g. sheet.py contains
class Sheet and some associated functions. Often files will include
not just one class but a superclass and several subclasses; such
files are named after the superclass. Other files contain a number
of thematically linked functions or classes, not necessarily a class
hierarchy; these should be named for the principle or theme that
relates them (as in arrayutil.py).

Accessing files and handling paths
----------------------------------

There are two points to consider when referring to files or paths on
the filesystem (which you would do, for instance, to open a file).
The first is how relative paths are processed, and the second is
differences in schemes for referring to paths on different operating
systems.

Relative paths
~~~~~~~~~~~~~~

While programming Topographica, you might wish to refer to a file
somewhere within the Topographica distribution. For instance, the
Topographica window icon is ``topo/tkgui/icons/topo.xbm``. This path
is relative to the topographica base path, so
``open('topo/tkgui/icons/topo.xbm')`` will successfully open the
file only when the topographica base path is the operating system's
current working directory (e.g. when topographica was started from
within its own directory, and the current working directory has not
subsequently been changed).

To avoid this problem, simply use the functions
``param.resolve_path()`` (to locate an existing file) or
``param.normalize_path()`` (to prepare a path for writing). The
example above would become
``open(resolve_path('topo/tkgui/icons/topo.xbm'))``; to create a
file for writing, one could write
``open(normalize_path('topo/new_file.txt'))``. See the documentation
for the two functions for more information.

Operating system differences
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Topographica is used on various platforms, and one of these is
Windows, which uses a different scheme for paths from the one used
by linux and OS X. For instance, the path ``topo/tkgui/`` is
``topo\tkgui\`` on Windows. To ensure that Topographica runs on all
platforms:

#. Do not attempt to perform operations such as ``open`` on 'raw'
   linux-style paths. Instead, use one of the functions
   ``param.normalize_path()`` or ``param.resolve_path()`` (as
   described above).
#. (For Windows developers) Never use Windows-style paths within the
   code: always specify paths in linux format. The above-mentioned
   functions correctly convert paths from linux to Windows, but do
   not handle the inverse conversion (in common with Python's own
   path-handling functions).

Python itself provides a number of functions for dealing with paths
in its `os.path`_ module. The functions above are based on those,
but facilitate the use of 'search paths', allowing users to specify
prefixes to search for relative paths.

.. _general info on writing in Python: #python
.. _Python-specific conventions: #conventions
.. _guidelines for naming: #naming
.. _comments, documentation: #communication
.. _parameters: #parameters-and-bounds
.. _numerical units: #units
.. _file extensions: #fileextensions
.. _docs.python.org: http://docs.python.org/
.. _Python for Lisp Programmers: http://www.norvig.com/python-lisp.html
.. _Python is not Java: http://dirtsimple.org/2004/12/python-is-not-java.html
.. _Python and Java Side-by-side comparison: http://www.ferg.org/projects/python_java_side-by-side.html
.. _Python coding conventions: http://www.python.org/peps/pep-0008.html
.. _revision control: revisioncontrol.html
.. _general principles of object-oriented design: ood.html
.. _ReStructuredText: http://docutils.sourceforge.net/docs/user/rst/quickstart.html
.. _continuous plane underlying the discrete units forming the model sheet: ../User_Manual/space.html
.. _continuous logical timeline behind the discrete timesteps in the model: ../User_Manual/time.html
.. _Bednar et al, Neuroinformatics, 2004: http://nn.cs.utexas.edu/keyword?bednar:neuroinformatics04
.. _os.path: http://docs.python.org/lib/module-os.path.html
