<h3>MacPorts Python</h3>

<p>This is a complete guide on how to set up Topographica on Mac OS X 10.6.* using a MacPorts Python 2.7/2.6 and extensions.<br /><br />
The EPD (Enthought Python Distribution) is preferable to those who wish to simply install a fully functional python distribution with minimum hassle.</p>

<p>That said, there are several advantages to building your own dependancies for Topographica. Firstly Topographica will not currently run on the 64bit EPD 7.0 distribution due to various missing dependancies, to run Topographica in 64bit on OS X you must build according to the instructions below. Luckily those missing dependancies are present on the 32bit EPD 7.0, though it has it's own set of disadvantages - namely it ues Tk/TCL 8.4 as opposed to 8.5, and must use the slower FixedPoint for simulation time (vs. the faster gmpy). The are also currently issues with audiolab on the EPD, there is luckily a workaround, see the Optional Installs section if you need audiolab.</p>

<p>Thus the method outlined below provides greater speed and compatibility than the EPD, especially when using Topographica's GUI. If none of these issues are important to you we advise using the 32bit EPD.</p>


<h3>Development Environment</h3>

<p>A valid development environment is required before proceeding, as of OS X 10.6.7 there are 2 ways to achieve this. One is paid, the other free. It is unknown how long the free option will continue to exist, the paid option is currently &#163;2.99 (&#36;4.99).</p>

<p>The 2 versions are currently equivalent for the purposes of building Topographica, unless you want the new Xcode Code Editor we advise the free Xcode 3.2.6. Only the Xcode Essentials and UNIX development tools are required for building Topographica, the remaining Xcode install options can safely be omitted.</p>

<p>Free Option: <a href="http://developer.apple.com/xcode/">[Apple Developer Website]</a> install Xcode 3.2.6 from the link in the lower bottom right of the page.<br />
Paid Option: <a href="http://itunes.apple.com/app/xcode/id422352214?mt=12">[Mac AppStore]</a> install Xcode 4.*</p>

<p>The following free tools provide the package manager and the X11 windowing system. Both are required.</p>

<p><a href="http://www.macports.org/">[MacPorts Website]</a> install MacPorts<br />
<a href="http://xquartz.macosforge.org/trac/wiki">[XQuartz Website]</a> install XQuartz<br /></p>


<h3>Topographica Requirements</h3>

<p>Run the following in a shell to install everything needed for Topographica, if you want to run Python 2.6 instead of 2.7 simply replace any instances of 27 with 26 and 2.7 with 2.6</p>

<blockquote><code>
sudo port selfupdate<br />
sudo port install tcl +threads tk python27 py27-numpy py27-pil py27-matplotlib py27-scipy py27-ipython gmp python_select<br />
<br />
sudo python_select python27<br />
sudo rm /opt/local/bin/ipython<br />
sudo ln -s /opt/local/bin/ipython-2.7 /opt/local/bin/ipython<br />
<br />
curl http://gmpy.googlecode.com/files/gmpy-1.14.zip > gmpy-1.14.zip<br />
unzip gmpy-1.14.zip<br />
cd gmpy-1.14<br />
sudo python setup.py install<br />
</code></blockquote>


<h3>Getting and Building Topographica</h3>

<p>The following information is from the Topographica Developer Guide, it's included here for convenience with the specific commands for an external Python setup.</p>

<blockquote><code>
export TOPOROOT=https://topographica.svn.sourceforge.net/svnroot/topographica<br />
svn co $TOPOROOT/trunk/topographica topographica<br />
<br />
cd topographica<br />
svn update<br />
make topographica-other-python<br />
</code></blockquote>

<p>You can also delete Topographica's external folder as you're now using your own system binaries.</p>

<blockquote><code>
rm -rf external<br />
</code></blockquote>


<h3>Optional Installs</h3>

<p>The audiolab package must be installed to use any of Topographica's auditory system models, however at the time of writing this guide no native Python 2.7 version exists so one must install the Python 2.6 version and manually copy it into the 2.7 directory. You can check if a 2.7 version of audiolab has been released by running:</p>

<blockquote><code>
port search py27-scikits-audiolab 
</code></blockquote>

<p>If one was found simply run the corresponding install and you're done:</p>

<blockquote><code>
sudo port install py27-scikits-audiolab 
</code></blockquote>

<p>Otherwise running the following single command should cause MacPorts to automatically install all the required dependancies including Python 2.6, and build audiolab:</p>

<blockquote><code>
sudo port install py26-scikits-audiolab 
</code></blockquote>

<p>Once that is done you only need to copy it into place for Python 2.7 and you're done.</p>

<blockquote><code>
sudo cp -r /opt/local/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/site-packages/scikits* /opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/
</code></blockquote>


<h3>Notes/Issues</h3>

<p>If you have any issues launching the GUI simply reinstall XQuartz and reboot.</p>
