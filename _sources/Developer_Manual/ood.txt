**********************
Object-oriented design
**********************

The design of Topographica is in terms of hierarchical sets of
classes of objects (plus a few collections of unrelated but useful
tidbits). Most new code will take the form of a new class within an
existing hierarchy, or a new method within an existing class.

When adding a new method, or changing the semantics of an old one,
it is absolutely crucial to think about where in the hierarchy the
new operation is appropriate. Specifically, an operation should be
added as high in the class hierarchy as is valid (for generality),
and no higher (for correctness).

For instance, consider a hierarchy containing geometric objects for
a drawing program: ProgramObject, Shape, Rectangle. If you realize
when working on Rectangle that it needs a resize() method, then
please stop and think before adding the operation directly to
Rectangle. In this case, any Shape can be resized, so resize()
should be a method of Shape. It may not actually be possible to
implement resize() for all shapes with the same program code, and in
that case Shape.resize() would be written as an abstract method
(i.e., would simply return NotImplementedError). The resize()
function would then be implemented for each particular shape. But
the semantics of resize() should be clear for all conceivable
Shapes, and thus providing the operation should be done at the Shape
level.

Conversely, it is not appropriate to add resize() to all
ProgramObjects, because there are surely objects in the program that
are not meaningful to resize. Thus it would not normally be
appropriate to have a ProgramObject.resize(). If such a method is
required to solve a particular design problem, it would have to be
documented heavily to ensure that the user only calls it on a Shape.
Such complexity should be avoided whenever possible, and so be sure
not to add the code at a higher level than appropriate.

In any case, when deciding where to add the code, be sure to think
about the operation in the most general terms for which it makes
sense. That is, when solving a problem, try interpret it broadly and
solve it at the highest level possible, so that it applies to the
largest appropriate class of objects. For example, an operation
change\_rectangle\_width() is clearly not applicable to all Shapes,
yet if the idea is reinterpreted in appropriately general terms,
i.e. resize(), it is clear that the method belongs in the Shape
superclass. The method then becomes a requirement for every subclass
of Shape -- henceforth every variety of Shape must be able to be
resize()d, and anything that cannot be resize()d cannot be a Shape,
by definition.

It is also extremely important to think about the appropriate name
for an operation or class, so that it is clear how generally or
specifically it can be applied. Once the name is decided, all
comments and documentation must match that level of generality. That
is, it would be quite inappropriate to use variable names like
"rect\_width" in the arguments to Shape.resize(), or to have
Shape.\_\_doc\_\_="Change the length and width of the rectangle",
because only a few shapes are also Rectangles. Of course, it is
perfectly ok to give an example in terms of a rectangle: "Change the
size of the given object. For a Rectangle, this will adjust the
length and width." But only in examples are such specific subclasses
allowed to be mentioned, because the operation itself applies to a
much larger class of objects.

One way to make sure that you are using appropriate language is to
look at the imports list at the top of the file. If the imports list
does not include Rectangle, Circle, etc., it is inappropriate ever
to write documentation or comments or use a variable, method, or
class name that assumes that there is anything like a Rectangle or
Circle in the universe. The fact that the file does not import those
other classes is a declaration that the code in the file may be used
whether or not such other classes exist. Thus the contents of the
file cannot depend on such external code, even implicitly. Even some
of the imported items may not be ok to use in names, comments, or
documentation for a particular class, if that particular class is
more widely applicable than the file as a whole. We need to use
every means available to convey to the reader just how generally
this code can be used, and exactly the sorts of conditions for which
it is applicable.

Such naming and documentation issues may seem trivial, but please
try to imagine that you are another programmer or user reading the
file. If the documentation and variable names suggest that an
operation is limited to some specific case, only an extremely
motivated and perceptive reader will be able to deduce that the
operation is actually applicable to the specific problem that the
reader is trying to solve. What the reader wants to do is
undoubtedly different from the specific case the programmer
originally had in mind, and only if everything is written at the
appropriate level of generality will it be clear whether the code
covers the intended usage or not.

Note that there can be serious consequences for inappropriately
describing the level of generality. If code is described in greater
generality than is appropriate, users and other programmers will
misuse the object, leading to bugs and other errors. If code is
described with too little generality, the user will be needlessly
constrained in what he or she can do. Often in the latter cases,
another programmer will write another function that does the same
thing as the existing one, but for another related case. This
happens because it was not clear that the existing function was
sufficient. Such extra functions make everyone's lives more
difficult, because they make the software much harder to maintain,
understand, and use.

To summarize: when adding new code, think (and discuss!) where it
should go and what level of generality is appropriate. If it is
clear how to solve the problem for all time, please do so!
Otherwise, solve it for the largest class whose solution *is* clear.
Once an appropriate level has been chosen, make sure all
documentation, comments, and names match that level, pretending that
no lower levels exist except as possible examples.

For further info from a scholarly perspective, you may want to read
`Producing reusable object-oriented components`_.

.. _Producing reusable object-oriented components: http://doi.acm.org/10.1145/379377.375236
