************************************
Translating UNIX commands to Windows
************************************

The Windows equivalent of 'the shell' is its 'Command Prompt'. The
easiest way to start this is by clicking on 'Start', then 'Run',
then typing ``cmd``, then clicking 'Ok'.

To convert UNIX shell commands to Windows Command Prompt commands:

-  Replace ``~`` in a path with the path to your user profile folder
   (``%HOMEPATH%``)
-  Replace ``~/Documents`` in a path with the path to your
   ``Documents`` (Windows Vista or later) or ``My Documents`` folder
   (e.g. ``~/Documents/Topographica`` might become
   ``"%HOMEPATH%\My Documents\Topographica"``)
-  Replace any forward slash '``/``\ ' in a path with a backslash
   '``\``\ '
-  Single quotes (``'``) must appear inside double quotes (``"``);
   double quotes cannot appear inside single quotes
-  Filenames on Windows usually need double quotes, because the
   paths often contain spaces (e.g. "My Documents" or "Program
   Files")

Example UNIX command:

::

  topographica -g ~/Documents/Topographica/examples/lissom_oo_or.ty

Windows Vista or later equivalent:

::
  topographica -g "%HOMEPATH%\Documents\Topographica\examples\lissom_oo_or.ty"

