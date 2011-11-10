# Goes through all entries in svn log file, removing any entry where
# all changed paths are in the excludes list.
#
# To get filtered log for revision X to latest:
# $ svn log --verbose -rX:HEAD > changes.log   
# $ python filterlog.py changes.log filtered.log

excludes = ['contrib','topo/tests','doc/News','doc/buildbot','doc/shared','doc/Team_Members','ChangeLog.txt','MANIFEST.in','doc/Home/news']
# and while pattern.audio is unstable
excludes += ['pattern/audio']

# only interested in changes in trunk
PATH_OF_INTEREST = "/trunk"

STATUS = ["A","M","D"] # svn describes paths as A, D, or M
ENTRY_SEPARATOR = "---------------" # svn log entries are separated by line starting with this

def filter_logfile(log_file,out_file):
    # writes entries from log_file to out_file if one more changed paths in entry is not in excludes
    current_section = []
    for line in log_file:
        if line.startswith(ENTRY_SEPARATOR):
            out_file.writelines(_process_section(current_section))
            current_section = []
        current_section.append(line)

def _process_section(lines):
    # removes section if all paths are excluded
    # (not that you could tell from the code below)
    skip = True
    for line in lines:
        line = line.strip()
        for thing in STATUS:
            if line.startswith("%s %s"%(thing,PATH_OF_INTEREST)):
                if not any([exclude in line for exclude in excludes]):
                    skip = False                
    if skip:
        return []
    else:
        return lines


if __name__=="__main__":
    import sys
    fin = open(sys.argv[1],'r')
    fout = open(sys.argv[2],'w')
    filter_logfile(fin,fout)
    
