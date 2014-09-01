"""
Provides optimized color conversion utilities to speedup imagen color conversion (imagen.colorspaces.rgb_to_hsv and imagen.colorspaces.hsv_to_rgb.
"""


import numpy

from topo.misc.inlinec import inline, provide_unoptimized_equivalent

from imagen.colorspaces import _rgb_to_hsv_array, _hsv_to_rgb_array  # pyflakes:ignore (optimized)


def _rgb_to_hsv_array_opt(RGB):
    """Equivalent to rgb_to_hsv_array()."""
    red = RGB[:,:,0]
    grn = RGB[:,:,1]
    blu = RGB[:,:,2]

    shape = red.shape
    dtype = red.dtype
    
    hue = numpy.zeros(shape,dtype=dtype)
    sat = numpy.zeros(shape,dtype=dtype)
    val = numpy.zeros(shape,dtype=dtype)

    code = """
//// MIN3,MAX3 macros from
// http://en.literateprograms.org/RGB_to_HSV_color_space_conversion_(C)
#define MIN3(x,y,z)  ((y) <= (z) ? ((x) <= (y) ? (x) : (y)) : ((x) <= (z) ? (x) : (z)))

#define MAX3(x,y,z)  ((y) >= (z) ? ((x) >= (y) ? (x) : (y)) : ((x) >= (z) ? (x) : (z)))
////

for (int i=0; i<Nred[0]; ++i) {
    for (int j=0; j<Nred[1]; ++j) {

        // translation of Python's colorsys.rgb_to_hsv()

        float r=RED2(i,j);
        float g=GRN2(i,j);
        float b=BLU2(i,j);

        float minc=MIN3(r,g,b); 
        float maxc=MAX3(r,g,b); 

        VAL2(i,j)=maxc;

        if(minc==maxc) {
            HUE2(i,j)=0.0;
            SAT2(i,j)=0.0;
        } else {
            float delta=maxc-minc; 
            SAT2(i,j)=delta/maxc;

            float rc=(maxc-r)/delta;
            float gc=(maxc-g)/delta;
            float bc=(maxc-b)/delta;

            if(r==maxc)
                HUE2(i,j)=bc-gc;
            else if(g==maxc)
                HUE2(i,j)=2.0+rc-bc;
            else
                HUE2(i,j)=4.0+gc-rc;

            HUE2(i,j)=(HUE2(i,j)/6.0);

            if(HUE2(i,j)<0)
                HUE2(i,j)+=1;
            //else if(HUE2(i,j)>1)
            //    HUE2(i,j)-=1;

        }

    }
}

"""
    inline(code, ['red','grn','blu','hue','sat','val'], local_dict=locals())
    return numpy.dstack((hue,sat,val))


provide_unoptimized_equivalent("_rgb_to_hsv_array_opt","_rgb_to_hsv_array",locals())




def _hsv_to_rgb_array_opt(HSV):
    """Equivalent to hsv_to_rgb_array()."""
    hue = HSV[:,:,0]
    sat = HSV[:,:,1]
    val = HSV[:,:,2]

    shape = hue.shape
    dtype = hue.dtype
    
    red = numpy.zeros(shape,dtype=dtype)
    grn = numpy.zeros(shape,dtype=dtype)
    blu = numpy.zeros(shape,dtype=dtype)

    code = """
for (int i=0; i<Nhue[0]; ++i) {
    for (int j=0; j<Nhue[1]; ++j) {

        // translation of Python's colorsys.hsv_to_rgb() using parts
        // of code from
        // http://www.cs.rit.edu/~ncs/color/t_convert.html
        float h=HUE2(i,j);
        float s=SAT2(i,j);
        float v=VAL2(i,j);

        float r,g,b;
        
        if(s==0) 
            r=g=b=v;
        else {
            int i=(int)floor(h*6.0);
            if(i<0) i=0;
            
            float f=(h*6.0)-i;
            float p=v*(1.0-s);
            float q=v*(1.0-s*f);
            float t=v*(1.0-s*(1-f));

            switch(i) {
                case 0:
                    r = v;  g = t;  b = p;  break;
                case 1:
                    r = q;  g = v;  b = p;  break;
                case 2:
                    r = p;  g = v;  b = t;  break;
                case 3:
                    r = p;  g = q;  b = v;  break;
                case 4:
                    r = t;  g = p;  b = v;  break;
                case 5:
                    r = v;  g = p;  b = q;  break;
            }
        }
        RED2(i,j)=r;
        GRN2(i,j)=g;
        BLU2(i,j)=b;
    }
}
"""
    inline(code, ['red','grn','blu','hue','sat','val'], local_dict=locals())
    return numpy.dstack((red,grn,blu))

provide_unoptimized_equivalent("_hsv_to_rgb_array_opt","_hsv_to_rgb_array",locals())


