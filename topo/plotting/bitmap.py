"""
Topographica Bitmap Class.

Encapsulates the PIL Image class so that an input matrix can be displayed
as a bitmap image without needing to know about PIL proper.

There are three different base image Classes which inherit Bitmap:

PaletteBitmap  - 1 2D Matrix, 1 1D Color Map
HSVBitmap    - 3 2D Matrices, Color (H), Confidence (S), Strength (V)
RGBBitmap    - 3 2D Matrices, Red, Green, Blue Channels.

All maps are assumed to be on a nominal range of 0.0 to 1.0.  Matrices
are passed in as part of the constructor and the image is generaed.
For more information, see the documentation for each of the Bitmap
classes.

The encapsulated PIL Image is accessible through the .bitmap attribute.
"""

import os
import Image
import ImageDraw
import ImageFont
from colorsys import hsv_to_rgb
import numpy as np

import param
from param import resolve_path


# CEBALERT: can we just use load_default()? Do we even need TITLE_FONT
# at all?
try:
   import matplotlib
   _vera_path = resolve_path(os.path.join(matplotlib.__file__,'matplotlib/mpl-data/fonts/ttf/Vera.ttf'))
   TITLE_FONT = ImageFont.truetype(_vera_path,20)
except:
   TITLE_FONT = ImageFont.load_default()


### JCALERT: To do:
###        - Update the test file.
###        - Write PaletteBitmap when the Palette class is fixed
###        - Get rid of accessing function (copy, show...) (should we really?)


class Bitmap(param.Parameterized):
    """
    Wrapper class for the PIL Image class.

    The main purpose for this base class is to provide a consistent
    interface for defining bitmaps constructed in various different
    ways.  The resulting bitmap is a PIL Image object that can be
    accessed using the normal PIL interface.

    If subclasses use the _arrayToImage() function provided, any
    pixels larger than the maximum that can be displayed will
    be counted before they are clipped; these are stored in the
    clipped_pixels attribute.
    """
    clipped_pixels = 0

    def __init__(self,image):
        self.image = image


    def __copy__(self):
        # avoid calling __getstate__ for copy (not required)
        image = self.image.copy()
        return Bitmap(image)

    # CB: could define a __deepcopy__ too, but we don't need
    # deepcopy to be fast.

    def __getstate__(self):
        """
        Return the object's state (as in the superclass), but replace
        the 'image' attribute's Image with a string representation.
        """
        state = super(Bitmap,self).__getstate__()
        import StringIO
        f = StringIO.StringIO()
        image = state['image']
        image.save(f,format=image.format or 'TIFF') # format could be None (we should probably just not save in that case)
        state['image'] = f.getvalue()
        f.close()

        return state

    def __setstate__(self,state):
        """
        Load the object's state (as in the superclass), but replace
        the 'image' string with an actual Image object.
        """
        import StringIO
        state['image'] = Image.open(StringIO.StringIO(state['image']))
        super(Bitmap,self).__setstate__(state)


    def show(self):
        """
        Renaming of Image.show() for the Bitmap.bitmap attribute.
        """
        self.image.show()

    def width(self): return self.image.size[0]
    def height(self): return self.image.size[1]

    def zoom(self, factor):
        """
        Return a resized Image object, given the input 'factor'
        parameter.  1.0 is the same size, 2.0 is doubling the height
        and width, 0.5 is 1/2 the original size.  The original Image
        is not changed.
        """
        if factor%1==0:
            # CEBALERT: work around PIL bug (see SF #2820821) so that
            # integer scaling works in the typical case (where an
            # image is being enlarged).
            a = np.array(self.image).repeat(int(factor),axis=0).repeat(int(factor),axis=1)
            zoomed = Image.fromarray(a,mode=self.image.mode)
        else:
            x,y = self.image.size
            zx, zy = int(x*factor), int(y*factor)
            zoomed = self.image.resize((zx,zy))

        return zoomed


    # CEBALERT: Might be worthwhile simplifying this
    # method. E.g. Image.fromarray() now exists (PIL>=1.1.6), and
    # probably various numpy operations can now be written more
    # clearly, too.
    def _arrayToImage(self, inArray):
        """
        Generate a 1-channel PIL Image from an array of values from 0 to 1.0.

        Values larger than 1.0 are clipped, after adding them to the total
        clipped_pixels.  Returns a one-channel (monochrome) Image.
        """

        # PIL 'L' Images use a range of 0 to 255, so we scale the
        # input array to match.  The pixels are scaled by 255, not
        # 256, so that 1.0 maps to fully white.
        max_pixel_value=255
        inArray = (np.floor(inArray * max_pixel_value)).astype(np.int)

        # Clip any values that are still larger than max_pixel_value
        to_clip = (np.greater(inArray.ravel(),max_pixel_value)).sum()
        if (to_clip>0):
            # CEBALERT: no explanation of why clipped pixel count is
            # being accumulated.
            self.clipped_pixels = self.clipped_pixels + to_clip
            inArray.clip(0,max_pixel_value,out=inArray)
            self.verbose("Bitmap: clipped",to_clip,"image pixels that were out of range")

        r,c = inArray.shape
        # The size is (width,height), so we swap r and c:
        newImage = Image.new('L',(c,r),None)
        newImage.putdata(inArray.ravel())
        return newImage


class PaletteBitmap(Bitmap):
    """
    Bitmap constructed using a single 2D array.

    The image is monochrome by default, but more colorful images can
    be constructed by specifying a Palette.
    """

    def __init__(self,inArray,palette=None):
        """
        inArray should have values in the range from 0.0 to 1.0.

        Palette can be any color scale depending on the type of ColorMap
        desired.  Examples:

        [0,0,0 ... 255,255,255] = grayscale
        [0,0,0 ... 255,0,0] = grayscale but through a Red filter.

        The default palette is grayscale, with 0.0 mapping to black
        and 1.0 mapping to white.
        """
        ### JABALERT: Should accept a Palette class, not a data
        ### structure, unless for some reason we want to get rid of
        ### the Palette classes and always use data structures
        ### instead.
        ### JC: not yet properly implemented anyway.
        max_pixel_value=255

        newImage = self._arrayToImage(inArray)
        if palette == None:
            palette = [i for i in range(max_pixel_value+1) for j in range(3)]
        newImage.putpalette(palette)
        newImage = newImage.convert('P')
        super(PaletteBitmap,self).__init__(newImage)



class HSVBitmap(Bitmap):
    """
    Bitmap constructed from 3 2D arrays, for hue, saturation, and value.

    The hue matrix determines the pixel colors.  The saturation matrix
    determines how strongly the pixels are saturated for each hue,
    i.e. how colorful the pixels appear.  The value matrix determines
    how bright each pixel is.

    An RGB image is constructed from the HSV matrices using
    hsv_to_rgb; the resulting image is of the same type that is
    constructed by RGBBitmap, and can be used in the same way.
    """

    def __init__(self,hue,sat,val):
        """Each matrix must be the same size, with values in the range 0.0 to 1.0."""
        shape = hue.shape # Assumed same as sat.shape and val.shape
        rmat = np.zeros(shape, dtype=np.float)
        gmat = np.zeros(shape, dtype=np.float)
        bmat = np.zeros(shape, dtype=np.float)

        # Note: should someday file a feature request for PIL for them
        # to accept an image of type 'HSV', so that they will do this
        # conversion themselves, without us needing an explicit loop
        # here.  That should speed this up.
        ch = hue.clip(0.0,1.0)
        cs = sat.clip(0.0,1.0)
        cv = val.clip(0.0,1.0)

        for i in range(shape[0]):
            for j in range(shape[1]):
                r,g,b = hsv_to_rgb(ch[i,j],cs[i,j],cv[i,j])
                rmat[i,j] = r
                gmat[i,j] = g
                bmat[i,j] = b

        rImage = self._arrayToImage(rmat)
        gImage = self._arrayToImage(gmat)
        bImage = self._arrayToImage(bmat)

        super(HSVBitmap,self).__init__(Image.merge('RGB',(rImage,gImage,bImage)))



class RGBBitmap(Bitmap):
    """
    Bitmap constructed from three 2D arrays, for red, green, and blue.

    Each matrix is used as the corresponding channel of an RGB image.
    """

    def __init__(self,rMapArray,gMapArray,bMapArray):
        """Each matrix must be the same size, with values in the range 0.0 to 1.0."""
        rImage = self._arrayToImage(rMapArray)
        gImage = self._arrayToImage(gMapArray)
        bImage = self._arrayToImage(bMapArray)

        super(RGBBitmap,self).__init__(Image.merge('RGB',(rImage,gImage,bImage)))



class MontageBitmap(Bitmap):
    """
    A bitmap composed of tiles containing other bitmaps.

    Bitmaps are scaled to fit in the given tile size, and tiled
    right-to-left, top-to-bottom into the given number of rows and columns.
    """
    bitmaps = param.List(class_=Bitmap,doc="""
        The list of bitmaps to compose.""")

    rows = param.Integer(default=2, doc="""
        The number of rows in the montage.""")
    cols = param.Integer(default=2, doc="""
        The number of columns in the montage.""")
    shape = param.Composite(attribs=['rows','cols'], doc="""
        The shape of the montage. Same as (self.rows,self.cols).""")

    margin = param.Integer(default=5,doc="""
        The size in pixels of the margin to put around each
        tile in the montage.""")

    tile_size = param.NumericTuple(default=(100,100), doc="""
        The size in pixels of a tile in the montage.""")

    titles = param.List(class_=str, default=[], doc="""
        A list of titles to overlay on the tiles.""")

    title_pos = param.NumericTuple(default=(10,10), doc="""
        The position of the upper left corner of the title in each tile.""")

    title_options = param.Dict(default={}, doc="""
        Dictionary of options for drawing the titles.  Dict should
        contain keyword options for the PIL draw.text method.  Possible
        options include 'fill' (fill color), 'outline' (outline color),
        and 'font' (an ImageFont font instance).  The PIL defaults will
        be used for any omitted options.""",
        instantiate=False)

    hooks = param.List(default=[], doc="""
        A list of functions, one per tile, that take a PIL image as
        input and return a PIL image as output.  The hooks are applied
        to the tile images before resizing.  The value None can be
        inserted as a placeholder where no hook function is needed.""")

    resize_filter = param.Integer(default=Image.NEAREST,doc="""
       The filter used for resizing the images.  Defaults
       to NEAREST.  See PIL Image module documentation for other
       options and their meanings.""")

    bg_color = param.NumericTuple(default=(0,0,0), doc="""
       The background color for the montage, as (r,g,b).""")

    def __init__(self,**params):
        ## JPALERT: The Bitmap class is a Parameterized object,but its
        ## __init__ doesn't take **params and doesn't call super.__init__,
        ## so we have to skip it.
        ## JAB: Good point; Bitmap should be modified to be more like
        ## other PO classes.
        param.Parameterized.__init__(self,**params)

        rows,cols = self.shape
        tilew,tileh = self.tile_size
        bgr,bgg,bgb = self.bg_color

        width  = tilew*cols + self.margin*(cols*2)
        height = tileh*rows + self.margin*(rows*2)
        self.image = Image.new('RGB',(width,height),
                               (bgr*255,bgg*255,bgb*255))

        self.title_options.setdefault('font',TITLE_FONT)

        for r in xrange(rows):
            for c in xrange(cols):
                i = r*self.cols+c
                if i < len(self.bitmaps):
                    bm = self.bitmaps[i]
                    bmw,bmh = bm.image.size
                    if bmw > bmh:
                        bmh = int( float(tilew)/bmw * bmh )
                        bmw = tilew
                    else:
                        bmw = int( float(tileh)/bmh * bmw )
                        bmh = tileh

                    if self.hooks and self.hooks[i]:
                        f = self.hooks[i]
                    else:
                        f = lambda x:x
                    new_bm = Bitmap(f(bm.image).resize((bmw,bmh)))
                    if self.titles:
                        draw = ImageDraw.Draw(new_bm.image)
                        draw.text(self.title_pos,self.titles[i],**self.title_options)
                    self.image.paste( new_bm.image,
                                      (c * width/cols + tilew/2 - bmw/2 + self.margin,
                                       r * height/rows + tileh/2 - bmh/2 + self.margin) )

                else:
                    break


class DrawBitmap(Bitmap):
    """
    Bitmap with primitives drawn for each unit
    The input matrix has a list of primitives and relative arguments
    for each unit.
    """

    draw_options	= {
    		"fill":		"DarkGray",	# note that is lighter than Gray!
		"width":	1
    }

    def __init__(self, primitive_matrix, box_size ):
        """The overall shape is derived by the sheet shape and the desired
	magnification"""

	border		= 1
        shape		= primitive_matrix.shape
	width		= box_size * shape[ 0 ]
	height		= box_size * shape[ 1 ]
#	seg_len		= int( ( box_size - border ) / 2 ) - 1

        self.image	= Image.new( 'RGB', ( width, height ), 'white' )
        dr_img		= ImageDraw.Draw( self.image )

        for x in range( shape[ 0 ] ):
	    bx		= x * box_size
            for y in range( shape[ 1 ] ):
                by		= y * box_size
		b0		= ( bx + border, by + border )
		b1		= ( bx + box_size - border, by + box_size - border )
                dr_img.rectangle( [ b0, b1 ], fill = self.draw_options[ 'fill' ] )
		for p in primitive_matrix[ y, x ]:
		    p_name	=  p.keys()[ 0 ]
		    if not p_name in dir( dr_img ):
		        raise NotImplementedError( p_name + ' is not a valid draw directive' )
		    val		= p[ p_name ]
		    arg		= self.__in_box( val[ 0 ], b0, box_size - 2 * border )
		    opts	= val[ 1 ]
		    getattr( dr_img, p_name )( arg, **opts )



    def __in_box( self, coordinates, box_corner, seg_len ):
        """convert normalized coordinates into image coordinates in the given
	unit box"""

	in_box_coords	= []
	for xy in coordinates:
	    in_box_coords.append( (
	    		box_corner[ 0 ] + seg_len * xy[ 0 ],
			box_corner[ 1 ] + seg_len * xy[ 1 ]
	    ) )
	return in_box_coords


__all__ = [
    "Bitmap",
    "PaletteBitmap",
    "HSVBitmap",
    "RGBBitmap",
    "MontageBitmap",
    "DrawBitmap",
]
