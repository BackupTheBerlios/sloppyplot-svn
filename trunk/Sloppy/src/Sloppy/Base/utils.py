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

 
#from Sloppy.Base.objects import *


import os.path

# ----------------------------------------------------------------------

def partial_key_extract(source,prefix='',remove_items=False,use_prefix=True):
    """
    Return a copy of the given source dictionary that contains only
    the keys from the original starting with the given prefix.
    
    If `remove_items` is set to True, these items will be removed from
    the original source.  If `use_prefix` is set to True, the key
    names of the new dictionary will contain the search prefix, while
    the prefix will be omitted if `use_prefix` is set to False.
    
    """
    nd = {}
    if use_prefix is False:
        startpos = len(prefix)
    else:
        startpos = 0
        
    for key in source.iterkeys():
        if key.startswith(prefix):
            value = source.get(key)                    
            nd[key[startpos:]] = value

    # remove items if request
    if remove_items is True:
        for key in nd.iterkeys():
            source.pop(key)

    return nd


def encode_as_key(key):
    " This function ensures that the key contains only valid characters ([a-zA-Z0-9_])."
    rv = ""
    for letter in key:
        if letter in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_":
            rv += letter
        else:
            rv += '_'
    return rv


def as_filename(key):
    """  The filename is dynamically created from the given key,
    appended by the extension '.dat'. Path separators are escaped."""
    key = key.replace(os.path.sep, u'_')
    if not isinstance(key, basestring):
        raise TypeError("construct_filename: 'key' must be a valid string, but it is of %s" % type(key))
    return "%s.dat" % key


def unique_names(names, old_names):
    """
    Return a list of names that are not contained in old_names.

    If you have a list of existing names ('old_names') and each name
    has to be unique, then it is difficult to add new names to this
    list. Every time you have to check if the name already exists,
    and if so, you have to change the name to a new, unique name.

    This is basically what this helper function does.

    >>> names = ['col1', 'col2', 'a', 'col1']
    >>> old_names = ['Niklas', 'col1', 'col2']
    >>> unique_names(names, old_names)
    ['col1_1', 'col2_1', 'a', 'col1_2']

    It is also possible to specify a single name for 'name'.
    """
    rv = []
    for name in list(names):
        j = 1
        while (name in old_names) or (name in rv):
            rpos = name.rfind('_%d' % j)
            if rpos == -1:
                name = '%s_%d' % (name, j+1)
            else:
                name = name[:rpos+1] + str(j+1)
            j+=1
        rv.append(name)
    return rv


if __name__ == "__main__":
    print unique_names( ['C']*5, ['C'] )
