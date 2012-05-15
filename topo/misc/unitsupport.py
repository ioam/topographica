"""
Unit Support: Classes and methods to allow Unum and Quantities unit
packages to interact with Topographica.

$Id$
"""

__version__ = "$Revision$"

import param
from param.parameterized import bothmethod

from topo import sheet, pattern, base, numbergen
import numpy as np

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

if True not in [got_unum, got_pq]: raise 'No unit package installed'


def strip_pq_hook(clas,obj,val):
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



def strip_unum_hook(cls,obj, val):
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
    _unit_types = {'temporal':'s','spatial':'m'}

    def __init__(self,units=None):
        """
        Initialize this object first by storing the unit
        specification, backing up the current unit table, creating the
        specified unum unit objects and then restoring the backed up
        unit table.
        """
        self._unit_objects = {}
        self._unit_specs = {}

        if 'unit_conversions' not in sheet.Sheet.params():
            sheet.Sheet._add_parameter("unit_conversions",param.Parameter(None))
        if 'unit_conversions' not in pattern.PatternGenerator.params():
            pattern.PatternGenerator._add_parameter("unit_conversions",param.Parameter(None))            
        if 'unit_conversions' not in numbergen.NumberGenerator.params():
            numbergen.NumberGenerator._add_parameter("unit_conversions",param.Parameter(None))

        self.initialize(units)


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


    @bothmethod
    def set_base_units(obj,spatial=None,temporal=None):
        """
        Set base unit using specified unit package.
        """
        if obj.package == 'Unum':
            obj._set_base_units_unum(spatial,temporal)
        elif obj.package == 'Quantities':
            obj._set_base_units_pq(spatial,temporal)
  

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
            raise 'Unum package not installed, call Conversions.set_package(\'Quantities\') or install Unum.'
        if obj.package == 'Quantities' and not got_pq: 
            raise 'Quantities package not installed, call Conversions.set_package = (\'Unum\') or install Quantities.'

        if obj.package =='Unum': selected = unum_methods
        else: selected = pq_methods
        [setattr(obj,pub,sel) for (sel,pub) in zip(selected, public_methods)]


    @bothmethod
    def del_unit(obj,unit_key):
        """
        Delete specified unit definition from global unum unit table.
        """
        unit_table = unum.Unum.getUnitTable()
        if unit_key in unit_table.keys():
            del unit_table[unit_key]
        unum.Unum.reset(unit_table)


    def _convert_to_base_pq(self,val):
        """
        Set local unit definitions and detect unit type then convert
        the value and return as a float.
        """
        self._set_local_units_pq()
        for key in self._base_units.keys():
            try:
                val.rescale(self._unit_types[key])
                break
            except: pass

        return val.rescale(self._base_units[key][1]).magnitude


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
            for key in self._base_units.keys():
                try:
                    val.asUnit(self.get_unit(self._unit_types[key]))
                    break
                except: pass
            val = float(val.asUnit(self._base_units[key][0])/self._base_units[key][0])

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
            self._unit_objects[unit_key] = unit[0]
            self._unit_specs[unit_key] = (unit[1],unit[0].getUnitTable()[unit_key][2])


    @bothmethod
    def _set_base_units_pq(obj,spatial,temporal):
        """
        Set base unit, which is used to interface with Topographicas
        coordinate system, using Quantities unit package.
        """
        obj._base_units = {}
        if spatial:
            base_unit = pq.UnitQuantity(spatial[2], definition=spatial[1], symbol=spatial[0])
            obj._base_units['spatial'] = (base_unit,spatial[0],spatial[1],spatial[2])
        if temporal:
            base_unit = pq.UnitQuantity(temporal[2], definition=temporal[1], symbol=temporal[0])
            obj._base_units['temporal'] = (base_unit,temporal[0],temporal[1],temporal[2])

    @bothmethod
    def _set_base_units_unum(obj,spatial,temporal):
        """
        Set base units, which are used to interface with Topographicas
        coordinate system, using Unum unit package.
        """
        obj._base_units = {}
        if spatial:
            obj.del_unit(spatial[0])
            base_unit = unum.Unum.unit(spatial[0],spatial[1],spatial[2])
            obj._base_units['spatial'] = (base_unit,spatial[0],spatial[1],spatial[2])
        if temporal:
            obj.del_unit(temporal[0])
            base_unit = unum.Unum.unit(temporal[0],temporal[1],temporal[2])
            obj._base_units['temporal'] = (base_unit,temporal[0],temporal[1],temporal[2])


    def _set_local_units_pq(self):
        """
        Set the local unit definitions according to stored unit definitions and using
        the Quantities unit package.
        """
        for unit in self._unit_specs.keys():
            self._unit_objects[unit]._conv_ref = np.array(self._unit_specs[unit][0].magnitude) * self._unit_specs[unit][0].units.simplified
        for key in self._base_units.keys():    
            self._base_units[key][0]._conv_ref = np.array(self._base_units[key][2].magnitude) * self._base_units[key][2].units.simplified
    

    def _set_local_units_unum(self):
        """
        Set the local unit definitions according to stored unit definitions and using
        the Quantities unit package.
        """
        for unit_key in self._unit_specs.keys():
            self.del_unit(unit_key)
            unit_spec = self._unit_specs[unit_key]
            self._unit_objects[unit_key] = unum.Unum.unit(unit_key,unit_spec[0],unit_spec[1]) 
