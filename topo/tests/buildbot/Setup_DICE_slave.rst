TOPOGRAPHICA'S DICE SLAVE
=========================

The DICE slave for Topographica is `mckellar.inf.ed.ac.uk`. It has a dummy local account (i.e. not valid for any other DICE machine) with no superuser
access that allows running Buildbot's daemons and performing basic user-wide setup tasks such as crontab, local dependency installations and PATH
management. The account is called `topo-builbot`; to log on to it, perform the following:

1. Log on to the Informatics network (or a specific DICE machine) with your DICE login.

2. Type `ssh mckellar`::

   [cameleopard]s0833773: ssh mckellar
   Last login: Mon Mar 18 01:24:41 2013 from shackleton.inf.ed.ac.uk
   [mckellar]s0833773: 

3. You're now logged on to `mckellar` with your DICE login, so now type `nsu topo-buildbot`::

   [mckellar]s0833773: nsu topo-buildbot
   [mckellar]topo-buildbot:

4. You're still in your own home directory on mckellar, so `cd` to `topo-buildbot`'s home:

   [mckellar]topo-buildbot: pwd
   /afs/inf.ed.ac.uk/user/s08/s0833773
   [mckellar]topo-buildbot: cd ~
   [mckellar]topo-buildbot: pwd
   /disk/scratch/topo-buildbot
   
If mckellar goes away for some reason, contact Informatics Support to get a new dummy user setup on a different DICE machine. Ideally, it should have
the same configuration as mckellar's.

The main purpose of running a DICE slave is to test Topographica under the default DICE environment; for this reason, do not use e.g. a `virtualenv`
but instead perform local dependency installations for `topo-buildbot`. Virtually all of the dependencies for Topographica (including nose) and 
buildslave (Twisted) are already available on DICE, so will not have to be installed separately. During installation, however, `buildslave` will
fetch newer versions of Twisted and Zope.Interface. These have no influence over how Topographica works and are only needed for the buildslave,
though, so the DICE environment remains "clean" for Topographica.

To install the buildslave locally for the `topo-buildbot` user, do roughly the following::

   [mckellar]topo-buildbot: wget http://buildbot.googlecode.com/files/buildbot-slave-0.8.7p1.tar.gz
   [mckellar]topo-buildbot: tar -zxvf buildbot-slave-0.8.7p1.tar.gz
   [mckellar]topo-buildbot: cd buildbot-slave-0.8.7p1/
   [mckellar]topo-buildbot: python setup.py build
   [mckellar]topo-buildbot: python setup.py install --user

This installs Buildslave v.0.8.7p1, Twisted v12.3.0 and Zope.Interface v.4.0.3 into `/disk/scratch/topo-buildbot/.local/lib/python2.6/site-packages`.

To make the `buildslave` executable available for use upon login (i.e. modify the PATH without making system-wide changes), do the following::

   [mckellar]topo-buildbot: cd ~
   [mckellar]topo-buildbot: nano .bashrc

and add the following lines to export the `.local` directory containing the user-specific installations::

   # User specific aliases and functions
   PATH="${PATH}:/disk/scratch/topo-buildbot/.local/bin/"
   export PATH

Starting the actual slave requires exactly two commands; choose a `basedir` and create the slave inside::

   [mckellar]topo-buildbot: mkdir buildslave
   [mckellar]topo-buildbot: cd buildslave/
   [mckellar]topo-buildbot: pwd
   /disk/scratch/topo-buildbot/buildslave
   [mckellar]topo-buildbot: buildslave create-slave . doozy.inf.ed.ac.uk:9989 mckellar PASSWD
   
then start it::  
  
   [mckellar]topo-buildbot: buildslave start .

To start the slave automatically upon reboot, use crontab::

   `@reboot /disk/scratch/topo-buildbot/.local/bin/buildslave start /disk/scratch/topo-buildbot/buildslave
   
Of course, the slave will first need to be defined in the master's config file, and the master will need to be restarted.