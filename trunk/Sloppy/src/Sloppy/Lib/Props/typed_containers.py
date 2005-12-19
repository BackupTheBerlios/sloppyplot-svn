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


class TypedList:

    def __init__(self, check, _list=None):
        self.check = check        
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

    def __getitem__(self, i):
        return self.data[i]
    
    def __setitem__(self, i, item):
        self.data[i] = self.check_item(item)
    
    def __delitem__(self, i):
        del self.data[i]
    
    def __getslice__(self, i, j):
        i = max(i, 0); j = max(j, 0)
        return self.__class__(self.data[i:j])
    
    def __setslice__(self, i, j, other):
        i = max(i, 0); j = max(j, 0)
        self.data[i:j] = self.check_list(other)
        
    def __delslice__(self, i, j):
        i = max(i, 0); j = max(j, 0)
        del self.data[i:j]

    def __add__(self, other):
        return self.__class__(self.data + self.check_list(other))
    
    def __radd__(self, other):
        return self.__class__(self.check_list(other) + self.data)
    
    def __iadd__(self, other):
        self.data += self.check_list(other)
        return self

    def __mul__(self, n):
        return self.__class__(self.data*n)
    __rmul__ = __mul__
    def __imul__(self, n):
        self.data *= n
        return self

    def append(self, item):
        self.data.append(self.check_item(item))
        
    def insert(self, i, item):
        self.data.insert(i, self.check_item(item))
        
    def pop(self, i=-1):
        return self.data.pop(i)
    
    def remove(self, item):
        self.data.remove(item)
        
    def count(self, item):
        return self.data.count(item)
    
    def index(self, item, *args):
        return self.data.index(item, *args)
    
    def reverse(self):
        self.data.reverse()
        
    def sort(self, *args, **kwds):
        self.data.sort(*args, **kwds)
        
    def extend(self, other):
        self.data.extend(self.check_list(other))              

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

    def __init__(self, owner, key, _dict=None, check=None):
        self.owner = owner
        self.key = key
        self.check = check or (lambda o,k,v: v)
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
            return self.check(self.owner, self.key, item)
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

