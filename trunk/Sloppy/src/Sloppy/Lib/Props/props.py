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

# $HeadURL: file:///home/nv/sloppysvn/trunk/Sloppy/src/Sloppy/Lib/Props/props.py $
# $Id: props.py 419 2005-07-21 17:46:47Z nv $


import weakref


# NOTE

# Inherited properties don't work, because Container.__init__
# only instantiates all properties of self.__class__ and not
# those of all sub-classes.
# I have not yet written a workaround for that.


# NOTE

# The keyword argument 'cast' could have been named 'coerce'.  While
# 'cast' should be an explicit type conversion, 'coerce' is an
# implicit one.  It was hard for me to decide which one it is.  After
# all, for each Prop, you can _specify_ the cast operation.



#
#
#--- H E L P E R  C L A S S E S -----------------------------------------------
#
#

class RangeError(Exception):
    pass


class TypedList:

    def __init__(self, initlist=None, types=()):
        self.data = []
        self.types = types or ()
        if initlist is not None:
            self.data = self.check_list(initlist)

    def check_item(self, item):
        if isinstance(item, self.types):
            return item
        else:
            raise TypeError("Item '%s' added to TypedList '%s' must be of %s, but it is %s." %
                            (item, repr(self), self.types, type(item)))

    def check_list(self, alist):
        if isinstance(alist, TypedList):
            return alist.data
        elif isinstance(alist, list):
            for item in alist:
                self.check_item(item)
            return alist
        else:
            raise TypeError("List required, got %s instead." % type(alist))
        
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
        return self.__class__(self.data[i:j], types=self.types)
    def __setslice__(self, i, j, other):
        i = max(i, 0); j = max(j, 0)
        self.data[i:j] = self.check_list(other)
    def __delslice__(self, i, j):
        i = max(i, 0); j = max(j, 0)
        del self.data[i:j]

    def __add__(self, other):
        return self.__class__(self.data + self.check_list(other), types=self.types)
    def __radd__(self, other):
        return self.__class__(self.check_list(other) + self.data, types=self.types)
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

class TypedDict:

    def __init__(self, dict=None, cast=None, types=None, **kwargs):
        self.cast = cast
        self.types = types or ()
        self.data = {}
        if dict is not None:
            self.update(dict)
        if len(kwargs):
            self.update(kwargs)
                
    def __repr__(self): return repr(self.data)
    def __cmp__(self, dict):
        return cmp(self.data, self.__cast(dict))
    def __len__(self): return len(self.data)
    def __getitem__(self, key): return self.data[key]
    def __setitem__(self, key, item):
        self.data[key] = self.check_item(item)
    def __delitem__(self, key): del self.data[key]
    def clear(self): self.data.clear()
    def copy(self):
        if self.__class__ is TypedDict:
            return TypedDict(self.data.copy(), types=self.types)
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

    def check_item(self, item): # maybe rename to check_value ?
        if self.cast is not None:
            return self.cast(item)
        elif isinstance(item, self.types):
            return item
        else:
            print "self.cast_to is ", self.cast
            raise TypeError("Item '%s' added to TypedDict '%s' must be of %s, but it is %s." %
                            (item, repr(self), self.types, type(item)))

    def check_dict(self, adict):
        if isinstance(adict, TypedDict):
            return adict.data
        elif isinstance(adict, dict):
            for val in adict.itervalues():
                self.check_item(val)
            return adict
        else:
            raise TypeError("Dict required, got %s instead." % type(adict))
        
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


#
#
#--- M E T A A T T R I B U T E S ----------------------------------------------
#
#


class MetaAttribute(object):

    def __init__(self, prop, key):
        object.__init__(self)
        self.key = key
        self.prop = prop

    def __get__(self, inst, cls=None):
        return inst.get_value(self.key)

    def __set__(self, inst, val):
        inst.set_value( self.key, self.prop.check_type(val))


class WeakMetaAttribute(object):
    
    def __init__(self, prop, key):
        object.__init__(self)
        self.key = key
        self.prop = prop

    def __get__(self, inst, cls=None):
        val = inst.get_value(self.key)
        if val is not None:
            return val()
        else:
            return val

    def __set__(self, inst, val):
        val = self.prop.check_type(val)
        if val is not None:
            val = weakref.ref(val)
        inst.set_value( self.key, val )


#
#
#--- P R O P E R T I E S ------------------------------------------------------       
#
#


class Prop:
    def __init__(self, types=None, cast=None, default=None,
                 doc=None, values=None, blurb=None, is_node=False):
        self.types = types
        self.cast = cast
        self.doc = doc
        self.blurb = blurb
        self.values = values
        self.is_node = is_node

        if default is not None:
            self.default = default
        elif self.values is not None and len(self.values) > 0:
            self.default = self.values[0]
        else:
            self.default = None

    def check_type(self, val):
        if val is None:
            return self.default

        if self.types is not None and not isinstance(val, self.types):
            raise TypeError("The value '%s' has %s while it should have %s" %
                            (val, type(val), self.types))                

        if self.cast is not None:
            val = self.cast(val)
            
        if self.values is not None and val not in self.values:
            raise ValueError("The value '%s' is not in the list of allowed values %s" %
                             (val, self.values))
        return val
                            
    def default_value(self):
        return self.default

    def meta_attribute(self, key):
        return MetaAttribute(self, key)

   

class RangeProp(Prop):

    def __init__(self, types=None, cast=None,
                 default=None,
                 doc=None, blurb=None,
                 min=None, max=None, steps=None):
        Prop.__init__(self, types=types, cast=cast,
                      default=default,
                      doc=doc, blurb=blurb)
        self.min = min
        self.max = max

        if steps is not None and self.min is None:
            raise RuntimeError("Keyword `steps` may only provided along with both a minimum value.")
        self.steps = steps

    def check_type(self, val):
        val = Prop.check_type(self, val)
        if val is None:
            return self.default
        
        if self.min is not None and val < self.min:
            raise RangeError("Property must have a minimum value of %s" % str(self.min))

        if self.max is not None and val > self.max:
            raise RangeError("Property must have a maximum value of %s" % str(self.max))

        if self.steps is not None:
            remainder = (val - self.min) % self.steps
            if remainder != 0.0:
                raise RangeError("Property value... steps ...")

        return val              


class StringProp(Prop):
    def __init__(self, default=None, doc=None, blurb=None):
        Prop.__init__(self, default=default, doc=doc, blurb=blurb,
                      types=basestring, cast=str)

class UnicodeProp(Prop):
    def __init__(self, default=None, doc=None, blurb=None):
        Prop.__init__(self, default=default, doc=doc, blurb=blurb,
                      types=basestring, cast=unicode)


class BoolProp(Prop):

    def __init__(self, default=None, doc=None, blurb=None):
        Prop.__init__(self, default=default, doc=doc, blurb=blurb)

    def check_type(self, val):
        if val is None:
            return self.default
        
        if isinstance(val, basestring):
            if val == "False":
                val = False
            elif val == "True":
                val = True
            else:
                raise ValueError("Unknown boolean string '%s'. Use either 'False' or 'True' or a real bool." % val)
        else:
            val = bool(val)

        return val
        
            
class WeakRefProp(Prop):

    def __init__(self, types=None, doc=None, blurb=None):
        Prop.__init__(self, types=types, doc=doc, blurb=blurb)

    def meta_attribute(self, key):
        return WeakMetaAttribute(self, key)

                
class ListProp(Prop):

    def __init__(self, types=None, blurb=None, doc=None):
        Prop.__init__(self, types=types, blurb=blurb, doc=doc)
        
    def check_type(self, val):
        if isinstance(val, TypedList):
            return val
        elif isinstance(val, list):
            return TypedList(val, self.types)
        elif isinstance(val, tuple):
            return TypedList(list(val), self.types)
        else:
            raise TypeError("The value '%s' has %s while it should be a list/tuple." %
                            (val, type(val)))

    def default_value(self):
        return TypedList(types=self.types)
  



class DictProp(Prop):

    def __init__(self, cast=None, types=None, doc=None, blurb=None):
        Prop.__init__(self, cast=cast, types=types, doc=doc, blurb=blurb)

    def check_type(self, val):
        if isinstance(val, TypedDict):
            return val
        elif isinstance(val, dict):
            return TypedDict(val, cast=self.cast, types=self.types)
        else:            
            raise TypeError("The value '%s' has %s while it should be a dict." %
                            (val, type(val)))

    def default_value(self):
        return TypedDict(cast=self.cast,types=self.types)



#
#
#--- C O N T A I N E R --------------------------------------------------------            
#
#

class Container(object):

    def __init__(self, **kwargs):

        for key, value in self.__class__.__dict__.iteritems():
            if isinstance(value, Prop):
                attrName = '_XO_%s' % key
                object.__setattr__(self, attrName, value.default_value())
                
        for k,v in kwargs.iteritems():
            setattr(self, k, v)
            
    def __setattr__(self, key, value):
        prop = self.__class__.__dict__.get(key, None)
        if prop is not None and isinstance(prop, Prop):
            prop.meta_attribute(key).__set__(self, value)
        else:
            object.__setattr__(self, key, value)
    
    def __getattribute__(self, key):
        if '_' not in key[:1]:
            prop = self.__class__.__dict__.get(key, None)
            if prop is not None and isinstance(prop, Prop):
                return prop.meta_attribute(key).__get__(self, None)
        return object.__getattribute__(self, key)

    def set_value(self, key, val):
        attrName = '_XO_%s' % key
        object.__setattr__(self, attrName, val)

    def set_values(self, *args, **kwargs):
        arglist = list(args)
        while len(arglist) > 1:
            key = arglist.pop(0)
            value = arglist.pop(0)
            self.set_value(key, value)

        for k,v in kwargs.iteritems():
            self.set_value(k,v)

    def get_value(self, key, default=None):
        attrName = '_XO_%s' % key
        rv = object.__getattribute__(self, attrName)
        if rv is None:
            return default
        return rv

    def get_values(self, *keys):
        rv = list()
        for key in keys:
            rv.append(self.get_value(key))
        return tuple(rv)
            

    def get_prop(cls, key):
        dict = cls.__dict__
        if dict.has_key(key):
            return dict.get(key, None)
        else:
            raise KeyError("No property %s defined for class %s" % (key, str(cls)))
    get_prop = classmethod(get_prop)

    def get_proplist(cls):
        rv = list()
        for k, v in cls.__dict__.iteritems():
            if isinstance(v, Prop):
                rv.append(k)
        return rv
    get_proplist = classmethod(get_proplist)
    
    def get_propdict(cls):
        rv = dict()
        for k,v in cls.__dict__.iteritems():
            if isinstance(v, Prop):
                rv[k] = v
        return rv
    get_propdict = classmethod(get_propdict)


    def getClassName(cls):
        return cls.__name__
    getClassName = classmethod(getClassName)

        

