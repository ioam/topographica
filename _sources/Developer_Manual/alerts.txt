******
Alerts
******

As a convention, problematic areas of the code have been marked with
comments containing the text ``ALERT`` or ``ERRORALERT``, usually
prefixed with the initials of the person who wrote the alert. These
comments help clarify how the code should look when it is fully
polished, and act as our to-do list. They also help prevent poor
programming style from being propagated to other parts of the code
before we have a chance to correct it.

Anyone who sees a problem in the code but is unable for any reason
to fix the problem should add an alert for it. The alert must
specifically describe what the problem is and how it could be
corrected (if known). If the problem is serious, especially if it
may affect any results seen by the users, it should be labeled an
ERRORALERT. Less serious issues, such as those primarily affecting
code readability, future maintainability, and generality, should be
labeled an ALERT.

All Topographica developers are responsible for fixing alerts. No
file in Topographica is owned by any single developer, and no
permission is needed from anyone to fix the problem. Anyone who
reads an alert should, at the minimum, add a comment saying how the
ALERT could be fixed (if they have any idea), and ideally should fix
the problem.

As soon as the problem is gone, the ALERT comment should be removed
entirely from the code.

If any Topographica developer ever runs out of tasks, a good thing
to do is to search the Topographica directory for ``ALERT``, and
then start fixing all those that seem fixable, starting with the
easiest.

