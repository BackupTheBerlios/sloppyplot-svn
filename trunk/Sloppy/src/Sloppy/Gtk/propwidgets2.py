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

""" I have been using the propwidgets.py module to automate the
creation of widgets and corresponding labels for Props.  From a user's
point of view, this worked fine, even though it did not look so nice.
This module aims to be a reimplementation of such a mechanism, but it
needs to be different in some ways.  We need to be able to use a UI
designed by a glade file, specify a Container and its Props, and have
this module automagically find the corresponding input widgets, fill
in the data (e.g. the Prop's value_list for a ComboBox and attach
callbacks!
"""

import logging
logger = logging.getLogger('Gtk.propwidgets')

try:
    import pygtk
    pygtk.require('2.0')
except ImportError:
    pass

import gtk

from Sloppy.Lib.Props import Container,Prop
from Sloppy.Base import uwrap





class Wrapper(object):

    """ Abstract base class for all wrappers.  Derived class must set
    the attribute 'widget_type' and must implement 'use_widget' """

    widget_type = None
    
    def __init__(self, container, key):
        self.container = container
        self.key = key
        self.widget = None
        self.init()

    #----------------------------------------------------------------------
    # Helper Functions
    
    def get_value(self):
        return self.container.get_value(self.key)
    def set_value(self, value):
        self.container.set_value(self.key, value)
    def get_prop(self):
        return self.container.get_prop(self.key)
    prop = property(get_prop)

    #----------------------------------------------------------------------
    # Check In/Out
    
    def check_in(self):
        " Retrieve value from container "
        raise RuntimeError("check_in() needs to be implemented.")

    def check_out(self, undolist=[]):
        " Set value in container "
        raise RuntimeError("check_out() needs to be implemented.")

    #----------------------------------------------------------------------
    # UI Stuff

    def create_widget(self):
        self.use_widget(self.widget_type())

    def check_widget_type(self, widget):
        if not isinstance(widget, self.widget_type):
            raise TypeError("Widget for wrapper class %s must be of %s and not of %s" % (self.__class__.__name__, self.widget_type, type(widget)))

    def use_widget(self, widget):
        self.check_widget_type(widget)
        self.widget = widget
        self.check_in()



    
class Entry(Wrapper):

    widget_type = gtk.Entry

    #----------------------------------------------------------------------

    def init(self):
        self.last_value = None

    def check_in(self):
        self.last_value = self.get_value()
        
        if self.last_value is not None:
            value = unicode(self.last_value)
        else:
            value = ""        
        self.widget.set_text(value)

    def check_out(self, undolist=[]):           
        value = self.widget.get_text()
        if len(value) == 0: value = None
        else: value = self.prop.check_value(value)

        if value != self.last_value:
            uwrap.set(self.container, self.key, value, undolist=undolist)
            self.last_value = value


    #----------------------------------------------------------------------
    # UI Stuff
    
    def use_widget(self, widget):
        Wrapper.use_widget(self, widget)
        
        widget.connect("focus-in-event", self.on_focus_in_event)
        widget.connect("focus-out-event", self.on_focus_out_event)

    def on_focus_in_event(self, widget, event):
        self.last_value = widget.get_text()
        
        
    def on_focus_out_event(self, widget, event):
        value = self.widget.get_text()
        try:
            self.prop.check_value(value)
        except (TypeError, ValueError):
            print "Entry Value is wrong, resetting."
            self.widget.set_text(self.last_value)



#------------------------------------------------------------------------------
# Test Setup

def test():
    import gtk.glade

    filename = "./Glade/example.glade"
    widgetname = 'main_box'
 
    win = gtk.Window()
    win.connect("destroy", gtk.main_quit)
    tree = gtk.glade.XML(filename, widgetname)    
    widget = tree.get_widget(widgetname)
    win.add(widget)

    # set up container
    class Options(Container):
        filename = Prop(coerce=unicode)
    options = Options(filename="test.dat")
    
    # set up Entry
    entry = Entry(options, 'filename')
    
    # try to connect to an existing widget
    widget = tree.get_widget('pw_filename')
    if widget is not None:
        entry.use_widget(widget)
    else:
        print "Widget not found!"

    def finish_up(sender):
        # check out everything
        entry.check_out()
        
        # display props
        for k,v in options.get_key_value_dict().iteritems():            
            print "%s = %s" % (k,v)
        gtk.main_quit()
    signals = {"on_button_ok_clicked": finish_up}
    tree.signal_autoconnect(signals)

    win.show()
    gtk.main()


if __name__ == "__main__":
    test()

        
