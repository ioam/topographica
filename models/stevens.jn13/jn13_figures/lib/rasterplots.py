"""
Rasterplots

Utilities for raster image manipulation (e.g. OR maps) using
PIL/Pillow and Numpy. Used for visualizing orientation maps (with and
without selectivity), polar FFT spectra and afferent model weight
patterns.
"""

import Image
import ImageOps
import numpy as np
import colorsys

rgb_to_hsv = np.vectorize(colorsys.rgb_to_hsv)
hsv_to_rgb = np.vectorize(colorsys.hsv_to_rgb)


def black_selectivity(image, whitelevel=0.2):
   """
   Makes zero selectivity black for publication. Swaps saturation and
   value and scales saturation by the whitelevel.
   """
   whitefactor = 1.0 / whitelevel  # 25% multiplies by 4.0
   image_rgba = image.convert('RGBA')
   arr = np.asarray(image_rgba).astype('float')

   r, g, b, a = np.rollaxis(arr, axis=-1)
   h, s, v = rgb_to_hsv(r, g, b)   # s is [0,1] all v are 255.0
   s *= (255.0 * whitefactor)
   r, g, b = hsv_to_rgb(h, (v / 255.0), np.clip(s, 0, 255.0))
   arr_stack = np.dstack((r, g, b, a))
   return Image.fromarray(arr_stack.astype('uint8'), 'RGBA')

def OR_map(preference, selectivity=None):
    """
    Supply the raw preference and (optionally) selectivity. Note that
    selectivity multiplier affects the raw selectivity data and is
    therefore automatically applied.
    """
    shape = preference.shape
    if selectivity is None:
        selectivity = np.ones(shape, dtype=np.float64)
    else:
        assert preference.shape == selectivity.shape, \
            "Preference and selectivity shapes must match."
    value = np.ones(shape, dtype=np.int64) * 255

    channels = (preference, selectivity, value)
    rgb_channels = hsv_to_rgb(*channels)
    arr_stack = np.dstack(rgb_channels)
    return Image.fromarray(arr_stack.astype('uint8'), 'RGB')

def greyscale(arr):
    """
    Converts a numpy 2D array of floats between 0.0 and 1.0 to a PIL
    greyscale image.
    """
    return Image.fromarray(np.uint8(arr*255))


def cf_image(cfs, coords, width=None, height=None, pos=(0,0), 
             size=26, border=5, bg=(0,0,0), colmap=None):
    """
    Returns a PIL image showing the selected connection fields (CFS)
    as supplied by extract_CFs. Does not support non-square CF
    shapes.

    'cfs' is an ndarray of N dstacked cfs, each of shape (X,X): (X,X,N)
    'coords' is an ndarray of N coordinates: (N,2)
    'width' and 'height' are either None (full) of integer grid sizes
    'pos' is the starting position of the block, (x,y)
    'size' and 'border' are the cf image size and the border size in pixels.
    'colmap' is an RGB array shape (N,M,3) with values between 0.0 and 1.0.
    """
    normalize = lambda arr: (arr - arr.min()) / (arr.max() - arr.min())
    cf_im = lambda cf, size: greyscale(normalize(cf)).resize((size,size), 
                                                             Image.NEAREST)
    (posx, posy) = pos
    (d1,d2) = zip(*coords)
    density = len(set(d1))
    assert density == len(set(d2)), "Not implemented for non-square sets"
    height = density if height is None else height
    width = density if width is None else width
    assert height>0 and width>0, "Height and width must be None or greater than zero"
    assert posx+width <= density, "X position and width greater than density"
    assert posy+height <= density, "Y position and width greater than density"
    # Functions mapping original coordinates onto consecutive grid indices
    fst_map =  dict(((ind,i) for (i,ind) in enumerate(sorted(set(d1)))))
    snd_map =  dict(((ind,i) for (i,ind) in enumerate(sorted(set(d2)))))
    # Generating a dictionary from the grid coordinates to the CF index
    mapped_coords = [(fst_map[fst],snd_map[snd]) for [fst,snd] in coords]
    indexed_coords = dict((coord,i) for (i, coord) in enumerate(mapped_coords))
    # Initialising the image
    imwidth = width*size+(width-1)*border
    imheight = height*size+(height-1)*border
    cf_block = Image.new('RGB', (imwidth, imheight), bg)

    # Building image row by row, top to bottom.
    for yind in range(height):
        for xind in range(width):
            # Swapped coordinate system
            cf_ind = indexed_coords[(yind+posy, xind+posx)]
            # Get color from the color map if available
            if colmap is not None:
                crd1, crd2 = coords[cf_ind]
                r,g,b = colmap[crd1, crd2, :]
                color = (r*255,g*255,b*255)
            else:
                color = (255, 255, 255)
            cf = cfs[:,:,cf_ind]
            (cf_dim1, cf_dim2) = cf.shape
            assert cf_dim1 == cf_dim2, "Only supports square CFs."
            cf_image = ImageOps.colorize(cf_im(cf, size), (0, 0, 0, 0), color)

            xoffset = xind*border
            yoffset = yind*border
            paste_coord = (xoffset+xind*size, yoffset+yind*size)
            cf_block.paste(cf_image, paste_coord)
    return cf_block


def resize(image, size, filter_type=Image.NEAREST):
    """
    Resizes the given image to the given size using the specified
    filter.  Default is box filter (no interpolation) appropriate for
    simulated orientation maps.
    """
    return image.resize(size, filter_type)


#########################
# DEPRACATION FUNCTIONS #
#########################



def greyscale_image(array2D, normalize=False, scale_factor=255):
    raise Exception("Use greyscale instead")

#########################
#########################
#########################
