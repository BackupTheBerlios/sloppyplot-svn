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


import logging
logger = logging.getLogger('proprenderer')

try:
    import pygtk
    pygtk.require('2.0')
except ImportError:
    pass

import gtk

import sys

from Sloppy.Base import uwrap
from Sloppy.Lib.Props import *
from Sloppy.Base.properties import *




###############################################################################

class Renderer(object):

   
    def __init__(self, container, key):
        self.container = container
        self.key = key
        self.prop = container.get_prop(key)
        self.cell = None

        self.last_value = None

        self.init()

    def init(self):
        pass

    def create(self):
        raise RuntimeError("create_renderer() needs to be implemented.")

renderers = {}




###############################################################################

class RendererUnicode(Renderer):

    """ Suitable for VUnicode. """

    type = object
    
    def create(self, model, index):
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited, model, index)
        
        column = gtk.TreeViewColumn(self.key)
        column.pack_start(cell)

        column.set_cell_data_func(cell, self.cell_data_func, index)
        #column.set_attributes(cell, text=index)

        self.column = column
        return column


    def on_edited(self, cell, path, new_text, model, index):    
        try:
            value = self.prop.check(new_text)
        except PropertyError:
            pass
        else:
            model[path][index] = value

    def cell_data_func(self, column, cell, model, iter, index):
        value = model.get_value(iter, index)
        cell.set_property('text', unicode(value))

    
        
renderers['Unicode'] = RendererUnicode


#------------------------------------------------------------------------------

class RendererChoice(Renderer):

    """ Suitable for VChoice. """

    type = object
    
    def create(self, model, index):

        # set up cell_model
        prop = self.container.get_prop(self.key)
        vchoices = [v for v in prop.validator.vlist if isinstance(v, VChoice)]
        if len(vchoices) == 0:
            raise TypeError("Property for connector 'Choice' has no choice validator!")
        self.vchoice = vchoice = vchoices[0]

        cell_model = gtk.ListStore(str, object)
        for value in vchoice.values:
            cell_model.append((unicode(value), value))

        cell = gtk.CellRendererCombo()                        
        cell.set_property('text-column', 0)
        cell.set_property('model', cell_model)

        # make editable
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited, model, index)

        column = gtk.TreeViewColumn(self.key)
        column.pack_start(cell)
        column.set_cell_data_func(cell, self.cell_data_func, index)

        self.column = column
        return column


    def on_edited(self, cell, path, new_text, model, index):
        try:
            value = self.prop.check(new_text)
        except PropertyError:
            pass
        else:        
            model[path][index] = new_text

    def cell_data_func(self, column, cell, model, iter, index):
        value = model.get_value(iter, index)
        cell.set_property('text', unicode(self.prop.check(value)))

        
renderers['Choice'] = RendererChoice


#------------------------------------------------------------------------------

class RendererBoolean(Renderer):

    """ Suitable for VBoolean. """

    type = object
    
    def create(self, model, index):
        cell = gtk.CellRendererToggle()

        cell.set_property('activatable', True)
        cell.connect('toggled', self.on_toggled, model, index)

        column = gtk.TreeViewColumn(self.key)
        column.pack_start(cell)
        column.set_cell_data_func(cell, self.cell_data_func, index)

        self.column = column
        return column


    def cell_data_func(self, column, cell, model, iter, index):
        value = model.get_value(iter, index)
        cell.set_property('active', bool(self.prop.check(value)))


    def on_toggled(self, cell, path, model, index):
        value = not model[path][index]
        try:
            value = self.prop.check(value)
        except PropertyError:
            pass
        else:        
            model[path][index] = value

renderers['Boolean'] = RendererBoolean
