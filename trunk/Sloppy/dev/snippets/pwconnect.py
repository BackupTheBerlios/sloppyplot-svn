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


from Sloppy.Base import uwrap
import sys


from Sloppy.Lib.Props.main import Undefined, VRange, PropertyError



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
        raise RuntimeError("crete_widget() needs to be implemented.")


connectors = {}



class Unicode(Connector):

    def create_widget(self):                      

        # create entry
        self.entry = gtk.Entry()

        entry = self.entry        
        entry.connect("focus-in-event", self.on_focus_in_event)
        entry.connect("focus-out-event", self.on_focus_out_event)

        # create checkbutton if requested
        try:
            prop = self.container.get_prop(self.key)
            prop.check(Undefined)
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

        return widget
        
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

        if self.checkbutton is not None:
            state = value is not Undefined
            self.checkbutton.set_active(state)
            self.entry.set_sensitive(state)            
        else:
            if value is Undefined:
                value = ""
            
        if value is not Undefined:
            self.entry.set_text(unicode(value))
        self.last_value = value


    def get_data(self):
        value = self.entry.get_text()

        if self.checkbutton is not None:
            state = self.checkbutton.get_active()
            if state is False:
                return Undefined
            
        try:
            return self.prop.check(value)
        except:
            return self.last_value


connectors['Unicode'] = Unicode

