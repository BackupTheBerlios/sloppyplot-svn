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

# $HeadURL: svn+ssh://niklasv@svn.berlios.de/svnroot/repos/sloppyplot/trunk/Sloppy/src/Sloppy/Lib/Props/typed_containers.py $
# $Id: typed_containers.py 423 2006-01-04 10:27:32Z niklasv $


class TypedList:

    def __init__(self, descr, _list=None):
        self.descr = descr
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
        item = self.descr.check(item)
        self.data[i] = item
        self.descr.on_update(self, 'added', [item])
        
    def __delitem__(self, i):
        item = self.data[i]
        del self.data[i]
        self.descr.on_update(self, 'removed', [item])
    
    def __getslice__(self, i, j):
        i = max(i, 0); j = max(j, 0)
        return self.__class__(self.descr.check, self.data[i:j])
    
    def __setslice__(self, i, j, other):
        i = max(i, 0); j = max(j, 0)
        self.data[i:j] = self.check_list(other)
        # TODO: 
        self.descr.on_update(self, 'updated', items)
        
    def __delslice__(self, i, j):
        i = max(i, 0); j = max(j, 0)
        items = self.data[i:j]
        del self.data[i:j]
        self.descr.on_update(self, 'removed', items)

    def __add__(self, other):
        return self.__class__(self.descr.check, self.data + self.check_list(other))
    
    def __radd__(self, other):
        return self.__class__(self.descr.check, self.check_list(other) + self.data)
        
    def __iadd__(self, other):
        items = items
        self.data += self.check_list(other)
        self.descr.on_update(self, 'updated', items)
        return self

    def __mul__(self, n):
        return self.__class__(self.descr, self.data*n)
    __rmul__ = __mul__
    def __imul__(self, n):
        self.data *= n
        return self

    def append(self, item):
        item = self.descr.check(item)
        self.data.append(item)
        self.descr.on_update(self, 'added', [item])
        
    def insert(self, i, item):
        item = self.descr.check(item)
        self.data.insert(i, item)
        self.descr.on_update(self, 'added', [item])        
        
    def pop(self, i=-1):    
        item = self.data.pop(i)
        self.descr.on_update(self, 'removed', [item])
        return item       
    
    def remove(self, item):
        self.data.remove(item)
        self.descr.on_update(self, 'removed', [item])
        
    def count(self, item):
        return self.data.count(item)
    
    def index(self, item, *args):
        return self.data.index(item, *args)
    
    def reverse(self):
        self.data.reverse()
        
    def sort(self, *args, **kwds):
        self.data.sort(*args, **kwds)
        
    def extend(self, other):
        items = self.check_list(other)
        self.data.extend(items)
        self.descr.on_update(self, 'added', items)

    def __iter__(self):
        for member in self.data:
            yield member

    #------------------------------------------------------------------------------
    def check(self, item):
        " check must be set from outside. "
        return item
    
    def check_list(self, alist):
        if isinstance(alist, TypedList):
            alist = alist.data

        if isinstance(alist, (list,tuple)):
            newlist = []
            for item in alist:
                newlist.append(self.descr.check(item))
            return newlist
        else:
            raise TypeError("List required, got %s instead." % type(alist))



    
class TypedDict:

    def __init__(self, key_descr, value_descr, _dict=None):
        self.key_descr = key_descr
        self.value_descr = value_descr
        self.data = {}

        if _dict is not None:
            self.update(_dict)

                
    def __repr__(self): return repr(self.data)
    def __cast(self, other): return self.check_dict(other)
    def __cmp__(self, other): return cmp(self.data, self.__cast(other))
    def __len__(self): return len(self.data)
    def __getitem__(self, key): return self.data[key]

    def __setitem__(self, key, item):
        item = self.value_descr.check(item)
        if self.data.has_key(key):
            self.data[key] = item
            self.value_descr.on_update({'update': [key]})
        else:
            self.data[key] = item
            self.value_descr.on_update({'added': [key]})
        
    def __delitem__(self, key):
        del self.data[key]
        self.value_descr.on_update({'removed': [key]})
        
    def clear(self):
        keys = self.data.keys()
        self.data.clear()
        self.value_descr.on_update({'removed': keys})
    
    def copy(self):
        # TODO
        if self.__class__ is TypedDict:
            return TypedDict(self.data.copy())
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
            adict = self.check_dict(dict)
        if len(kwargs) > 0:
            adict.update(self.check_dict(kwargs))
            
        self.data.update(adict)
        self.value_descr.on_update(self, 'update', adict.keys())
            
    def get(self, key, failobj=None):
        if not self.has_key(key):
            return failobj
        return self[key]
    
    def setdefault(self, key, failobj=None):
        # ????
        if not self.has_key(key):
            self[key] = self.value_descr.check(failobj)
        return self[key]
    
    def pop(self, key, *args):
        item = self.data.pop(key, *args)
        self.value_descr.on_update(self, 'removed', [key])
        return item
    
    def popitem(self):
        item = self.data.popitem()
        # ??? Which key?
        #self.value_descr.on_update({'-': [item]})
        return item
    
    def __contains__(self, key):
        return key in self.data
    
    def fromkeys(cls, iterable, value=None):
        # TODO
        d = cls() # TODO: type?
        for key in iterable:
            d[key] = value
        return d
    fromkeys = classmethod(fromkeys)

    def __iter__(self):
        return iter(self.data)


    #------------------------------------------------------------------------------

    def check_dict(self, adict):
        if isinstance(adict, TypedDict):
            adict = adict.data
            
        if isinstance(adict, dict):
            new_dict = {}
            for key, val in adict.iteritems():
                new_dict[key] = self.value_descr.check(val)
            return adict
        else:
            raise TypeError("Dict required, got %s instead." % type(adict))

