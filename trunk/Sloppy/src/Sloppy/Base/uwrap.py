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
Commonly used Undo wrappers.
"""


import logging

from Sloppy.Lib.Undo import UndoList, UndoInfo, NullUndo
from Sloppy.Lib import Signals

from Sloppy.Base.const import default_params


def set(container, *args, **kwargs):
    undolist = kwargs.pop('undolist', UndoList())
    olditems = dict()
    changed_props = []

    arglist = list(args)
    while len(arglist) > 1:
        key = arglist.pop(0)
        value = arglist.pop(0)
        olditems[key] = container.get_value(key, None)
        setattr(container, key, value)
        changed_props.append(key)

    for (key, value) in kwargs.iteritems():
        olditems[key] = container.get_value(key, None)            
        setattr(container, key, value)
        changed_props.append(key)

    undolist.append( UndoInfo(set, container, **olditems) )      

    if len(changed_props) > 0:
        Signals.emit(container, "prop-changed", changed_props)


def smart_set(container, *args, **kwargs):

    """ Like 'set', but only add undo information, if the values have
    actually changed. """
    
    undolist = kwargs.pop('undolist', UndoList())
    olditems = dict()
    changed_props = []

    def do_set(key, value):
        old_value = container.get_value(key, None)
        setattr(container, key, value)
        if old_value != container.get_value(key, None):
            olditems[key] = old_value
            changed_props.append(key)
            print "Prop '%s' has changed from '%s' to '%s'." % (key, container.get_value(key, None), old_value)

    arglist = list(args)
    while len(arglist) > 1:
        do_set(arglist.pop(0), arglist.pop(0))
        
    for (key, value) in kwargs.iteritems():
        do_set(key, value)


    if len(changed_props) > 0:
        undolist.append( UndoInfo(smart_set, container, **olditems) )      
        Signals.emit(container, "prop-changed", changed_props)
    else:
        undolist.append( NullUndo() )



def get(self, key, default=None):
    """
    Return value of given option or `default` value.
    If no default value is given, the default from const.py
    is returned.
    """
    try:
        value = getattr(self, key)
        if value == None:
            raise AttributeError
        return value
    except (AttributeError, TypeError):
        # TypeError may be raised if 'None' is an invalid value for the
        # given property.
        if default is not None:
            return default
        else:
            try:
                key = ("%s.%s" % (self.__class__.__name__, key)).lower()
                return default_params[key]
            except KeyError:
                logging.error("No default key for key: %s" % key)
                return None


def emit(sender, name, *args, **kwargs):
    " undo wrapper around emit. "
    undolist = kwargs.pop('undolist', [])
    Signals.emit(sender, name, *args, **kwargs)
    undolist.append(UndoInfo(emit, sender, name, *args, **kwargs))

def emit_last(sender, name, *args, **kwargs):
    ul = kwargs.pop('undolist', [])
    Signals.emit(sender, name, *args, **kwargs)
    ul.insert(0, UndoInfo(emit_last, sender, name, *args, **kwargs))
