"""
Compose

Utilities for manipulating SVGs and for applying SVG templates created
in Inkscape. SVG templates allow publication quality SVGs to be built
that dynamically reflect the available simulation data.
"""

import os, shutil, re, string
import xml.etree.ElementTree as etree
etree12 = etree.VERSION[0:3] == '1.2'

SVG_NS = 'http://www.w3.org/2000/svg'
sodipodi = 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd'
cc = 'http://creativecommons.org/ns#'
inkscape = 'http://www.inkscape.org/namespaces/inkscape'
xlink = 'http://www.w3.org/1999/xlink'

namespaces = {SVG_NS:'', sodipodi: 'sodipodi',
              cc : 'cc', inkscape: 'inkscape',
              xlink:'xlink'}

def fixtag(tag, namespaces):
   """
   Monkey patch for Python 2.6 to work around deficiencies in etree 1.2.
   """
    # stackoverflow.com/questions/8113296
    #/supressing-namespace-prefixes-in-elementtree-1-2
   if isinstance(tag, etree.QName): tag = tag.text
   namespace_uri, tag = string.split(tag[1:], "}", 1)
   prefix = namespaces.get(namespace_uri)
   if namespace_uri not in namespaces:
      prefix = etree._namespace_map.get(namespace_uri)
      if namespace_uri not in etree._namespace_map:
         prefix = "ns%d" % len(namespaces)
      namespaces[namespace_uri] = prefix
      if prefix == "xml":
         xmlns = None
      else:
         if prefix is not None: nsprefix = ':' + prefix
         else:                  nsprefix = ''
         xmlns = ("xmlns%s" % nsprefix, namespace_uri)
   else:  xmlns = None
   if prefix is not None:
      prefix += ":"
   else: prefix = ''
   return "%s%s" % (prefix, tag), xmlns

if etree12:
    etree.fixtag = fixtag
    namespaces[SVG_NS] = None
    etree._namespace_map.update(namespaces)
else:
    for ns in namespaces:
        etree.register_namespace(namespaces[ns],ns)


class SVGUtils(object):

   @staticmethod
   def load(fname):
       """
       Given a filename, return an SVG root object.
       """
       with open(fname) as f:
           return etree.parse(f).getroot()

   @staticmethod
   def group(svg):
       """
       Given an SVG root object, return an SVG group.
       """
       group = etree.Element('{'+SVG_NS+'}'+"g")
       for e in svg.getchildren():
           group.append(e)
       return group

   @staticmethod
   def string(svg):
       string = "<?xml version='1.0' encoding='ASCII' standalone='yes'?>\n"
       string += etree.tostring(svg)
       return string

   @staticmethod
   def save(svg, fname):
       """
       Given an SVG root object, save an SVG file.
       """
       with open(fname, 'w') as f:
           f.write(SVGUtils.string(svg))

   @staticmethod
   def size(svg, size=(None,None)):
       """
       If size not specified, returns the element size, otherwise sets
       the size.
       """
       if size == (None, None):
           width = svg.get('width')
           height = svg.get('height')
           return width, height
       else:
           width, height = size
           svg.set('width', width)
           svg.set('height', height)
           return width, height

   @staticmethod
   def inkscape_layers(svg, layer_fn):
       """
       Utility that applies a function that processes Inkscape layers.
       """
       for el in svg.findall('.//{%s}g' % SVG_NS):
           groupmode_match = '{%s}groupmode' % inkscape
           if groupmode_match in el.attrib:
              if el.attrib[groupmode_match] == 'layer':
                 settings = el.attrib['style'].rsplit(';')
                 hidden = "display:none" in settings
                 layer_fn(el, hidden)
       return svg

   @staticmethod
   def resize(svg, factor=1.0):
      """
      Resize SVG by factor. Note, this should be applied only be
      applied once per svg object as it overwrites the viewBox
      attribute of the root node.
      """
      if factor ==1.0: return svg
      root_pattern = '.'
      size = SVGUtils.size(svg)
      for root in svg.findall(root_pattern):
         root.attrib['width']= str(float(size[0])*factor)
         root.attrib['height']= str(float(size[1])*factor)
         root.attrib['viewBox'] = "%s 0 1 %s" % (str(float(size[0])/ 2), size[1])
      return svg

   @staticmethod
   def toggle_layers(svg, layers):
      """
      Utility to toggle SVG layers according to the Inkscape layer
      name. The layers dictionary is a dictionary of layer names and
      the boolean specifying whether the layer is active or not.
      """
      def toggle_layer(layer, hidden):
         styles = ["display:none", "display:inline"]
         label_match = '{%s}label' % inkscape
         label = layer.attrib[label_match]
         if label in layers:
            ind = int(layers[label])
            settings = layer.attrib['style'].rsplit(';')
            new_settings = [styles[ind] if s in styles else s 
                            for s in settings]
            layer.attrib['style'] = ';'.join(new_settings)

      return SVGUtils.inkscape_layers(svg, toggle_layer)


   @staticmethod
   def composite(svg, basepath):
      """
      Given an SVG object and a directory, look for SVG rectangles
      with labels that reference other SVG files and embed them. The
      labels are expected to contain relative paths made absolute
      according to the given basepath.
      """
      def embed_SVG(layer, hidden):

         if hidden: return
         rect_pattern = ".//{%s}rect" % SVG_NS
         for rect in layer.findall(rect_pattern):
            label_pattern = '{%s}label' % inkscape
            name = rect.attrib.get(label_pattern, None)
            if (name is None) or (name[-4:] != '.svg'): continue
            component_path = os.path.join(basepath, name)
            if not os.path.exists(component_path):
               print 'Skipping relative link %r (file not found)' % name
            component_svg = SVGUtils.load(component_path)
            # Following 2 lines fixes pyplot generated SVG.
            w,h = SVGUtils.size(component_svg)
            SVGUtils.size(component_svg, (w.replace('pt', ''),
                                          h.replace('pt', '')))
            # The x,y, width and height of the rectangle
            (x,y,w,h) = (rect.attrib['x'], rect.attrib['y'],
                         rect.attrib['width'], rect.attrib['height'])

            op = rect.attrib.get('transform', "translate(0.0,0.0)")
            if op.startswith('translate'):
               offset = re.split("\(|,|\)", op)[1:3]
               x_offset, y_offset = (float(el) for el in offset)
            else: 
               print "Please apply transformation to rectangle %r." % name

            rect.clear(); rect.tag = 'g'
            rect[:] = SVGUtils.group(component_svg)
            component_w, component_h = SVGUtils.size(component_svg)
            translation = "translate(%s, %s)" % (float(x) + x_offset, 
                                                 float(y) + y_offset,)
            scaling = "scale(%s, %s)" %  (float(w)/float(component_w),
                                          float(h)/float(component_h))
            rect.attrib["transform"] = (translation + ' ' + scaling)

      return SVGUtils.inkscape_layers(svg, embed_SVG)

   @staticmethod
   def encoder(filename):
      """
      Default encoder that takes a filename and returns a base64
      encoding.
      """
      with open(filename,"rb") as f:
         return f.read().encode("base64")

   @staticmethod
   def embed_rasters(svg, basepath, encoder=None):
      """
      Embeds linked images as base64 into the SVG object relative to
      basepath. The default encoder embeds the exact file contents but
      a custom encoder could manipulate images before embedding
      (e.g. resizing certain files using PIL).
      """
      encoder = SVGUtils.encoder if encoder is None else encoder
      supported_extensions = ['png', 'jpg', 'jpeg']
      def embed_raster(layer, hidden):
         if hidden: return
         for el in layer.findall('.//{%s}image' % SVG_NS):
            href_pattern = '{http://www.w3.org/1999/xlink}href'
            href = el.attrib[href_pattern]
            extension = href[-10:].rsplit('.')[-1]
            if os.path.isfile(href):
               im_path = href
            else:
               im_path = os.path.join(basepath,href)
            exists = os.path.exists(im_path)
            if exists and extension in supported_extensions:
               prefix = 'data:image/%s;base64,' % extension
               el.attrib[href_pattern] = prefix + encoder(im_path)
            elif (extension in supported_extensions):
               print 'Skipping relative link %r (file not found)' % href
      return SVGUtils.inkscape_layers(svg, embed_raster)

   @staticmethod
   def string_replace(svg, mapping):
      """
      Simple string substitutions may be made according
      to the mapping dictionary.These substitutions are
      applied across the XML string making the use of
      unique tokens essential.
      """
      input_str = SVGUtils.string(svg)
      for name in mapping:
         input_str = input_str.replace(name, str(mapping[name]))
      return etree.fromstring(input_str)



def apply_template(template_path, output_path, mapping={}, layers={}, 
                   embed=True, size_factor=1.0):
    """
    Helper method that takes a path to an Inkscape template, toggles
    the specified layers, applies string_replace according to mapping,
    composites the template, optionally embeds an raster images and
    saves the result to output_path. The SVG string itself is also
    returned.
    """
    svg = SVGUtils.load(template_path)
    (basepath, _) = os.path.split(output_path)
    svg = SVGUtils.toggle_layers(svg, layers)
    svg = SVGUtils.string_replace(svg, mapping)
    if embed: svg = SVGUtils.embed_rasters(svg, basepath)
    svg = SVGUtils.composite(svg, basepath)
    svg = SVGUtils.resize(svg, size_factor)
    with open(output_path, 'w') as output_file:
        output_file.write(SVGUtils.string(svg))
    return SVGUtils.string(svg)
