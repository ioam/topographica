"""
Topographica IPython extension for notebook support. Load with:

%load_ext topo.misc.ipython
"""
import imagen.ipython
from PIL import Image
from StringIO import StringIO
import numpy as np
import base64
import param


class Display(param.Parameterized):

    default_width = param.Integer(default=256, doc="""
                   The default width of the image displayed""")

    named_widths = param.Dict(default={}, doc="""
             An explicit set of display sizes by object name.
             Only works for objects with a 'name' attribute.""")


    def __init__(self, array_fn):
        self.array_fn = array_fn

    def _greyscale_image(self, arr, scale_factor=255, zero_black=True):
        """
        Converts a 2D numpy array of floats (eg. float64) to a
        normalized PIL image (greyscale).

        If zero_black is False, the image output is black to white,
        regardless of the minimum value.  Otherwise, only the maximum
        value is white so the lowest image value may not be
        black. This means 100% black always represent zero.
        """
        min_arr = arr.min()
        value_range = (arr.max() - min_arr)
        if (value_range == 0):
            arr.fill(min_arr)
        elif zero_black:
            arr = arr / arr.max()
        else:
            arr = (arr - min_arr) / value_range

        return Image.fromarray(np.uint8(arr*scale_factor))

    def _scale_bar(self, length, aspect=10, border=2, horizontal=True):
        " Generates a scale bar of a given length "
        width = int(length / aspect)
        background_size = (width+(2*border), length+(2*border))
        key_im = Image.fromarray(np.uint8(np.zeros(background_size)))
        # The greyscale gradient
        greyscale_arr = np.tile(np.linspace(0.0,1.0, length), (width,1))
        if not horizontal: greyscale_arr.transpose()
        greyscale_im = Image.fromarray(np.uint8(greyscale_arr*255))
        # Paste into background.
        key_im.paste(greyscale_im, box=(border,border))
        return key_im


    def _html_table(self, arr, size,  minval, maxval,
                    horizontal=True, border=False, zero_black=True):
        " Generates the HTML table to be displayed "

        open_table = '<table style="border:0px;"><tr>'
        item_clear = '<td %s style=" border: 1px solid transparent; vertical-align : "middle""><center>%s</center></td>'
        item_border = '<td %s style=" vertical-align : "middle""><center>%s</center></td>'
        separator = "</tr><tr>"
        close_table = "</tr></table>"
        mono = '<code>%s</code>'  # Monospace
        item = item_border if border else item_clear

        # The main image
        raw_im = self._greyscale_image(arr, zero_black=zero_black)
        resized_im = raw_im.resize(size, Image.NEAREST)
        b64_img = self._base64_img(resized_im)
        image_item = item % ('colspan = "3"', b64_img)

        # The greyscale key (if not constant)
        if minval == maxval:
            key_data = 'Constant value of %s' % minval
            key_items = [item % ('', el) for el in ['', key_data, '' ]]
            key_cell = ''.join(key_items)
        else:
            length = (size[1] - 20) if horizontal else (size[0] - 20)
            length = length if (length > 50) else 50
            scale_bar = self._scale_bar(length, horizontal=horizontal)
            b64_img_key = self._base64_img(scale_bar)
            (minstr, maxstr) = (' %.3g ' % minval, ' %.3g ' % maxval)
            if zero_black: minstr = '0.0'
            maxlen = max([len(minstr), len(maxstr)])
            key_items =  [mono % minstr.rjust(maxlen), b64_img_key, mono % maxstr.ljust(maxlen)]
            key_cell =  ''.join([item % ('', el) for el in key_items])

        return open_table + image_item + separator + key_cell + close_table


    def _base64_img(self, im):
        f = StringIO()
        im.save(f, format='png')
        f.seek(0)
        prefix = 'data:image/png;base64,'
        b64 = prefix+base64.encodestring(f.read())
        return '<img src="%s" />' % b64

    def __call__(self, obj):

        arr = self.array_fn(obj)
        (dim1, dim2 ) = arr.shape
        width = self.named_widths.get(getattr(obj,'name',None), self.default_width)
        array_aspect = float(width)/dim1
        size = (int(array_aspect*dim2), width)
        return self._html_table(arr, size,  arr.min(), arr.max())


def _get_activity(sheet_or_projection):
    return sheet_or_projection.activity

def _get_weights(cf):
    return np.array(cf.weights)


sheet_display = Display(_get_activity)
projection_display = Display(_get_activity)
cf_display = Display(_get_weights)

_loaded = False
def load_ipython_extension(ip):
    # Load Imagen's IPython extension
    imagen.ipython.load_ipython_extension(ip)

    global _loaded
    if not _loaded:
        _loaded = True
        html_formatter = ip.display_formatter.formatters['text/html']

        html_formatter.for_type_by_name('topo.base.sheet', 'Sheet', sheet_display)
        html_formatter.for_type_by_name('topo.base.projection', 'Projection', projection_display)
        html_formatter.for_type_by_name('topo.base.cf', 'ConnectionField', cf_display)
