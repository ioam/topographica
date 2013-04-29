VIRTUAL MACHINE MANAGEMENT
==========================

This document links to images hosted on doozy in `/var/www/buildbot/screenshots`. Should this no longer be available, they should be stored elsewhere.

CREATING A VM
-------------

VirtualBox is the virtualisation software of choice in Topographica. While there are different alternatives, VirtualBox is the best option overall;
it is free, has a great variety of supported guest operating systems, works reliably, and offers great power and flexibility. While creating a
virtual machine in VirtualBox is relatively straightforward, there are several considerations to be made during the process. This section gives
step-by-step instructions.

On the VirtualBox start screen, press New and then Next to start the New Virtual Machine Wizard. If you want the VM in a specific location, you may
need to change the default directory in the VirtualBox settings because I could not find an option to change the destination through the wizard. It
only gives the option to specify the location of the virtual harddrive.

Select the name of the VM and the OS type:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/virtualbox_03.png

Obtaining licenses for proprietary OSs can be tricky; for Windows, this has been solved by obtaining free copies via the DreamSpark program, of which
the School of Informatics is a member (ask James for details). These have been downloaded and stored - along with all files for the currently running
Buildbot virtual machines - in `/scratch2/buildslaveVMs` on doozy.

For Mac, the VM needs to be running on a physical Apple machine. Ask James for details and see `Work_on_CI.rst`.

Next, set the memory size that the new virtual machine can use. VirtualBox determines the default value based on the OS type, but the recommended
usually seems low:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/virtualbox_04.png

For virtual machines that will be used as buildbot slaves, use separate harddrives:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/virtualbox_05.png

Select VDI as the most common type, suited for most purposes, and make it dynamically allocated. Its size will converge with usage until it reaches
a "stable" size. VirtualBox will still require a maximum size of the virtual disk, again based on the OS type. For Windows XP, the default value is
10 GB and for Windows 7, 20 GB. For the purposes of running a Buildbot slave, these values will be sufficient:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/virtualbox_08.png

Confirm the settings and location for the new disk image:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/virtualbox_09.png

A progress bar will appear that shows the creation of the .vdi file. Next, confirm the final settings for the virtual machine:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/virtualbox_10.png

After the VM is created, it will appear in the VirtualBox list. It is not complete, though; start it to launch the First Run Wizard and actually
install the guest operating system:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/virtualbox_11.png

Select the location of the OS installation image:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/virtualbox_13.png

Once that happens, the guest OS then takes over. The rest of the setup process is dependant on whatever wizards and commands the guest OS requires
for installation; see `Setup_Windows_slave.rst` for details on Windows installation.

When the VM is running, additional options can be accessed from the VirtualBox window in which it is running. For example, new disk images can be
added to the VM's virtual CD/DVD drive via the Devices menu.

The VM should always be stopped gracefully since an improper shutdown will have the same data mangling effect on the virtual harddrive as a power
outage would on a physical machine.

VM AS A SLAVE: TREATED AS A SEPARATE HOST
-----------------------------------------

For a VirtualBox VM, there are `different ways for setting up network connection modes <http://www.virtualbox.org/manual/ch06.html>`_. The default is
NAT, and - for the purposes of connecting a VM as a slave to buildbot - it works just fine.

As explained in the buildbot README, the buildmaster configuration does not distinguish between remote slaves, local slaves, and virtual machine
slaves. In all cases, the slave and the master will connect via TCP as if they were separate hosts. This means that adding a VM slave to the buildbot
setup is as simple as defining it in the master configuration file and creating a buildslave process inside the VM.

To automate the process (instead of having to manually start the VM and the slave process every time), the following needs to be done:

1. The buildslave process must be configured to start automatically when the VM is powered on. In this way, Buildbot's Waterfall page will show it as
   "offline" when the VM is off and "online" when the VM is on. Under Ubuntu, a buildslave daemon is created automatically but uner Windows, special
   steps must be taken to make the buildslave autostart. See `Setup_Windows_slave.rst`.
   
2. The VMs must be scheduled (e.g. via `crontab`) to come up and down at scheduled times since they would consume too much resources if they were up
   all the time. See buildbot's `master.cfg` for the current builder schedule; the VMs have been crontabbed to start 5 minutes before the scheduled
   build to ensure that the guest OS has enough time to become ready before the build starts, otherwise the slave won't be online in buildbot. They
   are then scheduled to power off 10 to 15 minutes after the build would be done::
   
      55 3 * * * VBoxHeadless --startvm "WinXPvm"
      30 4 * * * VBoxManage controlvm "WinXPvm" poweroff
      55 4 * * * VBoxHeadless --startvm "Win7vm"
      30 5 * * * VBoxManage controlvm "Win7vm" poweroff
   
See a cron manual and `this discussion <http://superuser.com/questions/170866/how-to-run-a-cron-job-as-a-specific-user>`_ .

The above commands show the command-line mechanisms provided by VirtualBox for controlling virtual machines without a GUI and/or remotely.

`VBoxManage <http://www.virtualbox.org/manual/ch08.html>`_ enables a plethora of options for controlling VMs from the commandline, while
`VBoxHeadless <http://www.virtualbox.org/manual/ch07.html#vboxheadless>`_ allows to start a VM without the GUI running. Since the VM slaves are
running overnight with nobody observing them, there is no need for a GUI to come up. It will only consume resources unnecessarily.

When these are manually used from a terminal, typing `VBoxHeadless --startvm vmname` will occupy the current terminal instance and prevent it from
further use while the VM is running. The VM must be stopped from another terminal instance, which will free up the first one.

If the VirtualBox main window is up, it will list the VM as "Running" and show a preview of its screen, but will not launch a GUI. Using
`VBoxManage list <http://www.virtualbox.org/manual/ch08.html#vboxmanage-list>`_ is also a useful way to see available and running VMs.

VM AS A SLAVE: OUTSIDE CONTROL
------------------------------

Much greater flexibility would be provided if the Buildbot slave were able to itself control the VM, which is made possible thanks to the
`VBoxManage guestcontrol` command, which allows the host OS to excecute scripts and programs inside the
guest OS. `See the manual <http://www.virtualbox.org/manual/ch08.html#vboxmanage-guestcontrol>`_.

This approach would be useful to, for example, create slaves that serve as "running recipes" for making Topographica work on different platforms.
The slave would execute roughly the following sequence of steps:

1. Clone a blank VM

2. Power on the new clone

3. Execute script for installing Topographica dependencies

4. Install Topographica via e.g. `pip`

5. Run the tests

6. Power off the VM

7. Delete the clone VM

Thus, the buildbot does not treat the VM as a separate host but rather as an actual VM, controlled locally by the buildslave. This has proven very
difficult to achieve, and has been left as future work. See `Work_on_CI.rst`.