import bz2
import os
import re
from collections import defaultdict
from contextlib import closing

import matplotlib
import matplotlib.ticker
import matplotlib.pyplot

tests_to_plot = [
    "examples/lissom.ty",
    "examples/gcal.ty",
]

cpu_lower_bound = 98

stats_dir = "/var/lib/buildbot/master/performance"
stats_file = os.path.join(stats_dir, "{0}-log-shell_1-stdio.bz2")
svn_rev_file = os.path.join(stats_dir, "{0}-log-svn-stdio.bz2")

output_dir = "/var/lib/buildbot/master/public_html/p"
output_filename = "performance_plot.png"

_runtime_re = re.compile(
                r"""
                ^
                \[
                ([^\]]+)
                \]
                \s+
                Before:\ [^\s]+\ s
                \s+
                Now:\ ([^\s]+)\ s
                \s+
                \([^)]*\)
                $
                """, re.VERBOSE)

_cpu_re = re.compile(
            r"""
            ^
            .*
            \s+
            ([0-9]+)
            %CPU
            .*
            $
            """, re.VERBOSE)

_svn_re = re.compile(
            r"""
            ^
            .*
            (?:At|Updated\ to|Checked\ out)\ revision\ ([0-9]+)\.
            $
            """, re.VERBOSE)

def find_performance_stats(f):
    for line in f:
        match = _runtime_re.match(line)
        if match:
            path, duration = match.groups()
            # the next line might not always be the one with the cpu usage
            for next_line in f:
                cpu_match = _cpu_re.match(next_line)
                if cpu_match:
                    cpu, = cpu_match.groups()
                    yield path, float(duration), int(cpu)
                    break

def filter_stats(stats, tests):
    for stat in stats:
        stat_test, stat_duration, stat_cpu = stat
        for test in tests:
            if stat_test.endswith(test):
                if stat_cpu >= cpu_lower_bound:
                    yield test, stat_duration
                break

def get_svn_rev(f):
    for line in f:
        match = _svn_re.match(line)
        if match:
            return int(match.groups()[0])
    raise Exception

def get_stats(f):
    return dict(filter_stats(find_performance_stats(f), tests_to_plot))

def find_builds():
    builds = []
    for file in os.listdir(stats_dir):
        try:
            build = int(file)
            builds.append(build)
        except ValueError:
            pass
    builds.sort()
    return builds

def get_all_stats():
    build_stats = {}
    for build in find_builds():
        try:
            with closing(bz2.BZ2File(svn_rev_file.format(build))) as svn_rev_f:
                svn_rev = get_svn_rev(svn_rev_f)
        except IOError:
            continue
        try:
            with closing(bz2.BZ2File(stats_file.format(build))) as stats_f:
                stats = get_stats(stats_f)
        except IOError:
            continue
        build_stats[svn_rev] = stats
    return build_stats

def transpose(x):
    return zip(*x)

def plot_stats(stats):
    # flatten stats
    test_results = defaultdict(list)
    for svn_rev, results in sorted(stats.iteritems()):
        for test, duration in results.iteritems():
            test_results[test].append((svn_rev, duration))

    # plot
    fig = matplotlib.pyplot.figure()

    ax = fig.add_subplot(111)

    # disable scientific notation on svn revisions
    ax.xaxis.set_major_formatter(matplotlib.pyplot.FormatStrFormatter("%d"))

    for test in test_results:
        svn_revs, durations = transpose(test_results[test])
        ax.plot(svn_revs, durations, label=test)

    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    output_path = os.path.join(output_dir, output_filename)
    matplotlib.pyplot.savefig(output_path)

def main():
    plot_stats(get_all_stats())

if __name__ == '__main__':
    main()
