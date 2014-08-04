"""
Plot class.
"""

import copy
from math import sin, cos

import numpy as np
import param
from dataviews.ndmapping import NdMapping
from topo.base.sheetcoords import SheetCoordinateSystem,Slice
from bitmap import HSVBitmap, RGBBitmap, Bitmap, DrawBitmap



### JCALERT!
### - Re-write the test file, taking the new changes into account.
### - I have to change the order: situate, plot_bb and (normalize)
### - There should be a way to associate the density explicitly
###   with the sheet_views, because it must match all SheetViews
###   in that dictionary.  Maybe as a tuple?
### - Fix the plot name handling along with the view_info sheetview attribute
### - Get rid of release_sheetviews.


class Plot(param.Parameterized):
     """
     Simple Plot object constructed from a specified PIL image.
     """

     staleness_warning=param.Number(default=10,bounds=(0,None),doc="""
       Time length allowed between bitmaps making up a single plot before warning.

       If the difference between the SheetView with the earliest
       timestamp and the one with the latest timestamp is larger
       than this parameter's value, produce a warning.
       """)

     def __init__(self,image=None,**params):
          super(Plot,self).__init__(**params)
          self._orig_bitmap = Bitmap(image)
          self.bitmap = self._orig_bitmap # Possibly scaled copy (at first identical)
          self.scale_factor=1.0
          self.plot_src_name = ''
          self.precedence = 0.0
          self.row_precedence = 0.5
          # If False, this plot should be left in its native size
          # pixel-for-pixel, (e.g. for a color key or similar static
          # image), rather than being resized as necessary.
          self.resize=False

          # Time at which the bitmaps were created
          self.timestamp = -1


     def rescale(self,scale_factor):
          """
          Change the size of this image by the specified numerical factor.

          The original image is kept as-is in _orig_bitmap; the scaled
          image is stored in bitmap.  The scale_factor argument is
          taken as relative to the current scaling of the bitmap.  For
          instance, calling scale(1.5) followed by scale(2.0) will
          yield a final scale of 3.0, not 2.0.
          """
          self.scale_factor *= scale_factor

          if (self._orig_bitmap):
              self.bitmap = copy.copy(self._orig_bitmap)
              self.bitmap.image = self._orig_bitmap.zoom(self.scale_factor)


     def set_scale(self,scale_factor):
          """
          Specify the numerical value of the scaling factor for this image.

          The original image is kept as-is in _orig_bitmap; the scaled
          image is stored in bitmap.  The scale_factor argument is
          taken as relative to the original size of the bitmap.  For
          instance, calling scale(1.5) followed by scale(2.0) will
          yield a final scale of 2.0, not 3.0.
          """
          self.scale_factor = scale_factor

          if (self._orig_bitmap):
              self.bitmap = copy.copy(self._orig_bitmap)
              self.bitmap.image = self._orig_bitmap.zoom(self.scale_factor)

     def label(self):
          """Return a label for this plot."""
          return self.plot_src_name + '\n' + self.name



def _sane_plot_data(channels,sheet_views):
     # CEBALERT: was sf.net tracker item 1860837
     # (Avoid plotting only hue+confidence for a weights plot.)
     s_chan = channels.get('Strength')
     if s_chan is not None and len(s_chan)>0 and s_chan[0]=='Weights':
          return channels['Strength'] in sheet_views
     else:
          return True

# JABALERT: How can we handle joint normalization, where a set of
# plots (e.g. a CFProjectionPlotGroup, or the jointly normalized
# subset of a ConnectionFields plot) is all scaled by the same amount,
# so that relative strengths can be determined?  Maybe we can have
# make_template_plot and the various TemplatePlot types accept a
# parameter 'range_only' that makes them simply calculate a pair
# (min,max) with the values to use for scaling, and then the caller
# (e.g. CFProjectionPlotGroup._create_plots) would run through
# everything twice, first to get the ranges, and then the next time it
# would supply an explicit range for scaling (overriding the default
# single-plot normalization)?  See the commented-out code for
# value_range below for a start. I *think* that would work, but maybe
# there is some simpler way?
def make_template_plot(channels,sheet_views,density=None,
                       plot_bounding_box=None,normalize='None',
                       name='None',range_=False):
     """
     Factory function for constructing a Plot object whose type is not yet known.

     Typically, a TemplatePlot will be constructed through this call, because
     it selects the appropriate type automatically, rather than calling
     one of the Plot subclasses automatically.  See TemplatePlot.__init__ for
     a description of the arguments.
     """
     if _sane_plot_data(channels,sheet_views):
          plot_types=[SHCPlot,RGBPlot,PalettePlot,MultiOrPlot]
          for pt in plot_types:
               plot = pt(channels,sheet_views,density,plot_bounding_box,normalize,
                         name=name,range_=range_)
               if plot.bitmap is not None or range_ is None:
                    # range_ is None means we're calculating the range
                    return plot

     param.Parameterized(name="make_template_plot").verbose('No',name,'plot constructed for this Sheet')
     return None



class TemplatePlot(Plot):
    """
    A bitmap-based plot as specified by a plot template (or plot channels).
    """

    # Not sure why, but this has to be a Parameter to avoid spurious complaints
    warn_time=param.Number(-2,precedence=-1,doc="Time last warned about stale plots")


    def __init__(self,channels,sheet_views,density,
                 plot_bounding_box,normalize,
                 range_=False,**params):
        """
        Build a plot out of a set of SheetViews as determined by a plot_template.

        channels is a plot_template, i.e. a dictionary with keys
        (i.e. 'Strength','Hue','Confidence' ...).  Each key typically
        has a string value naming specifies a SheetView in
        sheet_views, though specific channels may contain other
        types of information as required by specific Plot subclasses.
        channels that are not used by a particular Plot subclass will
        silently be ignored.

        sheet_views is a dictionary of SheetViews, generally (but
        not necessarily) belonging to a Sheet object.

        density is the density of the Sheet whose sheet_views was
        passed.

        plot_bounding_box is the outer bounding_box of the plot to
        apply if specified.  If not, the bounds of
        the smallest SheetView are used.

        normalize specifies how the Plot should be normalized: any
        value of normalize other than 'None' will result in normalization
        according to the value of the range argument:

          range=(A,B) - scale plot so that A is 0 and B is 1

          range=False - scale plot so that min(plot) is 0 and
                        max(plot) is 1 (i.e. fill the maximim
                        dynamic range)

          range=None  - calculate value_range only


        name (which is inherited from Parameterized) specifies the name
        to use for this plot.
        """
        super(TemplatePlot,self).__init__(**params)
        # for a template plot, resize is True by default
        self.resize=True
        self.bitmap = None


        self.channels = channels
        self.view_dict = copy.copy(sheet_views)
        # bounds of the situated plotting area
        self.plot_bounding_box = plot_bounding_box


        ### JCALERT ! The problem of displaying the right plot name is still reviewed
        ### at the moment we have the plot_src_name and name attribute that are used for the label.
        ### generally the name is set to the plot_template name, except for connection
        # set the name of the sheet that provides the SheetViews
        # combined with the self.name parameter when creating the plot (which is generally
        # the name of the plot_template), it provides the necessary information for displaying plot label
        self._set_plot_src_name()


        # # Eventually: support other type of plots (e.g vector fields...) using
        # # something like:
        # def annotated_bitmap(self):
        # enable other construction....

    def _get_sv(self, key):
        sheet_view_key = self.channels.get(key, None)
        sv = self.view_dict.get(key,{}).get(sheet_view_key, None)
        if isinstance(sv, NdMapping):
            sv = sv.last

        return sv


    def _get_matrix(self,key):
        """
        Retrieve the matrix view associated with a given key, if any.

        If the key is found in self.channels and the corresponding
        sheetview is found in self.view_dict, the view's matrix is
        returned; otherwise None is returned (with no error).
        If the sheet_view derives from a cyclic distribution, and it
        will be used as Hue, the matrix is normalized in range 0..1
        """

        sv = self._get_sv(key)

        if sv == None:
            matrix = None
        else:
            matrix = sv.data.copy()
            if key=='Hue' and sv.cyclic_range is not None:
                matrix /= sv.cyclic_range

            # Calculate timestamp for this plot
            timestamp = sv.metadata.timestamp
            if timestamp >=0:
                if self.timestamp < 0:
                    self.timestamp = timestamp
                elif abs(timestamp - self.timestamp) > self.staleness_warning:
                    if TemplatePlot.warn_time != min(timestamp, self.timestamp):
                        self.warning("Combining SheetViews from different times (%s,%s) for plot %s; see staleness_warning" %
                                     (timestamp, self.timestamp,self.name))
                        TemplatePlot.warn_time = min(timestamp, self.timestamp)
        return matrix


    def _set_plot_src_name(self):
        """ Set the Plot plot_src_name. Called when Plot is created"""
        for key in self.channels:
            sheet_view_key = self.channels.get(key,None)
            sv = self.view_dict.get(key,{}).get(sheet_view_key)
            if sv != None:
                 self.plot_src_name = sv.metadata.src_name
                 self.precedence = sv.metadata.precedence
                 self.row_precedence = sv.metadata.row_precedence
                 if hasattr(sv.metadata,'proj_src_name'):
                      self.proj_src_name=sv.metadata.proj_src_name


    ### JCALERT: This could be inserted in the code of get_matrix
    def _get_shape_and_box(self):
        """
        Sub-function used by plot: get the matrix shape and the bounding box
        of the SheetViews that constitute the TemplatePlot.
        """
        for channel, name in self.channels.items():
            sv = self.view_dict.get(channel,{}).get(name, None)
            if isinstance(sv, NdMapping): sv = sv.last
            if sv != None:
                shape = sv.data.shape
                box = sv.bounds

        return shape, box


    # CEBALERT: needs simplification! (To begin work on joint
    # normalization, I didn't want to interfere with the existing
    # normalization calculations.)  Also need to update this
    # docstring.
    #
    # range=None  - calculate value_range; don't scale a
    # range=(A,B) - scale a so that A is 0 and B is 1
    # range=False - scale a so that min(array) is 0 and max(array) is 1
    def _normalize(self,a,range_):
        """
        Normalize an array s to be in the range 0 to 1.0.
        For an array of identical elements, returns an array of ones
        if the elements are greater than zero, and zeros if the
        elements are less than or equal to zero.
        """
        if range_: # i.e. not False, not None (expecting a tuple)
             range_min = float(range_[0])
             range_max = float(range_[1])

             if range_min==range_max:
                  if range_min>0:
                       resu = np.ones(a.shape)
                  else:
                       resu = np.zeros(a.shape)
             else:
                  a_offset = a - range_min
                  resu = a_offset/(range_max-range_min)

             return resu
        else:
             if range_ is None:
                  if not hasattr(self,'value_range'):
                       self.value_range=(a.min(),a.max())
                  else:
                       # If normalizing multiple matrices, take the largest values
                       self.value_range=(min(self.value_range[0],a.min()),
                                         max(self.value_range[1],a.max()))
                  return None # (indicate that array was not scaled)
             else: # i.e. range_ is False
                  a_offset = a-a.min()
                  max_a_offset = a_offset.max()

                  if max_a_offset>0:
                       a = np.divide(a_offset,float(max_a_offset))
                  else:
                       if min(a.ravel())<=0:
                            a=np.zeros(a.shape,dtype=np.float)
                       else:
                            a=np.ones(a.shape,dtype=np.float)
                  return a


    ### JC: maybe density can become an attribute of the TemplatePlot?
    def _re_bound(self,plot_bounding_box,mat,box,density):

        # CEBHACKALERT: for Julien...
        # If plot_bounding_box is that of a Sheet, it will already have been
        # setup so that the density in the x direction and the density in the
        # y direction are equal.
        # If plot_bounding_box comes from elsewhere (i.e. you create it from
        # arbitrary bounds), it might need to be adjusted to ensure the density
        # in both directions is the same (see Sheet.__init__()). I don't know where
        # you want to do that; presumably the code should be common to Sheet and
        # where it's used in the plotting?
        #
        # It's possible we can move some of the functionality
        # into SheetCoordinateSystem.
        if plot_bounding_box.containsbb_exclusive(box):
             ct = SheetCoordinateSystem(plot_bounding_box,density,density)
             new_mat = np.zeros(ct.shape,dtype=np.float)
             r1,r2,c1,c2 = Slice(box,ct)
             new_mat[r1:r2,c1:c2] = mat
        else:
             scs = SheetCoordinateSystem(box,density,density)
             s=Slice(plot_bounding_box,scs)
             s.crop_to_sheet(scs)
             new_mat = s.submatrix(mat)

        return new_mat





class SHCPlot(TemplatePlot):
    """
    Bitmap plot based on Strength, Hue, and Confidence matrices.

    Constructs an HSV (hue, saturation, and value) plot by choosing
    the appropriate matrix for each channel.
    """

    def __init__(self,channels,sheet_views,density,
                 plot_bounding_box,normalize,
                 range_=False,**params):
        super(SHCPlot,self).__init__(channels,sheet_views,density,
                                   plot_bounding_box,normalize,**params)

        # catching the empty plot exception
        s_mat = self._get_matrix('Strength')
        h_mat = self._get_matrix('Hue')
        c_mat = self._get_matrix('Confidence')

        # If it is an empty plot: self.bitmap=None
        if (s_mat==None and c_mat==None and h_mat==None):
            self.debug('Empty plot.')

        # Otherwise, we construct self.bitmap according to what is specified by the channels.
        else:

            shape,box = self._get_shape_and_box()

            hue,sat,val = self.__make_hsv_matrices((s_mat,h_mat,c_mat),shape,normalize,range_)

            if range_ is None:
                 return ##############################


            if self.plot_bounding_box == None:
               self.plot_bounding_box = box

            hue = self._re_bound(self.plot_bounding_box,hue,box,density)
            sat = self._re_bound(self.plot_bounding_box,sat,box,density)
            val = self._re_bound(self.plot_bounding_box,val,box,density)

            self.bitmap = HSVBitmap(hue,sat,val)

        self._orig_bitmap=self.bitmap


    def __make_hsv_matrices(self,hsc_matrices,shape,normalize,range_=False):
        """
        Sub-function of plot() that return the h,s,v matrices corresponding
        to the current matrices in sliced_matrices_dict. The shape of the matrices
        in the dict is passed, as well as the normalize boolean parameter.
        The result specified a bitmap in hsv coordinate.

        Applies normalizing and cropping if required.
        """
        zero=np.zeros(shape,dtype=np.float)
        one=np.ones(shape,dtype=np.float)

        s,h,c = hsc_matrices
        # Determine appropriate defaults for each matrix
        if s is None: s=one # Treat as full strength by default
        if c is None: c=one # Treat as full confidence by default
        if h is None:       # No color, gray-scale plot.
            h=zero
            c=zero

        # If normalizing, offset the matrix so that the minimum
        # value is 0.0 and then scale to make the maximum 1.0
        if normalize!='None':
             s=self._normalize(s,range_=range_)
             # CEBALERT: I meant False, right?
             c=self._normalize(c,range_=False)


        # This translation from SHC to HSV is valid only for black backgrounds;
        # it will need to be extended also to support white backgrounds.
        hue,sat,val=h,c,s
        return (hue,sat,val)





class RGBPlot(TemplatePlot):
  """
  Bitmap plot based on Red, Green, and Blue matrices.

  Construct an RGB (red, green, and blue) plot from the Red, Green,
  and Blue channels.
  """
  def __init__(self,channels,sheet_views,density,
               plot_bounding_box,normalize,
               range_=False,**params):

       super(RGBPlot,self).__init__(channels,sheet_views,density,
                                   plot_bounding_box,normalize,**params)


       # catching the empty plot exception
       r_mat = self._get_matrix('Red')
       g_mat = self._get_matrix('Green')
       b_mat = self._get_matrix('Blue')

       # If it is an empty plot: self.bitmap=None
       if (r_mat==None and g_mat==None and b_mat==None):
            self.debug('Empty plot.')
            # Otherwise, we construct self.bitmap according to what is specified by the channels.
       else:

            shape,box = self._get_shape_and_box()

            red,green,blue = self.__make_rgb_matrices((r_mat,g_mat,b_mat),shape,
                                                      normalize,range_=range_)

            if range_ is None:
                 return ############################

            if self.plot_bounding_box == None:
               self.plot_bounding_box = box

            red = self._re_bound(self.plot_bounding_box,red,box,density)
            green = self._re_bound(self.plot_bounding_box,green,box,density)
            blue = self._re_bound(self.plot_bounding_box,blue,box,density)

            self.bitmap = RGBBitmap(red,green,blue)

       self._orig_bitmap=self.bitmap

  def __make_rgb_matrices(self, rgb_matrices,shape,normalize,range_=False):
        """
        Sub-function of plot() that return the h,s,v matrices
        corresponding to the current matrices in
        sliced_matrices_dict. The shape of the matrices in the dict is
        passed, as well as the normalize boolean parameter.  The
        result specified a bitmap in hsv coordinate.

        Applies normalizing and cropping if required.
        """
        zero=np.zeros(shape,dtype=np.float)

        r,g,b = rgb_matrices
        # Determine appropriate defaults for each matrix
        if r is None: r=zero
        if g is None: g=zero
        if b is None: b=zero

        # CEBALERT: have I checked this works?
        if normalize!='None':
             r = self._normalize(r,range_=range_)
             g = self._normalize(g,range_=range_)
             b = self._normalize(b,range_=range_)

        return (r,g,b)





class PalettePlot(TemplatePlot):
     """
     Bitmap plot based on a Strength matrix, with optional colorization.

     Not yet implemented.

     When implemented, construct an RGB plot from a Strength channel,
     optionally colorized using a specified Palette.
     """

     def __init__(self,channels,sheet_views,density,
                  plot_bounding_box,normalize,**params):

          super(PalettePlot,self).__init__(channels,sheet_views,density,
                                           plot_bounding_box,normalize,**params)

          ### JABHACKALERT: To implement the class: If Strength is present,
          ### ask for Palette if it's there, and make a PaletteBitmap.






class MultiOrPlot(TemplatePlot):
    """
    Bitmap plot with oriented lines draws for every units, representing
    the most preferred orientations.
    Constructs a matrix of drawing directives displaying oriented lines
    in each unit, colored according to the order or preference, and selectivity
    This plot expects channels named "OrX" "SelX", with "X" the number
    ranking the preferred orientations.
    """
    unit_size       = param.Number(default=25,bounds=(9,None),doc="box size of a single unit")
    min_brightness  = param.Number(default=30,bounds=(0,50),doc="min brightness of lines")
    max_brightness  = param.Number(default=90,bounds=(50,100),doc="max brightness of lines")

    def __init__(self,channels,sheet_views,density,
                 plot_bounding_box,normalize,
                 range_=False,**params):
        super(MultiOrPlot,self).__init__(channels,sheet_views,density,
                                   plot_bounding_box,normalize,**params)

        n       = len( channels.keys() )
        if density > 10:
            self.unit_size = int( density )

        # there should be an even number of channels
        if n % 2:
            self.debug('Empty plot.')
            return

        if ( self.unit_size % 2 ) == 0:
            self.unit_size = self.unit_size + 1

        n       = n / 2
        m       = []
        for i in range( n ):
            o           = self._get_matrix( "Or%d" % (i+1) )
            s           = self._get_matrix( "Sel%d" % (i+1) )
            if ( o==None or s==None ):
                self.debug('Empty plot.')
                return
            m.append( ( o, s ) )

        shape,box         = self._get_shape_and_box()
        dm                = self.__make_lines_from_or_matrix( m, shape )
        box_size          = self.unit_size
        self.bitmap       = DrawBitmap( dm, box_size )
        self._orig_bitmap = self.bitmap


    def __vertices_from_or( self, o ):
        """
        help function for generating coordinates of line vertices
        from normalized orientation value.
        Return a list with two tuples, the coordinates of the segment with the
        given orientation, in the normalized range [ 0...1 ].
	Orientation is expected in range [ 0..pi ]. Space
        representation is in ordinary image convention: first coordinate is X,
        from left to right, second coordinate Y, from top to bottom.
        """

        s       = 0.5 * sin( o )
        c       = 0.5 * cos( o )
        return [ ( 0.5 - c, 0.5 + s ), ( 0.5 + c, 0.5 - s ) ]


    def __make_line_directive( self, os_list ):
        """
        help function for composing the list of line directives
        for a single unit.
        """

        d_hue   = 360 / len( os_list )
        hue     = 0
        p       = []
        n       = self.max_brightness - self.min_brightness
        for o,s in os_list:
            if s > 0.:
                f       = "hsl(%d,100%%,%2d%%)" % ( hue, max( self.min_brightness, n * ( 1. - s ) ) )
                p.append( { "line": [ o, { "fill": f } ] } )
            hue         = hue + d_hue

        return p


    def __make_lines_from_or_matrix( self, matrices, shape ):
        """
        return a matrix of line drawing directives for each unit, derived from
        the given list of tuples ( o, s ), where o is the orientation view and s
        is the selectivity. The list is ordered by the orientation preference.
        """

        vertices_from_or        = np.vectorize( self.__vertices_from_or, otypes=[np.object_] )
        mat_list                = []
        for o, s in matrices:
            a   = s.mean()
            d   = s.std()
            ad  = a + d
        if isinstance( ad, np.number ) and ad > 0:
            mat_list.append( ( vertices_from_or( o ), ( s - d ) / ad ) )

        lines   = np.empty( shape, np.object_ )
        for x in range( shape[ 0 ] ):
            for y in range( shape[ 1 ] ):
                os_list = []
                for o, s in mat_list:
                    os_list.append( ( o[ x, y ], s[ x, y ] ) )
                lines[ x, y ]   = self.__make_line_directive( os_list )

        return lines
