<H1>Working with Real World Units in Topographica</H1>

<P>Starting from May 2012, Topographica has limited support to
formally define physical quantities using units. This allows modellers
to express most variables in their models using real world units,
simplifying the tuning process and allowing for a much more intuitive
interaction between experiments and models.

<H3>Limitations and Planned Functionality</H3>

<P>For now there are several limitation to the unit system. The
primary limitation is the lack of support for non-linear
units. Secondly, the unit support is currently limited to the
specification side, i.e. models can be specified in different units
but there is no easy way of displaying scales and spatial units in the
GUI and the outputted files.

<H3>Installing Unum and/or Quantities</H3>

<P>Topographica now supports two units libraries, Unum and Quantities.

<P>The full documentation for the Unum Python library can be accessed <A
href="http://home.scarlet.be/be052320/Unum.html">here</A>. From
there you will also be able to download the package.

<P>The Quantities Python library is available <A
href="http://pypi.python.org/pypi/quantities">here</A>.

<P>The installation is the same as for other Python packages. Simply
extract the .zip archive in a folder, start the version of Python that
is associated with Topographica, go to the extracted folder and run:

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
<code>Conversions</code> objects in each sheet, so that the
appropriate conversion can be applied at the sheet level.

<H3>Importing and Defining Units in the Model.ty file</H3>

<P>We'll demonstrate how to work with units by working our way through
a version of the GCAL model with unit support. You can have a look at
the complete file here. We'll only cover the parts that have been
altered.

<P>We begin by importing unitsupport.

<pre>from.misc import unitsupport</pre>

Next, set the desired unit package either to 'Quantities' or 'Unum'.

<pre>unitsupport.Conversions.set_package('Quantities')</pre>

<P>Both packages include definitions for the most common physical
quantities including all SI and Imperial units. For now we will only
need millimetres and milliseconds. To return these units into the
current namespace, we call:

<pre>
mm = unitsupport.Conversions.get_unit('mm')
ms = unitsupport.Conversions.get_unit('ms')
</pre>

<P>In addition, we want to define distances in different sheets in
degrees of visual angle so we create a new unit by passing an
abbreviation, a conversion and a description to the
<code>create_unit</code> method. Since visual degrees describe
different distances depending on the sheet you are in, we don't yet
provide a conversion.

<pre>
vdeg = unitsupport.Conversions.create_unit('vdeg', None, 'Degrees of Visual Angle')
</pre>

<P>Next we have to define some of the basic conversion or
magnification factors. In the <code>global_params</code> section of
the <code>.ty</code> file we start by defining the number of degrees
of visual angle represented by a unit area in sheet coordinates:

<pre> vdeg_area=param.Number(default=1.33333*vdeg,doc=""" Degrees of
visual angle per unit area in sheet coordinates."""), </pre>

Now we just need to specify the magnification factor of each sheet.
In this case we specify it in the number of millimetres per degree of
visual angle:

<pre> 
retina_mf=param.Number(default=0.2*mm,doc="""The magnification
    factor of the retinal sheet, expressed per degree of visual
    angle."""),

lgn_mf=param.Number(default=0.3*mm,doc=""" The magnification
    factor of the LGN sheets, expressed per degree of visual
    angle."""),

cortex_mf=param.Number(default=3.0*mm,doc=""" The magnification
    factor of the cortical sheet, expressed per degree of visual
    angle."""), 
</pre>

<P>This is the basics of how to define the conversions between
units. In the next section we'll look at some of the implementational
details that are required for the conversions to work appropriately.

<H3>Implementational details</H3>

<P>Having defined the numeric conversions we now have to generate
instances of the UnitConversions class for each sheet. The
UnitConversions class has an attributes called the base units, which
are the default unit it will convert to when it's asked to provide a
numeric value. In our case this is sheet coordinates and the
topographica time base, which we'll define by passing the unit
abbreviation, conversion and description into the
<code>set_base_units</code> class method.

<pre> 
unitsupport.Conversions.set_base_units(spatial = ('sc',p.vdeg_per_sc,'Sheet Coordinates'),
				      temporal = ('tb',p.unit_time,'Topographica time base'))
</pre>

<P>Now it's time to instantiate the Conversions class. Since GCAL has
three seperate sheet groups we'll create three instances with
different conversion values for the visual degree unit. The unit
definitions can be set up calling the conversions class with the units
keyword and passing it a list of tuples containing the unit object and
conversion.

<pre> 
retina_scales = unitsupport.Conversions(units = [(vdeg,p.retina_mf)])
lgn_scales = unitsupport.Conversions(units = [(vdeg,p.lgn_mf)])
v1_scales = unitsupport.Conversions(units = [(vdeg,p.cortex_mf)])
</pre>

<H3>Define a model using units</H3>

<P>Now that we've defined the units and generated Conversions
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
<code>Conversions</code> object automatically. Therefore the
<code>unit_conversions</code> parameter needs to be defined for both
<code>pattern</code> and <code>Sheet</code> objects.

<P>A simple example to demonstrate how <code>UnitConversions</code>
objects are passed into <code>pattern</code> objects can be seen
below.

<pre> 
if p.dataset=="Gaussian":
    input_type=pattern.Gaussian
    total_num_inputs=int(p.num_inputs*p.area*p.area)
    inputs=[input_type(x=numbergen.UniformRandom(lbound=-1.0*vdeg,
                                                 ubound= 1.0*vdeg,seed=12+i,unit_conversions=retina_scales),
                       y=numbergen.UniformRandom(lbound=-1.0*vdeg,
                                                 ubound= 1.0*vdeg,seed=35+i,unit_conversions=retina_scales),
                       orientation=numbergen.UniformRandom(lbound=-pi,ubound=pi,seed=21+i),
                       size=0.11785*vdeg, aspect_ratio=4.66667, scale=p.scale, unit_conversions=retina_scales)
            for i in xrange(total_num_inputs)]
</pre>

<P>Since the input patterns will be installed in the retina, we have
to pass the <code>retina_scales</code> object into the
<code>unit_conversions</code> parameter. This also allows us to
specify the size of the pattern in terms of visual degrees, using our
unit abbreviation <code>vdeg</code> and the standard syntax
(i.e. multiplying the value by the desired unit).

<P>We do the exact same thing when defining a sheet:

<pre>
topo.sim['Retina']=sheet.GeneratorSheet(nominal_density=p.retina_density,
    input_generator=combined_inputs, period=1.0, phase=0.05, unit_conversions=retina_scales,
    nominal_bounds=sheet.BoundingBox(radius=2.16667*vdeg))
</pre>

<P>Let's do the same for the LGN sheets:

<pre>
for s in ['LGNOn','LGNOff']:
    topo.sim[s]=sheet.optimized.LISSOM_Opt(nominal_density=p.lgn_density,
        nominal_bounds=sheet.BoundingBox(radius=1.66667*vdeg),
        output_fns=[transferfn.misc.HalfRectify()],tsettle=2,strict_tsettle=1,
        measure_maps=False, unit_conversions=lgn_scales)
</pre>

<P>Finally, to initialize the connections from retina to LGN, we
create the weights and pass the <code>lgn_scales</code> object to the
pattern as its <code>unit_conversions</code> parameter and pass it to
the <code>topo.sim.connect</code> as its
<code>weights_generator</code> parameter.

<pre>
    lgn_surroundg = pattern.Gaussian(size=0.33333*vdeg,aspect_ratio=1.0,
        output_fns=[transferfn.DivisiveNormalizeL1()], unit_conversions=lgn_scales)

    topo.sim.connect(s,s,delay=0.05,name='LateralGC',dest_port=('Activity'),                     
        activity_group=(0.6,DivideWithConstant(c=0.11)),
        connection_type=projection.SharedWeightCFProjection,
        strength=0.6,weights_generator=lgn_surroundg,
        nominal_bounds_template=sheet.BoundingBox(radius=0.33333*vdeg))
</pre>

<P>We've now gone through all the requirements to specify a model
using real world units. To see an example of a whole model that has
been converted to units have a look at
<code>/examples/gcal_unum.ty</code>.
