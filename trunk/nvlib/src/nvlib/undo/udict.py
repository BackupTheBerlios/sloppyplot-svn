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


"""
Wrapper functions to add undo capabilites to dict objects.
"""


from undo import *


# TODO: update
# TODO: clear

def pop(obj, key, undolist=[]):        
    undolist.append( UndoInfo(setitem, obj, key, obj[key]) )
    return obj.pop(key)

def popitem(obj, key, undolist=[]):        
    undolist.append( UndoInfo(setitem, obj, key, obj[key]) )
    return obj.popitem(key)

def setitem(obj, key, value, undolist=[]):
    if obj.has_key(key):
        ui = UndoInfo(setitem, obj, key, obj[key])
    else:
        ui = UndoInfo(delitem, obj, key)
    obj[key] = value
    undolist.append(ui)

def delitem(obj, key, undolist=[]):
    ui = UndoInfo(setitem, obj, key, obj[key])
    del obj[key]
    undolist.append(ui)
