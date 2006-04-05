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

from defs import Undefined


"""
updateinfo contains these entries:
- removed
- updated

Removed and updated may be together in one updateinfo.

Lists have an additonal key 'reordered', which I am not sure about
yet. Its arg is set to -1 for a reversal.

Dicts have an additional key 'updated'.
"""

class TypedList:

    def __init__(self, check, _list=None):
        self._check = check
        self.data = []
        self.on_update = lambda sender, updateinfo: None
        self.set_data(_list)

    def set_data(self, _list):
        if _list is not None:
            olddata = self.data
            _list = self.check_list(_list)
            self.data = _list
            self.on_update(self, {'removed': (0, len(olddata), olddata), 'added': (0, len(_list), _list)})

    def check(self, item):
        try:
            return self._check(item)
        except ValueError, msg:
            raise ValueError("Item for list is invalid: %s" % msg)
    
    def check_list(self, alist):
        if isinstance(alist, TypedList):
            alist = alist.data

        if isinstance(alist, (list,tuple)):
            newlist = []
            for item in alist:
                newlist.append(self._check(item))
            return newlist
        else:
            raise TypeError("List required, got %s instead." % type(alist))


    #------------------------------------------------------------------------------
    # All functions below are implementations of methods from UserList.
    # Any new item must be checked via self.check, any new list of items
    # must be checked via self.check_list.
    
    def __repr__(self): return repr(self.data)
    def __lt__(self, other): return self.data <  self.__cast(other)
    def __le__(self, other): return self.data <= self.__cast(other)    
    def __eq__(self, other):
        try:
            return self.data == self.__cast(other)
        except:
            return False
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
        item = self.check(item)
        self.data[i] = item
        self.on_update(self, {'added': (i, 1, [item])})
        
    def __delitem__(self, i):
        item = self.data[i]
        del self.data[i]
        self.on_update(self, {'removed':(i, 1, [item])})
    
    def __getslice__(self, i, j):
        i = max(i, 0); j = max(j, 0)
        return self.__class__(self.check, self.data[i:j])
    
    def __setslice__(self, i, j, other):
        i = max(i, 0); j = max(j, 0)
        olditems = self.data[i:j]
        self.data[i:j] = self.check_list(other)
        self.on_update(self, {'removed': (i, j-i, [olditems]),'added': (i, j-i, [items])})
        
    def __delslice__(self, i, j):
        i = max(i, 0); j = max(j, 0)
        items = self.data[i:j]
        del self.data[i:j]
        self.on_update(self, {'removed': (i, j-1, items)})

    def __add__(self, other):
        # x = self + other => we don't need to check other!
        if isinstance(other, TypedList):
            other = other.data        
        return self.__class__(lambda i: i, self.data + other)
    
    def __radd__(self, other):
        return self.__class__(self.check, self.check_list(other) + self.data)
        
    def __iadd__(self, other):
        items = self.check_list(other)
        i = len(self.data)
        self.data += items
        self.on_update(self, {'added': (i, len(items), items)})
        return self

    def __mul__(self, n):
        return self.__class__(self._check, self.data*n)
    __rmul__ = __mul__

    def __imul__(self, n):
        self.data *= n
        return self

    def append(self, item):
        item = self.check(item)
        self.data.append(item)
        self.on_update(self, {'added': (len(self.data)-1, 1, [item])})
        
    def insert(self, i, item):
        item = self.check(item)
        self.data.insert(i, item)
        self.on_update(self, {'added': (i, 1, [item])})
        
    def pop(self, i=-1):    
        item = self.data.pop(i)
        self.on_update(self, {'removed': (i, 1, [item])})
        return item       
    
    def remove(self, item):
        i = self.data.index(item)
        self.data.remove(item)
        self.on_update(self, {'removed': (i, 1, [item])})
        
    def count(self, item):
        return self.data.count(item)
    
    def index(self, item, *args):
        return self.data.index(item, *args)
    
    def reverse(self):
        self.data.reverse()
        self.on_update(self, {'reordered': -1})
        
    def sort(self, *args, **kwds):
        self.data.sort(*args, **kwds)
        
    def extend(self, other):
        items = self.check_list(other)
        index = len(self.data)
        self.data.extend(items)
        self.on_update(self, {'added': (index, len(items), items)})

    def __iter__(self):
        for member in self.data:
            yield member




    
class TypedDict:

    def __init__(self, key_check, value_check, _dict=None):
        self.key_check = key_check
        self.value_check = value_check
        self.on_update = lambda sender, undoinfo: None
        self.data = {}
        if _dict is not None:
            self.update(_dict)

    def __doc__(self):
        return self.value_check.doc
    
    def set_data(self, adict):        
        olddata = self.data
        self.data = adict
        self.on_update(self, {'removed': olddata, 'added': self.data})

    def check(self, key, value):
        try:
            key = self.key_check(key)
        except ValueError, msg:
            raise ValueError("Key (%s) for dict item is invalid, it %s" % (key, msg))

        try:
            value = self.value_check(value)
        except ValueError, msg:
            raise ValueError("Value (%s) for dict item is invalid, it %s" % (value, msg))
        
        return (key, value)
    
    def check_dict(self, adict):
        if isinstance(adict, TypedDict):
            adict = adict.data
            
        if isinstance(adict, dict):
            new_dict = {}
            for key, value in adict.iteritems():
                key, value = self.check(key, value)
                new_dict[key] = value
            return adict
        else:
            raise TypeError("Dict required, got %s instead." % type(adict))


    #------------------------------------------------------------------------------
    # All functions below are implementations of methods from UserDict.
    # Any new key/item must be checked via self.key_check.__call__/self.value_check.__call__,
    # any new dict of items via self.check_dict.
                    

    def __repr__(self): return repr(self.data)
    def __cast(self, other): return self.check_dict(other)
    def __cmp__(self, other): return cmp(self.data, self.__cast(other))
    def __len__(self): return len(self.data)
    def __getitem__(self, key): return self.data[key]

    def __setitem__(self, key, item):
        key, item = self.check(key, item)
        if self.data.has_key(key):
            self.data[key] = item
            self.on_update(self, {'updated': {key:item}})
        else:
            self.data[key] = item
            self.on_update(self, {'added': {key:item}})
        
    def __delitem__(self, key):
        item = self.data[key]
        del self.data[key]
        self.on_update(self, {'removed': {key:item}})
        
    def clear(self):
        olddata = self.data
        self.data = []
        self.on_update(self, {'removed': olddata})
    
    def copy(self):
        return TypedDict(key_check=self.key_check, value_check=self.value_check,
                             _dict=self.data.copy())
    
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
        self.on_update(self, {'updated': adict})
            
    def get(self, key, failobj=None):
        if not self.has_key(key):
            return failobj
        return self[key]
    
    def setdefault(self, key, failobj=Undefined):
        if not self.has_key(key):
            if failobj is Undefined:
                failobj = self.value_check.on_default()
            key, value = self.check(key, failobj)
            self[key] = value
            self.on_update(self, {'added': {key:value}})
        return self[key]
    
    def pop(self, key, *args):
        item = self.data.pop(key, *args)
        self.on_update(self, {'removed': {key:item}})
        return item
    
    def popitem(self):
        key, value = self.data.popitem()
        self.on_update(self, {'removed': {key: value}})
        return (key, value)
    
    def __contains__(self, key):
        return key in self.data
    
    def fromkeys(cls, iterable, value=None):
        d = self.__class__(self.key_check, self.value_check)
        for key in iterable:
            d[key] = value
        return d
    fromkeys = classmethod(fromkeys)

    def __iter__(self):
        return iter(self.data)


