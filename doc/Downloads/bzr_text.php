<H2>Topographica using Bazaar</H2>

<P>** Draft documentation; likely to be out of date **

<P>The trunk of Topographica's SVN repository is continuously
mirrored<sup><a href="#footnote-1">1</a></sup> to a public Bazaar
(bzr) branch. This allows anyone to make his or her own Bazaar branch
easily, and keep that branch up to date by merging from the
Topographica SVN trunk (via the Bazaar mirror) over time. Starting
from this branch is an easy way for anyone (registered Topographica
developer or not) to develop a new feature or fix a bug.

<P>Note that at least with Bazaar 1.1.0, we have found
that <A HREF="git.html">Git</A> (another distributed version control
system) interoperates better with the Topographica SVN repository, so
unless you are familiar with Bazaar already, we recommend you use Git
instead.

<P>Our Bazaar mirror of Topographica's SVN repository is hosted
by <A HREF="https://launchpad.net/">Launchpad</A>.  The essentials for
using bzr at Launchpad are described below; see Launchpad's 
<A HREF="https://help.launchpad.net/FeatureHighlights/BazaarHosting">Bazaar
hosting introduction</A> for a longer tutorial. Note that you will
need to run at least bzr 0.92 on your machine, because older bzr
clients will complain that they do not recognize the Topographica
branch format.

<P>Change to the path where you want the <code>trunk/</code> directory
  to appear, then type:
<pre>
bzr branch http://bazaar.launchpad.net/~vcs-imports/topographica/trunk
</pre>

<P>
This command can take a while to
exectute<sup><A HREF="#footnote-1">1</A></sup>, but the progress will
be displayed (unless you are in a dumb terminal, such as Emacs's shell
mode, progress is displayed for XXXX all lengthy bzr
operations). Once complete, the new directory will occupy around 1 Gb
(as of 02/2008). After you have the source code, you probably want to
<A HREF="index.html#building-topographica">build Topographica</A>.

<P>XXXX mention lightweight checkout

<P>Alternatively, instead of using our Bazaar mirror, you yourself are
free to make a branch of Topographica's SVN trunk using
bzr... probably "bzr branch $TOPOROOT/trunk" or similar after
installing bzr-svn. Not sure how difficult to get working. Guess it
takes a long time, too.



<H3>Working with your Bazaar branch</H3>

<P>Now that you have your own branch, you are free to work with it
however you wish.  You can commit changes whether or not you are a
Topographica developer, and because Bazaar keeps track of the history
on your local copy, you can easily revert files. None of this activity
requires network access. 

<P>Before committing for the first time, you should inform bzr who you
are, so that changes are attributed to the correct username:
<pre>
XXXX formatting messed up - see source
bzr whoami "Your Name <user@address.ext>"
</pre>

<P>To stay up to date with the SVN version of Topographica, you
can update your own branch with changes committed to Topographica's
trunk:
<pre>
$ bzr update
Tree is up to date at revision 7820.
</pre>

<P>Note that you could also use <code>bzr pull</code> or <code>bzr merge</code>,
depending on the status of your branch. See help for those commands, or the
<A HREF="http://bazaar-vcs.org/FAQ#head-73f0b8ea8515a0087ce8705fbaafc55c80a0a30e">pull/merge</A>
or <A HREF="http://bazaar-vcs.org/FAQ#head-b08de2689c115dc966f1336ab90f1eddd9d85e0b">update/merge</A>
explanations in the list
of <A HREF="http://bazaar-vcs.org/FAQ">frequently asked questions
about Bazaar</A>.
<!--

$ bzr merge
Merging from remembered location http://bazaar.launchpad.net/~vcs-imports/topographica/trunk/
 M  topographica/examples/lissom_or_noshrinking.ty
All changes applied successfully.

$ bzr diff
# check what changed
# if there are conflicts, examine&resolve, then bzr resolved filename

$ bzr commit -m 'Merged changes from SVN trunk.' .
-->

<!--
Or, if your copy has not diverged from the SVN trunk, you can simply pull the changes:
<pre>
$ bzr pull
Using saved location: http://bazaar.launchpad.net/~vcs-imports/topographica/trunk/
+N  topographica/doc/Downloads/bzr_text.php
 M  topographica/external/Makefile
-D  topographica/external/ipython-0.7.3.tar.gz
 M  topographica/topo/tests/testDynamicParameter.txt
All changes applied successfully.
Now on revision 7812.
</pre>
-->

<!--
<P>Note that if you also merge changes from other branches, you should 
specify the branch from which to pull/merge. In such cases, the merge command
above would become:
<pre>
$ bzr merge http://bazaar.launchpad.net/~vcs-imports/topographica/trunk/
</pre>
-->

<!-- link to bzr for svn users? mention uncommit etc? -->


<P>Once you have done some work, you probably want to make your
changes publicly visible (currently they exist only on your local
copy).  To do this, you have two options. The first is simply to
publish your own branch somewhere; the second is to 'push' your
changes to the Topographica SVN repository (for which you need to be a
Topographica developer).


<H4>Publishing your branch</H4>

<P>Topographica developers might wish to make their changes publicly
visible while working on a new feature or fixing a bug. Non-developers
might like to make their changes available to anyone (for use or for
consideration to merge into the core Topographica code). Either way,
publishing a branch is an easy way to do this. 

<P>
Bazaar allows you to publish your branch using any of several
different transport protocols (e.g. sftp, ssh, http), so you can
publish to almost any server you wish. Here, however, we assume you
are a Launchpad user, and that you want to publish to your Launchpad
space and have the branch associated with Topographica:

<pre>
bzr push bzr+ssh://user@bazaar.launchpad.net/~user/topographica/branch_name
</pre>

where <code>user</code> is your Launchpad username,
and <code>branch_name</code> is the name you wish to give your
branch. For this command to work, you must first have 
<A HREF="https://launchpad.net/people/+me/+editsshkeys">added your
machine's SSH key to your Launchpad account</A>.

<P>
You (and anyone else) should then be able to see your branch at the
URL <code>https://code.launchpad.net/~user</code>.  If you do not want
to associate your branch with Topographica,
replace <code>topographica</code> in the command above
with <code>+junk</code>.



<H4>Pushing your changes to Topographica's SVN</H4>

<P>If you are a Topographica developer implementing a new feature or
fixing a bug, you will want to commit your finished work to the central
Topographica repository...

<P>Install bzr-svn:

XXXX
<pre>
ceball@doozy:~/b$ wget http://samba.org/~jelmer/bzr/bzr-svn-0.4.7.tar.gz
ceball@doozy:~/b$ tar zxvf bzr-svn-0.4.7.tar.gz 
ceball@doozy:~/b$ mv bzr-svn-0.4.7 svn
ceball@doozy:~/b$ mv svn/ ~/.bazaar/plugins/
</pre>

then:

<pre>
# editing
# bzr commit(s)
$ bzr push https://topographica.svn.sourceforge.net/svnroot/topographica/trunk
</pre>

<P>The first time you run this time, there is a long wait.  CEBALERT:
in fact I killed it because I got suspicious after a while that it
doing something bad - not sure. I'll just be using patch to move
changes...

<H3>Launchpad.net team branches</H3>

<P>
Launchpad's
<A HREF="https://help.launchpad.net/FeatureHighlights/TeamBranches">team
branches</A> allow multiple users to collaborate easily on a new
feature or fix, and they allow a workflow similar to SVN's. Our
Launchpad team
is <A HREF="https://launchpad.net/~topographica-developers/">topographica-developers</A>,
which you can join by cliking on the 'Join this team' button on the team homepage.

<P>Team branches are not required for collaboration; team members could already
<code>bzr push</code> and <code>bzr branch</code> code among themselves. XXXX Team branches make it easier to...


<H4>Team branch creation</H4>

<P>From the bzr branch you wish to publish for team collaboration, type:
<pre>
bzr push bzr+ssh://user@bazaar.launchpad.net/~topographica-developers/topographica/branch-name
</pre>


<H4>Getting a team branch</H4>

<P>Launchpad recommends that collaborators each make a checkout (rather than a branch) of the code:

<pre>
bzr checkout bzr+ssh://user@bazaar.launchpad.net/~topographica-developers/topographica/branch-name
</pre>

<P>A checked-out copy will automatically ensure you have changes from others before you commit, and will store all your changes on the central copy. If you do not have network access while working, your commits will remain local until you perform some operation that does connect to the network (XXXX check). You can use <code>bzr commit --local</code> to force your change to be local (but note that the commit will later be made to the central branch automatically when you later perform an action with network access). XXX mention what happens with bzr update (local commits -> pending merge)

<P>You might want to work on your own from a team branch, which is of course still possible by performing the usual <code>bzr branch</code> (rather than <code>bzr checkout</code>). You can then use <code>bzr push</code> to send your local commits back to the team branch.

<P>
You could also combine the above two approaches: <code>bzr checkout</code> the team branch, and then <code>bzr branch</code> your checkout to get a local branch. You would then be able to commit to your local branch, and after finishing some task, you could <code>bzr merge</code> your local branch changes into your checked-out copy before using <code>bzr commit</code> from the checked-out copy to send the changes to the team branch. XXXX not clear how that's better than just having your own branch and using push...maybe it makes the merge much easier?

<P> 
XXXX mention bzr checkout --lightweight for no history but every operation needs network connection.




<!--
What I found to work:

from /home/ceball/tile

bzr checkout --lightweight http://cball@bazaar.launchpad.net/~topographica-developers/topographica/tk85

or 

bzr branch http://cball@bazaar.launchpad.net/~topographica-developers/topographica/tk85

or 

bzr checkout http://cball@bazaar.launchpad.net/~topographica-developers/topographica/tk85


bzr+ssh on those gave me memoryerror.

-->



<!--
# Example where I checked out with http so have to push

ceball@doozy:~/tile$ bzr checkout http://cball@bazaar.launchpad.net/~topographica-developers/topographica/tk85

ceball@doozy:~/tile/tk85/topographica$ bzr commit -m "Removed some out-of-date comments." topo/tkgui/__init__.py
bzr: ERROR: Cannot lock LockDir(http://cball@bazaar.launchpad.net/%7Etopographica-developers/topographica/tk85/.bzr\
/branch/lock): Transport operation not possible: http does not support mkdir() 
ceball@doozy:~/tile/tk85/topographica$ bzr commit --local -m "Removed some out-of-date comments." topo/tkgui/__init\
__.py
Committing to: /home/ceball/tile/tk85/
modified topographica/topo/tkgui/__init__.py
Committed revision 7819.
ceball@doozy:~/tile/tk85/topographica$ bzr push bzr+ssh://cball@bazaar.launchpad.net/~topographica-developers/topog\
raphica/tk85
Pushed up to revision 7819.
ceball@doozy:~/tile/tk85/topographica$ 

-->



<H3>Notes</H3>

<pre>

* If you're going to have more than one branch of Topographica, you might
  consider using a shared repository:
  http://bazaar-vcs.org/SharedRepositoryTutorial

* any way to get emails for team branch commits? (how to get emails at
  all...)

* general info about branching with lp
  https://help.launchpad.net/FeatureHighlights/EasyBranching

* bzr/git+svn workflow
  http://info.wsisiz.edu.pl/~blizinsk/git-bzr.html

* http://wiki.list.org/display/DEV/MailmanOnLaunchpad

* https://help.ubuntu.com/community/EasyBazaar

* http://jam-bazaar.blogspot.com/2007/10/bazaar-vs-subversion.html

* http://sayspy.blogspot.com/2006/11/bazaar-vs-mercurial-unscientific.html

* http://ligarto.org/rdiaz/BzrCentralLocalRepoNotes.html I just found
  but haven't read seems to be this document but better! doh!

</pre>

<!--budget footnotes-->
<P>
[<A name="footnote-1">1</A>] The Launchpad mirror of Topographica's SVN
trunk can be 6-24 hours out of date.
<BR>
[<A name="footnote-2">2</A>] Bazaar currently does not support any
kind of 'history horizon', so all of Topographica's history must be
downloaded. Additionally, the SVN mirror is of trunk/, which includes
facespace/. Therefore, when creating branches, the waiting
times are unnecessarily big. See http://bazaar-vcs.org/HistoryHorizon
for more information about developments surrounding 'history
horizons'. Shallow checkouts feature: https://launchpad.net/bzr/+spec/shallow-checkouts

