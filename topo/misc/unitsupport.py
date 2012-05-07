"""
Unit Support: Classes and methods to allow Unum and Quantities unit
packages to interact with Topographica.

$Id$
"""
__version__ = "$Revision$"

import param
from param.parameterized import bothmethod

from topo import sheet, pattern, base
import numpy as np

got_unum = False; got_pq=False
try:  import quantities as pq; got_pq=True
except: pass

try: import unum; import unum.units; got_unum=True
except: pass

if True not in [got_unum, got_pq]: raise 'No unit package installed'

def strip_pq_hook(clas,obj,val):
    """
    Hook to convert units provided by the quantities package to the base
    unit as defined in the QuantityConversions class and return a float.
    """
    if hasattr(val,'units') and hasattr(obj,'unit_conversions'):
        val = obj.unit_conversions.convert_to_base(val)
    elif hasattr(val,'units') and hasattr(obj.src,'unit_conversions'):
        val = obj.src.unit_conversions.convert_to_base(val)
    return val

def strip_unum_hook(cls,obj, val):
    """
    Hook to convert unum unit objects to the specified base unit and
    return as a float.
    """

    if (val.__class__.__name__ == 'Unum') and hasattr(obj,'unit_conversions'):
        try:
            val.checkNoUnit()
            val = float(val)
        except unum.ShouldBeUnitlessError:
            val = obj.unit_conversions.convert_to_base(val)
    elif (val.__class__.__name__ == 'Unum') and hasattr(obj.src,'unit_conversions'):
        try:
            val.checkNoUnit()
            val = float(val)
        except unum.ShouldBeUnitlessError:
            val = obj.src.unit_conversions.convert_to_base(val)
    return val

class Conversions(object):
    """
    The UnumConversion class holds unit conversions and definitions,
    setting and resetting the unum unit table allowing sheet specific
    conversions to be performed.
    """
    
    #__slots__ = ['_base_unit','_unit_objects','_unit_specs','_ut_bak','package']

    package = 'Quantities'

    _public_methods = ['convert_to_base']
    _unum_methods = ['_convert_to_base_unum']
    _quantities_methods = ['_convert_to_base_pq']

    def __init__(self,units=None):
        """
        Initialize this object first by storing the unit
        specification, backing up the current unit table, creating the
        specified unum unit objects and then restoring the backed up
        unit table.
        """
        if self.package == 'Unum' and not got_unum: raise 'Unum package not installed, set Conversions.package = \'Quantities\' or install Unum.'
        if self.package == 'Quantities' and not got_pq: raise 'Quantities package not installed, set Conversions.package = \'Unum\' or install Quantities.'

        self._unit_objects = {}
        self._unit_specs = {}

        public_methods = ['convert_to_base','initialize','initialize_units','set_local_units']
        unum_methods = [self._convert_to_base_unum,self._initialize_unum,self._initialize_units_unum,self._set_local_units_unum]
        pq_methods = [self._convert_to_base_pq,self._initialize_pq,self._initialize_units_pq,self._set_local_units_pq]

        if self.package =='Unum': selected = unum_methods
        else: selected = pq_methods
        [setattr(self, pub,sel) for (sel,pub) in zip(selected, public_methods)]

        self.initialize(units)

        if 'unit_conversions' not in sheet.Sheet.params():
            sheet.Sheet._add_parameter("unit_conversions",param.Parameter(None))
        if 'unit_conversions' not in pattern.PatternGenerator.params():
            pattern.PatternGenerator._add_parameter("unit_conversions",param.Parameter(None))            

    @bothmethod
    def set_base_unit(obj,unit_key,conversion,name):
        """
        Set base unit using specified unit package.
        """
        if obj.package == 'Unum':
            obj._set_base_unit_unum(unit_key,conversion,name)
        elif obj.package == 'Quantities':
            obj._set_base_unit_pq(unit_key,conversion,name)

    @bothmethod
    def create_unit(obj,unit_key,conversion,name):
        """
        Create and return unit using specified package.
        """
        if obj.package == 'Quantities':
            return pq.UnitQuantity(name, definition=conversion,symbol=unit_key)
        if obj.package == 'Unum':
            if conversion == None:
                conversion = 0
            return unum.Unum.unit(unit_key,conversion,name)

    @bothmethod
    def del_unit(obj,unit_key):
        """
        Delete specified unit definition from global unum unit table.
        """
        unit_table = unum.Unum.getUnitTable()
        if unit_key in unit_table.keys():
            del unit_table[unit_key]
        unum.Unum.reset(unit_table)

    def get_local_unit(self,unit_key):
        """
        Returns local unit object or if nonexistent None.
        """
        if unit_key in self._unit_objects.keys():
            return self._unit_objects[unit_key]
        else:
            return None

    @bothmethod
    def get_unit(obj,unit_key):
        if obj.package == 'Unum': return getattr(unum.units,unit_key)
        elif obj.package == 'Quantities': return pq.registry.unit_registry[unit_key]
        elif unit_key in obj._unit_objects.keys(): return obj._unit_objects[unit_key]

    def _convert_to_base_pq(self,val):
        """
        Convert value to base unit using local unit definitions and
        return a float.
        """
        self._set_local_units_pq()

        return val.rescale(self._base_unit[1]).magnitude

    def _convert_to_base_unum(self,val):
        """
        Convert value to base unit using local unit
        definitions and return a float.
        """
        self._ut_bak = unum.Unum.getUnitTable()
        self._set_local_units_unum()
        val = float(val.asUnit(self._base_unit[0])/self._base_unit[0])
        unum.Unum.reset(self._ut_bak)

        return val

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

    def _initialize_units_pq(self,units):
        """
        Initialize specified units using Quantities unit package.
        """
        for unit in units:
            unit_key = unit[0].symbol
            self._unit_objects[unit_key] = unit[0]
            self._unit_specs[unit_key] = (unit[1],unit[0].name)

    def _initialize_units_unum(self,units):
        """
        Initialize specified units using Unum unit package.
        """
        for unit in units:
            unit_key = unit[0].strUnit()
            if unit_key[0] == '[':
                unit_key = unit_key[1:-1]
            self._unit_objects[unit_key] = unit[0]
            self._unit_specs[unit_key] = (unit[1],unit[0].getUnitTable()[unit_key][2])

    @bothmethod
    def _set_base_unit_pq(obj,unit_key,conversion,name):
        """
        Set base unit, which is used to interface with Topographicas
        coordinate system, using Quantities unit package.
        """
        base_unit = pq.UnitQuantity(name, definition=conversion, symbol=unit_key)
        obj._base_unit = (base_unit,unit_key,conversion,name)

    @bothmethod
    def _set_base_unit_unum(obj,unit_key,conversion,name):
        """
        Set base unit, which is used to interface with Topographicas
        coordinate system, using Unum unit package.
        """    
        obj.del_unit(unit_key)
        obj._base_unit = (unum.Unum.unit(unit_key,conversion,name),unit_key,conversion,name)

    def _set_local_units_pq(self):
        """
        Set the local unit definitions according to stored unit definitions and using
        the Quantities unit package.
        """
        for unit in self._unit_specs.keys():
            self._unit_objects[unit]._conv_ref = np.array(self._unit_specs[unit][0].magnitude) * self._unit_specs[unit][0].units.simplified
            self._base_unit[0]._conv_ref = np.array(self._base_unit[2].magnitude) * self._base_unit[2].units.simplified
    
    def _set_local_units_unum(self):
        """
        Set the local unit definitions according to stored unit definitions and using
        the Quantities unit package.
        """
        for unit_key in self._unit_specs.keys():
            self.del_unit(unit_key)
            unit_spec = self._unit_specs[unit_key]
            self._unit_objects[unit_key] = unum.Unum.unit(unit_key,unit_spec[0],unit_spec[1]) 
