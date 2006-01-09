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

    def init(self):
        self.model = None
        self.model_index = -1
        
    def create(self, model, index):
        self.model = model
        self.model_index = index

        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited)
        
        self.widget = cell
        return self.widget

    def get_attributes(self):
        return {'text':self.model_index}


    def on_edited(self, cell, path, new_text):    
        try:
            value = self.prop.check(new_text)
        except PropertyError:
            pass
        else:
            self.model[path][self.model_index] = unicode(value)

    def cell_data_func(self):
        pass

    # TODO: on_edited should set value
    # TODO: and cell_data_func should display unicode(value)
    
        
renderers['Unicode'] = RendererUnicode



class RendererChoice(Renderer):

    """ Suitable for VChoice. """

    def init(self):
        self.model = None
        self.model_index = -1

    def create(self, model, index):
        self.model = model
        self.model_index = index

        cell = gtk.CellRendererCombo()

        # set up cell_model
        prop = self.container.get_prop(self.key)
        vchoices = [v for v in prop.validator.vlist if isinstance(v, VChoice)]
        if len(vchoices) == 0:
            raise TypeError("Property for connector 'Choice' has no choice validator!")
        self.vchoice = vchoice = vchoices[0]

        cell_model = gtk.ListStore(str, object)
        for value in vchoice.values:
            cell_model.append((unicode(value), value))
                        
        cell.set_property('text-column', 0)
        cell.set_property('model', cell_model)

        # make editable
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited)

        self.widget = cell
        return cell
    
    def get_attributes(self):
        print "---", self.model_index
        return {'text':self.model_index}

    def on_edited(self, cell, path, new_text):
        print "on_edited", new_text
        self.model[path][self.model_index] = new_text
        
renderers['Choice'] = RendererChoice
