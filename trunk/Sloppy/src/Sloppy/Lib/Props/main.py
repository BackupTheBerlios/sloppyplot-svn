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

from typed_containers import TypedList, TypedDict


__all__ = ["HasProperties", "Property", "List", "Dictionary", "Undefined",
           "Validator", "ValidatorList", "RequireOne", "RequireAll",
           "VMap", "VBMap", "VString", "VInteger", "VFloat", "VBoolean",
           "VRegexp", "VUnicode", "VList", "VDictionary", "VRange",
           "VInstance"]

#------------------------------------------------------------------------------
# Helper Stuff
#

class DictionaryLookup(object):
    """ Helper class to allow access to members of a dictionary.

    >>> mydict = {'One': 1, 'Two': 2}
    >>> dl = DictionaryLookup(mydict)
    >>> print dl.One
    >>> print dl.Two
    """
    
    def __init__(self, adict):
        object.__setattr__(self, '_adict', adict)

    def __getattribute__(self, key):
        adict = object.__getattribute__(self, '_adict')         
        return adict[key]

    def __setattr__(self, key, value):
        adict = object.__getattribute__(self, '_adict')
        if adict.has_key(key) is False:
            raise KeyError("'%s' cannot be set, because it doesn't exist yet." % key)
        adict[key] = value
            
    def __str__(self):
        adict = object.__getattribute__(self, '_adict')
        return "Available items: %s" % str(adict)


class Undefined:
    def __str__(self):
        return "Undefined"

class PropertyError(Exception):
    pass

#------------------------------------------------------------------------------
# Validators
#

class Validator:
    is_mapping = False


class VMap(Validator):

    """ Map the given value according to the dict. """

    is_mapping = True
    
    def __init__(self, adict):
        self.dict = adict    

    def check(self, value):
        try:
            return self.dict[value]
        except KeyError:
            raise ValueError("one of '%s'" % (self.dict.keys()))

    def is_mapping(self):
        return True

    

class VBMap(Validator):

    """
    Map the given value according to the dict
    _or_ accept the given value if it is in the dict's values.
    """

    is_mapping = True
        
    def __init__(self, adict):
        self.dict = adict
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


class VUndefined(Validator):
    def check(self, value):
        if value == Undefined:
            return value
        else:
            raise ValueError("Undefined")

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
            if value is Undefined:
                raise
            return str(value)
        except:
            raise TypeError("a string")


class VUnicode(Validator):
    def check(self, value):
        try:
            if value is Undefined:
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

class VChoices(Validator):

    def __init__(self, alist):
        self.values = alist

    def check(self, value):
        print "Checking ", value
        if value in self.values:
            return value
        print "No"
        raise ValueError("one of %s" % str(self.values))
        

      

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
            except Exception, msg:
                raise PropertyError("Failed to set item in dictionary property '%s' of container '%s' to '%s': Value must be %s." %
                                    (key, owner.__class__.__name__, value, str(msg)))
            
        if isinstance(value, TypedDict):
            value.check_item = check_item
            return value
        elif isinstance(value, dict):
            return TypedDict(check_item, value)
        else:            
            raise TypeError("a dict")

    
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
                vlist.append(VChoices(list(item)))
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
            elif item == Undefined:
                vlist.append(VUndefined())
                on_default = Undefined
            elif inspect.isclass(item):
                vlist.append(VInstance(item))
            else:
                raise TypeError("Unknown validator: %s" % item)

        self.on_default = on_default
        self.vlist = vlist
        self.is_mapping = is_mapping

class RequireOne(ValidatorList):

    def check(self, value):
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
        return RequireOne()
    elif len(validators) == 1 and isinstance(validators[0], ValidatorList):
            return validators[0] # TODO: what about **kwargs?
    else:
        return RequireOne(*validators, **kwargs)


#------------------------------------------------------------------------------
# Base Class 'Property'
#

class Property:
    
    def __init__(self, *validators, **kwargs):
        self.blurb = kwargs.get('blurb', None)
        self.doc = kwargs.get('doc', None)
        self.validator = construct_validator_list(*validators, **kwargs)

        self.on_default = self.validator.on_default
        
    def get_value(self, owner, key):
        return owner._values[key]
        
    def set_value(self, value, owner, key):
        try:
            if self.validator.is_mapping is False:
                owner._values[key] = self.validator.check(value)
            else:
                owner._values[key] = value
                owner._mvalues[key] = self.validator.check(value)
        except Exception,msg:
            raise PropertyError("Failed to set property '%s' of container '%s' to '%s': Value must be %s." %
                                (key, owner.__class__.__name__, value, str(msg)))

    def get_default(self):
        return self.on_default()

    def check(self, value):
        try:
            return self.validator.check(value)
        except Exception,msg:
            raise PropertyError("Property check failed: Value '%s' must be %s." %
                                (value, str(msg)))
        

class List(Property):
    def __init__(self, *validators, **kwargs):
        # TODO: maybe I should set the default value
        # after initializing the Property.  After all the
        # ValidatorList default value is useless for the list,
        # isn't it?
        if kwargs.has_key('default') is False:
            kwargs['default'] = []
        Property.__init__(self, VList(*validators), **kwargs)


class Dictionary(Property):
    def __init__(self, *validators, **kwargs):        
        if kwargs.has_key('default') is False:
            kwargs['default'] = {}
        Property.__init__(self, VDictionary(*validators), **kwargs)
                


#------------------------------------------------------------------------------
# HasProperties
#

class HasProperties(object):

    """
    Base class for any class that uses Props.
    """

    def __init__(self, **kwargs):
        
        # Initialize props and values dict
        object.__setattr__(self, '_mvalues', {})
        object.__setattr__(self, '_values', {})
        object.__setattr__(self, '_props', {})
        
        # We need to init the Props of all classes that the object instance
        # belongs to.  To give meaningful error messages, we reverse the
        # order and define the base class Props first.
        classlist = list(object.__getattribute__(self,'__class__').__mro__[:-1])
        classlist.reverse()
        
        for klass in classlist:
            # initialize default values
            for key, prop in klass.__dict__.iteritems():
                if isinstance(prop, Property):
                    if self._props.has_key(key):
                        raise KeyError("%s defines Prop '%s', which has already been defined by a base class!" % (klass,key)  )
                    self._props[key] = prop
                    #self._values[key] = Undefined
                    #self._mvalues[key] = Undefined
                    
                    kwvalue = kwargs.pop(key,None)
                    if kwvalue is not None:
                        self.__setattr__(key,kwvalue)
                    else:
                        default = prop.get_default()
                        if default is not Undefined:  
                            self.set_value(key, default)
                        else:
                            self._values[key] = Undefined
                        
        # complain if there are unused keyword arguments
        if len(kwargs) > 0:
            raise ValueError("Unrecognized keyword arguments: %s" % kwargs)

        # quick property retrieval: self.props.key
        object.__setattr__(self, 'props', DictionaryLookup(self._props))

    #----------------------------------------------------------------------
    # Setting/Getting Magic
    #
    
    def __setattr__(self, key, value):
        if key in ('props', '_props','_values', '_mvalues'):
            raise RuntimeError("Attribute '%s' cannot be altered for HasProperties objects." % key)
        
        props = object.__getattribute__(self, '_props')
        if props.has_key(key):
            props[key].set_value(value, self, key)
        else:
            object.__setattr__(self, key, value)
    
    def __getattribute__(self, key):
        if key in ('_props','_values', '_mvalues'):
            return object.__getattribute__(self, key)
        else:
            props = object.__getattribute__(self, '_props')
            if props.has_key(key):
                return props[key].get_value(self, key)
            else:
                return object.__getattribute__(self, key)                       

    #----------------------------------------------------------------------
    # Value Handling
    #

    def set_value(self, key, value):
        self.__setattr__(key, value)

    def set_values(self, *args, **kwargs):
        arglist = list(args)
        while len(arglist) > 1:
            key = arglist.pop(0)
            value = arglist.pop(0)
            self.__setattr__(key, value)
           
        for (key, value) in kwargs.iteritems():
            self.__setattr__(key, value)

    set = set_value
    

    def get_value(self, key, **kwargs):
        
        if kwargs.has_key('default') is True:
            default = kwargs.get('default', None)
            value = self.__getattribute__(key)
            if value is Undefined:
                return default
            else:
                return value
        else:
            return self.__getattribute__(key)            

    def get_mvalue(self, key):
        ivalues = object.__getattribute__(self, '_mvalues')
        if ivalues.has_key(key):
            return ivalues.get(key)

        return self.get_value(key)

    # TODO: ivalues/values for List/Dictionary objects.
    # TODO: The List uses Property.check, which returns only
    # TODO: the ivalue.
    
    def get_values(self, include=None, exclude=None, **kwargs):

        rv = {}
        keys = self._limit_keys(include=include, exclude=exclude)
        
        if kwargs.has_key('default') is True:
            default = kwargs.get('default', None)            
            for key in keys:            
                value = self.__getattribute__(key)
                if value is Undefined:
                    rv[key] = default
                else:
                    rv[key] = value
        else:
            for key in keys:
                rv[key] = self.__getattribute__(key)

        return rv

    #----------------------------------------------------------------------
    # Prop Handling
    #

    def get_prop(self, key):
        return self._props[key]

    def get_props(self, include=None, exclude=None):
        rv = {}
        for key in self._limit_keys(include=include, exclude=exclude):
            rv[key] = self._props[key]

        return rv
            

    #----------------------------------------------------------------------
    # Convenience Methods

    def copy(self, include=None,exclude=None):
        kw = self.get_values(include=include,exclude=exclude,default=None)
        return self.__class__(**kw)

    def create_changeset(self, container):
        changeset = {}
        for key, value in container.get_values(default=None).iteritems():
            old_value = self.rget(key)
            if value != old_value:
                changeset[key] = value
        return changeset       


    #----------------------------------------------------------------------
    # internal
    
    def _limit_keys(self, include=None, exclude=None):
        if include is None:
            include = self._values.keys()        
        if exclude is not None:
            include = [key for key in include if key not in exclude]
        return include




HasProps = HasProperties

