TOPOGRAPHICA'S WINDOWS SLAVES
=============================

This document links to images hosted on doozy in `/var/www/buildbot/screenshots`. Should this no longer be available, they should be stored elsewhere.

Since working under Windows is a pain for many developers in Topographica, I've provided detailed instructions (with screenshots) on how to go
through the setup process. Hopefully this should be enough for somebody with limited knowledge of (and liking for) Windows to set up a VM and a slave
without having to go through too much effort to learn Windows.

NB: the DreamSpark licenses are limited to 2 activations per download (check the EULA) so use them sparingly. Reuse the existing VMs and if
necessary, clone the existing VMs without reinstalling the OS.

DEPENDENCIES, ENVIRONMENT AND CONSIDERATIONS
--------------------------------------------

All Topographica dependencies and the Python libraries required for running a buildslave have their corresponding versions for Windows. Use those
to install. However, it is highly recommended to use a third-party bundle; the current VMs have `Python(x,y) <http://code.google.com/p/pythonxy/`_ 
installed. It is a very large package (about 500 MB) but includes all required packages for scientific computing with Python, plus - more
importantly - the `MinGW suite <http://www.mingw.org/>`_ to allow using a C/C++ compiler. Topographica does not explicitly require one but not using
it causes different/erratic behaviour on Windows.

When installing nose, Python must be explicitly configured to use the available C/C++ compiler. Otherwise, it tries to use files from Microsoft
Visual Studio 2008, so under some circumstances - if VS2008 is not available - `nosetests` will fail with a very obscure error. `See the second answer
here <http://stackoverflow.com/questions/2817869/error-unable-to-find-vcvarsall-bat>`_. Create a file called `distutils.cfg` specifying the correct
compiler, then reinstall nose.

Under Linux, the Topographica script is evoked by typing `./topographica` with the desired options. Under Windows, this doesn't work; instead, a
batch file called `topographica.bat` must be created and placed somewhere on the PATH (e.g. in `C:\Python27\Scripts`), containing the locations
of the Python executable and the Topographica script. On the Windows VMs, this looks like so::

   @C:\Python27\python.exe C:\buildslave\WinXP_alltests\build\topographica %*

See buildbot logs and the config file for more on how the commands differ.

Running commands under both Linux and Windows can cause problems due to certain differences in how Windows handles paths and strings, since most
commands in Topographica consist of accessing paths given as strings.

1. Backslashes
   
   Windows uses backslashes as a path delimiter. When used in a string, this may result in evoking a special escape sequence. Consider the following
   case, where the name of a tempfile is used as a string:
   
      >>> from tempfile import mkdtemp
      >>> f = mkdtemp()
      >>> print f
      c:\docume~1\boris\locals~1\temp\tmpthdn31
   
   The string is then processed by other code, but eventually breaks with the following message:
   
      IOError: [Errno 22] invalid mode ('w') or filename: 'c:\\docume~1\x08oris\\locals~1\temp\tmphujy15\\script_repr_test.ty'
   
   The `\x08oris` indicates that the `\b` was parsed as a backspace, which deleted one of the characters. To avoid this when using a filename
   string, replace any backslashes in it with double (escaped) backslashes to ensure that the string will be handled correctly (use
   `string.replace("\\","\\\\")`). This will always work since - if there are no backslashes in the file path, e.g. under Linux - the replace
   operation will simply do nothing. Alternatively, using `repr` on the string will preserve it.
   
2. Quote marks
   
   Windows does not treat single and double quotes equally. A string containing whitespace will only be parsed in its entirety if
   it is surrounded by double quotes. Because of this, running `topographica   -c 'from topo.tests.test_script import test_script’` on Windows
   will result in the following error::
   
      File "E:\PROG\topographica\topo\misc\commandline.py", line 381, in c_action
          exec value in __main__.__dict__
      File "<string>", line 1
          'from
              ^
      SyntaxError: EOL while scanning string literal
	  
   To avoid this, use double quotes around the string and escape any internal quotes. Similar behaviour can be observed if you type
   `'targets=["all"]'` when running Topographica's tests. This results in a malformed argument being passed to the command line processor, which
   dismisses it and runs the default set of tests, instead of "all" tests.
   
3. Platform-specific tools
   
   To help make Topographica platform-independent, do not use Linux-specific functions in scripts and commands. Use the corresponding Python
   tools and methods.

BUILDSLAVE SETUP
----------------

Setting up the buildslave and its dependencies is a straightforward process, and so is creating and starting the slave itself. There are no
modifications required to the generic, platform-independent process.

However, unlike on Linux, a daemon is not automatically created. When the buildslave process is started from the commandline, the latter stops receiving input and, upon terminating it, the buildslave process stops. In order to make the buildslave autostart, a `complicated procedure
must be carried out <http://trac.buildbot.net/wiki/RunningBuildbotOnWindows#Service>`_ . The Buildbot instruction is sufficiently detailed and works
correctly with no additional work required; nevertheless, I have described the process below, including screenshots for easier setup.

INSTALLING AND CONFIGURING WINDOWS
----------------------------------

After a blank VM is created and started for the first time (with the correct OS image mounted), the Windows setup wizard starts. It has several
introductory steps:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_01.png

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_02.png

The virtual hard drive must be formatted:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_03.png

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_04.png

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_05.png

Setup will then copy the files from the installation image to the virtual harddrive, then reboot. When the option to boot from the CD appears,
allow it to time out so that setup boots from the files on the hard drive. 

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_06.png

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_07.png

The main installation process begins, and takes about 20 to 30 minutes. It requires input on several occasions: setting formats and languages...

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_08.png

setting system information...

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_09.png

entering the product key (can be found in the DreamSpark account under Order History; ask James for details)...

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_10.png

further system information; the password for Buildbot's Windows VMs is the same as the one used for authentication in `master.cfg`:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_11.png

setting time, network and other settings...

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_12.png

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_13.png

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_14.png

The process for configuring the ready installation now begins:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_15.png

The machine should be kept up-to-date to match the production environment as closely as possible:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_16.png

Select the "local network" setting:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_17.png

You must activate Windows within 30 days of installation. Best to do it immediately as it happens behind the scenes. Registering with Microsoft is
optional, though, and you'll probably want to skip it:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_18.png

Enter the name of the main user (Buildbot). A password will be required for logging on as a service (see below) but that will be set later.

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_20.png

You're then presented with the XP user interface. Adjust automatic update settings by clicking on the Security Center icon at the bottom right. The
"Let me choose when to install updates" option provides the best flexibility for our purposes:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_22.png

To manually install the initial batch of updates, click the yellow icon at the bottom right that mentions updates:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_23.png

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_25.png

You may want to install a different browser and text editor (e.g. Notepad++) since the ones that come with Windows (Internet Explorer and Notepad)
are terrible.

To allow greater control over the taskbar area at the bottom of the screen, right-click it and select Properties. You can enable Quick Launch for
using a few quick-access icons next to the Start Menu, or ensure that all icons are shown in the notification area at the bottom right.

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_26.png

To allow proper control over files and folders, open My Computer or another folder and click on Tools > Folder Options. Under View, select
"Show hidden files and folders" and uncheck "Hide extensions for known file types" and "Hide protected operating system files".

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_27.png

To make changes to the PATH - and verify that everything has been set correctly after Python has been installed - right-click on My Computer from the
Start Menu, select Properties, and click "Environment Variables" under Advanced. Find Path and click on Edit:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_29.png

To setup the buildslave as a process, the buildbot account will need to have a password. From the Start menu, go to Control Panel > Users:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_30.png

Select the buildbot user and set a password. The account could also be set to not have administrator privileges:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_31.png

I'll illustrate the typical installation process under Windows (using a setup wizard) with Git. First, select the folder; default location is 
`C:\Program Files\Git` and it's a good idea to leave it there:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_32.png

Windows also creates folders for installed programs under the Start menu for quick access:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_33.png

Git provides a few options such as adding Git to the Windows commandline...

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_34.png

and for converting line endings from Windows-style (\r and \n) to Unix-style (\n only):

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_35.png

Install Zope.interface via easy_install because it does not provide a dedicated Windows installer:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_36.png

Then, install Twisted and Buildslave. Buildslave does not have an installer either - only a .zip distribution - but Windows comes with a basic
decompression tool out-of-the-box:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_37.png

The process for starting a slave is straightforward. Note how the console stops receiving input once the buildslave is running; if the console
is then closed, the buildslave process will die:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_38.png

Next, add the batch file required for running Topographica:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_39.png

Now begins the process for setting up the buildslave as a service. Start the command prompt as an administrator (Start > All Programs > 
Accessories > right-click Command Prompt and select Run As):

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_40.png

Start the Security Settings manager by typing `secpol.msc` at the administrator command prompt (don't close it!):

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_42.png

Right-click Local Policies > User Rights Assignments > Log on as a service, select Add User or Group and add the buildbot user:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_43.png

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_44.png

Back at the administrator command prompt, type the command issued by Buildot (see link above) to create the buildbot service:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_45.png

Go to Start > Control Panel and switch it to Classic View in order to access all tools in it without searching through different categories:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_46.png

In Administrative Tools > Services, right-click the Buildbot service and click Start. It will complain that the service stopped immediately; carry on.

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_48.png

Back at the administrator command prompt, start the Registry Editor by typing `regedit`. From there, go to `HKEY_LOCAL_MACHINE\SYSTEM\
CurrentControlSet\Services\`. Right-click Buildbot and edit its permissions, again adding the buildbot user and giving it full control:

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_50.png

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_51.png

Then, under Buildbot, right-click Parameters and add a new string value named `directories`, containing the path to our buildslave (`C:\buildslave`):

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/WindowsXP_52.png

This is it. You can now go back to Administrative Tools > Services and start the Buildbot service; it should succeed. Now, every time the VM is
powered on, the slave will come up as soon as the VM loads (even if the Buildbot user has not been logged on through the start screen; after all, it
now automatically logs on as the Buildbot service!).

The process for setting up Windows 7 is mostly identical; the only differences are that the installation process is more streamlined...

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/Windows7_01.png

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/Windows7_02.png

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/Windows7_03.png

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/Windows7_04.png

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/Windows7_05.png

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/Windows7_06.png

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/Windows7_07.png

.. image:: http://doozy.inf.ed.ac.uk/buildbot/screenshots/Windows7_08.png

The only substantial differences are that the folder options (where file extensions and hidden files are enabled) are located under Organize >
Folder and search options (in any folder window), and showing all Control Panel items is enabled by setting "View by:" from Category to Small icons.

The rest of the process is identical.