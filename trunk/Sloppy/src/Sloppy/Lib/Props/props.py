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

"""
@group props: pList, pDictionary, pBoolean, pKeyword, pString,
pUnicode, pInteger, pFloat, pWeakref, pDict

@group checks: Coerce, CheckRegexp, CheckType, CheckTuple, CheckAll,
CheckBounds, CheckValid, CheckInvalid, ValueDict, Mapping
"""

import weakref
import re
import inspect

from typed_containers import TypedList, TypedDict

__extra_epydoc_fields__ = [('prop', 'Prop', 'Props')]

__all__ = ["HasProps", "HasProperties", "Prop", "Property", "List",
           "Dictionary", "pList", "pDict", "pDictionary",
           #
           "ValueDict", "Mapping", # experimental
           #
           "Check", "Transformation", "Coerce", "CoerceBool", "CheckRegexp", "CheckType",
           "CheckTuple", "CheckAll", "CheckBounds", "CheckValid", "CheckInvalid"
           ]

#------------------------------------------------------------------------------
# Helper Methods
#

def as_list(o):
    # make sure we are talking about a list!
    if isinstance(o, list):
        return o
    elif isinstance(o, tuple):
        return list(o)
    else:
        return [o]


class DictionaryLookup(object):

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


#------------------------------------------------------------------------------
# Meta Attributes
#

class MetaAttribute(object):

    def __init__(self, prop, key):
        object.__init__(self)
        self.key = key
        self.prop = prop

    def __get__(self, inst, nd=False):
        rv = inst._values[self.key]
        if rv is not None or nd is True:
            return rv
        else:
            return self.prop.on_default()

    def __set__(self, owner, value):
        try:
            value = self.prop.check(value)
            owner._values[self.key] = value
        except TypeError, msg:
            raise TypeError("Failed to set property '%s' of container '%s' to '%s':\n  %s" %
                            (self.key, repr(owner), value, msg))
        except ValueError, msg:
            raise ValueError("Failed to set property '%s' of container '%s' to '%s':\n %s" %
                             (self.key, repr(owner), value, msg))


class WeakMetaAttribute(MetaAttribute):
    
    def __get__(self, owner, nd=False):
        value = MetaAttribute.__get__(self, owner, nd)
        if value is not None:
            return value()
        else:
             return value

    def __set__(self, owner, value):
        value = self.prop.check(value)
        if value is not None:
            value = weakref.ref(value)
        owner._values[self.key] = value



#------------------------------------------------------------------------------
# Check objects
#

class Check:
    """ Abstract base class for all value check.

    In a derived class, implement __call__(self, value).

    @raise TypeError:
    @raise ValueError:
    """
    
    def get_description(self):
        return "No description for %s" % str(self)



class Transformation(Check):
    """ Abstract base class for all value transformations.

    In a derived class, implement __call__(self, value).

    @raise ValueError:
    @raise TypeError:
    """
    pass



class Coerce(Transformation):

    def __init__(self, _type):
        self.type = _type

    def __call__(self, value):
        if value is None:
            return None
        else:
            return self.type(value)

    def get_description(self):
        return "Coerce to: %s" % self.type



class CoerceBool(Transformation):

    def __init__(self):
        pass

    def __call__(self, value):
        if value is None:
            return None
        else:
            if isinstance(value, basestring):
                if "true".find(value.lower()) > -1:
                    return True
                elif "false".find(value.lower()) > -1:
                    return False
            else:
                return bool(value)

    def get_description(self):
        return "Coerce to Boolean"

class CheckRegexp(Check):
    
    """ Check value against a given regular expression. """
    
    def __init__(self, regexp):
        self.regexp=regexp
        self._expression = re.compile(regexp)

    def __call__(self, value):
        match = self._expression.match(value)
        if match is None:
            raise ValueError("Value %s does not match the regular expression %s" % (value,self.regexp))

    def get_description(self):
        return "Must match regular expression: '%s'" % self.regexp

    

class CustomCheck(Check):
    " Check value using a given function. "
    def __init__(self, function, doc="custom check"):
        self.function = function
        self.description = (lambda self: doc)

    def __call__(self, value):
        return self.function(value)
    
    
class CheckType(Check):

    """ Check value against a single type or a list of types. """

    def __init__(self, *types):
        self.types = as_list(types)

    def __call__(self, value):
        if value is None:
            return
        
        for _type in self.types:                   
            if isinstance(value, _type):
                return
        else:
            raise TypeError("Invalid type '%s', must be one of '%s'" % (type(value), self.types))

    def get_description(self):
        return "Require type(s): %s." % self.types



class CheckTuple(Check):

    """ Check that the value is a tuple of a given length. """

    def __init__(self, length):
        self.length = length
        
    def __call__(self, value):
        if isinstance(value, tuple) and len(value) == self.length:
            return
        else:
            raise TypeError("Value must be tuple of length %d!" % self.length )

    def get_description(self):
        return "Require tuple of length %d." % self.length

    
        
class CheckAll(Transformation):

    """ Apply all given Check's to the value. """
    
    def __init__(self, clist=None):

        # Make sure that the given list of Check instances are valid.
        self.items = []

        if clist is not None:
            for item in clist:
                if not isinstance(item, Check):
                    raise TypeError("Invalid Check specified: %s of %s" % (item, type(item)))
                self.items.append(item)
        
    def __call__(self, value):
        for item in self.items:
            if isinstance(item, Transformation):
                value = item(value)
            else:
                item(value)
        return value

    def __len__(self):
        return len(self.items)


    def get_description(self):
        rv = ["Check all of the following:"]
        for item in self.items:
            rv.append("  " + item.description())
        return "\n".join(rv)

        

class CheckList(Transformation):

    def __init__(self, *checks, **kwargs):

        checkdict = {}
        checks = list(checks)
        
        # create new checks from the kwargs and put them into checkdict        
        create_check = {'mapping' : Mapping,
                        'type' : CheckType,
                        'types': CheckType,                        
                        'coerce' : Coerce,
                        'custom' : CustomCheck,
                        'range': lambda range: CheckBounds(*range),
                        'valid': CheckValid,
                        'invalid': CheckInvalid
                        }
                        #'range': CheckRange       
        for key, value in kwargs.iteritems():
            checks.append(create_check[key](value))

        # add custom checks and put them into checkdict
        check_map =  {'Mapping': 'mapping',
                      'CheckType': 'type',
                      'Coerce': 'coerce',
                      'CheckValid': 'valid',
                      'CheckInvalid': 'invalid',
                      'CheckBounds': 'range',
                      'CustomCheck': 'custom'}
        for check in checks:
            if isinstance(check, CheckList):
                checkdict.update(check.checkdict)                
            else:                
                key = check_map[check.__class__.__name__]
                checkdict[key] = check

        # now create the check list in a certain order
        items = []        
        for key in ['mapping', 'type', 'coerce', 'range', 'valid', 'invalid']:
            if checkdict.has_key(key):
                items.append(checkdict.get(key))

        self.checkdict = checkdict
        self.items = items
        

    def __call__(self, value):
        for item in self.items:
            if isinstance(item, Transformation):
                value = item(value)
            else:
                item(value)
        return value

    def __len__(self):
        return len(self.items)


    def get_description(self):
        rv = ["Check all of the following:"]
        for item in self.items:
            rv.append("  " + item.get_description())
        return "\n".join(rv)

    
        

class CheckValid(Check):

    """ Require value to be in the list of valid values. """
    
    def __init__(self, values):
        self.values = as_list(values)
        
    def __call__(self, value):
        if value is None:
            return
        if (value in self.values) is False:
            raise ValueError("Value %s is not in the list of valid values: %s" % (value, self.values))

    def get_description(self):
        return "Valid values: '%s'" % self.values

    

class CheckInvalid(Check):

    """ Make sure value is not in the list of invalid values. """

    def __init__(self, values):
        self.values = as_list(values)       

    def __call__(self, value):
        if value is None:
            return
        if value in self.values:
            raise ValueError("Value %s in in the list of invalid values: %s" % (value, self.values))    

    def get_description(self):
        return "Invalid values: '%s'" % self.values

                
                
class CheckBounds(Check):
    """
    Check if the given value is in between the given bounds [min:max].

    If min or max is None, then the appropriate direction is unbound.
    A value of None is always valid.    
    """
    def __init__(self, min=None, max=None):
        self.min=min
        self.max=max

    def __call__(self, value):
        if value is None:
            return None
        
        if (self.min is not None and value < self.min) \
               or (self.max is not None and value > self.max):
            raise ValueError("Value %s should be in between [%s:%s]" % (value, self.min, self.max))

    def get_description(self):
        return "Valid range: %s:%s" % (self.min or "", self.max or "")


class Mapping(Transformation):

    """ Map the given value according to the dict.

    @todo: Not yet finished.
    """
    
    def __init__(self, adict):
        self.dict = adict
        self.values = adict.values()

    def __call__(self, value):
        if value in self.values:
            return value
        try:
            return self.dict[value]
        except KeyError:
            raise ValueError("Could not find value '%s' in the list of mappings '%s'" % (value, self.dict))

ValueDict = Mapping # deprecated




#------------------------------------------------------------------------------
# Base Class 'Property'
#

class Property:

    def __init__(self, *check, **kwargs):
        """        

        @keyword default: value/ function that will be
        assigned/called if prop value is requested but is None.
        
        @keyword reset: value/function that will be assigned/called on
        initialization
        
        @keyword blurb: Short description.
        @keyword doc: Longer description.
        """
       
        self.blurb = kwargs.pop('blurb', None)
        self.doc = kwargs.pop('doc', None)

        # new style
        check_kwargs = kwargs.copy()
        if check_kwargs.has_key('default'):
            check_kwargs.pop('default')
        if check_kwargs.has_key('reset'):
            check_kwargs.pop('reset')
        self.check = CheckList(*check, **check_kwargs)

        default = kwargs.pop('default', None)
        if inspect.isfunction(default) or inspect.ismethod(default):
            self.on_default = default
        else:
            if default is not None:
                default = self.check(default)
            self.on_default = (lambda: default)

        reset = kwargs.pop('reset', None)
        if inspect.isfunction(reset) or inspect.ismethod(reset):
            self.on_reset = reset
        else:
            if reset is not None:
                reset = self.check(reset)
            self.on_reset = (lambda: reset)

        self.name = None # set by the owning HasProperties class

        self.checks = DictionaryLookup(self.check.checkdict)

    def meta_attribute(self, key):
        return MetaAttribute(self, key)

    def get_description(self):
        if self.check is not None:
            return self.check.get_description()

    # DEPRECATED
    def description(self):
        return self.get_description()
    

    #----------------------------------------------------------------------
    # Helper methods for introspection
    #

    def get_mapping(self):
        """ Return first instance of Mapping or None. """
        for item in self.check.items:
            if isinstance(item, Mapping):
                return item
        else:
            return None

    def get_value_list(self):
        """ Return first instance of CheckValid or None. """
        for item in self.check.items:
            if isinstance(item, CheckValid):
                return item
        else:
            return None


    # BIG FAT TODO:
    # Replace these with something like
    #  property.checks.valid
    #  property.checks.range
    
    def valid_values(self):
        """ Collect all values of the prop specified by CheckValid. """
        values = []
        for item in self.check.items:
            if isinstance(item, CheckValid):
                values.extend(item.values)
        return values

    def invalid_values(self):
        """ Collect all values of the prop specified by CheckInvalid. """
        values = []
        for item in self.check.items:
            if isinstance(item, CheckInvalid):
                values.extend(item.values)
        return values

    def boundaries(self):
        """ Return the min, max boundary values given by the first
        instance of CheckBounds. """
        minimum, maximum = None, None
        for item in self.check.items:
            if isinstance(item, CheckBounds):
                return item.min, item.max                             



class List(Property):

    def __init__(self, *check, **kwargs):
        # The keyword arguments reset and default refer to the list.
        # They don't make sense for the items.       
        if kwargs.has_key('reset') is False:
            kwargs['reset'] = self.do_reset
        Property.__init__(self, *check, **kwargs)
        
        self.item_check = self.check
        self.check = self.DoCheck(self.item_check)

    class DoCheck(Transformation):

        def __init__(self, check):
            self.check = check
            self.items = [] # needed because Prop.check requires such an item!

        def __call__(self, value):
            if isinstance(value, TypedList):
                return value
            elif isinstance(value, list):
                return TypedList(value, self.check)
            else:            
                raise TypeError("The value '%s' has %s while it should be a list." %
                                (value, type(value)))
        
    def do_reset(self):
        return TypedList(check=self.item_check)

                
class Dictionary(Property):

    def __init__(self, *check, **kwargs):
        kwargs.update({'reset' : self.do_reset})
        Property.__init__(self, *check, **kwargs)
        self.item_check = self.check
        self.check = self.DoCheck(self.item_check)

    class DoCheck(Transformation):

        def __init__(self, check):
            self.check = check
            self.items = [] # needed because Prop.check requires such an item!            

        def __call__(self, value):
            if isinstance(value, TypedDict):
                return value
            elif isinstance(value, dict):
                return TypedDict(value, self.check)
            else:            
                raise TypeError("The value '%s' has %s while it should be a dictionary." %
                                (value, type(value)))

    def do_reset(self):
        return TypedDict(check=self.item_check)


Prop = Property
pDictionary = Dictionary
pDict = Dictionary
pList = List



#------------------------------------------------------------------------------
# HasProperties
#

class HasProperties(object):

    """
    Base class for any class that uses Props.
    """

    def __init__(self, **kwargs):
        
        # Initialize props and values dict
        object.__setattr__(self, '_values', {})
        object.__setattr__(self, '_props', {})
        
        # We need to init the Props of all classes that the object instance
        # belongs to.  To give meaningful error messages, we reverse the
        # order and define the base class Props first.
        classlist = list(object.__getattribute__(self,'__class__').__mro__[:-1])
        classlist.reverse()
        
        for klass in classlist:
            # initialize default values
            for key, value in klass.__dict__.iteritems():
                if isinstance(value, Prop):
                    if self._props.has_key(key):
                        raise KeyError("%s defines Prop '%s', which has already been defined by a base class!" % (klass,key)  )
                    self._props[key] = value
                    self._values[key] = value.on_reset()
                    kwvalue = kwargs.pop(key,None)
                    if kwvalue is not None:
                        self.__setattr__(key,kwvalue)
                    value.name = key

        # complain if there are unused keyword arguments
        if len(kwargs) > 0:
            raise ValueError("Unrecognized keyword arguments: %s" % kwargs)

        # quick property retrieval: self.props.key
        object.__setattr__(self, 'props', DictionaryLookup(self._props))

    #----------------------------------------------------------------------
    # Setting/Getting Magic
    #
    
    def __setattr__(self, key, value):
        if key in ('props', '_props','_values'):
            raise RuntimeError("Attributes '_props' and '_values' cannot be altered for HasProperties objects.")
        
        prop = object.__getattribute__(self, '_props').get(key,None)
        if prop is not None and isinstance(prop, Prop):
            prop.meta_attribute(key).__set__(self, value)
        else:
            object.__setattr__(self, key, value)
    
    def __getattribute__(self, key, nd=False):
        """ `nd` = nodefault = ignore Prop's default value. """                         
        if key in ('_props','_values'):
            return object.__getattribute__(self, key)
        else:
            prop = object.__getattribute__(self, '_props').get(key,None)
            if prop is not None and isinstance(prop, Prop):
                return prop.meta_attribute(key).__get__(self, nd=nd)
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

                   

    def get_value(self, key, **kwargs):
        if kwargs.has_key('default') is True:
            default = kwargs.get('default', None)
            value = self.__getattribute__(key, nd=True)
            if value is None:
                return default
            else:
                return value
        else:
            return self.__getattribute__(key)            

    
    def get_values(self, include=None, exclude=None, **kwargs):

        rv = {}
        keys = self._limit_keys(include=include, exclude=exclude)
        
        if kwargs.has_key('default') is True:
            default = kwargs.get('default', None)            
            for key in keys:            
                value = self.__getattribute__(key, nd=True)
                if value is None:
                    rv[key] = default
                else:
                    rv[key] = value
        else:
            for key in keys:
                rv[key] = self.__getattribute__(key)

        return rv

    mget = get_values  # NEEDED ?
    get = get_value

    # DEPRECATED   
    def rget(self, key, default=None):
        return self.get_value(key, default=default)

    
    def clear(self, include=None, exclude=None):
        " Clear all props. "
        for key in self._limit_keys(include=include, exclude=exclude):
            self._values[key] = self._props[key].on_reset()

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

