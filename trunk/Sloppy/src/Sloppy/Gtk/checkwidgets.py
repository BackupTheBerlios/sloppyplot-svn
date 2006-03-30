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
from Sloppy.Lib.Signals import *
from Sloppy.Lib.Undo import UndoList, UndoInfo
from Sloppy.Base import uwrap, utils
from Sloppy.Gtk import uihelper


import logging
logger = logging.getLogger('gtk.checkwidgets')

#------------------------------------------------------------------------------

# Text to use if the None value is offered in a ComboBox
COMBO_DEFAULT = ""


class DisplayFactory:


    def __init__(self, klass):
        self.klass = utils.as_class(klass)
        self.keys = [] 
        self.obj = None
        self.original_obj = None
        self.displays = {}
        
        
    def add_keys(self, *keys, **kwargs):            
        for key in keys:
            if isinstance(key, basestring):
                self.keys.append(key)                
            elif isinstance(key, (list, tuple)):
                self.add_keys(*key)
            else:
                raise TypeError("String, tuple or dict required.")

        for key, value in kwargs.iteritems():
            self.displays[key] = value


    def _create_displays(self, keys):

        """ Create Display instances for the given keys. The Display
        instances are initialized and their widgets are created. """
        
        for key in keys:
            if self.displays.has_key(key) is False:
                display = DisplayFactory.new_display(self.klass, key)
            else:
                # You can either pass a Display instance or a class
                # in add_keys. If a class was passed, then it needs
                # to be initialized.
                display = self.displays[key]
                if not isinstance(display, Display):
                    display = display()
            display.init_class(self.klass, key)
            display.create_widget()
            self.displays[key] = display


    def _create_table_from_keys(self, keys):
        table = gtk.Table(rows=len(self.keys), columns=2)
        tooltips = gtk.Tooltips()

        n = 0
        for key in keys:
            display = self.displays[key]
            # attach widget
            table.attach(display.widget, 1,2,n,n+1,
                         xoptions=gtk.EXPAND|gtk.FILL,
                         yoptions=0, xpadding=5, ypadding=1)

            # attach label (put into an event box to display the tooltip)
            label = gtk.Label(key)
            label.set_alignment(1.0, 0)
            #label.set_justify(gtk.JUSTIFY_RIGHT)

            ebox = gtk.EventBox()
            ebox.add(label)
            ebox.show()
            if display.check.doc is not None:
                tooltips.set_tip(ebox, display.check.doc)

            table.attach(ebox, 0,1,n,n+1,
                         xoptions=gtk.FILL, yoptions=0,
                         xpadding=5, ypadding=1)
            n += 1

        return table

    
    def create_sections(self, *layout):
        
        if not isinstance(layout, (list,tuple)):
            raise RuntimeError("Must be a list or tuple.")

        vbox = gtk.VBox()
        
        for section in layout:
            name, keys = section[0], section[1:]
            self._create_displays(keys)
            w = uihelper.new_section(name, self._create_table_from_keys(keys))
            vbox.pack_start(w, False, True)

        return vbox   

            
    def create_vbox(self):
        self._create_displays(self.keys)
        vbox = gtk.VBox()
        for d in self.displays.itervalues():
            vbox.add(d.widget)
        return vbox


    def create_table(self):
        self._create_displays(self.keys)
        
        table = gtk.Table(rows=len(self.keys), columns=2)
        tooltips = gtk.Tooltips()

        n = 0
        for key in self.keys:
            display = self.displays[key]
            # attach widget
            table.attach(display.widget, 1,2,n,n+1,
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

            table.attach(ebox, 0,1,n,n+1,
                      xoptions=gtk.FILL, yoptions=0,
                      xpadding=5, ypadding=1)

            n += 1

        return table


    def connect(self, obj):
        # The displays 'connect' is responsible for
        # disconnecting the old obj.
        for display in self.displays.itervalues():
            display.connect(obj)
        self.obj = obj
            
    
    def new_display(klass, key):

        """ Return a Display instance that is suitable for the given
        class attr. You still need to call init_class and create_widget
        on that instance before you can use the Display. """
        
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

        return v()
    
    new_display = staticmethod(new_display)    


    def check_in(self, obj):
        """ Create a copy of the objects and connect to them."""
        self.original_obj = obj
        copy = obj.__class__(**obj._values)            
        self.connect(copy)
        

    def check_out(self, undolist=[]):
        # create changeset
        new_values = self.obj._values
        old_values = self.original_obj._values

        changeset = {}
        for key, value in new_values.iteritems():
            if value != old_values[key]:
                changeset[key] = value

        changeset['undolist'] = undolist
        uwrap.set(self.original_obj, **changeset)
        




###############################################################################

    
class Display:
    
    def __init__(self):
        self.obj = None
        self.key = None
        self.klass = None
        self.check = None
        self.cb = None
       
    def init_class(self, klass, key):
        self.key = key
        self.klass = utils.as_class(klass)
        self.check = getattr(self.klass, key)        
    
    def connect(self, obj):
        if self.obj is not None:
            if self.cb is not None:
                self.cb.disconnect()
                self.cb = None            
            self.obj = None

        self.obj = obj
        if obj is not None:
            self.widget.set_sensitive(True)
            self.set_widget_data(obj.get(self.key))
            on_update_lambda = lambda sender, value: self.set_widget_data(value)        
            obj.signals['update::%s'%self.key].connect(on_update_lambda)
        else:
            self.widget.set_sensitive(False)

    def disconnect(self):
        self.connect(None)

    def use_widget(self, widget):
        self.widget = widget
        self._prepare(widget)

    def create_widget(self):
        self.use_widget(self._create())
        
    def set_value(self, obj, key, value):
        # this can be used as a hook for undo
        obj.set(key, value)



class As_Entry:

    def _create(self):                      
        return gtk.Entry()

    def _prepare(self, entry):
        entry.connect("focus-in-event", self.on_focus_in_event)

    def on_focus_in_event(self, widget, event):
        self.widget.connect("focus-out-event", self.on_focus_out_event)
        
    def on_focus_out_event(self, widget, event):
        try:
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
                self.set_value(self.obj, self.key, value)
        finally:
            return False

      


class As_Combobox:

    def _create(self):
        return gtk.ComboBox()

    def _prepare(self, cb):
        global COMBO_DEFAULT
        model = gtk.ListStore(str, object)
        cb.set_model(model)
        cell = gtk.CellRendererText()
        cb.pack_start(cell, True)
        cb.add_attribute(cell, 'text', 0)
        self.values = []
        self._fill_model(model)
        cb.connect("changed", self.on_changed)

        
    def _fill_model(self):
        " Append values to model. Don't forget to add the values to self.values. "
        pass


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
            self.set_value(self.obj, self.key, value)

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

    def _create(self):
        return gtk.SpinButton()

    def _prepare(self, spinbutton):
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
        try:
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
                self.set_value(self.obj, self.key, value)
        finally:
            return False


class As_Colorbutton:
    
    def _create(self):
        return gtk.ColorButton()

    def _prepare(self, colorbutton):
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
            self.set_value(self.obj, self.key, value)

        return False


    

class Display_Bool_As_Combobox(As_Combobox, Display):

    def _fill_model(self, model):
        global COMBO_DEFAULT        
        adict = {'True': True, 'False': False}
        if self.check.required is False:
            adict.update({COMBO_DEFAULT: None})

        model.clear()            
        for key, value in adict.iteritems():
            model.append((unicode(key), key))
            self.values.append(value)
            

class Display_Choice_As_Combobox(As_Combobox, Display):

    def _fill_model(self, model):
        model.clear()
        for value in self.check.choices:
            model.append((unicode(value or COMBO_DEFAULT), value))
            self.values.append(value)

class Display_Mapping_As_Combobox(As_Combobox, Display):
    def _fill_model(self, model):
        model.clear()
        for key, value in self.check.mapping.iteritems():
            model.append((unicode(key), key))
            self.values.append(value)
                

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

    def _prepare(self, spinbutton):
        Display_Number_As_Spinbutton._prepare(self, spinbutton)
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
    tv = df.create_sections( ['Section One', 'a_string'],
                             ['Section Two', 'an_integer', 'a_string'] )
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


    
