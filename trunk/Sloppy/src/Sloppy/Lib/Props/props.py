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
@author: Niklas Volbers
@copyright: Copyright (C) 2005 by Niklas Volbers
@license: This program is free software; you can redistribute it
and/or modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.
"""

import weakref
import re



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
            return self.prop.default_value()

    def __set__(self, inst, value):
        try:
            value = self.prop.check_value(value)            
            inst._values[self.key] = value
        except TypeError, msg:
            raise TypeError("Failed to set property '%s' of container '%s' to '%s':\n  %s" %
                            (self.key, repr(inst), value, msg))
        except ValueError, msg:
            raise ValueError("Failed to set property '%s' of container '%s' to '%s':\n %s" %
                             (self.key, repr(inst), value, msg))


# untested, therefore commented out
# class WeakMetaAttribute(MetaAttribute):
    
#     def __get__(self, inst, cls=None):
#         value = MetaAttribute.__get__(inst,cls)
#         if value is not None:
#             return value()
#         else:
#             return value

#     def __set__(self, inst, value):
#         value = self.prop.check_value(value)
#         if value is not None:
#             value = weakref.ref(value)
#         inst.set_value(self.key, value)



#------------------------------------------------------------------------------

class Check:
    """ Abstract base class for all value check.

    In a derived class, implement __call__(self, value).

    @raise TypeError:
    @raise ValueError:
    """
    pass


class Transformation(Check):
    """ Abstract base class for all value transformations.

    In a derived class, implement __call__(self, value).

    @raise ValueError:
    @raise TypeError:
    """
    pass


class Coerce(Transformation):

    def __init__(self, _type):
        self._type = _type

    def __call__(self, value):
        if value is None:
            return None
        else:
            return self._type(value)


class CheckRegexp(Check):
    
    """ Check value against a given regular expression. """
    
    def __init__(self, regexp):
        self._regexp=regexp
        self._expression = re.compile(regexp)

    def __call__(self, value):
        match = self._expression.match(value)
        if match is None:
            raise ValueError("Value %s does not match the regular expression %s" % (value,self._regexp))


class CheckType(Check):

    """ One of the given types must match the given value. """

    def __init__(self, *_types):
        self._types = as_list(_types)

    def __call__(self, value):
        if value is None:
            return
        
        for _type in self._types:                   
            if isinstance(value, _type):
                return
        else:
            raise TypeError("Invalid type '%s', must be one of '%s'" % (type(value), self._types))


class CheckTuple(Check):
    def __init__(self, length):
        self._length = length
    def __call__(self, value):
        if isinstance(value, tuple) and len(value) == self._length:
            return
        else:
            raise TypeError("Value must be tuple of length %d!" % self._length )
    
        
class CheckAll(Transformation):
    
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



class CheckValid(Check):
    def __init__(self, values):
        self.values = as_list(values)        
    def __call__(self, value):
        if (value in self.values) is False:
            raise ValueError("Value %s is not in the list of valid values: %s" % (value, self.values))


class CheckInvalid(Check):
    def __init__(self, values):
        self.values = as_list(values)        
    def __call__(self, value):
        if value in self.values:
            raise ValueError("Value %s in in the list of invalid values: %s" % (value, self.values))    

                
                
class CheckBounds(Check):
    """
    Check if the given value is in between the given bounds [min:max].

    If min or max is None, then the appropriate direction is unbound.
    If steps is given, then a min must be given as well.
    A value of None is always valid.    
    """
    def __init__(self, min=None, max=None, steps=None):
        self.min=min
        self.max=max
        self.steps=steps        

    def __call__(self,value):
        if value is None:
            return None
        
        if (self.min is not None and value < self.min) \
               or (self.max is not None and value > self.max):
            raise ValueError("Value %s should be in between [%s:%s]" % (value, self.min, self.max))

        if self.steps is not None:
            remainder = (value - self.min) % self.steps
            if remainder != 0.0:
                # TODO: how to word this?                
                raise ValueError("Value %s must .... Remainder %s" % (value, remainder) ) 






#------------------------------------------------------------------------------
# Base Class 'Prop'
#

class Prop:

    def __init__(self, *check, **kwargs):
        """
        @keyword default: (None)
        @keyword blurb: (None)
        @keyword doc: (None)
        """

        self.blurb = kwargs.get('blurb', None)
        self.doc = kwargs.get('doc', None)
        
        self.check = CheckAll(check or [])

        default = kwargs.get('default', None)        
        if default is not None:
            default = self.check_value(default)
        self.default = default
        

    def check_value(self, value):
        return self.check(value)

    def reset_value(self):
        """ Requested upon first initialization and when using
        Container.reset. """
        return None
        
    def default_value(self):
        """ Requested if value is None. """
        return self.default
            
    def meta_attribute(self, key):
        return MetaAttribute(self, key)

                      

#------------------------------------------------------------------------------
# Extended Props
#

class ListProp(Prop):
       
    def check_value(self, value):
        if isinstance(value, TypedList):
            return value
        elif isinstance(value, list):
            return TypedList(value, self.check)
        elif isinstance(value, tuple):
            return TypedList(list(value),self.check)
        else:
            raise TypeError("The value '%s' has %s while it should be a list/tuple." %
                            (value, type(value)))

    def reset_value(self):
        return TypedList(check=self.check)
    

                
class DictProp(Prop):

    def check_value(self, value):
        if isinstance(value, TypedDict):
            return value
        elif isinstance(value, dict):
            return TypedDict(value, self.check)
        else:            
            raise TypeError("The value '%s' has %s while it should be a dict." %
                            (value, type(value)))

    def reset_value(self):
        return TypedDict(check=self.check)


class BoolProp(Prop):
    def __init__(self, **kwargs):
        Prop.__init__(self, Coerce(bool), **kwargs)


class KeyProp(Prop):
    def __init__(self, **kwargs):
        Prop.__init__(self,
                      CheckType(basestring),
                      CheckRegexp('^\w*$'),
                      **kwargs)
        
    
class RangeProp(Prop):

    def __init__(self, *check, **kwargs):
        min = kwargs.get('min', None)
        max = kwargs.get('max', None)
        steps = kwargs.get('steps', None)
        
        self.min = min
        self.max = max
        if steps is not None and self.min is None:
            raise RuntimeError("Keyword `steps` may only provided along with a minimum value.")
        self.steps = steps

        check = list(check)
        check.append(CheckBounds(min,max,steps))
        Prop.__init__(self, *check, **kwargs)




    # #
# # UNTESTED!
# #
# class WeakRefProp(Prop):

#     def __init__(self, types=None, transform=None, values=None,
#                  doc=None, blurb=None):
#         Prop.__init__(self, types=types, transform=transform, values=values,
#                       doc=doc, blurb=blurb)

#     def meta_attribute(self, key):
#         return WeakMetaAttribute(self, key)

#------------------------------------------------------------------------------
# Container
#

class Container(object):

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
                    self._values[key] = value.reset_value()
                    kwvalue = kwargs.pop(key,None)
                    if kwvalue is not None:
                        self.__setattr__(key,kwvalue)

        # complain if there are unused keyword arguments
        if len(kwargs) > 0:
            raise ValueError("Unrecognized keyword arguments: %s" % kwargs)


    #----------------------------------------------------------------------
    # Setting/Getting Magic
    #
    
    def __setattr__(self, key, value):
        if key in ('_props','_values'):
            raise RuntimeError("Attributes '_props' and '_values' cannot be altered for Container objects.")
        
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
