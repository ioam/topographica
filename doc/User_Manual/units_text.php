<H1>Working with Real World Units in Topographica</H1>

<P>Starting from May 2012, Topographica has limited support to
formally define spatial dimensions using units. This allows modellers
to express most variables in their models using real world units,
simplifying the tuning process and allowing for a much more intuitive
interaction between experiments and models.

<H3>Limitations and Planned Functionality</H3>

<P>For now there are several limitation to the unit system. The
primary limitation is the lack of support for non-linear
units. Secondly, the unit support is currently limited to the
specification side, i.e. models can be specified in different units
but there is no easy way of displaying scales and spatial units in the
GUI and the outputted files. Finally, so far there is only support for
spatial units but ultimately this should be extended to temporal
units.

<H3>Installing Unum</H3>

<P>As pointed out above, unit support in Topographica depends on the
Unum Python library, the full documentation for which can be accessed
<A href="http://home.scarlet.be/be052320/Unum.html">here</A>. The
archived package can be downloaded from the direct link <A
href="http://bitbucket.org/kiv/unum/get/409befe069ac.zip">here</A>.

<P>The installation is the same as for other Python packages. Simply
extract the .zip archive in a folder, start the version of Python that
is associated with Topographica, go to extracted folder and run:

<pre>setup.py install</pre>

<P>Topographica should now run with support for units.

<H3>How do units work in Topographica?</H3>

<P>Models in Topographica can usually be broken down into individual
sheets or sheet groups. Taking GCAL as an example, there are four
sheets: the Retina, LGNOn, LGNOff and V1. Each sheet group has an
associated magnification factor, which defines the conversion between
millimetres on the sheet surface and degrees of visual angle as
represented on the retina. Depending on the cortical area being
simulated the magnification factor could also map between auditory
frequency or distance on the skin surface and the distance on the
sheet surface. In all these cases, magnification factors are well
defined and have been mapped in a number of different species and
areas.

<P>The magnification factor varies wildly from area to area, which is
why it makes sense to represent space in an invariant dimension, which
is either degrees in visual space or whatever other feature dimension
the modelled area can be mapped to. To hold the feature space
represented per unit area in sheet coordinates constant, we therefore
also have to define a mapping between millimetres and sheet
coordinates.

<P>Thus we only have to define conversions for "degrees of visual
angle" (or whatever feature dimension we are dealing with) and "sheet
coordinates" for each sheet group.

<P>These definitions are then stored by so called
<code>UnitConversion</code> objects in each sheet, so that the
appropriate conversion can be applied at the sheet level.

<H3>Importing and Defining Units in the Model.ty file</H3>

<P>We'll demonstrate how to work with units by working our way through
a version of the GCAL model with unit support. You can have a look at
the complete file here. We'll only cover the parts that have been
altered.

<P>The Unum package includes definitions for the most common physical
quantities including all SI and Imperial units, which you can import
by calling:

<pre> from unum import Unum, units </pre>

<P>In addition we have imported <code>Unum</code>, which we need to
define new units such as degrees of visual angle. The syntax to define
a new unit is simple, just use the <code>Unum.unit</code> method and
pass it an abbreviation of the unit, a conversion factor and a
description of the unit. In this particular case we aren't going to
define the actual conversion factor since visual degrees will have
different definitions depending on which sheet is being referenced.

<pre>vdeg = Unum.unit('vdeg', 0, 'Degrees of Visual Angle')</pre>

<P>Now that we have imported and initially defined the units we will
be working with we just have to import the classes and functions,
which provide or which need to be given unit support.

<pre> 
from topo.base.boundingregion import BoundingRegionParameter
from topo.misc.unitsupport import strip_units_hook, UnitConversions
</pre>

<P>Next we have to define some of the basic conversion or
magnification factors. In the <code>global_params</code> section of
the <code>.ty</code> file we start by defining the number of degrees
of visual angle represented by a unit area in sheet coordinates:

<pre> vdeg_area=param.Number(default=1.3333*vdeg,doc=""" Degrees of
visual angle per unit area in sheet coordinates."""), </pre>

Now we just need to specify the magnification factor of each sheet.
In this case we specify it in the number of millimetres per degree of
visual angle:

<pre> 
retina_mf=param.Number(default=0.2*units.mm,doc="""The magnification
    factor of the retinal sheet, expressed per degree of visual
    angle."""),

lgn_mf=param.Number(default=0.3*units.mm,doc=""" The magnification
    factor of the LGN sheets, expressed per degree of visual
    angle."""),

cortex_mf=param.Number(default=3.0*units.mm,doc=""" The magnification
    factor of the cortical sheet, expressed per degree of visual
    angle."""), 
</pre>

<P>This is the basics of how to define the conversions between
units. In the next section we'll look at some of the implementational
details that are required for the conversions to work appropriately.

<H3>Implementational details</H3>

<P>Having defined the numeric conversions we now have to generate
instances of the UnitConversions class for each sheet. The
UnitConversions class has an attribute called the base unit, which is
the default unit it will convert to when it's asked to provide a
numeric value. In our case this is sheet coordinates, which we'll
define by passing the unit abbreviation, conversion and description
into the <code>define_base</code> class method.

<pre> 
UnitConversions.define_base('sc',p.vdeg_area,'SheetCoordinates') 
</pre>

<P>Now it's time to instantiate the UnitConversions class. Since GCAL
has three seperate sheet groups we'll create three instances with
different conversion values for the visual degree unit. The unit
definitions can set up either by passing a list of tuples (containing
the abbreviation, conversion and description) or by using the
<code>define_unit</code> instance method, which accepts a single unit
definition in the form of a tuple at a time.

<pre> 
retina_scales = UnitConversions(units =[('vdeg',p.retina_mf,'Degrees of Visual Angle')])
lgn_scales = UnitConversions(units = [('vdeg',p.lgn_mf,'Degrees of Visual Angle')])
v1_scales = UnitConversions(units = [('vdeg',p.cortex_mf,'Degrees of Visual Angle')])
</pre>

<P>Before we can install these UnitConversions class instances in the
sheets we have to add parameters, which can hold them. This prevents
warnings from being generated.

<pre>
sheet.Sheet._add_parameter("unit_conversions",param.Parameter(None))
pattern.PatternGenerator._add_parameter("unit_conversions",param.Parameter(None))
</pre>

<P>Finally, we have to install the strip_units_hook, which we imported
earlier, in the Number and BoundingRegion parameters. This allows them
to look up the appropriate conversions in their containing
parameterized object and convert the value to sheet coordinates or
whatever other base unit you specified.

<pre> 
param.Number.set_hook = strip_units_hook
topo.base.boundingregion.BoundingRegionParameter.set_hook = strip_units_hook
</pre>

<H3>Define a model using units</H3>

<P>Now that we've defined the units and generated unit conversion
objects for each sheet group, we can actually begin to define the
model in terms of units.

<P>Before we do so, let's clarify how the unit conversion objects
work.  The unit conversion objects let a <code>BoundingBox</code> or
<code>Number</code> know, what conversions to
apply. <code>BoundingBox</code> objects define the radii of
<code>Sheet</code> and <code>Projection</code> objects and can
therefore easily retrieve the <code>UnitConversions</code> objects of
their own <code>Sheet</code> or of the input sheet of a
<code>Projection</code>. The <code>pattern</code> objects, on the
other hand, are instantiated long before they are installed in a
<code>Sheet</code> and therefore cannot retrieve the appropriate
<code>UnitConversions</code> object automatically. Therefore the
<code>unit_conversions</code> parameter needs to be defined for both
<code>pattern</code> and <code>Sheet</code> objects.

<P>A simple example to demonstrate how <code>UnitConversions</code>
objects are passed into <code>pattern</code> objects can be seen
below.

<pre> 
if p.dataset=="Gaussian":
    input_type=pattern.Gaussian
    total_num_inputs=int(p.num_inputs*p.area*p.area)
    inputs=[input_type(x=numbergen.UniformRandom(lbound=-(p.area/2.0+0.25),
                                                 ubound= (p.area/2.0+0.25),seed=12+i),
                       y=numbergen.UniformRandom(lbound=-(p.area/2.0+0.25),
                                                 ubound= (p.area/2.0+0.25),seed=35+i),
                       orientation=numbergen.UniformRandom(lbound=-pi,ubound=pi,seed=21+i),
                       size=0.11785*vdeg, aspect_ratio=4.66667, scale=p.scale, unit_conversions=retina_scales)
            for i in xrange(total_num_inputs)]
</pre>

<P>Since the input patterns will be installed in the retina, we have
to pass the <code>retina_scales</code> object into the
<code>unit_conversions</code> parameter. This also allows us to
specify the size of the pattern in terms of visual degrees, using our
unit abbreviation <code>vdeg</code> and the standard Unum syntax
(i.e. multiplying the value by the desired unit).

<P>We do the exact same thing when defining a sheet:

<pre>
topo.sim['Retina']=sheet.GeneratorSheet(nominal_density=p.retina_density,
    input_generator=combined_inputs, period=1.0, phase=0.05, unit_conversions=retina_scales,
    nominal_bounds=sheet.BoundingBox(radius=((p.area*p.vdeg_area)/2.0)+1.125*p.vdeg_area))
</pre>

<P>Let's do the same for the LGN sheets:

<pre>
for s in ['LGNOn','LGNOff']:
    topo.sim[s]=sheet.optimized.LISSOM_Opt(nominal_density=p.lgn_density,
        nominal_bounds=sheet.BoundingBox(radius=((p.area*p.vdeg_area)/2.0)+0.75*p.vdeg_area),
        output_fns=[transferfn.misc.HalfRectify()],tsettle=2,strict_tsettle=1,
        measure_maps=False, unit_conversions=lgn_scales)
</pre>

<P>Finally, to initialize the connections from retina to LGN, we
create the weights and pass the <code>lgn_scales</code> object to the
pattern as its <code>unit_conversions</code> parameter and pass it to
the <code>topo.sim.connect</code> as its
<code>weights_generator</code> parameter.

<pre>
    lgn_surroundg = pattern.Gaussian(size=0.33334*vdeg,aspect_ratio=1.0,
        output_fns=[transferfn.DivisiveNormalizeL1()], unit_conversions=lgn_scales)

    topo.sim.connect(s,s,delay=0.05,name='LateralGC',dest_port=('Activity'),                     
        activity_group=(0.6,DivideWithConstant(c=0.11)),
        connection_type=projection.SharedWeightCFProjection,
        strength=0.6,weights_generator=lgn_surroundg,
        nominal_bounds_template=sheet.BoundingBox(radius=0.33334*vdeg))
</pre>

<P>We've now gone through all the requirements to specify a model
using real world units. To see an example of a whole model that has
been converted to units have a look at
<code>/examples/gcal_unum.ty</code>.
