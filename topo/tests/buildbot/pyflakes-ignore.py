#!/usr/bin/env python

# modified version of pyflakes.scripts.pyflakes
# ignores lines with pyflakes:ignore

"""
Implementation of the command-line I{pyflakes} tool.
"""

import optparse
import sys
import os
import _ast
import re

from pyflakes import checker

ignore_re = re.compile(
                r"""
                ^
                .*
                \#
                .*
                pyflakes:ignore
                .*
                $
                """, re.VERBOSE)

ignored_paths = []

def ignored(path):
    for ignored_path in ignored_paths:
        if os.path.normpath(commonprefix(ignored_path, path)) == \
                os.path.normpath(ignored_path):
                    return True
    return False

# path handling functions below from:
# http://code.activestate.com/recipes/577016-path-entire-split-commonprefix/

def isplit(path):
    "Generator splitting a path"
    dirname, basename = os.path.split(path)
    if path == dirname:
        # stop recursivity
        yield path
    elif dirname:
        # continue recursivity
        for i in isplit(dirname):
            yield i
    if basename:
        # return tail
        yield basename

def join(iterable):
    """Join iterable's items as a path string

    >>> join(('a', 'b')) == os.path.join('a', 'b')
    True
    """
    items = tuple(iterable)
    if not items:
        return ''
    return os.path.join(*items)

def split(path):
    """Return the folder list of the given path

    >>> split(os.path.join('a', 'b'))
    ('a', 'b')
    """
    return tuple(isplit(path))

def commonprefix(*paths):
    """Return the common prefix path of the given paths

    >>> commonprefix(os.path.join('a', 'c'), os.path.join('a', 'b'))
    'a'
    """
    paths = map(split, paths)
    if not paths: return ''
    p1 = min(paths)
    p2 = max(paths)
    for i, c in enumerate(p1):
        if c != p2[i]:
            return join(p1[:i])
    return join(p1)

def check(codeString, filename):
    """
    Check the Python source given by C{codeString} for flakes.

    @param codeString: The Python source to check.
    @type codeString: C{str}

    @param filename: The name of the file the source came from, used to report
        errors.
    @type filename: C{str}

    @return: The number of warnings emitted.
    @rtype: C{int}
    """
    # First, compile into an AST and handle syntax errors.
    try:
        tree = compile(codeString, filename, "exec", _ast.PyCF_ONLY_AST)
    except SyntaxError, value:
        msg = value.args[0]

        (lineno, offset, text) = value.lineno, value.offset, value.text

        # If there's an encoding problem with the file, the text is None.
        if text is None:
            # Avoid using msg, since for the only known case, it contains a
            # bogus message that claims the encoding the file declared was
            # unknown.
            print >> sys.stderr, "%s: problem decoding source" % (filename, )
        else:
            line = text.splitlines()[-1]

            if offset is not None:
                offset = offset - (len(text) - len(line))

            print >> sys.stderr, '%s:%d: %s' % (filename, lineno, msg)
            print >> sys.stderr, line

            if offset is not None:
                print >> sys.stderr, " " * offset, "^"

        return 1
    else:
        # Okay, it's syntactically valid.  Now check it.
        lines = codeString.split("\n")
        w = checker.Checker(tree, filename)
        w.messages.sort(lambda a, b: cmp(a.lineno, b.lineno))
        non_ignored_messages = 0
        for warning in w.messages:
            if 'redefinition of unused' in str(warning):
                if filename.split(os.path.sep)[1] == 'submodel':
                    print "IGNORED: " + str(warning)
                    continue
            if not ignore_re.match(lines[warning.lineno - 1]):
                print warning
                non_ignored_messages += 1
        return non_ignored_messages


def checkPath(filename):
    """
    Check the given path, printing out any warnings detected.

    @return: the number of warnings printed
    """
    try:
        return check(file(filename, 'U').read() + '\n', filename)
    except IOError, msg:
        print >> sys.stderr, "%s: %s" % (filename, msg.args[1])
        return 1


def main(args, print_totals=False):
    warnings = 0
    if args:
        for arg in args:
            if os.path.isdir(arg):
                for dirpath, dirnames, filenames in os.walk(arg):
                    for filename in filenames:
                        if filename.endswith('.py'):
                            path = os.path.join(dirpath, filename)
                            if not ignored(path):
                                warnings += checkPath(path)
            else:
                warnings += checkPath(arg)
    else:
        warnings += check(sys.stdin.read(), '<stdin>')

    if print_totals:
        print "Pyflakes issues found: %s" % warnings

    raise SystemExit(warnings > 0)

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option("--ignore", dest="ignore", action="append",
            help="Path prefixes to ignore")
    parser.add_option("--totals", dest="totals", action="store_true",
            help="Print total number of warnings")
    options, args = parser.parse_args()
    ignored_paths = options.ignore if options.ignore else []
    main(args, options.totals)
