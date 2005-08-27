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


import weakref
from helpers import TypedList, TypedDict



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


# TESTING
# tcheck=props.coerce(int)
def coerce(_type):
    return (lambda value: _type(value))



class RangeError(Exception):
    pass




#------------------------------------------------------------------------------
# Meta Attributes
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



class WeakMetaAttribute(MetaAttribute):
    
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


#------------------------------------------------------------------------------
# Properties
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

        if self.types is not None:

            #self.types is either a type or a function
            if isinstance(self.types, (type,list,tuple)):
                # -> type
                if not isinstance(val, self.types):
                    raise TypeError("The value '%s' has %s while it should have %s" %
                                    (val, type(val), self.types))
            else:
                # -> function
                self.types(self, val)
                

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



#------------------------------------------------------------------------------
# Container
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


    def get_key_value_dict(self):
        rv = dict()
        for key, prop in self.get_propdict().iteritems():
            rv[key] = self.get_value(key)
        return rv
    

    def getClassName(cls):
        return cls.__name__
    getClassName = classmethod(getClassName)

        

