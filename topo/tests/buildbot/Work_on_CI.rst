FUTURE CI WORK ON TOPOGRAPHICA
==============================

ISSUES WITH DOOZY
-----------------

There are hard-to-identify performance issues with doozy, narrowed down most likely to issues with the harddrive controller. Because of this, it
was nearly impossible to use VMs until an external USB harddrive was obtained, which works well. It may be necessary to investigate this further.

PYTHON LIBRARIES
----------------

Obtain the next version of Buildbot (newer than 0.8.7p1) as soon as it comes out, and update the master. I've modified one of the library files
(`/usr/local/lib/Python2.7/dist-packages/buildbot/steps/slave.py`) to include the `CopyDirectory` method which will be made available at the next
release; I copied it from `Buildbot's GitHub repository <https://github.com/buildbot/buildbot/blob/master/master/buildbot/steps/slave.py>`_ . Restore the library to a default state after the next release comes out.

When upgrading the master, SQL Alchemy 0.8.0 caused problems::

   $ buildbot upgrade-master .
   Traceback (most recent call last):
       ...
   File "/usr/local/lib/python2.7/dist-packages/migrate/versioning/schema.py", line 10, in <module>
       from sqlalchemy import exceptions as sa_exceptions
   ImportError: cannot import name exceptions

I then manually installed version 0.7.6. No useful information came up in searches; this may be resolved in later versions, or may have to do with
how `pip` handles versions and library locations.

A general problem in the debate `apt-get` vs `pip` or other Python installation tools is that the latter may confuse the Ubuntu system package
manager. Usually, packages installed by `apt-get` go to `/usr/lib/` while ones installed by other means go to `/usr/local/lib/`. This may cause
confusion under certain circumstances, and in general it is recommended to use `apt-get`; however, it usually has out-of-date versions so if a newer
version is required, a tradeoff will be necessary. Generally, the system will almost never encounter problems in finding the correct location.

BUILDBOT
--------

Restore performance tracking, using files in the `buildbot/unused` directory in the repo. Ask James for details.

EXTERNAL CI
-----------

Get in touch with Yury V. Zaytsev ‎[zaytsev@fz-juelich.de]‎ for information and logon details for Topographica's Jenkins setup at the Juelich Research
Centre (ask James for details). Get to grips with Jenkins, find out why builds are failing, and fix them. Make the most out of the Jenkins setup.

Possibly research different options for externally hosted CI setups to complement (but not replace) the local buildbot. Externally hosted CI is
still a fresh idea and new companies emerge (but also close down) often. A useful option may appear in the future.

VIRTUAL MACHINE SLAVES
----------------------

1. Figure out how to install Topographica on a Mac (the process is different, depending on the OS X version and what's included in it). Once this is
   done, create a Mac slave. It must be running in a virtual machine (to make sure that it's as close to the commercially available environment as
   possible, and not a specific machine's environment that may change), which must itself be running on a physical Mac due to restrictions imposed by
   Apple. Ask James for details.

2. Figure out how to set up a buildslave and run Topographica under 64-bit Windows. A 1-year academic license has been obtained for 64-bit Windows EPD
   (ask James for details), and that supposedly includes a C compiler (64-bit MinGW?), but I was unable to get consistent, reliably working
   performance from other required packages that do not yet have a separate 64-bit version. E.g. the 32-bit Git version supposedly works under
   64-bit as well, but Windows was reporting problems with it. Some Python dependencies (e.g. nose and buildslave itself) seem to have that problem
   as well. The authors of some of these seem to intend to release 64-bit versions in the future but that is not certain.

3. Figure out how to make a buildslave control a VM from the outside. I attempted this with a Ubuntu 12.04 VM to create a "running recipe" for
   installing under Ubuntu by cloning a blank VM (with updates), installing dependencies and Topographica, and running the tests. However, it is
   incredibly difficult to run something on the guest OS from within the host OS. `The mechanism for this is very complicated <http://www.virtualbox.org/manual/ch08.html#vboxmanage-guestcontrol>`_. For example, to simply get the contents of the current working directory,
   one must do the following::
   
      VBoxManage --nologo guestcontrol "My VM" execute --image "/bin/ls"
                --username foo --passwordfile bar.txt --wait-exit --wait-stdout
   
   Only executable scripts and binaries can be run by specifying the absolute path to them. `--username` and `--password` must always be specified
   to run the selected script as a given user. `--wait-exit` must be specified in order to have the guest process report its exit code to the host,
   while `--wait-stdout` and `--wait-stderr` must be included to get output from the process.

   The latter makes it very difficult to get output from a script within a script. Since I'm not well versed at Linux scripting, I could not figure
   out how to do this. There are multiple difficulties when running tests on a library installation of Topographica obtained via `pip` and the only
   way I could do that involved `cd`ing to `/usr/local/lib/python2.7/dist-packages` in order to then evoke `topo/tests/runtests.py`. However, I was
   then unable to first do `cd /path/to/dir` (which requires the `#!/bin/sh` `shebang <http://en.wikipedia.org/wiki/Shebang_%28Unix%29>`_ ), then
   run the Topographica script (it uses a different shebang, `#!/usr/bin/env python`, and I could not get it to work), then channel the output from
   the nested script to the outer script, then send that over to whatever ran `VBoxManage guestcontrol`.
   
   Overall, this approach provides great flexibility, but it is arguable whether the benefits outweigh the significant configuration overhead it
   requires. I did not have enough time for it, so if it is deemed of importance in the future, it can be attempted again.