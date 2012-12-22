"""
The versionator module provides version information and allows for easy
manipulation of version numbers.

If this copy of the code is not a release, but instead has been pulled
straight from the repo, it will use git to find out the (live) version
numbers. On the other hand, the version numbers are hardcoded if this is a
proper release.
"""

from subprocess import check_output

version = (0, 0, 0, 0)
release = 0
commit  = ""

def version_string(v):
    """
    Converts a version four-tuple to a string of the following format: vXX.YY.ZZ
    """
    return "v%d.%d.%d" % v[:3]

def comparable(v):
    """
    Convers a version four-tuple to a format that can be used to compare version numbers
    """
    return int("%02d%02d%02d%05d" % v)

if not release:
    git_output = check_output(["git", "describe"]).strip()
    (_version, count, commit) = git_output[1:].split("-")
    _version = _version.split(".")
    version = (int(_version[0]), int(_version[1]), int(_version[2]), int(count))
    release = comparable(version)
