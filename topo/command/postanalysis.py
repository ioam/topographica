"""
User-level analysis commands, typically for processing existing SheetViews.

Most of this file consists of commands that accept SheetViews as
input, process the data in these SheetViews to create new SheetViews
with the analysed data.

For instance, the temporal_measurement command take a measurement
command as input, uses it to generate SheetViews over time which it
collapses into a new spatiotemporal SheetView with the name of the
original sheetviews prefixed by 'ST'.

Some of the commands are ordinary Python functions, but the rest are
ParameterizedFunctions, which act like Python functions but support
Parameters with defaults, bounds, inheritance, etc.  These commands
are usually grouped together using inheritance so that they share a
set of parameters and some code, and only the bits that are specific
to that particular plot or analysis appear below.  See the
superclasses for the rest of the parameters and code.
"""

import math
import time
import param
import topo
from topo.base.sheet import Sheet
 # For backward compatibility. Would be nice to generate a depracation warning.
from topo.command.analysis import *
from topo.command.analysis import Feature  # Why is this not handled by *?


class temporal_measurement(param.Parameterized):
    """
    Initialize using: temporal_measurement(<measurement command>, <steps>)
    Run by calling with arguments for the supplied <measurement command>.
    """

    measurement_command = param.Parameter( default=None, doc="""
         The measurement command that will be called to generate
         SheetViews over time. Must not be instantiated and must be a
         subclass of PatternPresentingCommand.""")

    prefix = param.String(default='Temporal', doc="""
        The prefix given to the SheetViews that are generated over
        time. If collapse_views is True, the sheetviews with this
        prefix are collapsed into a single sheetview starting with
        this prefix.""")


    duration = param.Number(default=100, doc="""
       The duration over which the measurement is to be repeated.""")

    time_density = param.Number(default=1.0, doc="""
       The interval that elapses between measurements.""")

    def __init__(self, measurement_command, duration, **kwargs):

        super(temporal_measurement, self).__init__(measurement_command=measurement_command,
                                                      duration=duration, **kwargs)
        self._prefix_map = {}
        self._padding = None
        self._unique_prefix = None

    def __call__(self, *args, **kwargs):
        """
        Run the specified measurement_command over time using the
        *args and **kwargs specified.
        """
        self._unique_prefix = '%d_' % int(time.time())
        if not issubclass(self.measurement_command, PatternPresentingCommand):
            raise ValueError('A PatternPresentingCommand Class is required.')

        steps = int(math.floor(self.duration / self.time_density))
        self._padding = len(str(steps))
        self._prefix_map = {}

        topo.sim.run(0.0)
        prefix_formatter = (self._unique_prefix + '%%0%dd_') % self._padding

        original_prefix = self.measurement_command.sheet_views_prefix
        topo.sim.state_push()

        for step in range(steps):
            timestamped_prefix = prefix_formatter % step
            self.measurement_command.sheet_views_prefix = timestamped_prefix
            step_duration = topo.sim.convert_to_time_type(self.time_density)
            timestamp = step * step_duration
            self._prefix_map[timestamped_prefix] = timestamp

            if self.measurement_command is measure_response:
                self.measurement_command.duration = step_duration
                self.measurement_command.instance()(*args, **dict(kwargs, restore_state=False, restore_events=False))
            else:
                self.measurement_command.duration = timestamp
                self.measurement_command.instance()(*args, **kwargs)

        topo.sim.state_pop()
        self.measurement_command.sheet_views_prefix = original_prefix
        self._collapse_views()


    def _collapse_views(self):
        """
        Collapses the timestamped SheetViews into a single SheetView
        with the specified prefix.
        """
        sheets = [s for s in topo.sim.objects(Sheet).values() if hasattr(s, 'sheet_views')]
        for sheet in sheets:
            # Filter out keys that are tuples (e.g. RFs and CFs)
            viewnames = [k for k in sheet.sheet_views.keys() if isinstance(k, str)]
            sorted_keys = sorted(self._prefix_map.keys())
            # All the sheetviews that have been automatically prefixed
            prefixed_names = [name for name in viewnames if any(name.startswith(k) for k in sorted_keys)]

            striplen = len(self._unique_prefix) + self._padding + 1
            basenames = set(name[striplen:] for name in prefixed_names)
            # Some measurements generate many SheetViews.
            for basename in basenames:
                filtered_names = [name for name in prefixed_names if name.endswith(basename)]
                views = [sheet.sheet_views.pop(name) for name in filtered_names]
                collapsed_view = views[0]

                for name,view in zip(filtered_names[1:], views[1:]):
                    timestamp = self._prefix_map[name[:striplen]]
                    data = view.view()[0]
                    collapsed_view.record(data, timestamp)

                sheet.sheet_views[self.prefix+basename] = collapsed_view
