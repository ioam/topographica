***********
Refactoring
***********

(From `refactoring.com`_):

    Refactoring is a disciplined technique for restructuring an
    existing body of code, altering its internal structure without
    changing its external behavior. Its heart is a series of small
    behavior preserving transformations. Each transformation (called
    a 'refactoring') does little, but a sequence of transformations
    can produce a significant restructuring. Since each refactoring
    is small, it's less likely to go wrong. The system is also kept
    fully working after each small refactoring, reducing the chances
    that a system can get seriously broken during the restructuring.

We rely heavily on refactoring in Topographica to ensure that the
design is always kept up to date and suitable for future scientific
advances.

Bad smells
==========

Fowler 1999, `Refactoring: Improving the Design of Existing Code`_,
pp. 417-418) contains a nice list of "bad smells" in code that drive
a developer to want or need to refactor it:

-  Duplicated Code
-  Long Method
-  Large Class
-  Long Parameter List
-  Divergent Change
-  Shotgun Surgery
-  Feature Envy
-  Data Clumps
-  Primitive Obsession
-  Switch Statements
-  Parallel Inheritance Hierarchies
-  Lazy Class
-  Speculative Generality
-  Temporary Field
-  Message Chains
-  Middle Man
-  Inappropriate Intimacy
-  Alternative Classes with Different Interfaces
-  Incomplete Library Class
-  Data Class
-  Refused Bequest
-  Comments

More information is available from the `bad smells`_ site.

Refactoring/testing tips
========================

This list of "soundbites" again comes from Fowler 1999,
`Refactoring: Improving the Design of Existing Code`_, pp. 417-418).
It seems to apply reasonably well to this project, particularly the
parts about testing.

-  Page 7: When you find you have to add a feature to a program, and
   the program's code is not structured in a convenient way to add
   the feature, first refactor the program to make it easy to add
   the feature, then add the feature.
-  Page 8: Before you start refactoring, check that you have a solid
   suite of tests. These tests must be self-checking.
-  Page 13: Refactoring changes the programs in small steps. If you
   make a mistake, it is easy to find the bug.
-  Page 15: Any fool can write code that a computer can understand.
   Good programmers write code that humans can understand.
-  Page 53: Refactoring (noun): a change made to the internal
   structure of software to make it easier to understand and cheaper
   to modify without changing the observable behavior of the
   software.
-  Page 43: Refactor (verb): to restructure software by applying a
   series of refactorings without changing the observable behavior
   of the software.
-  Page 58: Three strikes and you refactor.
-  Page 65: Don't publish interfaces prematurely. Modify your code
   ownership policies to smooth refactoring.
-  Page 88: When you feel the need to write a comment, first try to
   refactor the code so that any comment becomes superfluous.
-  Page 90: Make sure all tests are fully automatic and that they
   check their own results.
-  Page 90: A suite of tests is a powerful bug detector that
   decapitates the time it takes to find bugs.
-  Page 94: Run your tests frequently. Localize tests whenever you
   compile --- every test at least every day.
-  Page 97: When you get a bug report, start by writing a unit test
   that exposes the bug.
-  Page 98: It is better to write and run incomplete tests than not
   to run complete tests.
-  Page 99: Think of the boundary conditions under which things
   might go wrong and concentrate your tests there.
-  Page 100: Don't forget to test that exceptions are raised when
   things are expected to go wrong.
-  Page 101: Don't let the fear that testing can't catch all bugs
   stop you from writing the tests that will catch most bugs.

.. _refactoring.com: http://www.refactoring.com/
.. _`Refactoring: Improving the Design of Existing Code`: http://www.amazon.co.uk/exec/obidos/ASIN/0201485672/
.. _bad smells: http://sis36.berkeley.edu/projects/streek/agile/bad-smells-in-code.html
