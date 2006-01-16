# This file is part of SloppyPlot, a scientific plotting tool.
# Copyright (C) 2005 Niklas Volbers
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# $HeadURL$
# $Id$


import re
import inspect

from main import *
from typed_containers import TypedList, TypedDict


__all__ = ["VProperty", "VP",
           "Validator", "ValidatorList", "RequireOne", "RequireAll",
           "VMap", "VBMap", "VString", "VInteger", "VFloat", "VBoolean",
           "VRegexp", "VUnicode", "VList", "VDictionary", "VRange",
           "VInstance", "VChoice"]


#------------------------------------------------------------------------------

               
class VProperty(Property):

    " Validated Property. "
    
    def __init__(self, *validators, **kwargs):
        self.blurb = kwargs.get('blurb', None)
        self.doc = kwargs.get('doc', None)
        self.validator = construct_validator_list(*validators, **kwargs)
        self.on_default = self.validator.on_default
        
    def set_value(self, owner, key, value):
        try:
            if self.validator.is_mapping is False:
                owner._values[key] = self.validator.check(value)
            else:
                owner._values[key] = value
                owner._mvalues[key] = self.validator.check(value)
        except Exception,msg:
            raise PropertyError("Failed to set property '%s' of container '%s' to '%s': Value must be %s." %
                                (key, owner.__class__.__name__, value, str(msg)))

    def get_default(self, owner, key):
        return self.on_default()

    def check(self, value):
        try:
            return self.validator.check(value)
        except Exception,msg:
            raise PropertyError("Property check failed: Value '%s' must be %s." %
                                (value, str(msg)))

VP = VProperty


#------------------------------------------------------------------------------
# Validators
#

class Validator:
    is_mapping = False



class VMap(Validator):

    """ Map the given value according to the dict. """

    is_mapping = True
    
    def __init__(self, adict):
        if not isinstance(adict, dict):
            raise TypeError("Mapping for VMap validator must be a dictionary, not a %s" % type(adict))
        self.dict = adict
        self.values = adict.keys()

    def check(self, value):
        try:
            return self.dict[value]
        except KeyError:
            raise ValueError("one of '%s'" % (self.values))

    def is_mapping(self):
        return True

    

class VBMap(VMap):

    """
    Map the given value according to the dict
    _or_ accept the given value if it is in the dict's values.
    """

    is_mapping = True
        
    def __init__(self, adict):
        VMap.__init__(self, adict)
        self.values = adict.values()

    def check(self, value):
        if value in self.values:
            return value
        try:
            return self.dict[value]
        except KeyError:
            raise ValueError("one of '%s' or '%s'" % (self.dict.keys(), self.dict.values()))

    def is_mapping(self):
        return True


class VChoice(Validator):

    def __init__(self, alist):
        self.values = alist

    def check(self, value):
        if value in self.values:
            return value
        raise ValueError("one of %s" % str(self.values))



class VNone(Validator):

    def check(self, value):
        if value is None:
            return None
        raise TypeError("None")


class VBoolean(Validator):

    def check(self, value):
        if isinstance(value, bool):
            return bool(value)
        elif isinstance(value, basestring):
            if "true".find(value.lower()) > -1:
                return True
            elif "false".find(value.lower()) > -1:
                return False
        elif isinstance(value, (int,float)):
            return bool(value)

        raise ValueError("a valid True/False value")


class VString(Validator):
    def check(self, value):
        try:
            if value is None:
                raise
            return str(value)
        except:
            raise TypeError("a string")


class VUnicode(Validator):
    def check(self, value):
        try:
            if value is None:
                raise
            return unicode(value)
        except:
            raise TypeError("a unicode string")


class VInteger(Validator):
    def check(self, value):
        try:
            return int(value)
        except:
            raise TypeError("an integer")
            


class VFloat(Validator):
    def check(self, value):
        try:
            return float(value)
        except:
            raise TypeError("a floating point number")
    

class VRegexp(Validator):
    
    """ Check value against a given regular expression. """
    
    def __init__(self, regexp):
        self.regexp=regexp
        self._expression = re.compile(regexp)

    def check(self, value):
        try:
            match = self._expression.match(value)
            if match is not None:
                return value
        except:
            pass
        
        raise ValueError("a string matching the regular expression %s" % self.regexp)      

      

class VList(Validator):

    def __init__(self, *validators):        
        self.item_validator = construct_validator_list(*validators)

    def check(self, value):
        def check_item(v):
            try:
                return self.item_validator.check(v)
            except Exception, msg:
                raise PropertyError("Failed to set item in list property '%s' of container '%s' to '%s': Value must be %s." %
                                    (key, owner.__class__.__name__, value, str(msg)))
        if isinstance(value, TypedList):
            value.check_item = check_item
            return value
        if isinstance(value, list):
            return TypedList(check_item, value)
        else:            
            raise TypeError("a list")

class VDictionary(Validator):

    def __init__(self, *validators):
        self.item_validator = construct_validator_list(*validators)

    def check(self, value):
        def check_item(v):
            try:
                return self.item_validator.check(v)
            except:
                raise ValueError("a dictionary")
            
        if isinstance(value, TypedDict):
            value.check_item = check_item
            return value
        elif isinstance(value, dict):
            return TypedDict(check_item, value)
        else:            
            raise TypeError("a dictionary")

    
class VRange(Validator):

    """
    Check if the given value is in between the given bounds [min:max].
    If min or max is None, then the appropriate direction is unbound.
    A value of None is always invalid.
    """
     
    def __init__(self, min=None, max=None):
        self.min=min
        self.max=max

    def check(self, value):
        if (value is None) \
               or (self.min is not None and value < self.min) \
               or (self.max is not None and value > self.max):
            raise ValueError("in the range [%s:%s]" % (self.min, self.max))
        return value

#     def get_description(self):
#         return "Valid range: %s:%s" % (self.min or "", self.max or "")


class VInstance(Validator):

    def __init__(self, _type):
        self.type = _type

    def check(self, value):
        if isinstance(value, self.type):
            return value
        else:
            raise TypeError("an instance of %s" % self.type)


#------------------------------------------------------------------------------
# Validator Lists

class ValidatorList(Validator):

    def __init__(self, *validators, **kwargs):

        default = kwargs.get('default', Undefined)
        on_default = kwargs.get('on_default', lambda: default)

        # init validators
        vlist = []
        is_mapping = False
        for item in validators:
            if isinstance(item, Validator):
                vlist.append(item)
                is_mapping = is_mapping or item.is_mapping
            elif item is None:
                vlist.append(VNone())
                is_mapping = is_mapping or VNone.is_mapping
                on_default = lambda: None
            elif isinstance(item, dict):
                # 1:1 mapping if there is only a map as validator
                if len(validators) == 1:
                    vlist.append(VBMap(item))
                else:
                    vlist.append(VMap(item))
                is_mapping = True
                if len(item) > 0:
                    on_default = lambda: item.keys()[0]
            elif isinstance(item, (list,tuple)):
                vlist.append(VChoice(list(item)))
                if len(item) > 0:
                    on_default = lambda: item[0]
            elif isinstance(item, Property):
                vlist.extend(item.validator.vlist)
                is_mapping = is_mapping or item.validator.is_mapping
                on_default = item.on_default
            elif issubclass(item, Property):
                i = item()
                vlist.extend(i.validator.vlist)
                is_mapping = is_mapping or i.validator.is_mapping
                on_default = i.on_default
            elif inspect.isclass(item):
                vlist.append(VInstance(item))
            else:
                raise TypeError("Unknown validator: %s" % item)

        self.on_default = on_default
        self.vlist = vlist
        self.is_mapping = is_mapping

class RequireOne(ValidatorList):

    def check(self, value):
        if len(self.vlist) == 0:
            return value
        
        for validator in self.vlist:
            try:
                value = validator.check(value)
            except:
                continue
            else:
                return value
        raise       
        

class RequireAll(ValidatorList):

    def check(self, value):       
        try:
            for validator in self.vlist:
                value = validator.check(value)
        except:
            # TODO: construct error message
            raise

        return value

def construct_validator_list(*validators, **kwargs):
    if len(validators) == 0:
        return RequireOne(**kwargs)
    elif len(validators) == 1 and isinstance(validators[0], ValidatorList):
            return validators[0] # TODO: what about **kwargs?
    else:
        return RequireOne(*validators, **kwargs)
