### This file can't be used on its own (see e.g. lissom_or_reference)

### NOTE: c++ lissom does not output unsituated weights, so a function
### in lissom_log_parser guesses how to unsituate the weights. If your
### weights contains rows or columns of zeros, this guessing will fail.

from topo.tests.reference.lissom_log_parser import check_weights,check_activities,check_size
from math import ceil

def _check_proj(s,p,N):

    # to match save_all_units.command
    step = int(ceil(N/20.0))
    if step>2 and step%2==1:
        step+=1

    # check all sizes
    try:
        for i in range(0,N,step):
            for j in range(0,N,step):
                check_size(s,p,(i,j),display=verbose)
    except AssertionError, st:
        return "%s: %s\n"%(s,st)


    try:
        for i in range(0,N,step):
            for j in range(0,N,step):
                check_weights(s,p,(i,j),display=verbose)
        return 0
    except AssertionError, st:
        return "%s: %s\n"%(s,st)


def check(weights=True,activities=True):

    errs = ""

    if weights:
        try:
            check_all_weights()
        except AssertionError,we:
            errs+=we.args[0]+"\n"

    if activities:
        try:
            check_all_activities()
        except AssertionError,ae:
            errs+=ae.args[0]+"\n"

    if len(errs)>0:
        raise AssertionError("\n"+errs)



def check_all_weights():
    print "t=%s: Checking weights..."%topo.sim.time()

    e = ""
    # assumes 'Primary'
    for proj in topo.sim['Primary'].projections():
        print "...%s"%proj
        o =_check_proj('Primary',proj,BaseN)
        if o!=0:e+=o
    if len(e)>0:
        raise AssertionError("The following weights did not match:\n%s"%e)


def check_all_activities():
    print "t=%s: Checking activities..."%topo.sim.time()

    sheets = sorted(topo.sim.objects().values(), cmp=lambda x, y:
                    cmp(x.precedence,
                        y.precedence))
    errs = ""
    for s in sheets:
        print "...%s"%s.name
        try:
            check_activities(s.name,display=verbose)
        except AssertionError, st:
            errs+=st.args[0]+"\n"

    if len(errs)>0:
        raise AssertionError("The following activities did not match:\n%s"%errs)

##         try:
##             check_activities(s.name,display=verbose)
##         except AssertionError, st:
##             prjns = sorted(topo.sim[s.name].in_connections)[::-1]

##             e = ""
##             for pr in prjns:
##                 print "Checking %s."%pr.name
##                 o =_check_proj(s.name,pr.name,BaseN)
##                 if o!=0:e+=o

##             raise AssertionError("%s  (If any incoming projection did not match, it will be listed below.)\n%s\n"%(st,e))


# hack
L = locals()





def run_comparisons(l):


    # * times mark scheduled actions

    L.update(l)

    check(activities=False) #0 *

    for i in range(5):
        topo.sim.run(1)
        check()

    topo.sim.run(95) #100
    check()

    topo.sim.run(98) #198
    check()

    topo.sim.run(2) #200 *
    check()

    topo.sim.run(150) #350
    check()

    topo.sim.run(150) #500 *
    check()

    topo.sim.run(300) #800
    check()

    topo.sim.run(200) # 1000 *
    check()

    # CB: this stop_at_1000 stuff is a temporary hack; when topographica's
    # faster, I'm not going to need it.
    if not stop_at_1000:

        for i in range(4): # to 5000 *
            topo.sim.run(1000)
            check()


        topo.sim.run(1500) # 6500 *
        check()

        topo.sim.run(1500) # 8000 *
        check()

        topo.sim.run(5000) # 13000
        check()

        topo.sim.run(3000) # 16000
        check()

        topo.sim.run(4000) # 20000 *
        check()
