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


__all__ = ["HasProperties", "Property", "Validator", 
           "VMap", "VBMap", "VString", "VInteger", "VFloat", "VBoolean",
           "VRegexp", "VUnicode", "VList"]

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
    def __str__(self): return "Undefined"

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

    def check(self, owner, key, value):
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

    def check(self, owner, key, value):
        if value in self.values:
            return value
        try:
            return self.dict[value]
        except KeyError:
            raise ValueError("one of '%s' or '%s'" % (self.dict.keys(), self.dict.values()))

    def is_mapping(self):
        return True


class VNone(Validator):

    def check(self, owner, key, value):
        if value is None:
            return None
        raise TypeError("None")


class VBoolean(Validator):

    def check(self, owner, key, value):
        if isinstance(value, bool):
            return bool(value)
        elif isinstance(value, basestring):
            if "true".find(value.lower()) > -1:
                return True
            elif "false".find(value.lower()) > -1:
                return False
        elif isinstance(value, (int,float)):
            return bool(value)

        raise ValueError("Not a valid True/False value.")


class VString(Validator):
    def check(self, owner, key, value):
        return str(value)


class VUnicode(Validator):
    def check(self, owner, key, value):
        return unicode(value)


class VInteger(Validator):
    def check(self, owner, key, value):
        return int(value)


class VFloat(Validator):
    def check(self, owner, key, value):
        return float(value)


class VRegexp(Validator):
    
    """ Check value against a given regular expression. """
    
    def __init__(self, regexp):
        self.regexp=regexp
        self._expression = re.compile(regexp)

    def check(self, owner, key, value):
        match = self._expression.match(value)
        if match is not None:
            return value

        raise ValueError("Value %s does not match the regular expression %s" % (value,self.regexp))

class VTryAll(Validator):

    def __init__(self, *validators):
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
            elif isinstance(item, dict):
                # 1:1 mapping if there is only a map as validator
                if len(validators) == 1:
                    vlist.append(VBMap(item))
                else:
                    vlist.append(VMap(item))
                is_mapping = True
            elif isinstance(item, Property):
                vlist.extend(item.validator.vlist)
                is_mapping = is_mapping or item.validator.is_mapping
            elif issubclass(item, Property):
                vlist.extend(item().validator.vlist)
                is_mapping = is_mapping or item.validator.is_mapping
            else:
                raise TypeError("Unknown validator: %s" % item)

        self.vlist = vlist
        self.is_mapping = is_mapping


    def check(self, owner, key, value):
        error = []
        
        for validator in self.vlist:
            try:
                value = validator.check(owner, key, value)                    
            except ValueError, msg:
                error.append(str(msg))
            except TypeError, msg:
                error.append(str(msg))
            except:
                raise
            else:
                return value

        raise TypeError(' or '.join(error))


class VList(Validator):

    def __init__(self, *validators):        
        self.item_validator = VTryAll(*validators)

    def check(self, owner, key, value):
        check_item = lambda v: self.item_validator.check(owner, key, v)
        if isinstance(value, TypedList):
            value.check_item = check_item
            return value
        if isinstance(value, list):
            return TypedList(check_item, value)
        else:            
            raise TypeError("a list")

                 
                
# class CheckBounds(Check):
#     """
#     Check if the given value is in between the given bounds [min:max].

#     If min or max is None, then the appropriate direction is unbound.
#     A value of None is always valid.    
#     """
#     def __init__(self, min=None, max=None):
#         self.min=min
#         self.max=max

#     def __call__(self, owner, key, value):
#         if value is None:
#             return None
        
#         if (self.min is not None and value < self.min) \
#                or (self.max is not None and value > self.max):
#             raise ValueError("Value %s should be in between [%s:%s]" % (value, self.min, self.max))

#     def get_description(self):
#         return "Valid range: %s:%s" % (self.min or "", self.max or "")



#------------------------------------------------------------------------------
# Base Class 'Property'
#

class Property:
    
    def __init__(self, *validators, **kwargs):
        
        self.blurb = kwargs.pop('blurb', None)
        self.doc = kwargs.pop('doc', None)        
        
        # first item in validators is actually the default value
        # unless it is a validator instance
        if len(validators) > 0:
            default = validators[0]
            print "Found default value", default
            if not isinstance(default, Validator):
                self.default = default
                validators = tuple(validators[1:])
            else:
                self.default = Undefined

        self.validator = VTryAll(*validators)


    def get_value(self, owner, key):
        return owner._values[key]
        
    def set_value(self, owner, key, value):
        try:
            if self.validator.is_mapping is False:
                owner._values[key] = self.validator.check(owner, key, value)
            else:
                owner._values[key] = value
                owner._mvalues[key] = self.validator.check(owner, key, value)
        except Exception,msg:
            raise PropertyError("Failed to set property '%s' of container '%s' to '%s': Value must be %s." %
                                (key, owner.__class__.__name__, value, str(msg)))

    
                
# class Dictionary(Property):

#     def __init__(self, *check, **kwargs):
#         kwargs.update({'reset' : self.do_reset})
#         Property.__init__(self, *check, **kwargs)
#         self.item_check = self.check
#         self.check = self.DoCheck(self.item_check)

#     class DoCheck(Transformation):

#         def __init__(self, check):
#             self.check = check
#             self.items = [] # needed because Prop.check requires such an item!            

#         def __call__(self, owner, key, value):
#             if isinstance(value, TypedDict):
#                 return value
#             elif isinstance(value, dict):
#                 return TypedDict(owner, key, value, self.check)
#             else:            
#                 raise TypeError("The value '%s' has %s while it should be a dictionary." %
#                                 (value, type(value)))

#     def do_reset(self, owner, key):
#         return TypedDict(owner, key, check=self.item_check)


# pDictionary = Dictionary
# pDict = Dictionary


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
                        if prop.default is not Undefined:                           
                            self.set_value(key, prop.default)
                        
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
            props[key].set_value(self, key, value)
        else:
            object.__setattr__(self, key, value)
    
    def __getattribute__(self, key):
        """ `nd` = nodefault = ignore Prop's default value. """                         
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
                value = self.__getattribute__(key, nd=True)
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

