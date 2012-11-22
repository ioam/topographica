"""
Test for the Plot class.

$Id$
"""


import unittest
from pprint import pprint
from topo.plotting import plot
from topo.base.sheet import *
from topo.plotting.bitmap import RGBBitmap, HSVBitmap
#from testsheetview import ImageGenerator

SHOW_PLOTS = False


### JC: My new imports
from topo.plotting.plot import TemplatePlot, make_template_plot
import numpy.oldnumeric as Numeric
from numpy.oldnumeric import zeros, divide, Float, ones,reshape,array
from topo.base.boundingregion import BoundingBox
from topo.base.sheetview import SheetView
import numpy.oldnumeric.mlab as MLab
import numpy.oldnumeric.random_array as RandomArray

import param

from random import random


### This function is defined here, where it might be useful for testing
### Plot
def matrix_hsv_to_rgb(hMapArray,sMapArray,vMapArray):
    """
    First matrix sets the Hue (Color).
    Second marix sets the Sauration (How much color)
    Third matrix sets the Value (How bright the pixel will be)

    The three input matrices should all be the same size, and have
    been normalized to 1.  There should be no side-effects on the
    original input matrices.
    """
    
    shape = hMapArray.shape
    rmat = array(hMapArray,Float)
    gmat = array(sMapArray,Float)
    bmat = array(vMapArray,Float)
    
    ## This code should never be seen.  It means that calling code did
    ## not take the precaution of clipping the input matrices.
    if max(rmat.ravel()) > 1 or max(gmat.ravel()) > 1 or max(bmat.ravel()) > 1:
        param.Parameterized().warning('HSVBitmap inputs exceed 1. Clipping to 1.0')
        if max(rmat.ravel()) > 0: rmat = clip(rmat,0.0,1.0)
        if max(gmat.ravel()) > 0: gmat = clip(gmat,0.0,1.0)
        if max(bmat.ravel()) > 0: bmat = clip(bmat,0.0,1.0)

    # List comprehensions were not used because they were slower.
    for j in range(shape[0]):
        for i in range(shape[1]):
            rgb = hsv_to_rgb(rmat[j,i],gmat[j,i],bmat[j,i])
            rmat[j,i] = rgb[0]
            gmat[j,i] = rgb[1]
            bmat[j,i] = rgb[2]
                
    return (rmat, gmat, bmat)



### JCALERT !he file should be rewritten according to new changes in Plot.

class TestPlot(unittest.TestCase):

    def setUp(self):

        ### Simple case: we only pass a dictionnary to Plot()
        ### that does not belong to a Sheet:
        self.view_dict = {}

        ### SheetView1:
        ### Find a way to assign randomly the matrix.
        self.matrix1 = zeros((10,10),Float) + RandomArray.random((10,10))
        self.bounds1 = BoundingBox(points=((-0.5,-0.5),(0.5,0.5)))
        self.sheet_view1 = SheetView((self.matrix1,self.bounds1),
                                      src_name='TestInputParam')
        self.key1 = 'sv1'
        self.view_dict[self.key1] = self.sheet_view1

        ### SheetView2:
        ### Find a way to assign randomly the matrix.
        self.matrix2 = zeros((10,10),Float) + 0.3
        self.bounds2 = BoundingBox(points=((-0.5,-0.5),(0.5,0.5)))
        self.sheet_view2 = SheetView((self.matrix2,self.bounds2),
                                      src_name='TestInputParam')
        self.key2 = ('sv2',0,10)
        self.view_dict[self.key2] = self.sheet_view2

        ### SheetView3:
        ### Find a way to assign randomly the matrix.
        self.matrix3 = zeros((10,10),Float) + RandomArray.random((10,10))
        self.bounds3 = BoundingBox(points=((-0.5,-0.5),(0.5,0.5)))
        self.sheet_view3 = SheetView((self.matrix3,self.bounds3),
                                      src_name='TestInputParam')
        self.key3 = ('sv3',0,'hello',(10,0))
        self.view_dict[self.key3] = self.sheet_view3

        ### SheetView4: for testing clipping + different bounding box
        ### Find a way to assign randomly the matrix.
        self.matrix4 = zeros((10,10),Float) + 1.6
        self.bounds4 = BoundingBox(points=((-0.7,-0.7),(0.7,0.7)))
        self.sheet_view4 = SheetView((self.matrix4,self.bounds4),
                                      src_name='TestInputParam')
        self.key4 = 'sv4'
        self.view_dict[self.key4] = self.sheet_view4

        ### JCALERT! for the moment we can only pass a triple when creating plot
        ### adding more sheetView to test when plot will be fixed for accepting
        ### as much as you want.

        # plot0: empty plot + no sheetviewdict passed: error or empty plot?
        ### JCALERT! It has to be fixed what to do in this case in plot..
        ### disabled test for the moment.
        #self.plot0 = Plot((None,None,None),None,name='plot0')
        ### CATCH EXCEPTION

        plot_channels1 = {'Strength':None,'Hue':None,'Confidence':None}
        # plot1: empty plot 
        self.plot1 = make_template_plot(plot_channels1,self.view_dict,density=10.0,name='plot1')
        
        plot_channels2 = {'Strength':self.key1,'Hue':None,'Confidence':None}                       
        # plot2: sheetView 1, no normalize, no clipping
        self.plot2 = make_template_plot(plot_channels2,self.view_dict,density=10.0,name='plot2')
 
        plot_channels3 = {'Strength':self.key1,'Hue':self.key2,'Confidence':None}
        # plot3: sheetView 1+2, no normalize, no clipping
        self.plot3 = make_template_plot(plot_channels3,self.view_dict,density=10.0,name='plot3')

        plot_channels4 = {'Strength':self.key1,'Hue':self.key2,'Confidence':self.key3}
        # plot4: sheetView 1+2+3, no normalize , no clipping 
        self.plot4 = make_template_plot(plot_channels4,self.view_dict,density=10.0,name='plot4')

        plot_channels5 = {'Strength':self.key1,'Hue':None,'Confidence':self.key3}
        # plot5: sheetView 1+3, no normalize, no clipping
        self.plot5 = make_template_plot(plot_channels5,self.view_dict,density=10.0,name='plot5')

        plot_channels6 = {'Strength':None,'Hue':self.key2,'Confidence':self.key3}
        # plot6: sheetView 2+3, no normalize , no clipping 
        self.plot6 = make_template_plot(plot_channels6,self.view_dict,density=10.0,name='plot6')

        plot_channels7 = {'Strength':self.key4,'Hue':self.key2,'Confidence':self.key3}
        # plot7: sheetView 1+2+3, no normalize , clipping 
        self.plot7 = make_template_plot(plot_channels7,self.view_dict,density=10.0,name='plot7')

        plot_channels8 = {'Strength':self.key1,'Hue':self.key2,'Confidence':self.key3}
        # plot8: sheetView 1+2+3, normalize , no clipping 
        self.plot8 = make_template_plot(plot_channels8,self.view_dict,density=10.0,normalize=True,name='plot8')

        ### JCALERT! FOR THE MOMENT I TAKE THE DEFAULT FOR NORMALIZE.
        ### WE WILL SEE IF IT REMAINS IN PLOT FIRST.

        ### also makes a sheet to test realease_sheetviews

        self.sheet = Sheet()
        self.sheet.sheet_views[self.key1]=self.sheet_view1
        self.sheet.sheet_views[self.key2]=self.sheet_view2
        self.sheet.sheet_views[self.key3]=self.sheet_view3
        self.sheet.sheet_views[self.key4]=self.sheet_view4

        plot_channels9 = {'Strength':self.key1,'Hue':self.key2,'Confidence':self.key3}
        self.plot9 = make_template_plot(plot_channels9,self.sheet.sheet_views,density=10.0,name='plot9')

        
        

    def test_plot(self):
        pass
    
#       ### JCALERT! make a test for plot0

#       # plot 1
#       test = None
#       self.assertEqual(self.plot1,test)

#       # plot 2
#       sat = zeros((10,10),Float) 
#       hue = zeros((10,10),Float)
#       val = self.matrix1

#       test = matrix_hsv_to_rgb(hue,sat,val)
#       for each1,each2 in zip(self.plot2.rgb_matrices,test):
#           for each3,each4 in zip(each1.ravel(),each2.ravel()):
#               self.assertAlmostEqual(each3,each4)

#       # plot 3
#       sat = ones((10,10),Float) 
#       hue = zeros((10,10),Float) + 0.3
#       val = self.matrix1

#       test = matrix_hsv_to_rgb(hue,sat,val)
#       for each1,each2 in zip(self.plot3.rgb_matrices,test):
#           for each3,each4 in zip(each1.ravel(),each2.ravel()):
#               self.assertAlmostEqual(each3,each4)  

#       # plot 4
#       sat = self.matrix3 
#       hue = zeros((10,10),Float) + 0.3
#       val = self.matrix1

#       test = matrix_hsv_to_rgb(hue,sat,val)
#       for each1,each2 in zip(self.plot4.rgb_matrices,test):
#           for each3,each4 in zip(each1.ravel(),each2.ravel()):
#               self.assertAlmostEqual(each3,each4)  

#       # plot 5
#       sat = zeros((10,10),Float) 
#       hue = zeros((10,10),Float) 
#       val = self.matrix1

#       test = matrix_hsv_to_rgb(hue,sat,val)
#       for each1,each2 in zip(self.plot5.rgb_matrices,test):
#           for each3,each4 in zip(each1.ravel(),each2.ravel()):
#               self.assertAlmostEqual(each3,each4)

#       # plot 6
#       sat = self.matrix3 
#       hue = zeros((10,10),Float) + 0.3 
#       val = ones((10,10),Float) 

#       test = matrix_hsv_to_rgb(hue,sat,val)
#       for each1,each2 in zip(self.plot6.rgb_matrices,test):
#           for each3,each4 in zip(each1.ravel(),each2.ravel()):
#               self.assertAlmostEqual(each3,each4)  
    
#       # plot 7
#       sat = self.matrix3 
#       hue = zeros((10,10),Float) + 0.3 
#       val = self.matrix4

#         val = MLab.clip(val,0.0,1.0)
        
#       test = matrix_hsv_to_rgb(hue,sat,val)
#       for each1,each2 in zip(self.plot7.rgb_matrices,test):
#           for each3,each4 in zip(each1.ravel(),each2.ravel()):
#               self.assertAlmostEqual(each3,each4)
        

#       # plot 8
#       sat = self.matrix3 
#       hue = zeros((10,10),Float) + 0.3 
#       val = self.matrix1

#       val = divide(val,float(max(val.ravel())))
        
#       test = matrix_hsv_to_rgb(hue,sat,val)

#       for each1,each2 in zip(self.plot8.rgb_matrices,test):
#           for each3,each4 in zip(each1.ravel(),each2.ravel()):
#               self.assertAlmostEqual(each3,each4)




#       # plot 9
#       sat = self.matrix3 
#       hue = zeros((10,10),Float) + 0.3 
#       val = self.matrix1
        
#       test = matrix_hsv_to_rgb(hue,sat,val)
#       for each1,each2 in zip(self.plot9.rgb_matrices,test):
#           for each3,each4 in zip(each1.ravel(),each2.ravel()):
#               self.assertAlmostEqual(each3,each4)  

# #### Think about doing a plot test using sheet_dict and a sheet?
# ### Ask Jim if it is really necessary...

#     def test_release_sheetviews(self):

#       self.plot9.release_sheetviews()

#       test=self.sheet.sheet_views.get(self.key1,None)
#       self.assertEqual(test,None)
#       test=self.sheet.sheet_views.get(self.key2,None)
#       self.assertEqual(test,None)
#       test=self.sheet.sheet_views.get(self.key3,None)
#       self.assertEqual(test,None)
#       test=self.sheet.sheet_views.get(self.key4,None)
#       self.assertEqual(test,self.sheet_view4)


#     def test_matrix_hsv_to_rgb(self):
#         a = [j for i in range(256) for j in range(256)]
#         b = [i for i in range(256) for j in range(256)]
#         c = [max(i,j) for i in range(256) for j in range(256)]
#         a = Numeric.reshape(a,(256,256)) / 255.0
#         b = Numeric.reshape(b,(256,256)) / 255.0
#         c = Numeric.reshape(c,(256,256)) / 255.0
#         (h,s,v) = matrix_hsv_to_rgb(a,b,c)
#         rgb = RGBMap(h,s,v)
#         # rgb.show()

#     def test_matrix_hsv_to_rgb2(self):
#         h = Numeric.array([[0.0,0.0],[0.0,0.0]])
#         s = Numeric.array([[0.0,0.0],[0.0,0.0]])
#         v = Numeric.array([[0.5,0.5],[0.5,0.5]])
#         h_orig = Numeric.array(h)
#         s_orig = Numeric.array(s)
#         v_orig = Numeric.array(v)
#         r,g,b = matrix_hsv_to_rgb(h,s,v)
#         rgb_target = Numeric.array([[0.5,0.5],[0.5,0.5]])
#         self.assertEqual(h,h_orig)
#         self.assertEqual(s,s_orig)
#         self.assertEqual(v,v_orig)
    

### JC: THIS CODE IS LEFT TEMPORARY IN CASE IT IS OF ANY USE IN NEAR FUTURE
    
#         x = plot.Plot(('Activity',None,None),plot.COLORMAP,self.s2)
#         for o in dir():
#             # pprint(o)
#             if isinstance(o,plot.Plot):
#                 o.warning('Found ', o.name)

#         input = ImageGenerator(filename='topo/tests/testsheetview.ppm',
#                          density=100,
#                          bounds=BoundingBox(points=((-0.8,-0.8),(0.8,0.8))))
#         sv = input.sheet_view('Activity')

#         # Defined sheetview in the R channel
#         plot1 = plot.Plot((None,None,sv),plot.COLORMAP)
#         p_tuple = plot1.plot()
#         (r, g, b) = p_tuple.matrices
#         map = RGBMap(r,g,b)
#         if SHOW_PLOTS: map.show()


#     def test_HSV_plot(self):
#         input = ImageGenerator(filename='topo/tests/testsheetview.ppm',
#                          density=100,
#                          bounds=BoundingBox(points=((-0.8,-0.8),(0.8,0.8))))
#         sv = input.sheet_view('Activity')

#         # Defined sheetview in the R channel
#         plot1 = plot.Plot((sv,sv,sv),plot.HSV)
#         p_tuple = plot1.plot()
#         (r, g, b) = p_tuple.matrices
#         map = HSVMap(r,g,b)
#         if SHOW_PLOTS: map.show()

#     def test_plottemplate(self):
#         pt = plot.PlotTemplate()
#         pt = plot.PlotTemplate({'Strength'   : None,
#                                 'Hue'        : 'HueP',
#                                 'Confidence' : None})
#         pt = plot.PlotTemplate(channels={'Strength'   : None,
#                                          'Hue'        : 'HueP',
#                                          'Confidence' : None})



suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(TestPlot))
if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
