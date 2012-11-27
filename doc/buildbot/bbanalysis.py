# CB: this file is difficult to understand because it's been built up
# over a long time. Now that it's clearer what we want it to achieve,
# I could simplify it significantly.

# A complication is that as the buildbot setup has changed, the shell
# command that is checked for the timings has changed number. This
# means the timing data can change directory and filename. Therefore,
# this script cannot be used to get all historical data in one
# go. There's a MIN_BUILD variable that specifies the first build to
# check. That can be changed together with the filename_pattern
# variable to do chunks of the historical data, if desired. Once the
# script has processed data, it's stored in a pickle, so the data
# doesn't need to be retrieved again. As it is, we have a timings
# pickle on doozy that has quite a lot of historical data (i.e. I have
# changed MIN_BUILD and filename_pattern as time has gone on, to keep
# up to date with changes to the buildbot config).


import sys
import re
import pickle
from glob import glob

from sys import argv

script = "lissom_oo_or.ty"

alphabet = map(chr,range(65,91))

# leave time as None to have it be looked up.
# Note that you have to specify a version for which timing data
# exists.  If you were to specify a version for which there's no
# timing data, you'd have to fill in a time to use as the y
# coordinate...and that would have to be an invented time.
annotations = {
    # Near the start of the buildbot graph, I seem to remember making
    # multiple small changes and seeing the performance improve
    # gradually. Need to check that.
    (7984,None):"Revert Event to an object (rather than it being parameterized) [r7981]",
    # changes leading up to 8048?
    # changes leading up to 8082?
    (8089,None):"Remove apparently unnecessary array copy during change_bounds() [r8084]",
    # 8105?
    (8247,None):'Use mx.Number.Float for simulation time [r8244]',
    (8383,None):'Use gmpy.mpq for simulation time [r8383]',
    (9157,None):'Provide C code with faster access to weights [r9157]',
    (9190,None):'Use optimized joint normalization function [r9190]',
    (9395,None):'Some external cause (i.e. doozy)? [r9395, bb 465]'
    }




def get_timings():
    f = open('/home/ceball/buildbot/timings.pkl')
    timings = pickle.load(f)
    f.close()
    return timings


def _get_svnversion_timings():
    svnversion_timings = {}
    _timings = get_timings()
    for build in _timings[script]:
        info = _timings[script][build]
        if info is not None:
            version = info[1]
            timing = info[2]
            if version in svnversion_timings:
                if timing<svnversion_timings[version]:
                    svnversion_timings[version]=timing
            else:
                svnversion_timings[version]=timing
    return svnversion_timings

svnversion_timings = _get_svnversion_timings()

#for v in sorted(svnversion_timings.keys()):
#    print "%s: %s"%(v,svnversion_timings[v])

def _keys_and_points(annotations):
    points = sorted(annotations)
    keys = alphabet[0:len(points)]
    return zip(keys,points)

# CB: in progress - obviously the page construction should
# be separated out, etc
def write_page():
    locn = "/home/ceball/buildbot/buildmaster/public_html/p/"
    imgfile = "lissom_oo_or_250_svnversion.png"

    key_text = "<table>"
    key_text+="<tr><td>Event</td><td>Version</td><td>Performance</td><td>Description</td></tr>"
    for key,point in _keys_and_points(annotations):
        event = key
        version = point[0]
        performance = point[1] or svnversion_timings[version]
        description = annotations[point]
        key_text+="<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"%(event,version,performance,description)

    key_text+="</table>"

    s = "<html><body><p><img src='%s' /></p><p>%s</p></body></html>"%(imgfile,key_text)

    f = open(locn+"running.html",'w')
    f.write(s)
    f.close()


V=re.compile(r'[0-9]*-log')
def get_build_no(logfilename):
    return int(V.findall(logfilename)[0].rstrip('-log'))


def create_timings(i_am_sure=False):
    if i_am_sure:
        timings = {}
        f = open('/home/ceball/buildbot/timings.pkl','w')
        pickle.dump(timings,f,0)
        f.close()

def create_startups(i_am_sure=False):
    if i_am_sure:
        startups = {}
        f = open('/home/ceball/buildbot/startups.pkl','w')
        pickle.dump(startups,f,0)
        f.close()



def save_timings(timings):
    f = open('/home/ceball/buildbot/timings.pkl','w')
    pickle.dump(timings,f,0)
    f.close()


def get_startups():
    f = open('/home/ceball/buildbot/startups.pkl')
    startups = pickle.load(f)
    f.close()
    return startups

def save_startups(startups):
    f = open('/home/ceball/buildbot/startups.pkl','w')
    pickle.dump(startups,f,0)
    f.close()

# exclude these builds
exclusions = []
exclusions.append(153) # doc why this is excluded
exclusions.append(425) # ran with wrong no. of iterations

def get_date_version_time(logfile,timings=None,startups=None):

    build = get_build_no(logfile)

    f = open(logfile)
    all_lines = f.readlines()
    f.close()

    ok = ok2 = False

    datei=versioni=timingi=startupi=None

    i = 0;
    for line in all_lines:
        if line.find("Running at")>=0:

            datei=i
        elif line.find("svnversion")>=0:

            versioni=i
        elif line.startswith("[examples/%s]"%script):
            timingi=i

        elif line.find("[examples/%s startup]"%script)>=0:
            startupi=i

        elif line.find("Results from examples/%s have not changed."%script)>=0:
            ok2=True
        elif line.find('program finished')>=0:
            ok=True

        i+=1;

    if not ok:
        #print "...build %s currently incomplete"%build
        return None

    if not ok2:
        #print "...speed test invalid because results didn't match"
        if timings:
            timings[script][build] = None
        if startups:
            startups[script][build] = None
        return None

    if datei is None or versioni is None or timingi is None or startupi is None:
        #print "...not all data available - build didn't complete?"
        if timings:
            timings[script][build] = None
        if startups:
            startups[script][build] = None
        return None


    datel= all_lines[datei]
    d=re.compile(r'at [0-9]*')
    date = float(d.findall(datel)[0][3::])

    versionl = all_lines[versioni]
    v=re.compile(r'n [0-9]*')
    version = int(v.findall(versionl)[0][2::])

    timel = all_lines[timingi]
    t=re.compile(r'Now: [0-9.]* ')
    start,stop = t.search(timel).span()
    timing = float(timel[start+5:stop-1])

    cpusel = all_lines[timingi+1]
    start,stop = cpusel.index('elapsed')+8,cpusel.index('%CPU')
    cpu_usage = float(cpusel[start:stop])

    startupl = all_lines[startupi]
    t=re.compile(r'Now: [0-9.]* ')
    start,stop = t.search(startupl).span()
    startup = float(startupl[start+5:stop-1])

    startcpusel = all_lines[startupi+1]

    try:
        start,stop = startcpusel.index('elapsed')+8,startcpusel.index('%CPU')
        startcpusage = float(startcpusel[start:stop])
    except ValueError:
        startcpusage = 99  # HACK: for cases where it's missing, assume 99!

    if timings:

        if cpu_usage>95:
            timings[script][build] = (date,version,timing,cpu_usage)
        else:
            #print "...build %s had %s percent cpu during timing (not >95)"%(build,cpu_usage)
            timings[script][build] = None

    if startups:

        if startcpusage>95:
            startups[script][build] = (date,version,startup,startcpusage)
        else:
            #print "...build %s had %s percent cpu during startup (not >95)"%(build,startcpusage)
            startups[script][build] = None

    return (build,date,version,timing,startup,cpu_usage)


MIN_BUILD=153 # where to start analysis
filename_pattern = '*-log-shell_3-stdio'
def update_timings(location="/home/ceball/buildbot/buildmaster/slow-tests_x86_ubuntu7.04/"):

    timings = get_timings()

    if script not in timings:
        timings[script]={}


    startups = get_startups()

    if script not in startups:
        startups[script]={}

    filenames = glob(location+filename_pattern)
    for filename in filenames:

        build = get_build_no(filename)

        if build>=MIN_BUILD:

	    do_timings=do_startups=False

            if build not in timings[script] and build not in exclusions:
                #print "Adding timing for build...",build
		do_timings=True
            elif build in exclusions and build not in timings[script]:
                #print "Build %s excluded; timing skipped."%build
                timings[script][build]=None

            if build not in startups[script] and build not in exclusions:
                #print "Adding startup time for build...",build
            	do_startups=True
            elif build in exclusions and build not in startups[script]:
                #print "Build %s excluded; startup timing skipped."%build
                startups[script][build]=None
		
	    if do_timings and do_startups:
                get_date_version_time(filename,timings,startups)
            if do_timings and not do_startups:
                get_date_version_time(filename,timings,None)
            if not do_timings and do_startups:
                get_date_version_time(filename,None,startups)

    save_timings(timings)
    save_startups(startups)
    #print timings



def plot_timings():
    timings=get_timings()
    t=timings['lissom_oo_or.ty']
    tytle="lissom_oo_or.ty, 250 iterations"
    filename="/home/ceball/buildbot/buildmaster/public_html/p/lissom_oo_or_250"
    plott(t,tytle,filename)

def plot_startups():
    timings=get_startups()
    t=timings['lissom_oo_or.ty']
    tytle="lissom_oo_or.ty, startup"
    filename="/home/ceball/buildbot/buildmaster/public_html/p/lissom_oo_or_startup"
    plott(t,tytle,filename)

import matplotlib;matplotlib.use('Agg')

def sgn(x):
    return +1 if x>=0.0 else -1

def plott(t,tytle,filename):

    from pylab import title,xlabel,ylabel,savefig,figure,annotate,figtext

    builds=[]
    versions=[]
    times=[]
    for build,data in t.items():
        if data is not None:
            builds.append(build)
            versions.append(data[1])
            times.append(data[2]*data[3]/99.0)


    from topo.command.pylabplot import vectorplot
    figure()
    vectorplot(times,versions,style='bx')


    title(tytle)
    xlabel("svnversion")
    ylabel("time /s")


    xshift=2
    yshift=1
    arrowprops={'width':0.01,'frac':0.05,'headwidth':0}
    for key,point in _keys_and_points(annotations):
        text = key
        version = point[0]
        timing = point[1] or svnversion_timings[version]
        text_coords = version+xshift,timing+yshift
        annotate(text,(version,timing),xytext=text_coords,arrowprops=arrowprops)

    savefig(filename+"_svnversion.png")

    figure()
    vectorplot(times,builds,style='bx')

    title("lissom_oo_or.ty, 250 iterations")
    xlabel("build")
    ylabel("time /s")

    savefig(filename+"_buildno.png")





## if __name__=='__main__':

##     if len(sys.argv)>1:
##         if sys.argv[1]=='update':
##             update_timings()
