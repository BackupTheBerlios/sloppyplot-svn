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

# $HeadURL: svn+ssh://svn.berlios.de/svnroot/repos/sloppyplot/trunk/Sloppy/src/Sloppy/Lib/Props/props.py $
# $Id: props.py 43 2005-08-23 11:22:14Z niklasv $

"""
@group props: pList, pDictionary, pBoolean, pKeyword, pString,
pUnicode, pInteger, pFloat, pWeakref

@group checks: Coerce, CheckRegexp, CheckType, CheckTuple, CheckAll,
CheckBounds, CheckValid, CheckInvalid, MapValue

@author: Niklas Volbers

@copyright: Copyright (C) 2005 by Niklas Volbers

@license: This program is free software; you can redistribute it
and/or modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.

@version: 0.9

@contact: mithrandir42@web.de
"""

import weakref
import re
import inspect


__extra_epydoc_fields__ = [('prop', 'Prop', 'Props')]


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
            

#------------------------------------------------------------------------------
# Helper Types
#

class TypedList:

    def __init__(self, _list=None, check=None):
        self.check = check or CheckAll()
        self.metadata = {'check' : self.check}
        self.data = []
        if _list is not None:
            self.data = self.check_list(_list)


    #------------------------------------------------------------------------------
    def __repr__(self): return repr(self.data)
    def __lt__(self, other): return self.data <  self.__cast(other)
    def __le__(self, other): return self.data <= self.__cast(other)    
    def __eq__(self, other): return self.data == self.__cast(other)
    def __ne__(self, other): return self.data != self.__cast(other)
    def __gt__(self, other): return self.data >  self.__cast(other)
    def __ge__(self, other): return self.data >= self.__cast(other)

    def __cast(self, other): return self.check_list(other)
    def __cmp__(self, other): return cmp(self.data, self.__cast(other))
    def __contains__(self, item): return item in self.data
    def __len__(self): return len(self.data)

    def __getitem__(self, i): return self.data[i]
    def __setitem__(self, i, item): self.data[i] = self.check_item(item)
    def __delitem__(self, i): del self.data[i]
    
    def __getslice__(self, i, j):
        i = max(i, 0); j = max(j, 0)
        return self.__class__(self.data[i:j],**self.metadata())
    def __setslice__(self, i, j, other):
        i = max(i, 0); j = max(j, 0)
        self.data[i:j] = self.check_list(other)
    def __delslice__(self, i, j):
        i = max(i, 0); j = max(j, 0)
        del self.data[i:j]

    def __add__(self, other):
        return self.__class__(self.data + self.check_list(other), **self.metadata)
    def __radd__(self, other):
        return self.__class__(self.check_list(other) + self.data, **self.metadata)
    def __iadd__(self, other):
        self.data += self.check_list(other)
        return self

    def __mul__(self, n):
        return self.__class__(self.data*n)
    __rmul__ = __mul__
    def __imul__(self, n):
        self.data *= n
        return self

    def append(self, item): self.data.append(self.check_item(item))
    def insert(self, i, item): self.data.insert(i, self.check_item(item))
    def pop(self, i=-1): return self.data.pop(i)
    def remove(self, item): self.data.remove(item)
    def count(self, item): return self.data.count(item)
    def index(self, item, *args): return self.data.index(item, *args)
    def reverse(self): self.data.reverse()
    def sort(self, *args, **kwds): self.data.sort(*args, **kwds)
    def extend(self, other): self.data.extend(self.check_list(other))              

    def __iter__(self):
        for member in self.data:
            yield member

    #------------------------------------------------------------------------------
    def check_item(self, item):
        try:
            return self.check(item)
        except TypeError, msg:
            raise TypeError("Item '%s' added to TypedList '%s' is invalid:\n %s" %
                            (item, repr(self), msg))
        except ValueError, msg:
            raise ValueError("Item '%s' added to TypedList '%s' is invalid:\n %s" %
                            (item, repr(self), msg))


    def check_list(self, alist):
        if isinstance(alist, TypedList):
            return alist.data
        elif isinstance(alist, (list,tuple)):
            newlist = []
            for item in alist:
                newlist.append(self.check_item(item))
            return newlist
        else:
            raise TypeError("List required, got %s instead." % type(alist))



    
class TypedDict:

    def __init__(self, _dict=None, check=None):
        self.check = check or CheckAll()
        self.metadata = {'check' : self.check}        
        self.data = {}
        if _dict is not None:
            self.update(_dict)
                
    def __repr__(self): return repr(self.data)
    def __cast(self, other): return self.check_dict(other)
    def __cmp__(self, other): return cmp(self.data, self.__cast(other))
    def __len__(self): return len(self.data)
    def __getitem__(self, key): return self.data[key]
    def __setitem__(self, key, item):
        self.data[key] = self.check_item(item)
    def __delitem__(self, key): del self.data[key]
    def clear(self): self.data.clear()
    def copy(self):
        if self.__class__ is TypedDict:
            return TypedDict(self.data.copy(), **self.metadata)
        # OK ?
        import copy
        data = self.data
        try:
            self.data = {}
            c = copy.copy(self)
        finally:
            self.data = data
        c.update(self)
        return c
    def keys(self): return self.data.keys()
    def items(self): return self.data.items()
    def iteritems(self): return self.data.iteritems()
    def iterkeys(self): return self.data.iterkeys()
    def itervalues(self): return self.data.itervalues()
    def values(self): return self.data.values()
    def has_key(self, key): return self.data.has_key(key)
       
    def update(self, dict=None, **kwargs):
        if dict is not None:
            self.data.update(self.check_dict(dict))
        if len(kwargs):
            self.data.update(self.check_dict(kwargs))
            
    def get(self, key, failobj=None):
        if not self.has_key(key):
            return failobj
        return self[key]
    def setdefault(self, key, failobj=None):
        if not self.has_key(key):
            self[key] = self.check_item(failobj)
        return self[key]
    def pop(self, key, *args):
        return self.data.pop(key, *args)
    def popitem(self):
        return self.data.popitem()
    def __contains__(self, key):
        return key in self.data
    def fromkeys(cls, iterable, value=None):
        d = cls() # TODO: type?
        for key in iterable:
            d[key] = value
        return d
    fromkeys = classmethod(fromkeys)

    def __iter__(self):
        return iter(self.data)


    #------------------------------------------------------------------------------
    def check_item(self, item):
        try:
            return self.check(item)
        except TypeError, msg:
            raise TypeError("Item '%s' added to TypedDict '%s' is invalid:\n %s" %
                            (item, repr(self), msg))
        except ValueError, msg:
            raise ValueError("Item '%s' added to TypedDict '%s' is invalid:\n %s" %
                            (item, repr(self), msg))


    def check_dict(self, adict):
        if isinstance(adict, TypedDict):
            return adict.data
        elif isinstance(adict, dict):
            for val in adict.itervalues():
                self.check_item(val)
            return adict
        else:
            raise TypeError("Dict required, got %s instead." % type(adict))



#------------------------------------------------------------------------------
# Meta Attributes
#

class MetaAttribute(object):

    def __init__(self, prop, key):
        object.__init__(self)
        self.key = key
        self.prop = prop

    def __get__(self, inst, cls=None):
        rv = inst._values[self.key]
        if rv is not None:
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
    
    def __get__(self, owner, cls=None):
        value = MetaAttribute.__get__(self, owner,cls)
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

class Check:
    """ Abstract base class for all value check.

    In a derived class, implement __call__(self, value, owner).

    @raise TypeError:
    @raise ValueError:
    """

    def description(self):
        return "No description for %s" % str(self)



class Transformation(Check):
    """ Abstract base class for all value transformations.

    In a derived class, implement __call__(self, value, owner).

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

    def description(self):
        return "Coerce to: %s" % self.type



class CheckRegexp(Check):
    
    """ Check value against a given regular expression. """
    
    def __init__(self, regexp):
        self.regexp=regexp
        self._expression = re.compile(regexp)

    def __call__(self, value):
        match = self._expression.match(value)
        if match is None:
            raise ValueError("Value %s does not match the regular expression %s" % (value,self.regexp))

    def description(self):
        return "Must match regular expression: '%s'" % self.regexp

    

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

    def description(self):
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

    def description(self):
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


    def description(self):
        rv = ["Check all of the following:"]
        for item in self.items:
            rv.append("  " + item.description())
        return "\n".join(rv)
        


class CheckValid(Check):

    """ Require value to be in the list of valid values. """
    
    def __init__(self, values):
        self.values = as_list(values)
        
    def __call__(self, value):
        if (value in self.values) is False:
            raise ValueError("Value %s is not in the list of valid values: %s" % (value, self.values))

    def description(self):
        return "Valid values: '%s'" % self.values

    

class CheckInvalid(Check):

    """ Make sure value is not in the list of invalid values. """

    def __init__(self, values):
        self.values = as_list(values)       

    def __call__(self, value):
        if value in self.values:
            raise ValueError("Value %s in in the list of invalid values: %s" % (value, self.values))    

    def description(self):
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

    def description(self):
        return "Valid range: %s:%s" % (self.min or "", self.max or "")



#------------------------------------------------------------------------------
# TESTING AREA
#

class MapValue(Transformation):

    """ Map the given value according to the dict.

    @todo: Not yet finished.
    """
    
    def __init__(self, mapping):
        self.mapping = mapping
        self.values = mapping.values()

    def __call__(self, value):
        if value in self.values:
            return value
        try:
            return self.mapping[value]
        except KeyError:
            raise ValueError("Could not find value '%s' in the list of mappings '%s'" % (value, self.mapping))





#------------------------------------------------------------------------------
# Base Class 'Prop'
#

class Prop:

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

        self.check = CheckAll(check or [])

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

        self.name = None # set by the owning HasProps class
        

    def meta_attribute(self, key):
        return MetaAttribute(self, key)

    def description(self):
        if self.check is not None:
            return self.check.description()
    

    #----------------------------------------------------------------------
    # Helper methods for introspection
    #

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
            if isinstance(item, CheckValid):
                values.extend(item.values)
        return values

    def boundaries(self):
        """ Return the min, max boundary values given by the first
        instance of CheckBounds. """
        minimum, maximum = None, None
        for item in self.check.items:
            if isinstance(item, CheckBounds):
                return item.min, item.max
        


                      

#------------------------------------------------------------------------------
# Extended Props
#


class pList(Prop):

    def __init__(self, *check, **kwargs):
        kwargs.update({'reset' : self.do_reset})
        Prop.__init__(self, *check, **kwargs)
        self.item_check = self.check
        self.check = self.DoCheck(self.item_check)

    class DoCheck(Transformation):

        def __init__(self, check):
            self.check = check

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

                
class pDictionary(Prop):

    def __init__(self, *check, **kwargs):
        kwargs.update({'reset' : self.do_reset})
        Prop.__init__(self, *check, **kwargs)
        self.item_check = self.check
        self.check = self.DoCheck(self.item_check)

    class DoCheck(Transformation):

        def __init__(self, check):
            self.check = check

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

pDict = pDictionary


class pBoolean(Prop):
    def __init__(self, **kwargs):
        Prop.__init__(self, Coerce(bool), **kwargs)

pBool = pBoolean


class pKeyword(Prop):
    def __init__(self, **kwargs):
        Prop.__init__(self,
                      CheckType(basestring), #
                      CheckRegexp('^\w*$'),
                      **kwargs)

class pString(Prop):
    """ Coerce to regular string. """
    def __init__(self, *check, **kwargs):
        Prop.__init__(self, Coerce(str), *check, **kwargs)

        
class pUnicode(Prop):
    """ Coerce to regular string. """
    def __init__(self, *check, **kwargs):
        Prop.__init__(self, Coerce(unicode), *check, **kwargs)
        

class pInteger(Prop):
    def __init__(self, *check, **kwargs):
        Prop.__init__(self, Coerce(int), *check, **kwargs)


class pFloat(Prop):
    def __init__(self, *check, **kwargs):
        Prop.__init__(self, Coerce(float), *check, **kwargs)

        
class pWeakref(Prop):

    def __init__(self, *check, **kwargs):
        Prop.__init__(self, *check, **kwargs)
        
    def meta_attribute(self, key):
        return WeakMetaAttribute(self, key)



#------------------------------------------------------------------------------
# HasProps
#

class HasProps(object):

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


    #----------------------------------------------------------------------
    # Setting/Getting Magic
    #
    
    def __setattr__(self, key, value):
        if key in ('_props','_values'):
            raise RuntimeError("Attributes '_props' and '_values' cannot be altered for HasProps objects.")
        
        prop = object.__getattribute__(self, '_props').get(key,None)
        if prop is not None and isinstance(prop, Prop):
            prop.meta_attribute(key).__set__(self, value)
        else:
            object.__setattr__(self, key, value)
    
    def __getattribute__(self, key, default=None):        
        if key in ('_props','_values'):
            return object.__getattribute__(self, key)
        else:
            prop = object.__getattribute__(self, '_props').get(key,None)
            if prop is not None and isinstance(prop, Prop):
                return prop.meta_attribute(key).__get__(self, default)
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

                   
                   
    def get_value(self, key, default=None):
        return self.__getattribute__(key, default)

    def get_values(self, include=None, exclude=None):
        if include is None:
            include = self._values.keys()        
        if exclude is not None:
            include = [key for key in include if key not in exclude]

        rv = {}
        for key in include:
            rv[key] = self.__getattribute__(key)

        return rv


    #----------------------------------------------------------------------
    # Prop Handling
    #

    def get_prop(self, key):
        return self._props[key]

    def get_props(self, include=None, exclude=None):
        if include is None:
            include = self._props.keys()
        if exclude is not None:
            include = [key for key in include if key not in exclude]

        rv = {}
        for key in include:
            rv[key] = self._props[key]

        return rv
            

    #----------------------------------------------------------------------
    # Convenience Methods

    def copy(self, include=None,exclude=None):
        kw = self.get_values(include=include,exclude=exclude)                
        return self.__class__(**kw)




