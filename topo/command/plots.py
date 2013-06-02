import matplotlib.pyplot as plt
from matplotlib import animation

import param
from imagen import SheetCoordinateSystem


from functools import partial

class annotations(object):

    @staticmethod
    def markers(**kwargs):
        def _markers(ax, labels, coords=[(0,0)], marker_style='wo'):
            for (x,y) in coords:
                ax.plot(x,y, marker_style)
        return partial(_markers, **kwargs)

    @staticmethod
    def label(**kwargs):

        def _label(ax, labels, hpos='left', vpos='top',
                               halign='left', valign='top',
                               text='', color='w', fontsize=20):
            posmap = dict(zip(['left', 'bottom', 'right', 'top'], labels['lbrt']))
            ax.text(posmap[hpos],posmap[vpos], text,
                    color=color, fontsize=fontsize,
                    horizontalalignment= halign,
                    verticalalignment= valign)

        return partial(_label, **kwargs)


class Plot(param.Parameterized):

    size = param.NumericTuple(default=(5,5))

    precedence = param.Number(default=0.5)

    def __init__(self, *args, **kwargs):
        super(Plot, self).__init__(**kwargs)
        self.max_frames = None  # Make into a parameter
        self._figure = None
        self._handles = {}

    def label(self):
        return self.__class__.__name__

    def __lt__(self, other):
        if self.precedence < other.precedence:
            return True
        else:
            return False

    def _setup(self, views):
        """
        Method to process the input dataviews before visualization.
        """
        raise NotImplementedError

    def fig(self, frame=0, ax=False):
        """
        Method to return a matplotlib figure at the given frame (if
        specified).
        """
        raise NotImplementedError

    def update_frame(self, n):
        """
        Set the plot(s) to the given frame number.
        Works by manipulating the objects held in _handles
        """
        raise NotImplementedError

    def anim(self, start=0, stop=None, fps=30):
        """
        Method that returns a Matplotlib animation.
        The start and stop frames may be specified.
        """
        self.fig()
        frames = range(self.max_frames)[slice(start, stop, 1)]
        anim = animation.FuncAnimation(self._figure, self.update_frame,
                                       frames=frames, interval = 1000.0/fps)
        # Close the figure handle
        plt.close(self._figure)
        return anim

    def __call__(self, *args, **kwargs):
        """
        Call to return a matplotlib figure or an animation as
        appropriate.
        """
        if self.max_frames > 1:
            return self.anim(*args, **kwargs)
        else:
            return self.fig()

    def __add__(self, other):
        return SubPlots(self).concat(other)

    def __div__(self, other):
        return SubPlots(self).stack(other)


class SubPlots(Plot):

    @classmethod
    def grid(cls, grid,transpose=False):
        """
        Plots a grid layout which consist of a list of rows where each
        row is a list of plots, each of which may be a plot or None.
        """

        grid = [list(el) for el in zip(*grid)] if transpose else grid

        rowplots = []
        for rowlist in grid:
            rowplot = SubPlots(rowlist[0])
            for col in rowlist[1:]:
                rowplot.concat(col)
            rowplots.append(rowplot)

        gridplot= rowplots[0]
        for row in rowplots[1:]:
            gridplot.stack(row)
        return gridplot

    def __init__(self, plot=None):
        self.max_frames = 0
        self._subplots = [] # The subplot objects

        # Keeping track of the active row's width and height and col number
        self._last_row_width = 0
        self._last_row_height = 0
        self._last_col_num = 0

        # The total number of rows and columns
        self.numrows, self.numcols = 1, 1
        self.width, self.height = 0,0
        if plot: self.concat(plot)

    def fig(self, frame=0, ax=False):
        """
        Method to return a matplotlib figure at the given frame (if
        specified).
        """
        fig = plt.figure()
        fig.set_size_inches((self.width,self.height))
        for (i,subplot) in enumerate(self._subplots):
            if subplot is None: continue
            ax = plt.subplot(self.numrows,self.numcols,i+1)
            subplot.fig(axis=ax)
        self._figure = fig
        self.update_frame(frame)

    def update_frame(self, n):
        """
        Set the plot(s) to the given frame number.
        Works by manipulating the objects held in _handles
        """
        for subplot in self._subplots:
            subplot.update_frame(n)

    def concat(self, plot):  # plot may be another plotgrid or None

        subplots = plot._subplots if isinstance(plot, SubPlots) else [plot]

        # If initializing a new subplot, we need to initialize the width.
        if self._subplots == []:
            self.width = max(subplot.size[0] for subplot in subplots)

        self._subplots.extend(subplots)

        # Recomputing overall figure width and height
        extra_width = sum(subplot.size[0] for subplot in subplots)
        max_height = max(subplot.size[1] for subplot in subplots)
        self.height = max(max_height, self._last_row_height)

        self._last_row_width += extra_width
        if (self._last_row_width > self.width):
            self.width = self._last_row_width

        self._last_col_num += len(subplots)
        if self._last_col_num > self.numcols:
            self.numcols =self._last_col_num

        self._update_max_frames()
        return self

    def _update_max_frames(self):
        max_frames = max(subplot.max_frames for subplot in self._subplots)
        self.max_frames = max_frames if max_frames > self.max_frames else self.max_frames

    def stack(self, plot):
        subplots = plot._subplots if isinstance(plot, SubPlots) else [plot]
        # Finishing off last row byt padding with None if necessary
        empty_cols = self._last_col_num - self.numcols
        if empty_cols > 0: self._subplots += [None]*empty_cols
        self._subplots.extend(subplots)

        # New row: height must be incremented by the maximum height of the plots added
        self.height += max(subplot.size[1] for subplot in subplots)
        # New row: reset active row and column number. Increment numrows.
        self._last_col_num, self._last_row_width = 0,0
        self.numrows += 1

        self._update_max_frames()
        return self

class matrixplot(Plot):

    show_axes = param.Boolean(default=True)

    colorbar = param.ObjectSelector(default='H', objects=['H','V', None], doc="""
         The style of the colorbar (if any) """)

    annotations = param.List(default=[], doc="""
         List of callable that allows the plot to be annotated,
         allowing markers or contours to be overlaid for example.""")

    def __init__(self, view, **kwargs):
        super(matrixplot, self).__init__(**kwargs)
        self._annotation_labels = {}
        self._setup(view)


    def _setup(self, view):
        self.odict = view[:]
        self.cmap = 'hsv' if view.cyclic else 'gray'

        self._normalization = max(v.max() for v in self.odict.values())
        self.max_frames = len(self.odict)
        self.key_map = dict(enumerate(self.odict.keys()))
        l,b,r,t = view.bounds.lbrt()
        self._annotation_labels['lbrt'] = (l,b,r,t)
        self.extent = [l,r,b,t]

    def _initialize(self):
        fig = plt.figure()
        fig.set_size_inches(list(self.size))
        self._figure = fig
        ax = fig.add_subplot(111)
        ax.set_aspect('equal')
        if not self.show_axes:
            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)
        return ax

    def fig(self, frame=0, axis=None):
        ax = axis if axis else self._initialize()

        for annotation in self.annotations:
            annotation(ax, self._annotation_labels)


        data = self.odict[self.key_map[frame]]
        im = ax.imshow(data, extent=self.extent,
                       cmap=self.cmap, interpolation='nearest')

        if self._normalization != 0.0:
            im.set_clim([0.0, self._normalization])
        self._handles['image'] = im

        if self.colorbar is not None and (self._normalization != 0.0):
            plt.colorbar(im, ax=ax, orientation='horizontal' if self.colorbar =='H' else 'vertical')
        else:
            plt.tight_layout()

        self.update_frame(frame)

        if not axis: plt.close(self._figure)
        return ax if axis else self._figure

    def update_frame(self, n):
        n = n  if n < self.max_frames else self.max_frames
        data = self.odict[self.key_map[n]]
        im = self._handles['image']
        im.set_data(data)
        #im.set_clim([data.min(),data.max()])
        if self._normalization != 0.0:
            im.set_clim([0.0, self._normalization])



class PSTHplot(Plot):

    coords = param.NumericTuple(default=(0,0))

    def __init__(self, activity, **kwargs):
        super(PSTHplot, self).__init__(**kwargs)
        self._setup(activity)

    def _initialize(self):
        fig = plt.figure()
        fig.set_size_inches(list(self.size))
        self._figure = fig
        return fig.add_subplot(111)


    def _setup(self, view):
        odict = view[:]
        self.max_frames = len(odict)
        key_map = dict(enumerate(odict.keys()))

        responses = []
        for array in view[:].values():
            (l,b,r,t) = view.bounds.lbrt()
            (dim1,dim2) = array.shape
            xdensity = dim1 / (r-l)
            ydensity = dim2 / (t-b)
            sc = SheetCoordinateSystem(view.bounds, xdensity,ydensity)
            (i,j) = sc.sheet2matrixidx(self.coords[0], self.coords[1])
            responses.append(array[i,j])

        self._responses = responses
        self._key_map = key_map

    def fig(self, frame=0, axis=None):
        """
        Figure or initial frame of the animation.
        """
        ax = axis if axis else self._initialize()
        plt.plot(self._key_map.values(), self._responses, lw=2)
        self._handles['vline'] = plt.axvline(0, color='r')
        self.update_frame(frame)
        if not axis: plt.close(self._figure)
        return ax if axis else self._figure

    def update_frame(self, n):
        n = n  if n < self.max_frames else self.max_frames
        xpos = self._key_map[n]
        self._handles['vline'].set_xdata([xpos, xpos])
