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
logger = logging.getLogger('pwconnect')

try:
    import pygtk
    pygtk.require('2.0')
except ImportError:
    pass

import gtk

import sys

from Sloppy.Base import uwrap
from Sloppy.Lib.Props.main import *
from Sloppy.Base.properties import *




###############################################################################

class Connector(object):

    """ Abstract base class for all wrappers.  
    
    Derived class must implement 'create_widget'.  Of course, for the
    widget to be useful, it should also implement 'check_in' and
    'check_out'.  The default 'check_out' method relies on 'get_data',
    so it might make more sense to implement this instead.

    """
    
    def __init__(self, container, key):
        self.container = container
        self.key = key
        self.widget = None
        self.last_value = None
        self.init()

    def init(self):
        pass

    #----------------------------------------------------------------------
    # Helper Functions
    
    def get_value(self):
        return self.container.get_value(self.key)
    def set_value(self, value):
        if value != self.last_value:
            self.container.set_value(self.key, value)
            self.last_value = value
    def get_prop(self):
        return self.container.get_prop(self.key)
    prop = property(get_prop)

    def set_container(self, container):
        self.container = container

    #----------------------------------------------------------------------
    # Check In/Out
    
    def check_in(self):
        " Retrieve value from container "
        raise RuntimeError("check_in() needs to be implemented.")

    def get_data(self):
        """
        Return checked value from widget, so it can be passed on to
        the container.
        """        
        raise RuntimeError("get_data() needs to be implemented.")
    
    def check_out(self, undolist=[]):
        " Set value in container "
        new_value = self.get_data()
        if new_value != self.last_value:
            uwrap.smart_set(self.container, self.key, new_value, undolist=undolist)
            self.last_value = new_value

    #----------------------------------------------------------------------
    # UI Stuff

    def create_widget(self):
        raise RuntimeError("create_widget() needs to be implemented.")


connectors = {}




###############################################################################

class Unicode(Connector):

    """ Suitable for VUnicode. """

    def create_widget(self):                      
        # create entry
        self.entry = gtk.Entry()

        entry = self.entry        
        entry.connect("focus-in-event", self.on_focus_in_event)
        entry.connect("focus-out-event", self.on_focus_out_event)

        # create checkbutton if requested
        try:
            prop = self.container.get_prop(self.key)
            prop.check(None)
        except PropertyError:
            self.checkbutton = None            
        else:
            self.checkbutton = gtk.CheckButton()
            self.checkbutton.connect("toggled",
              (lambda sender: entry.set_sensitive(sender.get_active())))


        # pack everything together
        self.widget = gtk.HBox()

        widget = self.widget
        widget.pack_start(entry,True,True)
        if self.checkbutton is not None:
            widget.pack_start(self.checkbutton,False,True)                    
        widget.show_all()

        return self.widget


    def on_focus_in_event(self, widget, event):
        self.last_value = widget.get_text()
        
        
    def on_focus_out_event(self, widget, event):
        value = widget.get_text()
        if value == self.last_value:
            return
        
        try:
            self.prop.check(value)
        except (TypeError, ValueError):
            widget.set_text(self.last_value)
            

    #----------------------------------------------------------------------

    def check_in(self):
        value = self.get_value()
        if value is Undefined:
            value = None
            
        if self.checkbutton is not None:
            state = value is not None
            self.checkbutton.set_active(state)
            self.entry.set_sensitive(state)            
        else:
            if value is None:
                value = ""
            
        if value is not None:
            self.entry.set_text(unicode(value))
        self.last_value = value


    def get_data(self):
        value = self.entry.get_text()

        if self.checkbutton is not None:
            state = self.checkbutton.get_active()
            if state is False:
                return None

        try:
            return self.prop.check(value)
        except:
            return self.last_value


connectors['Unicode'] = Unicode



###############################################################################

class Range(Connector):

    """ Suitable for VRange. """
    
    def create_widget(self):
        # create spinbutton
        self.spinbutton = gtk.SpinButton()

        #
        # create checkbutton, if None is a valid value.
        #
        try:
            prop = self.container.get_prop(self.key)
            prop.check(None)
        except PropertyError:
            self.checkbutton = None
        else:
            self.checkbutton = gtk.CheckButton()
            self.checkbutton.connect("toggled",\
              (lambda sender: self.spinbutton.set_sensitive(sender.get_active())))
            
        #
        # pack everything together
        #
        self.widget = gtk.HBox()

        widget = self.widget
        widget.pack_start(self.spinbutton,True,True)
        if self.checkbutton is not None:
            widget.pack_start(self.checkbutton,False,True)
        widget.show_all()


        #
        # set spinbutton values
        #

        sb = self.spinbutton
        sb.set_numeric(True)

        vranges = [v for v in self.prop.validator.vlist if isinstance(v, VRange)]
        if len(vranges) > 0:
            vrange = vranges[0]
            lower,upper = vrange.min, vrange.max
        else:
            lower,upper = None,None

        if lower is None:
            lower = -sys.maxint

        if upper is None:
            upper = +sys.maxint

        sb.set_range(float(lower), float(upper))
        sb.set_increments(1,1)
        sb.set_digits(0)

        return self.widget
    
        
    def check_in(self):
        value = self.get_value()
        if value is not None:
            value = float(value)
        
        if self.checkbutton is not None:
            state = value is not None
            self.checkbutton.set_active(state)
            self.spinbutton.set_sensitive(state)
        if value is not None:
            self.spinbutton.set_value(value)

        self.last_value = value
            
        

    def get_data(self):
        if (self.checkbutton is not None) and \
               (self.checkbutton.get_active() is not True):
            return None

        try:
            return self.prop.check(self.spinbutton.get_value())
        except:
            raise ValueError("Invalid value %s in spinbutton." % self.spinbutton.get_value())

        
connectors['Range'] = Range


###############################################################################

class Map(Connector):

    """ Suitable for VMap and VBMap. """
    
    def init(self):
        self.vmap = None
        self.last_index = -1
        
    def create_widget(self):
        # create combobox
        self.combobox = gtk.ComboBox()

        # create combobox model
        combobox = self.combobox
        model = gtk.ListStore(str, object)
        combobox.set_model(model)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)

        # fill model
        model.clear()

        prop = self.container.get_prop(self.key)
        vmaps = [v for v in prop.validator.vlist if isinstance(v, VMap)]
        if len(vmaps) == 0:
            raise TypeError("Property for connector 'Map' has no map validator!")
        self.vmap = vmap = vmaps[0]        
        if vmap is not None:
            for key, value in vmap.dict.iteritems():
                model.append((unicode(key), key))

        # pack everything together
        self.widget = gtk.HBox()

        widget = self.widget
        widget.pack_start(combobox,True,True)
        widget.show_all()

        return self.widget
        
    #----------------------------------------------------------------------

    def check_in(self):
        value = self.container.get_mvalue(self.key)
        values = self.vmap.dict.values()
        
        if value != Undefined:
            try:
                index = values.index(value)
            except:
                raise ValueError("Connector for %s.%s failed to retrieve prop value '%s' in list of available values '%s'" % (self.container.__class__.__name__, self.key, value, values))

            model = self.combobox.get_model()
            iter = model.get_iter((index,))
            self.combobox.set_active_iter(iter)
            self.last_index = index
            
        self.last_value = value

    
    def get_data(self):
        index = self.combobox.get_active()
        if index == self.last_index:
            return self.get_value()
        elif index < 0:
            return Undefined            
        else:
            model = self.combobox.get_model()
            prop = self.container.get_prop(self.key)
            return model[index][1]


connectors['Map'] = Map


###############################################################################

class RGBColor(Connector):

    def create_widget(self):
        self.type = TYPE_WIDGET
        
        self.colorbutton = gtk.ColorButton()
        self.widget = self.colorbutton

        widget = self.widget
        
        return self.widget

    def create_renderer(self, model, index):
        self.type = TYPE_RENDERER

        cell = gtk.CellRenderer
        return self.widget

    
    def to_gdk_color(self, color):
        return gtk.gdk.Color(int(color[0]*65535), int(color[1]*65535), int(color[2]*65535))

    def to_rgb(self, color):
        return (color.red/65535.0, color.green/65535.0, color.blue/65535.0)

    def get_data(self):
        gdk_color = self.colorbutton.get_color()
        print "Comparing ", gdk_color, self.last_value
        if (gdk_color.red == self.last_value.red) and \
               (gdk_color.blue == self.last_value.blue) and \
               (gdk_color.green == self.last_value.green):
            return self.container.get_mvalue(self.key)
        
        return self.to_rgb(gdk_color)

    def check_in(self):
        rgb_color = self.container.get_mvalue(self.key) or (0.0,0.0,0.0)
        gdk_color = self.to_gdk_color(rgb_color)
        self.colorbutton.set_color(gdk_color)
        self.last_value = gdk_color
    
connectors['RGBColor'] = RGBColor


###############################################################################

class Choice(Connector):

    """ Suitable for VChoice. """
    
    def init(self):
        self.vchoice = None
        self.last_index = -1
        
    def create_widget(self):
        # create combobox
        self.combobox = gtk.ComboBox()

        # create combobox model
        combobox = self.combobox
        model = gtk.ListStore(str, object)
        combobox.set_model(model)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)

        # fill model
        prop = self.container.get_prop(self.key)
        vchoices = [v for v in prop.validator.vlist if isinstance(v, VChoice)]
        if len(vchoices) == 0:
            raise TypeError("Property for connector 'Choice' has no choice validator!")
        self.vchoice = vchoice = vchoices[0]

        model.clear()
        for value in vchoice.values:
            model.append((unicode(value), value))

        # pack everything together
        self.widget = gtk.HBox()

        widget = self.widget
        widget.pack_start(combobox,True,True)
        widget.show_all()

        return self.widget
        
    #----------------------------------------------------------------------

    def check_in(self):
        value = self.container.get_value(self.key)
        values = self.vchoice.values
        
        if value != Undefined:
            try:
                index = values.index(value)
            except:
                raise ValueError("Connector for %s.%s failed to retrieve prop value '%s' in list of available values '%s'" % (self.container.__class__.__name__, self.key, value, values))

            model = self.combobox.get_model()
            iter = model.get_iter((index,))
            self.combobox.set_active_iter(iter)
            self.last_index = index
            
        self.last_value = value

    
    def get_data(self):
        index = self.combobox.get_active()
        if index == self.last_index:
            return self.get_value()
        elif index < 0:
            return Undefined            
        else:
            model = self.combobox.get_model()
            prop = self.container.get_prop(self.key)
            return model[index][1]


connectors['Choice'] = Choice


###############################################################################

class Boolean(Connector):

    def init(self):
        self.values = []
        self.last_index = -1
        
    def create_widget(self):

        # create combobox
        self.combobox = gtk.ComboBox()

        # create model
        combobox = self.combobox        
        model = gtk.ListStore(str, object)
        combobox.set_model(model)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)

        # fill combo
        try:
            self.prop.check(None)
        except:
            value_dict = {}
        else:
            value_dict = {'None': None}
            
        value_dict.update({'True': True, 'False': False})
        self.values = value_dict.values()
        
        model.clear()        
        for key, value in value_dict.iteritems():
            model.append((key, value))
        
        #
        # pack everything together
        #
        self.widget = gtk.HBox()

        widget = self.widget
        widget.pack_start(combobox,True,True)
        widget.show_all()

        return self.widget


    def check_in(self):
        value = self.get_value()

        if value is not Undefined:            
            index = self.values.index(value)

            model = self.combobox.get_model()
            iter = model.get_iter((index,))
            self.combobox.set_active_iter(iter)
        else:
            index = -1
            
        self.last_value = value
        self.last_index = index

    def get_data(self):
        index = self.combobox.get_active()
        if index == self.last_index:
            return self.get_value()
        elif index < 0:
            return Undefined            
        else:
            model = self.combobox.get_model()
            prop = self.container.get_prop(self.key)
            return model[index][1]

        
        
connectors['Boolean'] = Boolean



###############################################################################

def get_cname(owner, key):
    prop = owner.get_prop(key)
    vlist = prop.validator.vlist    
    while len(vlist) > 0:
        v = vlist[0]
        if isinstance(v, VMap):
            return 'Map'
        elif isinstance(v, (VUnicode,VInteger,VFloat,VString,VRegexp)):
            return 'Unicode'
        elif isinstance(v, VRange):
            return'Range'
        elif isinstance(v, VRGBColor):
            return 'RGBColor'
        elif isinstance(v, VChoice):
            return 'Choice'
        elif isinstance(v, VBoolean):
            return 'Boolean'
        vlist.pop(0)

    logger.warning("No connector found for property %s.%s." % (owner.__class__.__name__, key))
    return 'Unicode'


def new_connector(owner, key):  
    cname = get_cname(owner, key)
    connector = connectors[cname](owner, key)
    return connector


def new_connectors(owner, include=None, exclude=None):
    keys = owner.get_keys(include=include,exclude=exclude)
    clist = []
    for key in keys:
        clist.append(new_connector(owner, key))
    return clist

