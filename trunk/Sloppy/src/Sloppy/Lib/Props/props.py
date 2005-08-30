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


import weakref
import re



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
            
          
def _coerce(_type):
    def do_coerce(value):
        try:
            if value is not None:
                return _type(value)
            else:
                return None
        except:
            raise TypeError("Could not coerce value '%s' to %s" % (value, _type))
    return do_coerce

def generic_value_check(value, types=(), coerce=None, values=()):

    # Coercion should be _after_ type checking.
    # If you need to check before coercion, then
    # put the type checking manually into the coercion method.

    # Only one of the types must match.

    #
    # type checking
    #
    def require_one(value, items):
        # 'One of the listed types/methods should be successful'
        for item in items:
            if item is None:
                if value is None: break
                else: continue
            elif isinstance(item, type):
                if isinstance(value, item): break
                else: continue
            else:
                try: item(value)
                except TypeError, ValueError:continue
                else: break
        else:
            raise TypeError("Not a valid type %s." % type(value))
        
    if len(types) > 0:
        require_one(value, types)

    #
    # coercion
    #
    if coerce is not None:
        value = coerce(value)

    #
    # value checking (only if value is not None)
    #
    if value is not None and len(values) > 0:
        for item in values:
            item(value)

    return value



#------------------------------------------------------------------------------
# Helper Types
#

class TypedList:

    def __init__(self, initlist=None, types=(),coerce=None,values=()):
        """
        Note that there is no type checking for types, coerce and
        values as in Prop.__init__ !
        """ 

        self.data = []

        self.types = types
        self.coerce = coerce
        self.values = values
        
        if initlist is not None:
            self.data = self.check_list(initlist)


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
        return self.__class__(self.data + self.check_list(other), **self.metadata())
    def __radd__(self, other):
        return self.__class__(self.check_list(other) + self.data, **self.metadata())
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
            value = generic_value_check(item,**self.metadata())
            return value
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

    def metadata(self):
        """
        Use **self.metadata() as shortcut for
           types=self.types,coerce=self.coerce,values=self.values
        in function calls.
        """
        return {'types':self.types,'coerce':self.coerce,'values':self.values}


    
class TypedDict:

    def __init__(self, dict=None, types=(),coerce=None,values=()):
        self.data = {}
        
        self.types = types
        self.coerce = coerce
        self.values = values

        if dict is not None:
            self.update(dict)
                
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
            return TypedDict(self.data.copy(), **self.metadata())
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
            value = generic_value_check(item,**self.metadata())
            return value
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

    def metadata(self):
        """
        Use **self.metadata() as shortcut for
           types=self.types,coerce=self.coerce,values=self.values
        in function calls.
        """
        return {'types':self.types,'coerce':self.coerce,'values':self.values}



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
# Check Type, Coerce and Check Value Methods
#

def ct_tuple(length):
    def check_type(value):
        if isinstance(value, tuple) and len(value) == length: return
        else: raise TypeError("Value must be tuple of length %d!" % length )
    return check_type



def coerce_bool(value):
    if isinstance(value, basestring):
        if value == "False": return False
        elif value == "True": return True
        else:
            raise ValueError("Unknown boolean string '%s'. Use either 'False' or 'True' or a real bool." % value)
    else:
        return bool(value)



def cv_valid(alist):
    alist = as_list(alist)
    def check_value(value):
        if (value in alist) is False:
            raise ValueError("Value %s is in the list of valid values: %s" % (value, alist))
    return check_value

def cv_invalid(alist):
    alist = as_list(alist)
    def check_value(value):
        if value in alist:
            raise ValueError("Value %s in in the list of invalid values: %s" % (value, alist))    
    return check_value
            
def cv_bounds(start, end,steps=None):
    def check_value(value):
        if (start is not None and value < start) \
           or (end is not None and value > end):
            raise ValueError("Value %s should be in between [%s:%s]" % (value, start or "", end or ""))

        if steps is not None:
            remainder = (value - start) % steps
            if remainder != 0.0:
                raise ValueError("Value %s must .... Remainder %s" % (value, remainder) ) # TODO: how to word this?

        return value
    return check_value

def cv_regexp(regexp):
    expression = re.compile(regexp)
    def check_value(value):
        match = expression.match(value)
        if match is None:
            raise ValueError("Value %s does not match the regular expression %s" % (value,regexp))

    return check_value



#------------------------------------------------------------------------------
# Base Class 'Prop'
#

class Prop:

    def __init__(self, types=None, coerce=None,
                 values=None, value_list=None,
                 default=None,
                 blurb=None, doc=None):

        if isinstance(coerce, type):
            coerce = _coerce(coerce)                
        self.coerce = coerce
        
        self.types = as_list(types or [])
        self.values = as_list(values or [])

        # value_list is just a shorthand for
        #  values=cv_valid(...), default=first_value_of_the_list
        # 
        self.value_list = value_list
        if value_list is not None:
            self.values.append(cv_valid(self.value_list))
            if default is None and len(value_list) > 0:
                default = value_list[0]

        if default is not None:
            default = self.check_value(default)
        self.default = default
        
        self.blurb = blurb        
        self.doc = doc
    
    def check_value(self, value):
        return generic_value_check(value, types=self.types, coerce=self.coerce, values=self.values)

    def reset_value(self):
        " Reset value is requested upon first initialization and when using Container.reset. "
        return None
        
    def default_value(self):
        " Default value is requested if value is None. "
        return self.default
            
    def meta_attribute(self, key):
        return MetaAttribute(self, key)

                      

#------------------------------------------------------------------------------
# Extended Props
#

class ListProp(Prop):

    def __init__(self, types=None, coerce=None, values=None,
                 blurb=None, doc=None):
        Prop.__init__(self, types=types, coerce=coerce, values=values,
                      blurb=blurb, doc=doc)
        
    def check_value(self, value):
        if isinstance(value, TypedList):
            return value
        elif isinstance(value, list):
            return TypedList(value,types=self.types,coerce=self.coerce,values=self.values)
        elif isinstance(value, tuple):
            return TypedList(list(value),types=self.types,coerce=self.coerce,values=self.values)
        else:
            raise TypeError("The value '%s' has %s while it should be a list/tuple." %
                            (value, type(value)))

    def reset_value(self):
        return TypedList(types=self.types,coerce=self.coerce,values=self.values)
    

                
class DictProp(Prop):

    def __init__(self, types=None, coerce=None, values=None,
                 blurb=None, doc=None):
        Prop.__init__(self, types=types, coerce=coerce, values=values,
                      blurb=blurb, doc=doc)

    def check_value(self, value):
        if isinstance(value, TypedDict):
            return value
        elif isinstance(value, dict):
            return TypedDict(value, types=self.types,coerce=self.coerce,values=self.values)
        else:            
            raise TypeError("The value '%s' has %s while it should be a dict." %
                            (value, type(value)))

    def reset_value(self):
        return TypedDict(types=self.types,coerce=self.coerce,values=self.values)


# #
# # UNTESTED!
# #
# class WeakRefProp(Prop):

#     def __init__(self, types=None, coerce=None, values=None,
#                  doc=None, blurb=None):
#         Prop.__init__(self, types=types, coerce=coerce, values=values,
#                       doc=doc, blurb=blurb)

#     def meta_attribute(self, key):
#         return WeakMetaAttribute(self, key)


    
class BoolProp(Prop):

    def __init__(self, default=None, doc=None, blurb=None):
        Prop.__init__(self, types=(bool,str), coerce=coerce_bool,
                      default=default, doc=doc, blurb=blurb)

    
class RangeProp(Prop):

    def __init__(self, types=None, coerce=None,
                 default=None,
                 doc=None, blurb=None,
                 min=None, max=None, steps=None):
        
        Prop.__init__(self, types=types, coerce=coerce, values=cv_bounds(min,max,steps),
                      default=default,
                      doc=doc, blurb=blurb)

        self.min = min
        self.max = max

        if steps is not None and self.min is None:
            raise RuntimeError("Keyword `steps` may only provided along with a minimum value.")
        self.steps = steps

class KeyProp(Prop):

    def __init__(self, default=None, blurb=None, doc=None):
        Prop.__init__(self, types=(basestring,None), values=cv_regexp('^\w*$'),
                      default=default, doc=doc, blurb=blurb)


    
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





#------------------------------------------------------------------------------
# Testing


if __name__ == "__main__":

    class CBaseContainer(Container):
        myinherited = Prop(types=float)
        
    class NC(CBaseContainer):
        myint = Prop(types=(int,None),
                     default=5)

        mynumber = Prop(coerce=int)

        myfloat = Prop(types=float)
        
        myvalue = Prop(types=(int,float,str),
                       coerce=float)

        mytuple = Prop(types=ct_tuple(2))
        
        mylistvalue = Prop(types=str,
                           value_list=['Anne','Niklas'])

        mybounded = Prop(types=int,
                       values=(cv_bounds(0,20),
                               cv_invalid(10)))

        mylist = ListProp(types=int,
                          values=(cv_bounds(0,100)))

        mydict = DictProp(types=str,
                          values=(cv_regexp("^\w*$")))

        mybool = BoolProp()

        myrange = RangeProp(coerce=int, min=0, max=10, steps=2)
        #myinherited = BoolProp()
        
    nc = NC(myrange='4')
    print nc.myrange, type(nc.myrange)


    nc.myint=None
    print nc.myint
    #nc.myint=5.3 # fails
    nc.mynumber = 17
    print "Should be 17: ", nc.mynumber
    nc.mynumber = 17.4
    print "Should still be 17: ", nc.mynumber
    nc.mynumber = '18'
    #nc.mynumber = None
    print "Should be 18: ", nc.mynumber
    nc.myfloat = 27.5
    print nc.myfloat, type(nc.myfloat)

    nc.myvalue = 5.2
    print nc.myvalue
    nc.myvalue = '5.2'
    print nc.myvalue
    #nc.myvalue = (10,5) #fails

    nc.mytuple = (4,3)
    #nc.mytuple = 'Hallo' # fails
    print nc.mytuple
    
    nc.mylistvalue = 'Anne'
    #nc.mylistvalue = 'Anne2'

    nc.mybounded = 9
    #nc.mybounded = 10
    #nc.mybounded = 22 # fails


    print "List"
    nc.mylist.append(5)#
    print nc.mylist
    nc.mylist = (10,5)
    #nc.mylist = [5,10.4] # fails
    print nc.mylist

    nc.mylist.insert(0,100)
    print nc.mylist

    nc.mydict.update( {'Author':'Niklas_Volbers', 'Version': 'a'} )
    print nc.mydict
    

    nc.mybool = False
    print nc.mybool
    nc.mybool = True
    print nc.mybool
    nc.mybool = "True"
    print nc.mybool
    nc.mybool = "False"
    print nc.mybool
    
    #nc.mybool = "Tru" # fails
    #nc.mybool = 52 # fails

    nc.myrange = 0
    nc.myrange = '4'
    print nc.myrange, type(nc.myrange)
    #nc.mylist.append(None)

    nc.myinherited = 4.2
    print nc.myinherited, type(nc.myinherited)
