"""
Commands for running the examples files in various ways.

Like a Makefile: contains a list of targets (and groups of targets)
that specify various commands to run.

E.g.

  topographica -c 'from topo.misc.genexamples import generate; generate(targets=["all_quick","saved_examples"])'

Runs the 'all_quick' target if called without any arguments:

  topographica -c 'from topo.misc.genexamples import generate; generate()'

To add new single targets, add to the targets dictionary;
for groups of targets, add to the group_targets dictionary.
"""


# JABALERT: Should be cut down and simplified; most of what it does is
# for historical rather than functional reasons.  E.g. the quick
# options should be in the tests, rather than here, and then the other
# options need not specify how long they should be run; instead that
# should be set by a parameter in the .ty file and then respected by
# this file.  The .ty file could also specify a set of default
# analysis functions to run, e.g. selecting from some options to be
# made available in topo.command, and if so this file need not have any
# handling for specific scripts.  Meanwhile, at least it works.

# Note: has none of the Makefile's dependency processing, so just does
# what you tell it (i.e. over-writes existing files).

import sys
import os.path

from os import system

import param
from param import ParamOverrides

### Convenience functions
def snapshot(filename):
    """Return a command for saving a snapshot named filename."""
    return "from topo.command import save_snapshot ; save_snapshot('%s')"%filename

def or_analysis():
    """Return a command for orientation analysis."""
    return """\
from featuremapper.command import measure_or_pref ; \
from topo.command.analysis import measure_cog ; \
measure_or_pref(); \
measure_cog()"""

def retinotopy_analysis():
    """Return a command for retinotopy analysis."""
    return """\
from featuremapper.command import measure_position_pref ; \
from topo.command.analysis import measure_cog ; \
measure_position_pref(); \
measure_cog()"""
###



def run(examples,script_name,density=None,commands=["topo.sim.run(1)"]):
    """
    Return a complete command for running the given topographica
    example script (i.e. a script in the examples/ directory) at the
    given density, along with any additional commands.
    """

    if density:
        density_cmd = ' -c "default_density='+`density`+'" '
    else:
        density_cmd = " "

    cmds = ""
    for c in commands:
        cmds+=' -c "'+c+'"'

    topographica = sys.argv[0]
    script = os.path.join(examples,script_name)

    return topographica+density_cmd+script+' '+cmds



scripts = {
    'hierarchical':'hierarchical.ty',
    'lissom_or'   :'lissom_or.ty',
    'lissom_oo_or':'lissom_oo_or.ty',
    'som_retinotopy':'som_retinotopy.ty',
    'trickysyntax':'hierarchical.ty',
    'obermayer_pnas90':'obermayer_pnas90.ty',
    'lissom_fsa':'lissom_fsa.ty',
    'gcal':'gcal.ty',
    'lissom_oo_or_10000.typ':'lissom_oo_or.ty',
    'lissom_fsa_10000.typ':'obermayer_pnas90.ty',
    'obermayer_pnas90_40000.typ':'obermayer_pnas90.ty',
    'som_retinotopy_40000.typ':'som_retinotopy.ty',
    'gcal_10000.typ':'gcal.ty'}


def copy_examples():
# topographica -c "from topo.misc.genexamples import copy_examples; copy_examples()"
    examples = find_examples()
    locn = os.path.join(param.normalize_path.prefix,"examples")
    if os.path.exists(locn):
        print "%s already exists; delete or rename it if you want to re-copy the examples."%locn
        return
    else:
        print "Creating %s"%locn
        import shutil
        print "Copying %s to %s"%(examples,locn)
        shutil.copytree(examples,locn)


def print_examples_dir(**kw):
    examples = find_examples(**kw)
    if examples:
        print "Found examples in %s"%examples

def find_examples(specified_examples=None,dirs=None):
    import topo

    if not specified_examples:
        # CEBALERT: hack!
        specified_examples = ["hierarchical","som_retinotopy"]


    if not dirs:
        # CEBALERT: is there any significance to the order? E.g. if I have ~/Documents/Topographica/examples
        # from an installation, will my development copy in ~/topographica-git still find its examples in
        # ~/topographica-git/examples ?
        candidate_example_dirs = [
            # CEBALERT: ~/topographica/examples is out of date. I just
            # added the line below without testing it or removing the
            # ~/topographica line.
            param.normalize_path.prefix,
            os.path.join(os.path.expanduser("~"),'topographica/examples'),
            # version-controlled topographica dir
            os.path.join(topo._package_path,"../examples"),
            # debian package
            os.path.join(topo._package_path,"../../../share/topographica/examples"),
            # setup.py package
            os.path.join(topo._package_path,"../../../../../share/topographica/examples"),
            os.path.join(topo._package_path,"../../../../share/topographica/examples"),
            # egg
            os.path.join(topo._package_path,"../share/topographica/examples"),
            # expected bdist_mpkg location...
            "/usr/local/share/topographica/examples",
            # ...but actually this; not sure why
            "/usr/local/share/share/topographica/examples"]
    else:
        candidate_example_dirs = dirs

    ced = [os.path.normpath(d) for d in candidate_example_dirs]
    candidate_example_dirs = ced
    # CEBALERT: horrible way to find directory that contains all the
    # examples specified.
    examples = None
    for d in candidate_example_dirs:
        if not examples:
            for cmd in specified_examples:
                if os.path.isfile(os.path.join(d,scripts[cmd])):
                    examples = d
                else:
                    examples = False

                if examples is False:
                    break

    return examples


# CEBALERT: should be rewritten!

def _stuff(specified_targets):

    # shortcuts for executing multiple targets
    group_targets = dict( all_quick=["hierarchical","som_retinotopy","lissom_oo_or"],
                          all_long=["lissom_oo_or_10000.typ","som_retinotopy_40000.typ",
                                    "lissom_or_10000.typ","lissom_fsa_10000.typ"],
                          saved_examples=["lissom_oo_or_10000.typ"])

    ### Create the list of commands to execute either by getting the
    ### command labels from a target, or by inserting the command label
    # CB: I don't know any string methods; I'm sure this can
    # be simplified!
    command_labels=[]


    for a in specified_targets:
        if a in group_targets:
            command_labels+=group_targets[a]
        else:
            command_labels.append(a)

    examples = find_examples(specified_examples=command_labels)

    if not examples:
        raise IOError("Could not find examples.")
    else:
        print "Found examples in %s"%examples

    # CB: so much repeated typing...

    available_targets = {
        "hierarchical":   run(examples,scripts["hierarchical"],density=4),
        "lissom_or":      run(examples,scripts["lissom_or"],density=4),
        "lissom_oo_or":   run(examples,scripts["lissom_oo_or"],density=4),
        "som_retinotopy": run(examples,scripts["som_retinotopy"],density=4),

        "trickysyntax":run(examples,scripts["hierarchical"],commands=["topo.sim.run(1)",
                                                       "print 'printing a string'"]),

        "lissom_oo_or_10000.typ":run(examples,scripts["lissom_oo_or"],
                                     commands=["from topo.misc.ipython import RunProgress",
                                               "RunProgress(label=None)(10000)",
                                               or_analysis(),
                                               snapshot("lissom_oo_or_10000.typ")]),


        "lissom_or_10000.typ":run(examples,scripts["lissom_or"],
                                  commands=["from topo.misc.ipython import RunProgress",
                                            "RunProgress(label=None)(10000)",
                                            or_analysis(),
                                            snapshot("lissom_or_10000.typ")]),

        "lissom_fsa_10000.typ":run(examples,scripts["lissom_fsa"],
                                   commands=["from topo.misc.ipython import RunProgress",
                                             "RunProgress(label=None)(10000)",
                                             snapshot("lissom_fsa_10000.typ")]),

        "obermayer_pnas90_40000.typ":run(examples,scripts["obermayer_pnas90"],
                                         commands=["from topo.misc.ipython import RunProgress",
                                                   "RunProgress(label=None)(40000)",
                                                   or_analysis(),
                                                   snapshot("obermayer_pnas90_30000.typ")]),

        "som_retinotopy_40000.typ":run(examples,scripts["som_retinotopy"],
                                       commands=["from topo.misc.ipython import RunProgress",
                                                 "RunProgress(label=None)(40000)",
                                                 retinotopy_analysis(),
                                                 snapshot("som_retinotopy_40000.typ")]),

        "gcal_10000.typ":run(examples,scripts["gcal"],
                             commands=["from topo.misc.ipython import RunProgress",
                                       "RunProgress(label=None)(10000)",
                                       or_analysis(),
                                       snapshot("gcal_10000.typ")])
        }

    return command_labels,available_targets


class generate(param.ParameterizedFunction):

    targets = param.List(default=['all_quick'])

    def __call__(self,**params):
        p = ParamOverrides(self,params)

        command_labels,available_targets = _stuff(p.targets)
        for cmd in command_labels:
            c = available_targets[cmd]
            print c
            system(c)

