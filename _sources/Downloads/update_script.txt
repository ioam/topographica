*******************************************************
Updating your scripts for a new version of Topographica
*******************************************************

Topographica is used in current research, and as such it can change
quickly. Sometimes changes are made that render existing code
obsolete in some way. This usually manifests itself in two ways: the
first is that old snapshots can contain out-of-date code, and the
second in that old scripts can contain out-of-date code.

Old snapshots should be supported automatically; if you find you
have an old snapshot that will not load in a newer version of
Topographica, please let us know by `filing a bug report`_.

Old scripts can be supported by starting Topographica with legacy
support (i.e. by passing ``-l`` to Topographica at startup).
Usually, however, it is better simply to update the script, so that
Topographica does not need to be used with legacy support (which is
not as well tested as current code). For some versions, we provide a
utility to update scripts to run with newer versions, though it is
not guaranteed to convert every script properly, and isn't available
for all versions.

Upgrading from 0.9.5 to 0.9.6
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To update a script (e.g. ``/home/user/my_script.ty``) written for
0.9.4, first update to 0.9.5 as described below.

To update your script from 0.9.5, change to your topographica/
directory, e.g.:

::

    $ cd /home/user/topographica

and run the update utility:

::

    $ etc/update_095_to_096 /home/user/my_script.ty

This will produce a new script, ``/home/user/my_script.ty_0.9.6``,
which should run on the latest version of Topographica. Some of the
changes will require manual editing, e.g. to fix the numbers of
parentheses in some expression, but these should be relatively
simple to correct in the .ty file.

If you find the script still will not run, please `file a bug
report`_ so that we can fix the problem. (To work with your original
script immediately, you can instead try running Topographica with
legacy support enabled, as described earlier.)

Upgrading from 0.9.4 to 0.9.5
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To update a script (e.g. ``/home/user/my_script.ty``) written for
0.9.4, first change to your topographica/ directory, e.g.:

::

    $ cd /home/user/topographica

Then run the update utility:

::

    $ etc/update_094_to_095 /home/user/my_script.ty

This will produce a new script, ``/home/user/my_script.ty_0.9.5``,
which should run on the version 0.9.5 of Topographica.

Upgrading from a version prior to 0.9.4
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently, we do not explicitly support code written for versions of
Topographica prior to 0.9.4. Depending on the age of the code,
though, such support is possible in theory. Please let us know if
you have an old script (or snapshot) that you need to use in a
modern version of Topographica.

.. _filing a bug report: ../Forums/problems.html
.. _file a bug report: ../Forums/problems.html
