"""Generates ReST for the Reference Manual pages"""

import os, sys

path = ["external/imagen", "external/lancet", "external/param", "external/paramtk", "topo"]
for p in path: sys.path.insert(0, os.path.abspath(os.path.join("..", p)))
sys.path.insert(0, os.path.abspath(".."))

refman = "Reference_Manual"

module_template = """\
***************
__module_name__
***************

.. inheritance-diagram:: __module_name__

__submodules__

Module
======

.. automodule:: __module_name__
   :members:
   :show-inheritance:
"""

def submodules(module, modules):
    ms = []
    for m in modules:
        if m != module and m[:len(module+".")] == module+".":
            ms.extend([m])
    return ms


def analyse_modules(module_path):
    modules = []
    classes = []
    for dirpath, dirnames, filenames in os.walk((os.path.join("..", module_path))):
        for filename in filenames:
            if filename[-3:] == ".py" and filename != "setup.py":
                filename = filename[:-3]
            if dirpath[:len("../external")] == "../external":
                dirpath = dirpath[len(module_path)+1:]
            if filename == "__init__":
                filename = ""
            modules.extend([str.replace(os.path.join(dirpath[3:], filename).rstrip("/"), "/", ".")])
    return (modules, classes)

def generate_module_rst(module, submodules):
    text = str.replace(module_template, "__module_name__", module)
    sub_text = ""
    if submodules:
        sub_text = """\
Submodules
==========
"""
        for submodule in submodules:
            sub_text += "* `%s <%s-module.html>`_\n" % (submodule, submodule)
    text = str.replace(text, "__submodules__", sub_text)
    with open(os.path.join(refman, module + "-module.rst"), "w") as f:
        f.write(text)

if __name__ == "__main__":
    modules = []
    classes = []
    for module in path:
        (m, c) = analyse_modules(module)
        modules.extend(m)
        classes.extend(c)
    for m in modules:
        generate_module_rst(m, submodules(m, modules))
