# This file is part of nvlib.
# Copyright (C) 2005-2006 Niklas Volbers
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



# TODO: CLARIFY set, get, get_as_list, get_as_dict and so on...

from defs import Undefined


__all__ = ['Property', 'ValidatingProperty', 'vprop',
           'MetaHasProperties', 'HasProperties']
           


class Property:

    def get(self, obj, key, **kw):
        raise RuntimeError("not implemented")

    def set(self, obj, key, value):
        raise RuntimeError("not implemented")

    

class ValidatingProperty(Property):

    def __init__(self, validator, **kwargs):
        self.validator = validator

        self.doc = None
        self.blurb = None        
        self.raw = False        
        
        # the on_init is a lambda function returning the
        # init value for a given object. You can either
        # specify a keyword 'init' which will be translated
        # to (lambda obj: init) or you can specify a direct
        # lambda function using the keyword 'on_init'.
        # If nothing is given, then the value is Undefined.
        init = kwargs.pop('init', Undefined)        
        self.on_init = kwargs.pop('on_init', lambda obj, key: init)

        self.__dict__.update(kwargs)                              

        
    def get(self, obj, key, **kw):
         try:
             mode = kw.pop('mode', 'default')             
             if mode == 'raw' and self.raw is True:
                 key=key+"_"
             return obj.__dict__[key]
         except KeyError:
             return Undefined


    def set(self, obj, key, value):
        try:
            obj.__dict__[key] = self.validator(value)
            if self.raw is True:
                obj.__dict__[key+"_"] = value
        except ValueError, msg:
            raise ValueError("Value (%s) for attribute '%s' is invalid, it %s." % (value, key, msg))


vprop = ValidatingProperty



#------------------------------------------------------------------------------

class MetaHasProperties(type):
  
    def __new__(cls, class_name, bases, attrs):        

        attrs['_props'] = {}
        
        if attrs.has_key('on_update') is False:
            attrs['on_update'] = lambda self, sender, key, value: None
            
        new_class = type.__new__(cls, class_name, bases, attrs)

        # Collect Property instances from the new class and all base
        # classes. Reversing the klasslist is a nice little trick: The
        # base class Property objects are defined first, any Property
        # with the same name from a child class will re-define the
        # Property, which is exactly what one would expect.        
        klasslist = list(new_class.__mro__[:-1])
        klasslist.reverse()

        props = {}
        for klass in klasslist:
            for key, item in klass.__dict__.iteritems():
                if isinstance(item, Property):
                    props[key] = item                
        new_class._props = props        
        
        return new_class


class HasProperties(object):

    __metaclass__ = MetaHasProperties

    def __init__(self, **kwargs):

        #object.__setattr__(self, 'on_update', lambda sender, key, value: None)
        
        # set default values for Property instance values
        for key, prop in self._props.iteritems():
            if kwargs.has_key(key):
                value = kwargs.pop(key)
            else:
                value = prop.on_init(self, key)
        
            if value is not Undefined:
                prop.set(self, key, value)
            else:
                # TODO: must set it _somehow_ to Undefined ?
                pass
            #self.__setattr__(key, value)
                    
        # complain if there are unused keyword arguments
        if len(kwargs) > 0:
            raise ValueError("Unrecognized keyword arguments: %s" % kwargs)


    def __getattribute__(self, key):
        props = object.__getattribute__(self, '_props')
        if props.has_key(key):
            kw = {} # TODO: parse key to interpret key__raw as kw={'mode':'raw'}
            return props[key].get(self, key, **kw)
        return object.__getattribute__(self, key)


    def __setattr__(self, key, value):
        props = self._props
        if props.has_key(key):
            props[key].set(self, key, value)
            self.on_update(self, key, value)
        else:
            object.__setattr__(self, key, value) 



    ### CLARIFY set, get, get_as_list, get_as_dict and so on...

    def set(self, *args, **kw):
        """ Set the given attribute(s) to specified value(s).

        You may pass an even number of arguments, where one
        argument is the attribute name and the next one the
        attribute value. You may also pass this as keyword
        argument, i.e. use the key=value notation.
        """
        props = self._props
        for arg in args:
            arglist = list(args)
            while len(arglist) > 1:
                key = arglist.pop(0)
                value = arglist.pop(0)
                props[key].set(self, key, value)
                self.on_update(self, key, value)
            
        for key, value in kw.iteritems():
            props[key].set(self, key, value)
            self.on_update(self, key, value)
            
        
    def get(self, key, **kwargs):
        """ Return a single attribute value or the undefined value if the
        attribute value is Undefined. """
        undefined = kwargs.pop('undefined', Undefined)
        prop = self._props[key]
        v = prop.get(self, key, **kwargs)
        if v is Undefined:  # TODO: maybe put this into prop.get ???
            return undefined
        if v is None and kwargs.has_key('default'):
            return kwargs.pop('default')
        return v


    def get_as_dict(self, *keys, **kwargs):
        undefined = kwargs.pop('undefined', Undefined)
        if len(keys) == 0:
            keys = self._props.keys()
        
        rv = {}
        for key in keys:
            prop = self._props[key]
            v = prop.get(self, key, **kwargs)            
            if v is Undefined:
                v = undefined
            if v is None and kwargs.has_key('default'):
                return kwargs.pop('default')                
            rv[key] = v

        return rv

    def get_as_list(self, *keys, **kwargs):
        undefined = kwargs.pop('undefined', Undefined)
        if len(keys) == 0:
            keys = self._props.keys()
        
        rv = []
        for key in keys:
            prop = self._props[key]
            v = prop.get(self, key, **kwargs)            
            if v is Undefined:
                v = undefined
            if v is None and kwargs.has_key('default'):
                return kwargs.pop('default')                
            rv.append(v)
        return rv
        
        return tuple(self.get_as_dict(*keys, **kwargs).values())

    def get_as_tuple(self, *keys, **kwargs):
        return tuple(self.get_as_list(*keys, **kwargs))
        

    def dump(self):
        for key in self._props.iterkeys():
            print "  %15s = %s" % (key, self.get(key))

