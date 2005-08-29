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

from Sloppy.Lib.Props import Container,Prop, BoolProp
from Sloppy.Base import uwrap





class Wrapper(object):

    """ Abstract base class for all wrappers.  Derived class must set
    the attribute 'widget_type' and must implement 'use_widget' """

    widget_type = None
    
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


    
class Entry(Wrapper):

    widget_type = gtk.Entry
    
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

    #----------------------------------------------------------------------

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
            uwrap.smart_set(self.container, self.key, value, undolist=undolist)
            self.last_value = value



class ComboBox(Wrapper):
    
    widget_type = gtk.ComboBox

    def use_widget(self, widget):
        Wrapper.use_widget(self, widget)

        # if value_list is available
        model = gtk.ListStore(str, object)
        widget.set_model(model)
        cell = gtk.CellRendererText()
        widget.pack_start(cell, True)
        widget.add_attribute(cell, 'text', 0)

        # fill combo
        model.clear()
        for value in self.prop.value_list:
            model.append((value or "<None>", value) )

            
    #----------------------------------------------------------------------

    
    def check_in(self):
        try:
            index = self.prop.value_list.index(self.get_value())
        except:
            raise ValueError("Failed to retrieve prop value %s in list of available values %s" % (self.get_value(), self.value_list))

        model = self.widget.get_model()
        iter = model.get_iter((index,))
        self.widget.set_active_iter(iter)
        self.last_value = index
        
    
    def check_out(self, undolist=[]):
        index = self.widget.get_active()
        if index != self.last_value:
            if index < 0:
                value = None
            else:
                model = self.widget.get_model()
                value = model[index][1]
            uwrap.smart_set(self.container, self.key, value, undolist=undolist)
            self.last_value = index
        
        

class CheckButton(Wrapper):

    widget_type = gtk.CheckButton

    def use_widget(self, widget):
        Wrapper.use_widget(self, widget)
        self.widget.connect('toggled', self.on_toggled)
        
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

    def check_out(self, undolist=[]):
        # determine value (None,False,True)
        if self.widget.get_inconsistent() is True:
            value = None
        else:
            value = self.widget.get_active()

        # set new value
        if self.last_value != value:
            uwrap.set(self.container, self.key, value, undolist=undolist)
            self.last_value = value



    


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
        mode = Prop(coerce=unicode,
                    value_list=[None, u'read-only', u'write-only', u'read-write'])
        include_header = BoolProp(default=None)
        
    options = Options(filename="test.dat", mode=u'read-only')


    def wrap(container, key, wrapper_class):
        wrapper = wrapper_class(container, key)
        widget_key = 'pw_%s' % key
        widget = tree.get_widget(widget_key)
        if widget is not None:
            wrapper.use_widget(widget)
        else:
            raise RuntimeError("Could not find widget '%s'" % widget_key)
        wrapper.check_in()
        return wrapper

    to_be_wrapped = {'filename' : Entry,
                     'mode' : ComboBox,
                     'include_header' : CheckButton}

    wrapped = {}
    for k,v in to_be_wrapped.iteritems():
        wrapped[k] = wrap(options, k, v)    
        
    def finish_up(sender):
        for wrapper in wrapped.itervalues():
            wrapper.check_out()
        
        # display props
        print 
        for k,v in options.get_key_value_dict().iteritems():            
            print "%s = %s" % (k,v)
        print
        
        gtk.main_quit()
    signals = {"on_button_ok_clicked": finish_up}
    tree.signal_autoconnect(signals)

    win.show()
    gtk.main()


if __name__ == "__main__":
    test()

        
