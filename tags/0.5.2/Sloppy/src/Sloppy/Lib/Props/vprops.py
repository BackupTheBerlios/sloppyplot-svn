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
           "VChoice", "VString", "VInteger", "VFloat", "VBoolean",
           "VRegexp", "VUnicode", "VList", "VDictionary", "VRange",
           "VInstance"]


#------------------------------------------------------------------------------

               
class VProperty(Property):

    " Validated Property. "
    
    def __init__(self, *validators, **kwargs):
        self.blurb = kwargs.get('blurb', None)
        self.doc = kwargs.get('doc', None)

        default = kwargs.pop('default', Undefined)
        self.validator = construct_validator_list(*validators, **kwargs)
        if default is not Undefined:
            self.on_default = lambda: default
        else:
            self.on_default = self.validator.on_default
        
    def set_value(self, owner, key, value):
        try:
            owner._values[key] = self.validator.check(value)
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
    pass


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



class VInstance(Validator):

    def __init__(self, _instance):
        self.instance = _instance

    def check(self, value):
        if isinstance(value, self.instance):
            return value
        else:
            raise InstanceError("an instance of %s" % self.instance)



class VChoice(Validator):
   
    def __init__(self, alist):
        self.choices = alist
        
    def check(self, value):
        if value in self.choices:
            return value
        raise ValueError("one of %s" % str(self.choices))



#------------------------------------------------------------------------------



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



#------------------------------------------------------------------------------
# Validator Lists

class ValidatorList(Validator):

    def __init__(self, *validators, **kwargs):

        default = kwargs.get('default', Undefined)
        on_default = kwargs.get('on_default', lambda: default)

        # helper function
        def simplify_validator(validator):
            " Simplify validator if it has a length of 1. "
            if len(validator.vlist) == 1:
                return validator.vlist[0]
            else:
                return validator
        
        # init validators
        vlist = []
        for item in validators:
            if isinstance(item, Validator):
                vlist.append(item)
            elif item is None:
                vlist.append(VNone())
                on_default = lambda: None
            elif isinstance(item, (list,tuple)):
                vlist.append(VChoice(list(item)))
                if len(item) > 0:
                    on_default = lambda: item[0]
            elif isinstance(item, Property):
                vlist.append(simplify_validator(item.validator))                
                on_default = item.on_default
            elif issubclass(item, Property):
                item = item()
                vlist.append(simplify_validator(item.validator))                
                on_default = item.on_default
            elif inspect.isclass(item):
                vlist.append(VInstance(item))
            else:
                raise TypeError("Unknown validator: %s" % item)

        self.on_default = on_default
        self.vlist = vlist


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


def _dump_validator(validator, indent=0):
    " For debugging. "
    print "  "*indent, validator.__class__.__name__
    indent += 2
    for v in validator.vlist:
        if isinstance(v, ValidatorList):
            _dump_validator(v, indent+2)
        else:
            print "  "*indent, v.__class__.__name__


def construct_validator_list(*validators, **kwargs):
    if len(validators) == 0:
        return RequireOne(**kwargs)
    elif len(validators) == 1 and isinstance(validators[0], ValidatorList):
        return validators[0].__class__(*validators[0].vlist, **kwargs)
    else:
        return RequireOne(*validators, **kwargs)
