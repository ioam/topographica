"""
Palette class hierarchy, for constructing an RGB color out of a scalar value.

$Id$
"""
__version__='$Revision$'

import param

import plot

### JABALERT: Should be able to construct a Palette automatically by
### accepting a string specification whose characters each stand for
### colors between which to interpolate.
###
### We'd like to support a string interface like:
### colormap(somestring), where somestring is a list of characters
### corresponding to colors between which to interpolate.
### (Interpolation is performed linearly in RGB space.)  Available
### colors include:
### 
###   R Red
###   Y Yellow
###   G Green
###   C Cyan
###   B Blue
###   M Magenta
###   K Black
###   W White
### 
### Use a lowercase letter to indicate that a color should use half intensity.
### For instance, a <colorspec> of 'KgYW' would map the level range 0.0->1.0
### to the color range black->dark green->yellow->white, with smooth
### interpolation between the specified colors.
###
### In addition to these string-specified palettes (the basic
### necessity), we would like to support classes for other methods for
### constructing palettes based on the hue, saturation, and value:
### 
### Hue [saturation [value]]
###   Useful for plotting cyclic quantities, such as orientation.
###   The hue is computed from the level, and is combined with the given fixed
###   saturation and value (default '1.0 1.0') to determine the color.  The hue
###   wraps around at each end of the range (e.g. red->yellow->green->blue->magenta
###   ->red), and thus is usually appropriate only when the quantity plotted has
###   that same property.  For the defaults, nearly identical to RYGCBMR.
### 
### Saturation [hue [value]]
###   Usually SpecifiedHue is used instead of specifying this type directly.
###   The saturation is computed from the level, and is combined with the given
###   fixed hue and value (default '0.0 1.0') to determine the color.
### 
### Value [hue [saturation]]
###   Usually Grayscale is used instead of specifying this type directly.
###   The value is computed from the level, and is combined with the given fixed
###   hue and saturation (default '0.0 0.0') to determine the color.  The defaults
###   result in a range of grayscale values from black to white; the optional
###   arguments allow other colors to be used instead of gray.
###   For the defaults, nearly identical to KW.
### 
### Grayscale [hue [saturation]]
###   Useful for monochrome displays or printers, or to show photographs.
###   Same as Value but the scale is flipped when ppm_paper_based_colors=True.
###   This makes the most-active areas show up with the intensity that is most
###   visible for the given medium (video or paper).  For the defaults, nearly
###   identical to KW, or WK for ppm_paper_based_colors.
### 
### SpecifiedHue [hue [confidence]]
###   Useful for color-coding a plot with a specific hue visible on the default
###   background. For paper_based_colors=False, same as ValueColorLookup;
###   the confidence is used as the saturation.  Such a plot works well for
###   showing color on a black background.  For paper_based_colors==True,
###   returns the specified hue masked by the specified confidence, such
###   that low values produce white, and high values produce black for low
###   confidences and the specified hue for high confidences.  Such a plot
###   is good for showing colors on light backgrounds.
### 
### MapSpecifiesHue [nameofhuemap [nameofconfidencemap]]
###   Neural-region-specific variant of SpecifiedHue where these colorspec
###   arguments specify not the actual hue and confidence, but the names of
###   registered maps (as in define_plot) in which to look up the hue and
###   confidence when plotting.  This colorspec can be used by plot_unit or
###   plot_unit_range to colorize a plot based on some property of a unit;
###   it is not supported in other contexts.  Examples:
###   Region::Eye0::Afferent0::colorspec='MapSpecifiesHue OrientationPreference OrientationSelectivity'
###   Region::Ganglia*::Afferent*::colorspec='MapSpecifiesHue OrientationPreference OrientationSelectivity
### 
### SpecifiedColor [hue [saturation [value]]]
###   Used to turn off color ranges, e.g. for a plot whose shape is more
###   important than the intensity of each pixel, such as a histogram.  Ignores
###   the level, and always returns the single given fixed color.  The default
###   color is a medium gray: '0.0 0.0 0.5'.  For the defaults, nearly identical
###   to 'w'.
### 
### 
### 
### Notes on implementing the string-based palette construction, taken
### from lissom/src/colorlookup.h:
### 
###    Might consider making the numcolors odd and adding a special
###    entry for the top of the range to make the range inclusive.
###    This might be more intuitive and would make plotting
###    inversely-scaled items (with a reversed color order) match
###    regularly-scaled ones.
###
###  StringBasedPalette
###  def __init__(spec,numcolors=0,scale=default_scale):
###    steps     = spec.length()
###    stepsize  = size_t(colors.size()/(steps>1 ? (steps-1) : 1))
###    start,i
###    for (i=0,start=0; i<steps-1; i++,start+=stepsize)
###      interpolate(start, start+stepsize,color(spec[i]), color(spec[i+1]))
###    interpolate(start, colors.size(),color(spec[i]), color(spec[steps-1]))
###
###  def interpolate(start, finish, startcolor, finishcolor):
###    """
###    Fill the lookup table (or a portion of it) with linear
###    interpolations between two colors.  The upper array index 
###    and finishcolor are exclusive.
###    """
###    assert (start<=finish);
###    
###    num_vals = int(finish-start)
###    division = (num_vals!=0 ? 1.0/num_vals : 0)
###    
###    rs       = startcolor.red()
###    gs       = startcolor.green()
###    bs       = startcolor.blue()
###    
###    rinc     = division*(finishcolor.red()   - startcolor.red())
###    ginc     = division*(finishcolor.green() - startcolor.green())
###    binc     = division*(finishcolor.blue()  - startcolor.blue())
###    
###    for(i=0; i<num_vals; i++)
###      colors[start+i]=PixelType(rs+rinc*i,gs+ginc*i,bs+binc*i)
###
###  def color(char):
###    """
###    Returns a color given a one-character name.  Uppercase is full-strength,
###    lowercase is half-strength.
###    """
###    h=0.5
###    switch (char)
###    case 'R': p=PixelType(1,0,0); break;   case 'r': p=PixelType(h,0,0); break;  /* Red     */
###    case 'Y': p=PixelType(1,1,0); break;   case 'y': p=PixelType(h,h,0); break;       /* Yellow  */
###    case 'G': p=PixelType(0,1,0); break;   case 'g': p=PixelType(0,h,0); break;       /* Green   */
###    case 'C': p=PixelType(0,1,1); break;   case 'c': p=PixelType(0,h,h); break;       /* Cyan    */
###    case 'B': p=PixelType(0,0,1); break;   case 'b': p=PixelType(0,0,h); break;       /* Blue    */
###    case 'M': p=PixelType(1,0,1); break;   case 'm': p=PixelType(h,0,h); break;       /* Magenta */
###    case 'W': p=PixelType(1,1,1); break;   case 'w': p=PixelType(h,h,h); break;       /* White   */
###    case 'K': p=PixelType(0,0,0); break;   case 'k': p=PixelType(0,0,0); break;       /* Black   */
###    return p



# Supported background types, used for such things as determining
# what color to be used for outlines, fills, etc.
BLACK_BACKGROUND = 0
WHITE_BACKGROUND = 1



########################  JC: starting new implementation #############
from numpy.oldnumeric import zeros

class StringBasedPalette(param.Parameterized):
    
    ### JCALERT: What is the default scale?
    def __init__(spec="KRYW",num_colors=0,scale=1.0):

        steps = len(spec)
        ### JCALERT! I am not sure about that...
        ### I have to check again with the C++ code
        if num_colors>0:
            colors = zeros(num_colors,'O')
        else:
            colors = array(252,'O')

        if steps>1:
            stepsize = len(colors)/(steps-1)
        else:
            stepsize = len(colors)
            
        for i,start in zip(range(steps-1),range(0,(steps-1)*stepsize,stepsize)):
            interpolate(start,start+stepsize,color(spec[i]),color(spec[i+1]))

        ### JCALERT! I do not really understand the last line
        interpolate(start,len(colors),color(spec[steps-1]),color(spec[steps-1]))
        
###    start,i
###    for (i=0,start=0; i<steps-1; i++,start+=stepsize)
###      interpolate(start, start+stepsize,color(spec[i]), color(spec[i+1]))
###    interpolate(start, colors.size(),color(spec[i]), color(spec[steps-1]))


# CB: lazy hack around the lambda that was in Palette.colors_
class F(object):
    def __call__(self):
        return [(i,i,i) for i in range(256)]

### JABHACKALERT: Needs significant cleanup -- should be much more
### straightforward, taking some specification and immediately
### constructing a usable object (without e.g. requiring set() to be
### called).
class Palette(param.Parameterized):
    """
    Each palette has 3*256 values that are keyed by an index.
    This base class takes in a list of 256 triples.

    A Palette object has 256 triples of RGB values ranging from 0
    ... 255.  The purpose of the class is to maintain an accurate
    palette conversion between a number (0..255) and an RGB triple
    even as the background of the plots change.  If the background is
    Black, then the 0 intensity should often be 0, but if the
    background of the Plot should be white, then the 0 intensity
    should probably be 255.  This automatic updating is possible
    through the use of Dynamic Parameters, and lambda functions.

    This class stores a passed in variable named colors.  If the
    variable is a lambda function that gives the 256 triples, then it
    will evaluate the lambda each time a datarequest is made.  If it
    is a static list, then the palette is fixed.  It may be possible
    to make Palette a 'pure' Dynamic parameter, with different types
    of palettes setting the lambda.  More power to you if you do that.

    """
    background = param.Dynamic(default=BLACK_BACKGROUND)
    colors_ = param.Dynamic(default=F())    #(lambda:[(i,i,i) for i in range(256)])

    def __init__(self,**params):
        """
        Does not fill in the colors, must call with a set
        function call preferably from a subclass of Palette
        """
        super(Palette,self).__init__(**params)

    def set(self, colors):
        """
        Colors is a list of 256 triples, each with a 0..255 RGB value
        or a lambda function that generates the list.  Lambdas will be
        necessary for dynamic shifts in black or white background
        changes.
        """
        self.colors_ = colors

    def flat(self):
        """
        Return the palette in a flat form of 768 numbers.  If the
        colors parameter is a callable object, call it for the
        list of values.
        """
        c = self.colors_
        return_list = []
        if callable(c):
            self.warning('Callable Parameter value returned, ', callable(c))
            c = c()
        for each in c:
            return_list.extend(list(each))
        return return_list

    def color(self, pos):
        """
        Return the tuple of RGB color found at pos in color list
        """
        c = self.colors_
        if callable(c):
            self.warning('Callable Parameter value returned, ', callable(c))
            c = c()
        return c[pos]

    def colors(self):
        """
        Return the complete list of palette colors in tuple form
        """
        c = self.colors_
        if callable(c):
            self.warning('Callable Parameter value returned, ', callable(c))
            c = c()
        return c


### JABALERT: There is probably no reason to have this class; this
### functionality is likely to be a special case of many other
### classes.
class Monochrome(Palette):
    """
    Color goes from Black to White if background is Black. It goes
    from White to Black if background is set to White.  By using
    a Dynamic Parameter, it should be able to update the palette
    automatically if the plot background color changes.
    """

    def __init__(self,**params):
        """
        Set a lambda function to the colors list which switches
        if the background switches.  This makes the accessors in
        the parent class rather slow since it has to do a list
        comprehension each time it accesses the list.
        """
        super(Monochrome,self).__init__(**params)
        self.colors = lambda: self.__mono_palette__()

    def __mono_palette__(self):
        """
        Function to be passed as a lambda to the Parameter
        """
        if self.background == BLACK_BACKGROUND:
            set_ = [(i,i,i) for i in range(256)]
        else:                  # Reverse the order 255 ... 0
            set_ = [(i,i,i) for i in range(255,-1,-1)]
        return set_
                

    
