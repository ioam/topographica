<h3>MacPorts Python</h3>
<p>This is a complete guide on how to set up Topographica on Mac OS X 10.6.* using a MacPorts Python 2.6 and extensions.<br /><br />
The EPD (Enthought Python Distribution) is preferable to those who wish to simply install a fully functional python distribution.<br /><br />
The method outlined below provides greater speed and compatibility than the EPD, especially when using Topographica's GUI. The EPD also currently has issues with audiolab, though of course these may be fixed in future releases. If neither of these issues are important to you we advise using the EPD.</p>

<h3>Development Environment</h3>
<p>A valid development environment is required before proceeding, as of OS X 10.6.7 there are 2 ways to achieve this. One is paid, the other free. It is unknown how long the free option will continue to exist, the paid option is currently &#163;2.99 (&#36;4.99).</p>

<p>Free Option: <a href="http://developer.apple.com/xcode/">[Apple Developer Website]</a> install Xcode 3.2.6 from the link in the lower bottom right of the page.<br />
Paid Option: <a href="http://itunes.apple.com/app/xcode/id422352214?mt=12">[Mac AppStore]</a> install Xcode 4.*</p>

<p>Only the Xcode Essentials & UNIX development tools are required for Topographica, the remaining Xcode install options can safely be omitted.</p>

<p><a href="http://xquartz.macosforge.org/trac/wiki">[XQuartz Website]</a> install XQuartz<br />
<a href="http://www.macports.org/">[MacPorts Website]</a> install MacPorts</p>


<h3>Topographica Requirements</h3>

Run the following in a shell to install everything needed for topographica:

<blockquote><code>
sudo port selfupdate<br />
sudo port install tcl +threads tk python26 py26-numpy py26-pil py26-matplotlib py26-scipy py26-ipython gmp python_select<br />
<br />
sudo python_select python26<br />
sudo ln -s /opt/local/bin/ipython-2.6 /opt/local/bin/ipython<br />
<br />
curl http://gmpy.googlecode.com/files/gmpy-1.14.zip > gmpy-1.14.zip<br />
unzip gmpy-1.14.zip<br />
cd gmpy-1.14<br />
sudo python setup.py install<br />
</code></blockquote>

<h3>Getting and Building Topographica</h3>

<p>The following information is from the Topographica Developer Guide, it's included here with the specific commands for an external python setup, for convenience.</p>

<blockquote><code>
export TOPOROOT=https://topographica.svn.sourceforge.net/svnroot/topographica<br />
svn co $TOPOROOT/trunk/topographica topographica<br />
<br />
cd topographica<br />
svn update<br />
make topographica-other-python<br />
</code></blockquote>

<h3>Optional Installs</h3>
<p>The audiolab package must be installed to use any of Topographica's auditory system models.</p>

<blockquote><code>
sudo port install py26-scikits-audiolab 
</code></blockquote>

<h3>Notes/Issues</h3>
<p>If you have any issues launching the GUI simply reinstall XQuartz and reboot.</p>