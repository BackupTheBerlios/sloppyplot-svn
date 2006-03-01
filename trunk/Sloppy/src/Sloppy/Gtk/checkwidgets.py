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


import gtk, sys

from Sloppy.Lib.Check import *
from Sloppy.Lib.Undo import UndoList
from Sloppy.Base import uwrap

import logging
logger = logging.getLogger('gtk.checkwidgets')


###############################################################################


class Display:
    
    def __init__(self, obj, key):
        self.obj = None
        self.key = None
        self.check = None
        self.set_source(obj, key)

        self.last_value = None
        self.widget = None

        self.widget = self.create_widget()
        self.prepare_widget(self.widget)

    def set_source(self, obj, key):        
        self.obj = obj
        self.key = key
        self.check = obj._checks[key]

    #----------------------------------------------------------------------
    # UI Stuff

    def use_widget(self, widget):
        self.widget = widget
        self.prepare_widget(widget)
                
    #----------------------------------------------------------------------
    # Check In/Out
    
    def check_in(self):
        " Retrieve value from object. "
        value = self.get_object_data()
        self.set_widget_data(value)
        self.last_value = value

    def check_out(self, undolist=[]):
        " Set value in object. "
        new_value = self.get_widget_data()
        if new_value != self.last_value:
            uwrap.smart_set(self.obj, self.key, new_value, undolist=undolist)

    def get_object_data(self):
        return self.obj.get(self.key)


    


class As_Combobox:
    # prepare_widget should define and fill the dict self.values
    # the model should be of the form str, object.

    def create_widget(self):
        return gtk.ComboBox()
    
    def get_widget_data(self):
        index = self.widget.get_active()
        if index < 0:
            return Undefined            
        else:
            model = self.widget.get_model()
            return  model[index][1]

    def set_widget_data(self, data):
        try:
            index = self.values.index(data)
        except:
            index = -1
        self.widget.set_active(index)


class As_Entry:

    def create_widget(self):                      
        return gtk.Entry()

    def get_widget_data(self):
        value = self.widget.get_text()
        if value is Undefined:
            value = ""

        if self.check.required is False and value=="":
            return None
            
        try:
            return self.check(value)
        except ValueError:
            self.set_widget_data(self.last_value)

    def set_widget_data(self, data):
        if data is Undefined or data is None:
            data = u""
        else:
            data = unicode(data)
            
        self.widget.set_text(data)

    

class Display_Bool_As_Combobox(As_Combobox, Display):
            
    def prepare_widget(self, combobox):
        model = gtk.ListStore(str, object)
        combobox.set_model(model)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)
        
        adict = {'True': True, 'False': False}
        if self.obj._checks[self.key].required is False:
            adict.update({'None': None})
        self.values = adict.values() # for reference

        model = combobox.get_model()
        model.clear()        
        for key, value in adict.iteritems():
            model.append((key, value))            
        
        

class Display_Choice_As_Combobox(As_Combobox, Display):
        
    def prepare_widget(self, cb):
        model = gtk.ListStore(str, object)
        cb.set_model(model)
        cell = gtk.CellRendererText()
        cb.pack_start(cell, True)
        cb.add_attribute(cell, 'text', 0)
        model.clear()
        self.values = {}
        for value in self.check.choices:
            model.append((unicode(value), value))
            self.values[value] = value


class Display_Mapping_As_Combobox(As_Combobox, Display):

    def prepare_widget(self, cb):
        model = gtk.ListStore(str, object)
        cb.set_model(model)
        cell = gtk.CellRendererText()
        cb.pack_start(cell, True)
        cb.add_attribute(cell, 'text', 0)
        model.clear()
        self.values = {}
        for key, value in self.check.mapping.iteritems():
            model.append((unicode(key), key))
            self.values[value] = value
            

class Display_Anything_As_Entry(As_Entry, Display):

    def prepare_widget(self, entry):
        entry.connect("focus-in-event", self.on_focus_in_event)

    def on_focus_in_event(self, widget, event):
        self.widget.connect("focus-out-event", self.on_focus_out_event)
        
    def on_focus_out_event(self, widget, event):
        value = widget.get_text()
        if self.check.required is False and value == "":
            return

        try:
            value = unicode(self.check(value))
            self.last_value = value
            self.set_widget_data(value)
        except ValueError:
            self.set_widget_data(self.last_value)

        return False    
                


class As_Spinbutton:

    def create_widget(self):
        return gtk.SpinButton()

    def get_widget_data(self):
        return self.widget.get_value()
    
    def set_widget_data(self, data):
        if data not in (None, Undefined):
            self.widget.set_value(float(data))
        
class Display_Number_As_Spinbutton(As_Spinbutton, Display):
    
    def prepare_widget(self, spinbutton):
        check = self.obj._checks[self.key]

        spinbutton.set_numeric(False)

        # should be customizable        
        spinbutton.set_increments(1, 1)
        spinbutton.set_digits(2) 

        min, max = check.min, check.max
        if min is None:
            min = -sys.maxint
        if max is None:
            max = +sys.maxint            
        spinbutton.set_range(min, max)

class Display_Integer_As_Spinbutton(Display_Number_As_Spinbutton):

    def prepare_widget(self, spinbutton):
        Display_Number_As_Spinbutton.prepare_widget(self, spinbutton)
        spinbutton.set_digits(0)
        

Display_Number_As_Entry = Display_Anything_As_Entry
Display_String_As_Entry = Display_Unicode_As_Entry = Display_Anything_As_Entry


class Display_RGBColor_As_Colorbutton(Display):

    def create_widget(self):
        return gtk.ColorButton()

    def prepare_widget(self, colorbutton):
        colorbutton.set_use_alpha(False)
        colorbutton.set_title(self.obj._checks[self.key].blurb or "Select Color")

    def set_widget_data(self, data):
        color = gtk.gdk.color_parse('#%s' % hex(data)[2:])
        self.widget.set_color(color)

    def get_widget_data(self):
        c = self.widget.get_color()
        v = (int(c.red/256.0)<<16) + (int(c.green/256.0)<<8) + (int(c.blue/256.0))
        return v




        
    
#------------------------------------------------------------------------------

class TestObject(HasChecks):
    is_valid = Bool()
    is_valid_or_none = Bool()
    choices = Choice(['One', 'Two', 'Three'])

    an_integer = Integer()
    a_float = Float()
    another_float = Float(max=27.0)
    a_third_float = Float(min=-5, max=12.874)
    what_an_integer = Integer(max=20)

    a_color = RGBColor(raw=True, doc="A color")

    a_mapping = Mapping({'One':1, 'Two':2, 'Three':3})
    

obj = TestObject(is_valid=False)

cv = CheckView(obj)
print "a_color is: %s " % str(cv.a_color.doc)
for value in ['black', (0.5, 1.0, 0.3), '#FFEE00']:
    obj.a_color = value
    print "color %s = %s (=%s)" % (value, obj.a_color, obj._raw_values['a_color'])


cdict = {'is_valid': Display_Bool_As_Combobox,
         'is_valid_or_none': Display_Bool_As_Combobox,
         'choices': Display_Choice_As_Combobox,
         'an_integer': Display_Number_As_Entry,
         'a_float': Display_Number_As_Entry,
         'another_float': Display_Number_As_Entry,
         'a_third_float': Display_Number_As_Spinbutton,
         'what_an_integer': Display_Integer_As_Spinbutton,
         'a_color': Display_RGBColor_As_Colorbutton,
         'a_mapping': Display_Mapping_As_Combobox
         }

clist = []
for key, connector in cdict.iteritems():
    new_connector = connector(obj, key)
    new_connector.check_in()    
    clist.append(new_connector)
    


def quit(sender):
    for connector in clist:
        connector.check_out()
    print obj._values
    gtk.main_quit()
    
win = gtk.Window()
win.set_size_request(480,320)
win.connect('destroy', quit)

vbox = gtk.VBox()
for c in clist:
    hbox = gtk.HBox()
    label = gtk.Label(c.key)
    hbox.pack_start(label, False, False)
    hbox.pack_start(c.widget, True, True)
    vbox.pack_start(hbox, False, True)

win.add(vbox)
win.show_all()

gtk.main()
    
