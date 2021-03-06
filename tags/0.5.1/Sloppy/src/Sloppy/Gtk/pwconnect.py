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

"""Create widgets (or use existing widgets) to enter values for Props.

>>> # Get a Connector instance
>>> c = connectors['ComboBox'](container, 'propname')

>>> # create a widget
>>> c.create_widget()
>>> w = c.widget

>>> # check in / check out data into the container
>>> c.check_in()
>>> c.check_out()
"""

import logging
logger = logging.getLogger('pwconnect')

try:
    import pygtk
    pygtk.require('2.0')
except ImportError:
    pass

import gtk

from Sloppy.Lib.Props import CheckBounds
import sys



__all__ = ['Connector', 'connectors',
           #
           'Entry', 'ComboBox', 'CheckButton', 'SpinButton'
           ]


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
    
    def check_out(self):
        " Set value in container "
        self.set_value(self.get_data())

    #----------------------------------------------------------------------
    # UI Stuff

    def create_widget(self):
        raise RuntimeError("crete_widget() needs to be implemented.")


connectors = {}



    
class Entry(Connector):

    def create_widget(self):
        widget = gtk.Entry()    
        widget.connect("focus-in-event", self.on_focus_in_event)
        widget.connect("focus-out-event", self.on_focus_out_event)
        self.widget = widget
        
    def on_focus_in_event(self, widget, event):
        self.last_value = widget.get_text()
        
        
    def on_focus_out_event(self, widget, event):
        value = self.widget.get_text()
        try:
            self.prop.check(value)
        except (TypeError, ValueError):
            print "Entry Value is wrong, resetting."
            self.widget.set_text(self.last_value)

    #----------------------------------------------------------------------

    def check_in(self):
        self.last_value = self.get_value()
        
        if self.last_value is not None:
            value = unicode(self.last_value)
        else:
            value = ""        
        self.widget.set_text(value)

    def get_data(self):
        value = self.widget.get_text()
        if len(value) == 0:
            return None
        else:
            return self.prop.check(value)


connectors['Entry'] = Entry



class ComboBox(Connector):
    
    def init(self):
        self.value_dict = {}
        self.value_list = []
        
    def create_widget(self):
        widget = gtk.ComboBox()

        # if value_list is available
        model = gtk.ListStore(str, object)
        widget.set_model(model)
        cell = gtk.CellRendererText()
        widget.pack_start(cell, True)
        widget.add_attribute(cell, 'text', 0)

        # fill combo
        model.clear()
        value_dict = self.prop.get_value_dict()
        if value_dict is not None:
            for key, value in value_dict.dict.iteritems():
                model.append((key or "<None>", value))
                self.value_dict[value] = value
                self.value_list.append(value)
        else:
            # if no ValueDict was found, try ValueList
            value_list = self.prop.get_value_list()
            if value_list is not None:
                for value in value_list.values:
                    model.append((value or "<None>", value))
                    self.value_dict[value] = value
                    self.value_list.append(value)                

        self.widget = widget
            
    #----------------------------------------------------------------------

    
    def check_in(self):
        try:
            value = self.get_value()
            index = self.value_list.index(value)
        except:
            raise ValueError("Connector for %s.%s failed to retrieve prop value '%s' in list of available values '%s'" % (self.container, self.key, self.get_value(), self.value_list))

        model = self.widget.get_model()
        iter = model.get_iter((index,))
        self.widget.set_active_iter(iter)
        self.last_value = value
        
    
    def get_data(self):
        index = self.widget.get_active()
        if index < 0:
            return None
        else:
            model = self.widget.get_model()
            return model[index][1]


connectors['ComboBox'] = ComboBox



class TrueFalseComboBox(ComboBox):

    def create_widget(self):
        widget = gtk.ComboBox()

        # predefined value_list
        model = gtk.ListStore(str, object)
        widget.set_model(model)
        cell = gtk.CellRendererText()
        widget.pack_start(cell, True)
        widget.add_attribute(cell, 'text', 0)

        # fill combo
        model.clear()
        value_dict = {'Default' : None, 'True': True, 'False': False}
        for key, value in value_dict.iteritems():
            model.append((key, value))
            self.value_dict[value] = value
            self.value_list.append(value)

        self.widget = widget
        
connectors['TrueFalseComboBox'] = TrueFalseComboBox
            

class CheckButton(Connector):

    def create_widget(self):
        widget = gtk.CheckButton()
        widget.connect('toggled', self.on_toggled)
        self.widget = widget
        
    def on_toggled(self, widget):
        if self.widget.get_inconsistent() is True:
            self.widget.set_inconsistent(False)

    def check_in(self):
        value = self.get_value()
        self.last_value = value

        if value is None:
            self.widget.set_inconsistent(True)
        else:
            self.widget.set_inconsistent(False)
            self.widget.set_active(value is True)

    def get_data(self):
        # determine value (None,False,True)
        if self.widget.get_inconsistent() is True:
            return None
        else:
            return self.widget.get_active()


connectors['CheckButton'] = CheckButton




class SpinButton(Connector):

    def create_widget(self):
        sb = gtk.SpinButton()
        checkbutton = gtk.CheckButton()

        checkbutton.connect("toggled",\
          (lambda sender: self.spinbutton.set_sensitive(sender.get_active())))
        
        widget = gtk.HBox()
        widget.pack_start(sb,True,True)
        widget.pack_start(checkbutton,False,True)
        widget.show_all()
        
        self.widget = widget
        self.spinbutton = sb
        self.checkbutton = checkbutton

        sb = self.spinbutton
        sb.set_numeric(True)
        
        cbounds = [c for c in self.prop.check.items if isinstance(c, CheckBounds)]
        if len(cbounds) > 0:
            c = cbounds[0]
            lower,upper = c.min, c.max
        else:
            lower,upper = None,None

        if lower is None:
            lower = -sys.maxint

        if upper is None:
            upper = +sys.maxint

        sb.set_range(float(lower), float(upper))
            
        value = self.get_value()
        if value is not None:
            sb.set_value(float(value))
        sb.set_sensitive(value is not None)

        sb.set_increments(1,1)
        sb.set_digits(0)

        
    def check_in(self):
        value = self.get_value()
        self.last_value = value

        if value is not None:
            self.spinbutton.set_value(float(value))
            self.checkbutton.set_active(True)
        else:
            self.checkbutton.set_active(False)

    def get_data(self):
        if self.checkbutton.get_active() is True:
            return self.spinbutton.get_value()
        else:
            return None

        
connectors['SpinButton'] = SpinButton
