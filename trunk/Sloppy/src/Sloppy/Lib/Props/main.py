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



__all__ = ["HasProperties", "Property", "PropertyError", "Undefined"]


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
# Base Class 'Property'
#

class Property:
        
    def get_value(self, owner, key):
        return owner._values[key]

    def set_value(self, value, owner, key):
        owner._values[key] = value

    def get_default(self):
        return Undefined
       
        

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
        # order and define the base class Properties first.
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
        if key.startswith('_'):
            return object.__getattribute__(self, key)

        if key.endswith('_'):
            mvalues = object.__getattribute__(self, '_mvalues')
            key = key[:-1]
            if mvalues.has_key(key):
                return mvalues.get(key)           
        
        props = object.__getattribute__(self, '_props')
        if props.has_key(key):
            return props[key].get_value(self, key)

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
    

    def get_value(self, key, default=Undefined):
        value = self.__getattribute__(key)
        if value is Undefined:
            return default
        else:
            return value

    get = get_value

    def get_values(self, include=None, exclude=None, **kwargs):

        rv = {}
        keys = self.get_keys(include=include, exclude=exclude)
        
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

    # mapped values
    
    def get_mvalue(self, key):
        mvalues = object.__getattribute__(self, '_mvalues')
        if mvalues.has_key(key):
            return mvalues.get(key)

        return self.get_value(key)

    

    #----------------------------------------------------------------------
    # Prop Handling
    #

    def get_prop(self, key):
        return self._props[key]

    def get_props(self, include=None, exclude=None):
        rv = {}
        for key in self.get_keys(include=include, exclude=exclude):
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
            old_value = self.get(key)
            if value != old_value:
                changeset[key] = value
        return changeset       


    #----------------------------------------------------------------------
    
    def get_keys(self, include=None, exclude=None):
        if include is None:
            include = self._values.keys()        
        if exclude is not None:
            include = [key for key in include if key not in exclude]
        return include




HasProps = HasProperties

