<H2><A NAME="build-on-cygwin">Building Topographica on Cygwin</A></H2>

<!--
Could host a "local directory" with the right packages, which
people could use to install a cygwin setup that would build
topographica without any extra work. Unless there's some
way to pass a list of packages into cygwin's setup.exe.
http://cygwin.com/faq/faq.setup.html#faq.setup.cli
--> 

<H3>Notes from July 13, 2008</H3>

<H4>Tcl/Tk</H4>
Topographica's "make" builds tcl without any problems, but 
fails on tk. I decided to skip this problem for the moment.

<H4>Python</H4>
Won't compile with 'make'. Downloaded patched python source
from cygwin e.g. ftp://ftp.heanet.ie/mirrors/cygwin/release/python/

Try:
./configure --prefix=/home/User/topographica LDFLAGS=-Wl,-rpath,/home/User/topographica/lib

didn't work

Try:
./configure --prefix=/home/User/topographica

didn't work

   this python bug? http://bugs.python.org/issue1706863
http://thread.gmane.org/gmane.os.cygwin/93415/focus=93515

in setup.py, line 795, replaced something with None:
sqlite_libdir = None #[os.path.abspath(os.path.dirname(sqlite_libfile))]

then ./configure --prefix=/home/User/topographica
   (forgot other options)

Now it builds and will run!


# from cygwin's own build script for python:
# make executables user writable to guarantee strip succeeds
find $InstallPrefix -name '*.exe' -o -name '*.dll' | xargs chmod u+w

# strip executables
find $InstallPrefix -name '*.exe' -o -name '*.dll' | xargs strip 

where $InstallPrefix is /home/User/topographica in this case


Now continue with topographica's make, but get errors like this:

$ make
make -C external
make[1]: Entering directory `/home/User/topographica/external'
tar -xzf Imaging-1.1.5.tgz
cd Imaging-1.1.5; env PREFIX=/home/User/topographica/ LD_LIBRARY_PATH=/home/User/topographica//lib /home/User/topographica//bin/python setup.py build_ext -i
running build_ext
building '_imaging' extension
gcc -fno-strict-aliasing -DNDEBUG -g -O3 -Wall -Wstrict-prototypes -DHAVE_LIBJPEG -DHAVE_LIBZ -I/usr/include/freetype2 -IlibImaging -I/home/User/topographica/include -I/usr/include -I/home/User/topographica/include/python2.5 -c _imaging.c -o build/temp.cygwin-1.5.25-i686-2.5/_imaging.o
      5 [main] python2.5 2848 C:\cygwin\home\User\topographica\bin\python2.5.exe: *** fatal error - unable to remap C:\cygwin\bin\tk84.dll to same address as parent(0x18710000) != 0x18C20000
      5 [main] python 484 fork: child 2848 - died waiting for dll loading, errno 11
error: Resource temporarily unavailable
make[1]: *** [pil] Error 1
make[1]: Leaving directory `/home/User/topographica/external'
make: *** [ext-packages] Error 2
0;~/topographica 

i.e. cygwin needs 'rebasing'
e.g. http://inamidst.com/eph/cygwin
http://www.tishler.net/jason/software/rebase/rebase-2.4.README
http://www.cygwin.com/ml/cygwin/2007-01/msg00571.html
and so on.

Now cygwin seems to be really slow (e.g. Imaging never compiles, 100% CPU for hours), and emacs won't start, and then X won't start...this has happened to me on three different computers each time I've done it over the last 3 years or so.



<H3>Notes from start of March 2007</H3>

<P>pre-March copy of Topographica, cygwin, etc.

<P>Build of all default targets completed without errors with the
changes listed below. Only major change is for python. 
make tests gives no error, simulations appear to work
(with and without weave), and the plots seem ok (except for
matplotlib ones, which give a file not found error).

<P>Note that to see the GUI, you have to call mainloop. Otherwise nothing appears.

<P><a href="cygwin_packages">Cygwin packages</a> I used

<H4>TCL/Tk</H4>
http://wiki.tcl.tk/11891
<code>
export CC="gcc -mno-cygwin"

cd win/
./configure --prefix=/home/chris/topographica/
make
make install

cd win/
./configure --prefix=/home/chris/topographica
make
make install
</code>

<H4>Python</H4>
http://www.tishler.net/jason/software/python/python-2.4.README

(1) rebaseall to solve fork problem
cmd prompt:
/cygwin/bin/ash.exe
rebaseall

did that make everything really slow?
Same problem as...?
http://cygwin.com/ml/cygwin/2007-02/msg00404.html
(except I don't have virus checker)
http://lists-archives.org/cygwin/24041-slow-compile-issue-with-cygwin-make-since-v1-5-17.html
http://article.gmane.org/gmane.os.cygwin/84307/match=slow+compile+cygwin+make
http://thread.gmane.org/gmane.os.cygwin/84257/focus=84307

(2) Replace Python-2.4.4.tgz with cygwin's own python sources!

(3) 
cd python-2.4.3-1
./configure --prefix=/home/chris/topographica
make
make install

./configure --prefix=/home/chris/topographica LDFLAGS=-rpath,/home/chris/topographica/lib ; make; make instal

# make executables user writable to guarantee strip succeeds
find $InstallPrefix -name '*.exe' -o -name '*.dll' | xargs chmod u+w

# strip executables
find $InstallPrefix -name '*.exe' -o -name '*.dll' | xargs strip 


pil
==========

did it compile?


numpy
==========
current svn version works with no changes
 

pmw
==========

no problems


fixedpoint
==========

no problems


weave
==========

no problems



matplotlib
==========


chris@ghost ~/topographica/lib
$ ln -s libtk84.a libtk8.4.a

chris@ghost ~/topographica/lib
$ ln -s libtcl84.a libtcl8.4.a


gnosis
===========

no problems


pychecker
===========

no problems

common
===========

no problems


pylint
===========
no problems


epydoc
===========
no problems

docutils
===========
no problems

