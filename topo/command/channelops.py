from topo.command.plots import Plot
import matplotlib as mpl
import matplotlib.pyplot as plt
import param
import numpy as np

from topo.base.sheetview import SheetView


class ChannelOp(param.Parameterized):

    input_mode = param.String(default='RGB')

    output_mode = param.String(default='RGB')

    # norm and cmap??

    def __init__(self, **kwargs):

        super(ChannelOp, self).__init__(**kwargs)
        self.transforms = []

    def _check_shape(self, arr):
        if self.input_mode in ['RGB', 'HSV']:
            if (arr.ndim != 3) and arr.shape[-1] != 3:
                raise Exception('Input array needs hue, saturation and value channels')
        if self.input_mode == 'P':
            if arr.ndim != 2:
                raise Exception('Input array must have exactly two dimensions')

    def __call__(self, arr, arrays=None):
        intermediate = arr
        for transform in self.transforms:
            intermediate = transform(intermediate, arrays)

        return intermediate

    def __rshift__(self, other):
        if self.output_mode != other.input_mode:
            raise Exception("Incompatible modes")
        transform = ChannelOp()
        transform.transforms= self.transforms + other.transforms

        transform.input_mode = self.input_mode
        transform.output_mode = other.output_mode
        return transform

class HSV_to_RGB(ChannelOp):

    input_mode = param.String(default='HSV')

    output_mode = param.String(default='RGB')

    def __init__(self, **kwargs):
        super(HSV_to_RGB, self).__init__(**kwargs)
        self.transforms = [self]

    def __call__(self, arr, arrays=None):
        self._check_shape(arr)
        return mpl.colors.hsv_to_rgb(arr)



class HSVSelectivity(ChannelOp):
    """ For white/black selectivity """
    pass


class Normalize(ChannelOp):

    input_mode = param.String(default='P')

    output_mode = param.String(default='P')

    maximum = param.Number(default=1.0)

    def __init__(self, **kwargs):
        super(Normalize, self).__init__(**kwargs)
        self.transforms = [self]
        self.max = None

    def __call__(self, arr, arrays=None):
        self._check_shape(arr)
        if not arrays:
            raise Exception('No data for normalization')
        if self.max is None:
            self.max = np.max([el.max() for el in arrays])

        return self.maximum * (arr / self.max) if (self.max != 0.0) else arr

class RGB_to_HSV(ChannelOp):

    input_mode = param.String(default='RGB')

    output_mode = param.String(default='HSV')

    def __init__(self, **kwargs):
        super(RGB_to_HSV, self).__init__(**kwargs)
        self.transforms = [self]

    def __call__(self, arr,arrays=None):
        self._check_shape(arr)
        return mpl.colors.rgb_to_hsv(arr)

class P_to_RGB(ChannelOp):

    input_mode = param.String(default='P')

    cmap= param.Parameter(default=mpl.cm.hsv)

    def __init__(self, **kwargs):
        super(P_to_RGB, self).__init__(**kwargs)
        self.transforms = [self]

    def __call__(self, arr,arrays=None):
        self._check_shape(arr)
        return self.cmap(arr)[...,0:3]


def SHCPlot(channels, sheet_views, *args, **kwargs):

    channel_names = ['Hue', 'Strength', 'Confidence']
    sheetview_names = [channels.get(name, None) for name in channel_names]
    HSC = [sheet_views.get(svname, None) for svname in sheetview_names]

    hue, strength, confidence = HSC
    strength = 1.0 if strength is None else strength
    confidence = 1.0 if confidence is None else confidence
    hue = 0.0 if hue is None else hue

    [H, S, V] = [hue, confidence, strength]
    # If hue is 0.0, saturation should be disabled
    raise NotImplementedError
    return ChannelPlot([H, (S if H!=0.0 else 0.0), V])


class ChannelPlot(Plot):
    """
    By default behaves like an RGB plot.

    Allows scalars as well as sheetviews which are interpreted as a constant channel with the given value.

    Views that have been recorded over time must be of the same length.
    """

    transformation = param.ClassSelector(default=None, class_=ChannelOp, allow_None=True)

    input_mode = param.ObjectSelector(default='RGB', objects=['HSV', 'RGB', 'P'])

    show_axes = param.Boolean(default=True)

    colorbar = param.ObjectSelector(default='H', objects=['H','V', None], doc="""
         The style of the colorbar (if any) """)

    annotations = param.List(default=[], doc="""
         List of callable that allows the plot to be annotated,
         allowing markers or contours to be overlaid for example.""")

    def __init__(self, views, **kwargs):
        super(ChannelPlot, self).__init__(**kwargs)
        self._validate_views(views)
        self._annotation_labels = {}
        self.RGB_arrays = self._get_RGB_arrays(views) # List of MxNx3 RGB arrays
        self.max_frames = len(self.RGB_arrays)

    def _get_RGB_arrays(self, views):

        if len(views) == 1: # Palette mode: it is the job of the transformation to convert to RGB.
            view = views[0]
            l,b,r,t = view.bounds.lbrt()
            self._annotation_labels['lbrt'] = (l,b,r,t)
            self.extent = [l,r,b,t]
            values = view[:].values()
            RGB_arrays = [self.transformation(val, values) for val in values]


            # IDEA: DON'T ENFORCE OUTPUT TO 'RGB'!

            # THEN WE KNOW THE MODE! IF P (palette -> get cmap/norm). IF HSV, then HSV cmap.
            # colorbar cannot makes sense if truly RGB.
            return RGB_arrays

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

        data = self.RGB_arrays[frame]
        im = ax.imshow(data, extent=self.extent, interpolation='nearest')
        self._handles['image'] = im

        if self.colorbar is not None:
            plt.colorbar(im, ax=ax, orientation='horizontal' if self.colorbar =='H' else 'vertical')
        else:
            plt.tight_layout()

        self.update_frame(frame)

        if not axis: plt.close(self._figure)
        return ax if axis else self._figure

    def update_frame(self, n):
        n = n  if n < self.max_frames else self.max_frames
        data = self.RGB_arrays[n]
        im = self._handles['image']
        im.set_data(data)

    def _validate_views(self, views):

        if self.input_mode == 'P' and len(views)!=1:
            raise Exception('Only a single SheetView may be supplied if input in palette mode.')

        if self.input_mode == 'P' and not isinstance(views[0],SheetView):
            raise Exception('Cannot accept scalar value channel in palette mode.')

        if self.input_mode in ['RGB', 'HSV'] and len(views) != 3:
            raise Exception('Three SheetViews required for RGB and HSV input modes.')

        if (self.transformation is None) and self.input_mode != 'RGB':
            raise Exception('Input mode must be RGB if no color transform object is supplied.')

        if self.transformation and self.transformation.input_mode != self.input_mode:
            raise Exception('Input mode of color transform does not match declared input mode.')

        if self.transformation and self.transformation.output_mode != 'RGB':
            raise Exception('The supplied color transform must have RGB output.')
