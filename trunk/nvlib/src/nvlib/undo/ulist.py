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
Wrapper functions to add undo capabilites to list objects.
"""

from undo import *


def append(obj, item, undolist=[]):
    ui = UndoInfo(remove, obj, item)
    obj.append(item)
    undolist.append(ui)

def pop(obj, i=-1, undolist=[]):        
    undolist.append( UndoInfo(insert, obj, i, obj[i]) )
    return obj.pop(i)

def insert(obj, i, item, undolist=[]):
    ui = UndoInfo(remove, obj, item)
    obj.insert(i, item)
    undolist.append(ui)

def remove(obj, item, undolist=[]):        
    ui = UndoInfo(insert, obj, obj.index(item), item)
    obj.remove(item)
    undolist.append(ui)

def setitem(obj, i, item, undolist=[]):
    ui = UndoInfo(setitem, obj, i, obj[i])
    obj[i] = item
    undolist.append(ui)

def delitem(obj, i, undolist=[]):
    ui = UndoInfo(insert, obj, i, obj[i])
    del obj[i]
    undolist.append(ui)
