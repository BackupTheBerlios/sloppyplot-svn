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


"""
Wrappers for pseudo dictionary access to lists.
Each list element must have an attribute 'key'.
"""


def getitem(obj, key, **kwargs):
    " You may provide a keyword argument `default` "    
    items = [ item for item in obj if item.key == key ]
    if len(items) > 0:
        return items[0]
    elif kwargs.has_key('default'):
        return kwargs.pop('default')
    else:
        raise KeyError("Key '%s' not found" % key)

def setitem(obj, key, item):
    if has_key(obj, key) or item is None:
        delitem(obj, key)

    if item is not None:
        if not hasattr(item, 'key'):
            raise TypeError("Item '%s' must have a `key` member." % item)
        item.key = key
        obj.append(item)
                   


def delitem(obj, key):
    items = [ item for item in obj if item.key == key ]
    for item in items:
        obj.remove(item)


def has_key(obj,key):
    " Return True if an item with the given key exists. "
    if isinstance(obj, dict):
        return obj.has_key(key)
    
    for member in obj:
        if member.key == key:
            return True
    return False


def keys(obj): return [item.key for item in obj]
def values(obj): return obj


#--- ITERATORS --------------------------------------------------------
    
def iteritems(obj):
    for member in obj:
        yield (member.key, member)

def iterkeys(obj):
    for member in obj:
        yield member.key

def itervalues(obj):
    for member in obj:
        yield member


#--- CONVERT TO/FROM REAL DICTIONARIES --------------------------------

def to_dict(self):
    result = dict()
    for item in obj:
        result[item.key] = item
    return result

def from_dict(obj, item_dict):
    obj = []
    for (key, item) in item_dict.iteritems():
        if hasattr(item, "key"):
            item.key = key
            obj.append(item)
        else:
            raise TypeError("Item '%s' must have a `key` member." % item)


def unique_key(obj, keyproposal):

    """    
    Return a valid key that is not yet in use in the dict based on the
    proposal.    
    """
    
    counter = 0
    suggestion = keyproposal
    while has_key(obj, suggestion):
        counter += 1
        suggestion = "%s_%02d" % (keyproposal, counter)
    return suggestion


#----------------------------------------------------------------------
# Methods with extended notation (xn)

# extended notation means that you may either specify
#  - an index
#  - the object's key
#  - the object itself (but it has to be in the list)


def xn_get(alist, key, default=-1):
    try:
        if isinstance(key, int):
            return alist[key]
        elif isinstance(key, basestring):
            return getitem( alist, key )
        elif not key in alist:
            raise KeyError("Given Key is not in Project")
        return key
                
    except (KeyError, IndexError):
        if default != -1:
            return default
        else:
            raise
            
    raise TypeError("xn_get: 'key' must be an integer, a key string or an object.")


def xn_has_key(alist, key):
    if xn_get(alist, key, None) is not None:
        return True
    else:
        return False



#------------------------------------------------------------------------------
# EXAMPLES

# this section is outdated and should be moved to the Test directory



if __name__ == "__main__":

    class Element:
        def __init__(self, key, val):
            self.key = key
            self.val = val

    alist = [Element('niki', 1),
             Element('anne', 2),
             Element('joerg', 3)]

    setitem(alist, 'niki', Element('a',17))
    print getitem(alist, 'niki').val

    for key, value in iteritems(alist):
        print key, value
