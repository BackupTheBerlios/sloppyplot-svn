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


""" Commonly used Undo wrappers. """

import logging

from undo import UndoList, UndoInfo, NullUndo


# A word of warning!
# Don't use set for lists and dicts !!
# TODO: why not? document set better; maybe raise an exception
# TODO: if used for invalid objects ?

def set(container, *args, **kwargs):
    
    undolist = kwargs.pop('undolist', UndoList())
    olditems = dict()
    changeset = []

    arglist = list(args)
    while len(arglist) > 1:
        key = arglist.pop(0)
        value = arglist.pop(0)
        olditems[key] = getattr(container, key)
        setattr(container, key, value)
        changeset.append(key)

    for (key, value) in kwargs.iteritems():
        olditems[key] = getattr(container, key)
        setattr(container, key, value)
        changeset.append(key)

    undolist.append( UndoInfo(set, container, **olditems) )      


def smart_set(container, *args, **kwargs):

    """ Like 'set', but only add undo information, if the values have
    actually changed. """
    
    undolist = kwargs.pop('undolist', UndoList())
    olditems = dict()
    changed_props = []

    def do_set(key, value):
        old_value = getattr(container, key)
        setattr(container, key, value)
        if old_value != getattr(container, key):
            olditems[key] = old_value
            changed_props.append(key)
            print "Prop '%s' has changed from '%s' to '%s'." % (key, old_value, getattr(container,key))

    arglist = list(args)
    while len(arglist) > 1:
        do_set(arglist.pop(0), arglist.pop(0))
        
    for (key, value) in kwargs.iteritems():
        do_set(key, value)


    if len(changed_props) > 0:
        undolist.append( UndoInfo(smart_set, container, **olditems) )
    else:
        undolist.append( NullUndo() )




# This part is currently commented out, because I am not yet
# sure if I should mix the libraries among each other.

# def emit(sender, name, *args, **kwargs):
#     " undo wrapper around emit. "
#     undolist = kwargs.pop('undolist', [])    
#     if isinstance(sender, HasSignals):
#         sender.sig_emit(name, *args, **kwargs)        
#     undolist.append(UndoInfo(emit, sender, name, *args, **kwargs))

# def emit_last(sender, name, *args, **kwargs):
#     ul = kwargs.pop('undolist', [])
#     if isinstance(sender, HasSignals):
#         sender.sig_emit(name, *args, **kwargs)        
#     ul.insert(0, UndoInfo(emit_last, sender, name, *args, **kwargs))
