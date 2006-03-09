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
 

import gtk, sys, inspect

from Sloppy.Lib.Check import *
from Sloppy.Lib.Signals import *
from Sloppy.Lib.Undo import UndoList
from Sloppy.Base import uwrap

import logging
logger = logging.getLogger('gtk.checkwidgets')


# TODO: For testing
import uihelper



def as_class(obj):
    if inspect.isclass(obj):
        return obj
    else:
        return obj.__class__


                
class DisplayFactory:

    def __init__(self, klass):           
        self.klass = as_class(klass)
        self.keys = []
        self.displays = {}
        self.instance = None
        self.original_instance = None
        
    def add_keys(self, *keys, **kwargs):
        for key in keys:
            if isinstance(key, basestring):
                self.keys.append(key)
            elif isinstance(key, (list, tuple)):
                self.keys.extend(key)
            else:
                raise TypeError("String, tuple or dict required.")

        for key, value in kwargs.iteritems():
            self.displays[key] = value


    def _create_displays(self):
        for key in self.keys:
            display = DisplayFactory.new_display(self.klass, key)
            display.create_widget()
            self.displays[key] = display
    
            
    def create_vbox(self):
        self._create_displays()
        vbox = gtk.VBox()
        for d in self.displays.itervalues():
            vbox.add(d.widget)
        return vbox

    def create_table(self):
        self._create_displays()
        
        tw = gtk.Table(rows=len(self.keys), columns=2)
        tooltips = gtk.Tooltips()

        n = 0
        for key in self.keys:
            display = self.displays[key]
            # attach widget
            tw.attach(display.widget, 1,2,n,n+1,
                      xoptions=gtk.EXPAND|gtk.FILL,
                      yoptions=0, xpadding=5, ypadding=1)

            # attach label
            # (put into an event box to display the tooltip)
            label = gtk.Label(key)
            label.set_alignment(1.0, 0)
            #label.set_justify(gtk.JUSTIFY_RIGHT)
            label.show()

            ebox = gtk.EventBox()
            ebox.add(label)
            ebox.show()
            if display.check.doc is not None:
                tooltips.set_tip(ebox, display.check.doc)

            tw.attach(ebox, 0,1,n,n+1,
                      xoptions=gtk.FILL, yoptions=0,
                      xpadding=5, ypadding=1)

            n += 1

        return tw

    def connect(self, obj):
        self.instance = obj
        for display in self.displays.itervalues():
            # the displays are responsible for disconnecting the old obj
            display.connect(obj)
    
    def new_display(klass, key):
        check = getattr(klass, key)
        if isinstance(check, Bool):
            v = Display_Bool_As_Combobox
        elif isinstance(check, Choice):
            v = Display_Choice_As_Combobox
        elif isinstance(check, Integer):
            v = Display_Integer_As_Spinbutton
        elif isinstance(check, Float):
            v = Display_Anything_As_Entry
        elif isinstance(check, RGBColor):
            v = Display_RGBColor_As_Colorbutton
        elif isinstance(check, Mapping):
            v = Display_Mapping_As_Combobox
        else:
            v = Display_Anything_As_Entry

        return v(klass, key)
    
    new_display = staticmethod(new_display)    


    def check_in(self, obj):
        """ Create a copy of the object and connect to it."""        
        self.original_instance = obj
        copy = obj.__class__(**obj._values)
        self.connect(copy)
        print "checked in ", copy, "and original instance is ", obj, "and instance is ", self.instance        

    def check_out(self, undolist=[]):
        # create changeset
        new_values = self.instance._values
        old_values = self.original_instance._values
        changeset = {}
        for key, value in new_values.iteritems():
            if value != old_values[key]:
                changeset[key] = value

        changeset['undolist'] = undolist
        uwrap.set(self.original_instance, **changeset)
        




###############################################################################

    
class Display:
    
    def __init__(self, klass, key):
        self.obj = None
        self.key = None
        self.check = None
        self.key = key
        self.klass = as_class(klass)
        self.check = getattr(self.klass, key)
        self.cb = None
        self.obj = None

        self.init()
        
        self.widget = self.create_widget()
        self.prepare_widget(self.widget)

    def init(self):
        pass
    
    def connect(self, obj):
        if self.obj is not None:
            if self.cb is not None:
                self.cb.disconnect()
                self.cb = None            
            self.obj = None

        self.obj = obj
        if obj is not None:
            self.set_widget_data(obj.get(self.key))
            on_update_lambda = lambda sender, value: self.set_widget_data(value)        
            obj.signals['update::%s'%self.key].connect(on_update_lambda)
        else:
            self.widget.set_sensitive(False)



    def disconnect(self):
        self.connect(None)


    def use_widget(self, widget):
        self.widget = widget
        self.prepare_widget(widget)

    def on_update(self, sender):
        # this can be used as a hook for undo
        pass
        #print "on update of ", sender.key, "=", self.obj.get(sender.key)



class As_Entry:

    def create_widget(self):                      
        return gtk.Entry()

    def prepare_widget(self, entry):
        entry.connect("focus-in-event", self.on_focus_in_event)

    def on_focus_in_event(self, widget, event):
        self.widget.connect("focus-out-event", self.on_focus_out_event)
        
    def on_focus_out_event(self, widget, event):
        value = self.get_widget_data()
        obj_value = self.obj.get(self.key)

        if unicode(value) == unicode(obj_value):
            return False
        
        if self.check.required is False and value == "":
            value = None

        try:
            value = self.check(value)
        except ValueError, msg:
            print "Value Error", msg
            self.set_widget_data(obj_value)
        else:
            ##self.set_widget_data(value)
            self.obj.set(self.key, value)
            self.on_update(self)

        return False

      


class As_Combobox:

    def create_widget(self):
        return gtk.ComboBox()

    def prepare_widget(self, cb):
        model = gtk.ListStore(str, object)
        cb.set_model(model)
        cell = gtk.CellRendererText()
        cb.pack_start(cell, True)
        cb.add_attribute(cell, 'text', 0)
        model.clear()
        self.values = []

        if hasattr(self, 'alist'):
            for value in self.alist:
                model.append((unicode(value), value))
                self.values.append(value)
        elif hasattr(self, 'adict'):
            for key, value in self.adict.iteritems():
                model.append((unicode(key), key))
                self.values.append(value)
        else:
            raise RuntimeError("Combobox Display needs either alist or adict.")

        cb.connect("changed", self.on_changed)

    def on_changed(self, widget):
        value = self.get_widget_data()
        obj_value = self.obj.get(self.key)
        if value == obj_value:
            return False
        
        try:
            value = self.check(value)
        except ValueError, msg:
            print "Value Error", msg
            self.set_widget_data(obj_value)
        else:
            self.obj.set(self.key, value)
            self.on_update(self)

        return False
            
    def get_widget_data(self):
        index = self.widget.get_active()
        if index < 0:
            return Undefined
        else:
            return self.values[index]

    def set_widget_data(self, data):
        try:
            index = self.values.index(data)
        except:
            index = -1
        self.widget.set_active(index)

class As_Spinbutton:

    def create_widget(self):
        return gtk.SpinButton()

    def prepare_widget(self, spinbutton):
        spinbutton.set_numeric(False)
        # should be customizable        
        spinbutton.set_increments(1, 1)
        spinbutton.set_digits(2) 

        min, max = self.check.min, self.check.max
        if min is None:
            min = -sys.maxint
        if max is None:
            max = +sys.maxint            
        spinbutton.set_range(min, max)

        spinbutton.connect("focus-in-event", self.on_focus_in_event)

    def on_focus_in_event(self, widget, event):
        self.widget.connect("focus-out-event", self.on_focus_out_event)

    def on_focus_out_event(self, widget, event):
        self.widget.update()
        value = self.get_widget_data()
        obj_value = self.obj.get(self.key)
        if value == obj_value:
            return False
        
        try:
            value = self.check(value)
        except ValueError, msg:
            print "Value Error", msg
            self.set_widget_data(obj_value)
        else:
            self.obj.set(self.key, value)
            self.on_update(self)

        return False


class As_Colorbutton:
    
    def create_widget(self):
        return gtk.ColorButton()

    def prepare_widget(self, colorbutton):
        colorbutton.set_use_alpha(False)
        colorbutton.set_title(self.check.blurb or "Select Color")

        colorbutton.connect("color-set", self.on_color_set)       

    def on_color_set(self, widget):
        value = self.get_widget_data()
        obj_value = self.obj.get(self.key)
        if value == obj_value:
            return False
        
        try:
            value = self.check(value)
        except ValueError, msg:
            print "Value Error", msg
            self.set_widget_data(obj_value)
        else:
            self.obj.set(self.key, value)
            self.on_update(self)

        return False


    

class Display_Bool_As_Combobox(As_Combobox, Display):
    def init(self):
        adict = {'True': True, 'False': False}
        if self.check.required is False:
            adict.update({'None': None})
        self.adict = adict
       

class Display_Choice_As_Combobox(As_Combobox, Display):
    def init(self):
        self.alist = self.check.choices

class Display_Mapping_As_Combobox(As_Combobox, Display):
    def init(self):
        self.adict = self.check.mapping


            

class Display_Anything_As_Entry(As_Entry, Display):

    def get_widget_data(self):
        value = self.widget.get_text()
        if value is Undefined:
            value = u""

        if self.check.required is False and value==u"":
            return None

        return value

    def set_widget_data(self, data):
        if data is Undefined or data is None:
            data = u""
        else:
            data = unicode(data)            
        self.widget.set_text(data)

                

    
           
        
class Display_Number_As_Spinbutton(As_Spinbutton, Display):
    
    def get_widget_data(self):
        return self.widget.get_value()
    
    def set_widget_data(self, data):
        if data not in (None, Undefined):
            self.widget.set_value(float(data))



class Display_Integer_As_Spinbutton(Display_Number_As_Spinbutton):

    def prepare_widget(self, spinbutton):
        Display_Number_As_Spinbutton.prepare_widget(self, spinbutton)
        spinbutton.set_digits(0)
        
        
class Display_RGBColor_As_Colorbutton(As_Colorbutton, Display):

    def set_widget_data(self, data):
        red, green, blue = (data&0xFF0000)>>16, (data&0xFF00)>>8, data&0xFF
        color = gtk.gdk.Color(*[c*256 for c in (red, green, blue)])
        self.widget.set_color(color)

    def get_widget_data(self):
        c = self.widget.get_color()
        v = (int(c.red/256.0)<<16) + (int(c.green/256.0)<<8) + (int(c.blue/256.0))
        return v
    






        
    
#------------------------------------------------------------------------------

def test():
    
    class TestObject(HasChecks):
        is_valid = Bool(init=True)
        is_valid_or_none = Bool(init=None)
        choices = Choice(['One', 'Two', 'Three'], init='Two')

        an_integer = Integer(init=0)
        a_float = Float(init=3.14)
        another_float = Float(init=-7892, max=27.0)
        a_third_float = Float(init=7.0, min=-5, max=12.874)
        what_an_integer = Integer(init=19, max=20)

        a_color = RGBColor(raw=True, init="lightgreen", doc="A color")

        a_mapping = Mapping({'One':1, 'Two':2, 'Three':3}, init='Three')

        a_string = String(init=None)

        def __init__(self, **kwargs):
            HasChecks.__init__(self, **kwargs)

            # set up available Signals
            self.signals = {}            
            self.signals['update'] = Signal()
            for key in self._checks.keys():                
                self.signals['update::%s'%key] = Signal()

            # trigger Signals on attribute update
            def dispatch(sender, key, value):
                sender.signals['update::%s'%key].call(sender, value)
            self.signals['update'].connect(dispatch)

            def on_update(sender, key, value):
                sender.signals['update'].call(sender, key,value)
            self.on_update = on_update
                             


    class MainObject(HasChecks):
        obj_list = List(Instance(TestObject))


    obj = TestObject(a_string="object ONE", is_valid=False, a_mapping='One')
    obj2 = TestObject(a_string="object TWO", an_integer=5, a_mapping=1)
    main = MainObject(obj_list=[obj, obj2])

    # This is how the notification works:

    # The object has an on_update function.
    # This function is set to emit a signal 'update'.
    # If you want to be informed of changes to the object,
    # just connect to this signal.

    # Each display should connect to the 'update' signal
    # of the object and call set_widget_data whenever
    # the value changes.

    df = DisplayFactory(obj)        
    df.add_keys(obj._checks.keys())
    tv = df.create_table()
    df.check_in(obj)

    def quit(sender):
        df.check_out()
        print
        print "Obj1 ===>", obj._values
        gtk.main_quit()
    
    win = gtk.Window()
    win.set_size_request(640,480)
    win.connect('destroy', quit)

    hbox = gtk.HBox()
    hbox.add(tv)
    
    vbox = gtk.VBox()
    vbox.add(uihelper.add_scrollbars(hbox, viewport=True))
    win.add(vbox)
    win.show_all()

    gtk.main()




if __name__ == "__main__":
    test()


    
