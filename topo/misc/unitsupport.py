"""
Unit Support: Classes and methods to allow Unum and Quantities unit
packages to interact with Topographica.
"""


import param
from param.parameterized import bothmethod

from topo import sheet, pattern, base, numbergen
import numpy as np

from nose.plugins.skip import SkipTest

got_unum = False; got_pq=False

try:
    import quantities as pq
    got_pq=True
except: pass

try:
    import unum
    import unum.units
    unum.Unum.UNIT_FORMAT = '%s'
    got_unum=True
except: pass

if True not in [got_unum, got_pq]: raise SkipTest('Could not find Quantities or Unum.')


class strip_pq_hook(param.ParameterizedFunction):
    def __call__(self,obj,val):
        """
        Hook to convert units provided by the quantities package to the base
        unit as defined in the QuantityConversions class and return a float.
        """
        if not hasattr(val,'units'):
            return val

        if hasattr(obj,'unit_conversions'):
            return obj.unit_conversions.convert_to_base(val)
        elif hasattr(obj,'src') and hasattr(obj.src,'unit_conversions'):
            return obj.src.unit_conversions.convert_to_base(val)


class strip_unum_hook(param.ParameterizedFunction):
    def __call__(self,obj,val):
        """
        Hook to convert unum unit objects to the specified base unit and
        return as a float.
        """
        if not val.__class__.__name__ == 'Unum':
            return val

        if hasattr(obj,'unit_conversions'):
            return obj.unit_conversions.convert_to_base(val)
        elif hasattr(obj,'src') and hasattr(obj.src,'unit_conversions'):
            return obj.src.unit_conversions.convert_to_base(val)



class Conversions(object):
    """
    The UnumConversion class holds unit conversions and definitions,
    setting and resetting the unum unit table allowing sheet specific
    conversions to be performed.
    """

    package = 'Quantities'

    initialized = False

    def __init__(self,units=None):
        """
        Initialize this object first by storing the unit
        specification, backing up the current unit table, creating the
        specified unum unit objects and then restoring the backed up
        unit table.
        """
        if not hasattr(self,'_unit_objects'):
            self._unit_objects = {}
        if not hasattr(self,'_unit_specs'):
            self._unit_specs = {}

        if 'unit_conversions' not in sheet.Sheet.params():
            sheet.Sheet._add_parameter("unit_conversions",param.Parameter(None))
        if 'unit_conversions' not in pattern.PatternGenerator.params():
            pattern.PatternGenerator._add_parameter("unit_conversions",param.Parameter(None))
        if 'unit_conversions' not in numbergen.NumberGenerator.params():
            numbergen.NumberGenerator._add_parameter("unit_conversions",param.Parameter(None))

        self.initialize(units)
        self.initialized = True


    @bothmethod
    def declare_unit(obj,unit_key,conversion,name,base=False):
        """
        Create and return unit using specified package.
        """
        if obj.package == 'Quantities':
            unit_obj = pq.UnitQuantity(name, definition=conversion,symbol=unit_key)

            if base:
                unit = [(unit_obj,unit_key,conversion,name)]
                obj._set_base_units_pq(unit)
            else:
                unit = [(unit_obj,conversion)]
                obj.initialize_units(unit)

            return unit_obj

        if obj.package == 'Unum':
            if conversion is None:
                conversion = 0

            obj.del_unit(unit_key)
            unit_obj = unum.Unum.unit(unit_key,conversion,name)

            if base:
                unit = [(unit_obj,unit_key,conversion,name)]
                obj._set_base_units_unum(unit)
            else:
                unit = [(unit_obj,conversion)]
                obj.initialize_units(unit)

            return unit_obj


    @bothmethod
    def get_unit(obj,unit_key,local=True,global_=True):
        """
        Looks up and returns unit_key in local then global unit
        dictionary, if not in either returns None.
        """
        unit = None
        if local and obj.initialized:
            unit = obj._get_local_unit(unit_key)
        if global_ and not unit:
            unit = obj._get_global_unit(unit_key)
        return unit


    @classmethod
    def set_package(obj,package):
        """
        Set the public methods in accordance with the selected package.
        """
        obj.package = package

        public_methods = ['convert_to_base','initialize','initialize_units','set_local_units']
        unum_methods = [obj._convert_to_base_unum,obj._initialize_unum,obj._initialize_units_unum,obj._set_local_units_unum]
        pq_methods = [obj._convert_to_base_pq,obj._initialize_pq,obj._initialize_units_pq,obj._set_local_units_pq]

        if obj.package == 'Unum' and not got_unum:
            raise ImportError('Unum package not installed, call Conversions.set_package(\'Quantities\') or install Unum.')
        if obj.package == 'Quantities' and not got_pq:
            raise ImportError('Quantities package not installed, call Conversions.set_package = (\'Unum\') or install Quantities.')

        if obj.package =='Unum': selected = unum_methods
        else: selected = pq_methods
        [setattr(obj,pub,sel) for (sel,pub) in zip(selected, public_methods)]


    def _convert_to_base_pq(self,val):
        """
        Set local unit definitions and detect unit type then convert
        the value and return as a float.
        """
        self._set_local_units_pq()
        for idx,unit in enumerate(self._base_units):
            try:
                val.rescale(unit[1])
                break
            except: pass
            if idx == len(self._base_units): print 'Cannot convert {0} to base unit.'.format(val)

        return val.rescale(self._base_units[idx][1]).magnitude


    def _convert_to_base_unum(self,val):
        """
        Convert value to base unit using local unit
        definitions and return a float.
        """
        self._ut_bak = unum.Unum.getUnitTable()
        self._set_local_units_unum()
        try:
            val.checkNoUnit()
            val = float(val)
        except unum.ShouldBeUnitlessError:
            for idx,unit in enumerate(self._base_units):
                try:
                    val.asUnit(unit[0])
                    break
                except: pass
                if idx == len(self._base_units): print 'Cannot convert {0} to base unit.'.format(val)
            val = float(val.asUnit(self._base_units[idx][0])/self._base_units[idx][0])

        unum.Unum.reset(self._ut_bak)

        return val


    @bothmethod
    def _del_unit(obj,unit_key):
        """
        Delete specified unit definition from global unum unit table.
        """
        unit_table = unum.Unum.getUnitTable()
        if unit_key in unit_table.keys():
            del unit_table[unit_key]
        unum.Unum.reset(unit_table)


    @bothmethod
    def _get_local_unit(self,unit_key):
        """
        Returns local unit object or if nonexistent None.
        """
        if unit_key in self._unit_objects.keys():
            return self._unit_objects[unit_key]
        else:
            return None


    @bothmethod
    def _get_global_unit(obj,unit_key):
        if obj.package == 'Unum': return getattr(unum.units,unit_key)
        elif obj.package == 'Quantities': return pq.registry.unit_registry[unit_key]
        else: return None


    def _initialize_pq(self,units):
        """
        Initialize param and Topographica to deal with Quantities unit
        package by installing appropriate set hook on parameters and
        initializing specified units.
        """
        param.Number.set_hook = strip_pq_hook
        base.boundingregion.BoundingRegionParameter.set_hook = strip_pq_hook

        self.initialize_units(units)


    def _initialize_unum(self,units):
        """
        Initialize param and Topographica to deal with Unum unit
        package by installing appropriate set hook on parameters and
        initializing specified units.
        """
        param.Number.set_hook = strip_unum_hook
        base.boundingregion.BoundingRegionParameter.set_hook = strip_unum_hook

        self.initialize_units(units)


    @bothmethod
    def _initialize_units_pq(obj,units):
        """
        Initialize specified units using Quantities unit package.
        """
        if not hasattr(obj,'_unit_objects'):
            obj._unit_objects = {}
        if not hasattr(obj,'_unit_specs'):
            obj._unit_specs = {}

        for unit in units:
            unit_key = unit[0].symbol
            obj._unit_objects[unit_key] = unit[0]
            obj._unit_specs[unit_key] = (unit[1],unit[0].name)


    @bothmethod
    def _initialize_units_unum(obj,units):
        """
        Initialize specified units using Unum unit package.
        """
        if not hasattr(obj,'_unit_objects'):
            obj._unit_objects = {}
        if not hasattr(obj,'_unit_specs'):
            obj._unit_specs = {}

        for unit in units:
            unit_key = unit[0].strUnit()
            obj._unit_objects[unit_key] = unit[0]
            obj._unit_specs[unit_key] = (unit[1],unit[0].getUnitTable()[unit_key][2])


    @bothmethod
    def _set_base_units_pq(obj,units):
        """
        Set base unit, which is used to interface with Topographicas
        coordinate system, using Quantities unit package.
        """
        if not hasattr(obj,'_base_units'):
            obj._base_units = []
        for unit in units:
            obj._base_units.append((unit[0],unit[1],unit[2],unit[3]))


    @bothmethod
    def _set_base_units_unum(obj,units):
        """
        Set base units, which are used to interface with Topographicas
        coordinate system, using Unum unit package.
        """
        if not hasattr(obj,'_base_units'):
            obj._base_units = []
        for unit in units:
            obj._base_units.append((unit[0],unit[1],unit[2],unit[3]))


    def _set_local_units_pq(self):
        """
        Set the local unit definitions according to stored unit definitions and using
        the Quantities unit package.
        """
        for unit in self._unit_specs.keys():
            self._unit_objects[unit]._conv_ref = np.array(self._unit_specs[unit][0].magnitude) * self._unit_specs[unit][0].units.simplified
        for idx,unit in enumerate(self._base_units):
            self._base_units[idx][0]._conv_ref = np.array(unit[2].magnitude) * unit[2].units.simplified


    def _set_local_units_unum(self):
        """
        Set the local unit definitions according to stored unit definitions and using
        the Quantities unit package.
        """
        for unit_key in self._unit_specs.keys():
            self.del_unit(unit_key)
            unit_spec = self._unit_specs[unit_key]
            self._unit_objects[unit_key] = unum.Unum.unit(unit_key,unit_spec[0],unit_spec[1])
        for unit in self._base_units:
            self.del_unit(unit[1])
            unum.Unum.unit(unit[1],unit[2],unit[3])

