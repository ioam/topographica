"""
PatternGenerators based on bitmap images stored in files.

$Id$
"""

import Image
import ImageOps
import numpy

from numpy.oldnumeric import array, Float, sum, ravel, ones

import param
from param.parameterized import overridable_property

from topo.base.boundingregion import BoundingBox
from topo.base.patterngenerator import PatternGenerator
from topo.base.sheetcoords import SheetCoordinateSystem
from topo.transferfn.basic import DivisiveNormalizeLinf,TransferFn


class ImageSampler(param.Parameterized):
    """
    A class of objects that, when called, sample an image.
    """
    __abstract=True

    def _get_image(self):
        # CB: In general, might need to consider caching to avoid
        # loading of image/creation of scs and application of wpofs
        # every time/whatever the sampler does to set up the image
        # before sampling
        return self._image

    def _set_image(self,image):
        self._image = image

    def _del_image(self):
        del self._image

    # As noted by JP in FastImageSampler, this isn't easy to figure out.
    def __call__(self,image,x,y,sheet_xdensity,sheet_ydensity,width=1.0,height=1.0):
        raise NotImplementedError
    
    image = overridable_property(_get_image,_set_image,_del_image)
    


# CEBALERT: ArraySampler?
class PatternSampler(ImageSampler):
    """
    When called, resamples - according to the size_normalization
    parameter - an image at the supplied (x,y) sheet coordinates.
    
    (x,y) coordinates outside the image are returned as the background
    value.
    """
    whole_pattern_output_fns = param.HookList(class_=TransferFn,default=[],doc="""
        Functions to apply to the whole image before any sampling is done.""")

    background_value_fn = param.Callable(default=None,doc="""
        Function to compute an appropriate background value. Must accept
        an array and return a scalar.""")

    size_normalization = param.ObjectSelector(default='original',
        objects=['original','stretch_to_fit','fit_shortest','fit_longest'],
        doc="""
        Determines how the pattern is scaled initially, relative to the
        default retinal dimension of 1.0 in sheet coordinates:
            
        'stretch_to_fit': scale both dimensions of the pattern so they
        would fill a Sheet with bounds=BoundingBox(radius=0.5) (disregards
        the original's aspect ratio).
    
        'fit_shortest': scale the pattern so that its shortest dimension
        is made to fill the corresponding dimension on a Sheet with
        bounds=BoundingBox(radius=0.5) (maintains the original's aspect
        ratio, filling the entire bounding box).
    
        'fit_longest': scale the pattern so that its longest dimension is
        made to fill the corresponding dimension on a Sheet with
        bounds=BoundingBox(radius=0.5) (maintains the original's
        aspect ratio, fitting the image into the bounding box but not
        necessarily filling it).
    
        'original': no scaling is applied; each pixel of the pattern 
        corresponds to one matrix unit of the Sheet on which the
        pattern being displayed.""")

    def _get_image(self):
        return self.scs.activity

    def _set_image(self,image):
        # Stores a SheetCoordinateSystem with an activity matrix
        # representing the image
        if not isinstance(image,numpy.ndarray):
            image = array(image,Float)

        rows,cols = image.shape
        self.scs = SheetCoordinateSystem(xdensity=1.0,ydensity=1.0,
                                         bounds=BoundingBox(points=((-cols/2.0,-rows/2.0),
                                                                    ( cols/2.0, rows/2.0))))
        self.scs.activity=image
        
    def _del_image(self):
        self.scs = None
        

    def __call__(self, image, x, y, sheet_xdensity, sheet_ydensity, width=1.0, height=1.0):
        """
        Return pixels from the supplied image at the given Sheet (x,y)
        coordinates.

        The image is assumed to be a NumPy array or other object that
        exports the NumPy buffer interface (i.e. can be converted to a
        NumPy array by passing it to numpy.array(), e.g. Image.Image).
        The whole_pattern_output_fns are applied to the image before
        any sampling is done.

        To calculate the sample, the image is scaled according to the
        size_normalization parameter, and any supplied width and
        height. sheet_xdensity and sheet_ydensity are the xdensity and
        ydensity of the sheet on which the pattern is to be drawn.
        """
        # CEB: could allow image=None in args and have 'if image is
        # not None: self.image=image' here to avoid re-initializing the
        # image.
        self.image=image

        for wpof in self.whole_pattern_output_fns:
            wpof(self.image)
        if not self.background_value_fn:
            self.background_value = 0.0
        else:
            self.background_value = self.background_value_fn(self.image)

        pattern_rows,pattern_cols = self.image.shape

        if width==0 or height==0 or pattern_cols==0 or pattern_rows==0:
            return ones(x.shape, Float)*self.background_value

        # scale the supplied coordinates to match the pattern being at density=1
        x=x*sheet_xdensity # deliberately don't operate in place (so as not to change supplied x & y)
        y=y*sheet_ydensity
      
        # scale according to initial pattern size_normalization selected (size_normalization)
        self.__apply_size_normalization(x,y,sheet_xdensity,sheet_ydensity,self.size_normalization)

        # scale according to user-specified width and height
        x/=width
        y/=height

        # now sample pattern at the (r,c) corresponding to the supplied (x,y)
        r,c = self.scs.sheet2matrixidx(x,y)
        # (where(cond,x,y) evaluates x whether cond is True or False)
        r.clip(0,pattern_rows-1,out=r)
        c.clip(0,pattern_cols-1,out=c)
        left,bottom,right,top = self.scs.bounds.lbrt()
        return numpy.where((x>=left) & (x<right) & (y>bottom) & (y<=top),  
                           self.image[r,c],
                           self.background_value)
    

    def __apply_size_normalization(self,x,y,sheet_xdensity,sheet_ydensity,size_normalization):
        pattern_rows,pattern_cols = self.image.shape

        # Instead of an if-test, could have a class of this type of
        # function (c.f. OutputFunctions, etc)...
        if size_normalization=='original':
            return
        
        elif size_normalization=='stretch_to_fit':
            x_sf,y_sf = pattern_cols/sheet_xdensity, pattern_rows/sheet_ydensity
            x*=x_sf; y*=y_sf

        elif size_normalization=='fit_shortest':
            if pattern_rows<pattern_cols:
                sf = pattern_rows/sheet_ydensity
            else:
                sf = pattern_cols/sheet_xdensity
            x*=sf;y*=sf
            
        elif size_normalization=='fit_longest':
            if pattern_rows<pattern_cols:
                sf = pattern_cols/sheet_xdensity
            else:
                sf = pattern_rows/sheet_ydensity
            x*=sf;y*=sf




def edge_average(a):
    "Return the mean value around the edge of an array."
    
    if len(ravel(a)) < 2:
        return float(a[0])
    else:
        top_edge = a[0]
        bottom_edge = a[-1]
        left_edge = a[1:-1,0]
        right_edge = a[1:-1,-1]

        edge_sum = sum(top_edge) + sum(bottom_edge) + sum(left_edge) + sum(right_edge)
        num_values = len(top_edge)+len(bottom_edge)+len(left_edge)+len(right_edge)

        return float(edge_sum)/num_values



class FastImageSampler(ImageSampler):
    """
    A fast-n-dirty image sampler using Python Imaging Library
    routines.  Currently this sampler doesn't support user-specified
    size_normalization or cropping but rather simply scales and crops
    the image to fit the given matrix size without distorting the
    aspect ratio of the original picture.
    """
    
    sampling_method = param.Integer(default=Image.NEAREST,doc="""
       Python Imaging Library sampling method for resampling an image.
       Defaults to Image.NEAREST.""")

    def _set_image(self,image):
        if not isinstance(image,Image.Image):
            self._image = Image.new('L',image.shape)
            self._image.putdata(image.ravel())
        else:
            self._image = image
        
    def __call__(self, image, x, y, sheet_xdensity, sheet_ydensity, width=1.0, height=1.0):
        self.image=image

        # JPALERT: Right now this ignores all options and just fits the image into given array.
        # It needs to be fleshed out to properly size and crop the
        # image given the options. (maybe this class needs to be
        # redesigned?  The interface to this function is pretty inscrutable.)            
        im = ImageOps.fit(self.image,x.shape,self.sampling_method)
        return array(im,dtype=Float)



# Would be best called Image, but that causes confusion with Image's Image
class GenericImage(PatternGenerator):
    """
    Generic 2D image generator.

    Generates a pattern from a Python Imaging Library image object.
    Subclasses should override the _get_image method to produce the
    image object.

    The background value is calculated as an edge average: see
    edge_average().  Black-bordered images therefore have a black
    background, and white-bordered images have a white
    background. Images with no border have a background that is less
    of a contrast than a white or black one.

    At present, rotation, size_normalization, etc. just resample; it
    would be nice to support some interpolation options as well.
    """

    __abstract = True
    
    aspect_ratio  = param.Number(default=1.0,bounds=(0.0,None),
        softbounds=(0.0,2.0),precedence=0.31,doc="""
        Ratio of width to height; size*aspect_ratio gives the width.""")

    size  = param.Number(default=1.0,bounds=(0.0,None),softbounds=(0.0,2.0),
        precedence=0.30,doc="""
        Height of the image.""")

    pattern_sampler = param.ClassSelector(class_=ImageSampler,
        default=PatternSampler(background_value_fn=edge_average,
                               size_normalization='fit_shortest',
                               whole_pattern_output_fns=[DivisiveNormalizeLinf()]),doc="""
        The PatternSampler to use to resample/resize the image.""")

    cache_image = param.Boolean(default=True,doc="""
        If False, discards the image and pattern_sampler after drawing the pattern each time,
        to make it possible to use very large databases of images without
        running out of memory.""")


    def _get_image(self,p):
        raise NotImplementedError

    # CEB: not currently possible, because _get_image needs access to p
    #image = property(_get_image,_set_image,_del_image,doc=" ")
        
    def function(self,p):
        height   = p.size
        width    = p.aspect_ratio*height
                    
        result = p.pattern_sampler(self._get_image(p),p.pattern_x,p.pattern_y,float(p.xdensity),float(p.ydensity),
                                   float(width),float(height))

        if p.cache_image is False:
            self._image = None
            del self.pattern_sampler.image 

        return result

    ### support pickling of Image.Image

    # CEBALERT: almost identical code to that in topo.plotting.bitmap.Bitmap.
    # Can we instead patch PIL? (Note that we can't use copy_reg as we do for
    # e.g. numpy ufuncs because Image's Image is not a new-style class. So patching
    # PIL is probably the only option to handle this problem in one place.)
    
    # CEB: by converting to string and back, we probably incur some speed
    # penalty on copy()ing GenericImages (since __getstate__ and __setstate__ are
    # used for copying, unless __copy__ and __deepcopy__ are defined instead).
    def __getstate__(self):
        """
        Return the object's state (as in the superclass), but replace
        the '_image' attribute's Image with a string representation.
        """
        state = super(GenericImage,self).__getstate__()

        if '_image' in state and state['_image'] is not None:
            import StringIO
            f = StringIO.StringIO()
            image = state['_image']
            image.save(f,format=image.format or 'TIFF') # format could be None (we should probably just not save in that case)
            state['_image'] = f.getvalue()
            f.close()

        return state

    def __setstate__(self,state):
        """
        Load the object's state (as in the superclass), but replace
        the '_image' string with an actual Image object.
        """
        # CEBALERT: Need to figure out how state['_image'] could ever
        # actually be None; apparently it is sometimes (see SF
        # #2276819).
        if '_image' in state and state['_image'] is not None:
            import StringIO
            state['_image'] = Image.open(StringIO.StringIO(state['_image']))
        super(GenericImage,self).__setstate__(state)



class FileImage(GenericImage):
    """
    2D Image generator that reads the image from a file.
    
    The image at the supplied filename is converted to grayscale if it
    is not already a grayscale image. See Image's Image class for
    details of supported image file formats.
    """

    filename = param.Filename(default='images/ellen_arthur.pgm',precedence=0.9,doc="""
        File path (can be relative to Topographica's base path) to a bitmap image.
        The image can be in any format accepted by PIL, e.g. PNG, JPG, TIFF, or PGM.
        """)


    def __init__(self, **params):
        """
        Create the last_filename attribute, used to hold the last
        filename. This allows reloading an existing image to be
        avoided.
        """
        super(FileImage,self).__init__(**params)
        self.last_filename = None


    def _get_image(self,p):
        """
        If necessary as indicated by the parameters, get a new image,
        assign it to self._image and return True.  If no new image is
        needed, return False.
        """
        if p.filename!=self.last_filename or self._image is None:
            self.last_filename=p.filename
            self._image = ImageOps.grayscale(Image.open(p.filename))
        return self._image




