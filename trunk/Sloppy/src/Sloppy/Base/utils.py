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

 
from Sloppy.Base.objects import *


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



# def unique_key(dict, keyproposal):

#     """    
#     Return a valid key that is not yet in use in the dict based on the
#     proposal.    
#     """
    
#     counter = 0
#     suggestion = keyproposal
#     while dict.has_key(suggestion):
#         counter += 1
#         suggestion = "%s%02d" % (keyproposal, counter)
#     return suggestion



