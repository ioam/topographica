BUILDBOT DETAILS
================

NOTES AND GUIDELINES
--------------------

Use this document only as a quick reference. Any detailed explanation of concepts and techniques should be obtained from the Buildbot Manual
(`here's a link as one page for quick searching <http://buildbot.net/buildbot/docs/0.8.7p1/full.html>`_ ) which is incredibly detailed and helpful.
It can be, however, quite difficult to find something specific, so throughout this document I've provided links to relevant sections.

The current version of doozy's buildmaster is 0.8.7p1. When consulting the manual, check the URL to see what you're reading as there are some
changes and mismatches between versions. The "latest" version of the manual is for the yet-to-be-released version in the Buildbot repository so
anything documented there will not be in the code yet.

When tweaking the buildbot configuration, please do NOT use custom methods in the config file. That file uses a single dictionary data structure
(called `c[]`) which contains all information needed by the buildbot in the form of (entity, definition) pairs. Buildbot parses this file upon
startup and creates the required configuration. Use buildbot's dictionary directly::

   c['slaves'] = [ BuildSlave("slave1","pass1"),
                   BuildSlave("slave2","pass2"),
				   .....
	 
Do not create methods that obfuscate this unnecessarily::

   def add_slave(name, password):
       c['slaves'].append(BuildSlave(name, password))
	   
   add_slave("slave1", "passwd1")
   
Also, do NOT add unnecessary gimmicks to avoid duplicating a few lines of code::

   for n,p in [("slave1","pass1"),
           ("slave2","pass2"),
           ("slave3","pass3"),
           ("slave4","pass4")
           ]:
   add_slave(n,p)
	
Master.cfg is not a script or program that will ever be executed, but rather a simple configuration file accessed exactly once when Buildbot
(re)starts. Therefore, when making any changes, go against your programmer instincts that tell you to e.g. not copy and paste a block of code with
minor modifications. Readability and maintainability should be the most important guideline; think of master.cfg as something written in
`description language <http://en.wikipedia.org/wiki/Specification_language>`_ .

The main purpose of this document is to explain the concepts behind Buildbot and provide relevant links to more detailed documentation. It does not
discuss the configuration details of Topographica's buildbot; these can be found in comments throughout the `master.cfg` file. Here, I've only
given a high-level overview of our buildbot's architecture. To properly understand the configuration, it would be best to read `master.cfg` and the
`README` side-by-side and compare concepts to implementation.

CONCEPTS AND OVERVIEW
---------------------

`Buildbot <http://buildbot.net/buildbot/docs/0.8.7p1/manual/introduction.html>`_ is a `continuous integration <http://en.wikipedia.org/wiki/Continuous_integration>`_ tool used in Topographica
to automatically monitor the build status and rerun regression tests.

At the highest level, the buildbot consists of one master and multiple slaves. Put briefly, the master issues the commands and the slaves execute
them, reporting the results back to the master.

Many possible configurations are possible; the slaves and the master can be on separate machines, share the same machine, or be part of a more
complex setup involving e.g. slaves on both physical and virtual machines. In all cases, the master and the slaves communicate via TCP, and the
master's configuration is completely oblivious to the slave's actual location and whether it's a physical or a virtual machine. They connect the
same way in all cases. `More information here <http://buildbot.net/buildbot/docs/0.8.7p1/manual/introduction.html#system-architecture>`_ .

The configuration of `the master <http://buildbot.net/buildbot/docs/0.8.7p1/manual/introduction.html#buildmaster-architecture>`_ governs what, when,
how and where to run. It contains the definitions of multiple "builders", each containing a list of tasks ("buildsteps") to be performed. These
builders are attached to "schedulers", which determine which series of tasks are performed when. The builders are then assigned to slaves; each
slave can run multiple builders and each builder can be reused across different slaves.

The most basic builder for Topographica would perform these steps:

1) checkout repository from GitHub
2) run unit tests
3) run system tests
4) run speed tests

(For a proper description of what tests are there, see the README files for the topo.tests and the topo.tests.unit packages.)

Should any of these steps fail, the build will be shown as a failure and a notification e-mail will be sent to the designated mailing list. The
build health, however, should be collective responsibility; everyone should monitor buildbot and the current build status, especially after committing
new changes. Problems and errors ("broken builds") should be fixed as fast as possible.

TOPOGRAPHICA'S BUILDBOT
-----------------------

Here is the current structure of buildbot:

- **MASTER: doozy**

- **MAIN SLAVE: doozy**
  - builder "full build": builds all external Python dependencies and runs the full test suite
  - builder "coverage": runs unit tests with coverage enabled, produces HTML reports and makes them available on the buildbot website
  - builder "docs": runs unit tests and compiles documentation
  - builder "backups": stores a daily copy of the GitHub repository
  
- **DICE SLAVE: mckellar** (see `Slaves_DICE.rst`)
  - basic builder: checkout, unit tests, system tests, speed tests
  
- **WINDOWS XP SLAVE: virtual machine on doozy** (see `Slaves_Windows.rst` and `VirtualBox_setup.rst`)
  - basic builder
  
- **WINDOWS 7 SLAVE: virtual machine on doozy**
  - basic builder

In general, the basic builder would be sufficient for basic testing under other platforms. Other tasks (such as building external dependencies or
producing coverage reports) are unlikely to be necessary on slaves other than the doozy slave.

On doozy, there's a dedicated user called buildbot with HOME directory in `/var/lib/` ::

   $ echo ~buildbot
   /var/lib/buildbot

The master lives in `buildbot/masters/`, and the slave in `buildbot/slaves/`. Inside those directories, there is a separate directory for each
builder (e.g. `buildbot/masters/coverage/` and `buildbot/slaves/coverage/`). The one under `masters` contains each build's logfiles (displayed on the
webpage), and the one under slaves contains files related to the actual build (e.g. the repository source files). This illustrates how buildbot works;
the master issues commands and retains logs, and the slaves do the work required by the build.

Further, Topographica saves various files to the user's HOME directory when run. For example, when the tests are run, simulation datafiles are saved
there. This means that a `Topographica` directory should appear in `/var/lib/buildbot/`; however, each builder that runs tests has been designated a
separate "home" directory in order to avoid potential conflicts with generated files. This may be unnecessary; currently, there are no actual files
being saved there.

Doozy's buildbot directory layout therefore looks like this::

   /var/lib/buildbot/
                     masters/
                             backups/
                             coverage/
                             DICE_alltests/
                             docs/
                             full_build/
                             gitpoller-work/
                             templates/
                             Win7_32_alltests/
                             WinXP_alltests/
                     slaves/
                             backups/
                                     build/ #most current version of the repo
                                     YYYY-MM-DD/ #backups of the repo at that date
                             coverage/
                                     build/
                                           htmlcov/ #HTML reports generated by the unit tests; not checked in
                                           rest-of-topographica's-dirs/
                             docs/
                                  build/
                             full_build/
                                        build/
                                        external/ #cached tarballs of Topographica's Python dependencies
                             info/ #contains information files for buildbot
							 
Regarding `masters/gitpoller-work/` and `masters/templates/`: the former contains files generated by the part of buildbot that connects to the
Git repository, while the latter is the place where `Jinja2 <http://jinja.pocoo.org/docs/>`_ templates should be put if it is necessary to override
Buildbot's default templates with customised ones. For more information, see "Web Interface" below.

Buildbot requires a further directory called `public_html` for files related to displaying the web interface. This normally lives under
`masters/public_html`, but instead has been set to `/var/www/buildbot/` because that's the Document Root of doozy's Apache server. Any files to be
displayed on the webpage require `o=rx` permissions (see info on `chmod <http://en.wikipedia.org/wiki/Chmod>`_ ) so if `public_html` was kept at its
default location, `o=rx` permissions would need to be specified all the way down on `/var/lib/`, `/var/lib/buildbot/`, `/var/lib/buildbot/masters/`.
This is a potential security issue so it is better to place the publicly accessible files in the default Apache location that has no sensitive or
system-critical files.

Virtually all of Buildbot's settings are specified in its main configuration file, `/var/lib/buildbot/masters/master.cfg`. Further sections
dissect it in great depth.

STARTING A BUILDBOT
-------------------

See the `Installation section <http://buildbot.net/buildbot/docs/0.8.7p1/manual/installation.html>`_ of the Buildbot manual for more details.

The only work required outside of the main configuration file is to start the master and slave processes on their respective machines. It is thus
`entirely possible to get a basic, running Buildbot out-of-the-box <http://buildbot.net/buildbot/docs/0.8.7p1/tutorial/firstrun.html>`_ . Everything
after that consists of reconfiguring it via the main .cfg file.

`Installing the buildbot <http://buildbot.net/buildbot/docs/0.8.7p1/manual/installation.html>`_ is a relatively straightforward process, despite
the large number of dependencies required by the master. These are usually handled automatically by whatever package manager is used.
   
Once the buildmaster package and its dependencies have been installed, the master is created and started by doing the following:

1. select a `basedir` (in our case, `/var/lib/buildbot/masters/`)

2. type `buildbot create-master /path/to/basedir` (or, `cd` to `basedir` and then type `buildbot create-master .`)

3. get Topographica's configuration file from the repository and place it instead of the default `master.cfg` in `basedir/master.cfg`

4. type `buildbot start /path/to/basedir`. That's all.

Alternatively, you can start the buildbot first, replace `master.cfg` (it's only read once when the process is started), and then reconfigure
Buildbot by restarting the process. Type `buildbot restart /path/to/basedir`. This is also the procedure when making changes to the configuration:
edit master.cfg, then restart the process for the changes to take effect. In the latter case, it is better to first run `buildbot checkconfig /path/to/new_version_of_master.cfg` in order to use buildbot's configuration-checking utility before restarting the process, otherwise it will
fail to start if there are errors in the file.

When updating to a newer version of Buildbot and there's already a master running on the system, `upgrade it to use the new code libraries. <http://buildbot.net/buildbot/docs/0.8.7p1/manual/installation.html#upgrading-an-existing-buildmaster>`_

STARTING A SLAVE
----------------

On a slave, only the `buildslave` package needs to be installed. Its only dependencies are Twisted and Zope.Interface. To add a new slave to the
system, the following is done:

1. Specify the SLAVENAME, PASSWORD, and PORT in the master's configuration file::

      c['slavePortnum'] = "tcp:9989"
      
      c['slaves' ] = [
          BuildSlave("SLAVENAME", "PASSWORD")
          ]
	   
2. Choose a `basedir`.

3. Type `buildslave create-slave /path/to/basedir/ MASTERHOST:PORT SLAVENAME PASSWORD`. The command to add a new slave to the doozy master is thus::

      buildslave create-slave /path/to/basedir doozy.inf.ed.ac.uk:9989 slavename password

4. Type `buildslave start /path/to/basedir`. No further configuration is required, and the buildslave will be available to run tasks as soon as the
   process is up.
   
Note that the HOSTNAME of the master needs to be given to the slave, but not the other way around. Therefore, the master does not differentiate
between remote or local slaves, physical slaves or VM slaves; it only has their names and passwords, and the connection is always established in the
same way. The rationale is to ensure greater portability of the slaves; the master should be fairly persistent but that slaves can come and go. In
larger setups, the admin of a slave host will contact the master's admin to obtain the slavename and password needed for connection.

BUILDERS & FACTORIES
--------------------

`Builders <http://buildbot.net/buildbot/docs/0.8.7p1/manual/cfg-builders.html>`_ are defined by adding a list with the required options to Buildbot's configuration dictionary::

   c['builders'] = [
                    BuilderConfig(name = "full_build",
					slavename = MAIN_SLAVE,
					factory = full_build_factory,
                    locks = [MAIN_SLAVE_LOCK],
					env = {'HOME': MAIN_SLAVE_OUTPUT + "full_build", 'PATH': "/usr/local/bin:/usr/bin:/bin"})
                   ]

Here, the name of the builder, the factory (see below) it will use, and the name of the slave to which it is attached are specified. `Locks <http://buildbot.net/buildbot/docs/0.8.7p1/manual/cfg-interlocks.html>`_ can be used to prevent more than one build from taking place on a 
given machine at any given time. The build environment can be modified using the `env` option to pass a list of environmental variables, e.g.
in this case HOME (see discussion above on having separate homes for different builders on the same slave) and PATH.

A `build factory <http://buildbot.net/buildbot/docs/0.8.7p1/manual/cfg-buildfactories.html>`_ is the collection of steps performed by a builder. Each
builder must have exactly one factory, which could be defined either separately or specifically for that builder. If defined separately, however,
build factories can be reused , Build
factories can be defined and attached to more than one builder::

   windows_factory = BuildFactory()
   windows_factory.addStep(Git(repourl = GITURL, mode = "full", method = "clobber", submodules = True, haltOnFailure = True, retry = (10,2)))
   windows_factory.addStep(ShellCommand(command=CMD_WIN_UNIT, description="unit tests", flunkOnFailure=True))
   windows_factory.addStep(ShellCommand(command=CMD_WIN_ALL, description="system tests", flunkOnFailure=True))
   windows_factory.addStep(ShellCommand(command=CMD_WIN_SPEED, description="speed tests", flunkOnFailure=True))
   
   c['builders'] = [BuilderConfig(name="WinXP_alltests", slavename=WINXP_SLAVE, factory=windows_factory),
                    BuilderConfig(name="Win7_32_alltests", slavename=WIN732_SLAVE, factory=windows_factory)
                    ]

COMMANDS AND BUILDSTEPS
-----------------------

The examples above have shown some of the basic `commands and buildsteps <http://buildbot.net/buildbot/docs/0.8.7p1/manual/cfg-buildsteps.html>`_ performed by buildbot; here is a more in-depth explanation.

`Source checkout <http://buildbot.net/buildbot/docs/0.8.7p1/manual/cfg-buildsteps.html#module-buildbot.steps.source>`_ steps define how the code
repository should be cloned, and work with most major version control systems. The difference between the `mode` and `method` arguments is a bit
ambiguous, but setting them to `full` and `clobber`, respectively, ensures that the old copy from the previous build will be deleted entirely and
a fresh copy will be fetched for the current build. This also takes care of the need to delete files generated by the build, if they are generated
in the same directory; for example, coverage reports. The `submodules` argument is specific to Git and is used to fetch Git submodules included as
linked repositories, such as Topographica's Param, ParamTK, ImaGen and Lancet.

`ShellCommand <http://buildbot.net/buildbot/docs/0.8.7p1/manual/cfg-buildsteps.html#shellcommand>`_ is the most common buildstep where most of the
work occurs. The slave is told to perform a certain action in the form of a shell command given as a list of strings corresponding to each
executable or argument, such as `["make", "doc"]`, `["nosetests", "-v", "--with-doctest"]` or `["rm", "-rf", "tests/old_coverage_reports"]`. This is
where Topographica tests are run.

To achieve the same on the master, `MasterShellCommand <http://buildbot.net/buildbot/docs/0.8.7p1/manual/cfg-buildsteps.html#running-commands-on-the-master>`_ is used.

To transfer files and directories (e.g. coverage reports) between the slave and the master, `FileUpload, FileDownload and DirectoryUpload <http://buildbot.net/buildbot/docs/0.8.7p1/manual/cfg-buildsteps.html#transferring-files>`_ are used.

There are a number of other convenience functions to run on the slave, such as `directory copying, deletion and creation <http://buildbot.net/buildbot/docs/0.8.7p1/manual/cfg-buildsteps.html#slave-filesystem-steps>`_ or different `Python buildsteps <http://buildbot.net/buildbot/docs/0.8.7p1/manual/cfg-buildsteps.html#python-buildsteps>`_ such as PyFlakes or removing PYCs. These should definitely
be studied and used in the future since many of them are currently done manually.

Buildbot offers many other goodies that I didn't have the time to use or simply didn't know about. The setup should be perpetually improved and
maintained, constantly seeking to find a better solution.

SCHEDULERS
----------

`Buildbot's schedulers <http://buildbot.net/buildbot/docs/0.8.7p1/manual/cfg-schedulers.html>`_ trigger builds at either predefined times or upon
detecting some event. The ones used in Topographica are all `Nightly <http://buildbot.net/buildbot/docs/0.8.7p1/manual/cfg-schedulers.html#nightly-scheduler>`_ schedulers running at selected times overnight; it is also
possible to include schedulers that monitor the repository and trigger builds as soon as they detect new commits, such as the `SingleBranchScheduler http://buildbot.net/buildbot/docs/0.8.7p1/manual/cfg-schedulers.html#singlebranchscheduler`_ . This was not deemed usable, however; as of yet, there
is no single set of tests that is BOTH sufficiently thorough to be reliable and dependable AND fast enough to be run multiple times a day. Ideally,
the unit tests will become such a set, but currently they are insufficient and instead all tests are run to ensure everything works. Running all tests
takes about 20 to 30 minutes so it's not practical to run them multiple times after new commits; even though the branch scheduler has a "stable timer"
which waits for a certain time to pass with no new commits, running all tests will still impose restrictions on the process. Branch schedulers have
therefore been left out for the time being, and can be added in the future when the unit tests are reliable enough.

`Force scheduler <http://buildbot.net/buildbot/docs/0.8.7p1/manual/cfg-schedulers.html#forcescheduler-scheduler>`_ is the other kind of scheduler in Topographica's buildbot; all builders are attached to it in order to enable forcing builds from the web interface (see below).

NOTIFICATIONS AND WEB INTERFACE
-------------------------------

Buildbot has various ways of notifying about the build status; the simplest one was chosen for Topographica, consisting of e-mails sent to a 
predefined address (see `MailNotifier status target <http://buildbot.net/buildbot/docs/0.8.7p1/manual/cfg-statustargets.html#mailnotifier>`_ )::

   c['status'].append(mail.MailNotifier(fromaddr="buildbot@topographica.org",
                                        mode=('failing'),
                                        extraRecipients=[NOTIFICATION_EMAIL],
                                        sendToInterestedUsers=False))

`mode` can also have other values, e.g. 'passing' or 'change' though the former will generate unneeded mail traffic while the latter is not reliable
enough. 'Failing' is the most basic type, ensuring that an e-mail will be sent for every failed built and that failures won't be forgotten.

To send to a predefined address (e.g. a mailing list), use `extraRecipients`. Emails will always be sent there, regardless of whether
`sendToInterestedUsers` is set to True. If it is, Buildbot will attempt to find which developers made changes into the current build, and send e-mails
specifically to them. See `Doing Things With Users <http://buildbot.net/buildbot/docs/0.8.7p1/manual/concepts.html#doing-things-with-users>`_.
However, Buildbot has a rather limited conception of "users", and a build will only have "responsible users" if it was triggered by a Branch
Scheduler. Nightly Schedulers will list no responsible users even if there were multiple commits made since the last build. If a Branch Scheduler is
used, the "blamelist" will also be included in the body of e-mails sent to `extraRecipients` thereby "publicly shaming" developers in mail sent to a
group mailing list. I am not a proponent of this approach, though, and find that a blamelist is unnecessarily antagonising. Monitoring Buildbot and
maintaining code health should be a collective responsibility, and problems should be resolved in cooperation. This doesn't mean that the team should
have to clean up somebody's mess for them but means that any complex problems that involve work by multiple people (A LOT of problems in Topographica
are of this kind) may have more serious implications that go beyond what the last person committed. Such problems should be discussed by everyone.

In order for Buildbot to send e-mail from the University of Edinburgh network, the machine needs to be properly configured. See `Setup_Mail.rst`.

Buildbot's web interface is `another Status Target <http://buildbot.net/buildbot/docs/0.8.7p1/manual/cfg-statustargets.html#webstatus>`_ that is
essential for using the Buildbot effectively. Topographica's buildmaster on doozy is configured as follows::

   c['status'].append(WebStatus(8010, authz=authz, public_html="/var/www/buildbot"))
   
The webpage will be displayed at `c['buildbotURL'] = "http://buildbot.topographica.org/"`, which redirects to `http://doozy.inf.ed.ac.uk:8010/waterfall`. As can be seen, the master uses the specified connection settings to display the webpage using the files
available in the `public_html` directory (see above for discussion on where to find it).

Buildbot uses Jinja2 templates to render the webpage. To customise its content, override default templates by placing a modified copy in
`/var/lib/buildbot/masters/templates`. Currently, Buildbot has been configured to include a link to the coverage reports in `/var/www/buildbot`;
the link is included in the navigation menu at the top by modifying the `layout.html` template. See more in the manual, and compare against the
default version in `/usr/local/lib/Python2.7/dist-packages/buildbot/status/web/templates/layout.html`.

The web page is an incredibly useful resource, showing the results of all builds in the "Waterfall" page. Columns correspond to builders (see
`master.cfg` and compare), and rows correspond to time. Newest builds appear on top. Successful builds are shown in green and failed ones in red.
Builds in progress are shown in yellow, warnings in orange, and exceptions (e.g. build interrupted) in purple. Clicking on each completed step will
display the entire build log for that step, including the command that started it and all of the generated output.

The Login field at the top can enable additional actions for use in the web interface; see `master.cfg` to find out how to protect them against
access by strangers and how to set a maintenance username and password. Once logged in, the developer can:

- Force a new build on any builder (after clicking on the builder);

- Stop an ongoing build;

- Perform a Graceful Shutdown on a given slave. Note: only the slave process will be terminated; the host will not be powered off!

FUTURE WORK
-----------

See `Work_on_CI.rst`.
