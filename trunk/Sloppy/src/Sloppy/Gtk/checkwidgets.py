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


"""

  Both factories should have similar interfaces:
  
  f = DisplayFactory(obj)
  f.add_keys(obj._checks.keys()
  table = f.create_table()
  f.check_in()
  ...
  f.check_out()


  f = ColumnFactory(mainobj, listkey, obj.__class__)
  f.add_keys(..keys()..)
  treeview = f.create_treeview()
  f.check_in()
  ...
  f.check_out()

  Since each factory keeps track of the created Column/Display
  objects, it is also possible to show/hide these:

  f.show(*keys)
  f.hide(*keys) 
  
"""

 # TODO: maybe rename Column To ColumnCreator ?
 

import gtk, sys, inspect

from Sloppy.Lib.Check import *
from Sloppy.Lib.Undo import UndoList
from Sloppy.Base import uwrap

import logging
logger = logging.getLogger('gtk.checkwidgets')


# TODO: For testing
import uihelper


###############################################################################


   
class ColumnFactory:

    def __init__(self, listowner, listkey, itemclass):
        self.listowner = listowner
        self.itemclass = itemclass
        self.listkey = listkey
        self.keys = []
        self.columns = {}
        self.old_list = []
        
    def add_keys(self, *keys, **kwargs):
        for key in keys:
            if isinstance(key, basestring):
                self.keys.append(key)
            elif isinstance(key, (list, tuple)):
                self.keys.extend(key)
            else:
                raise TypeError("String or tuple required.")

        for key, value in kwargs.iteritems():
            self.columns[key] = value

    def show_keys(self, *keys):           
        if len(keys) == 0:
            keys = self.keys

        for key in keys:
            if key == '_all':
                self.show_keys(*self.keys)
            elif isinstance(key, (list,tuple)):
                self.show_keys(*key)
            else:
                self.columns[key].set_property('visible', True)

    def hide_keys(self, *keys):
        if len(keys) == 0:
            keys = self.keys
        
        for key in keys:
            if key == '_all':
                self.hide_keys(*self.keys)
            elif isinstance(key, (list,tuple)):
                self.hide_keys(*key)
            else:
                self.columns[key].set_property('visible', False)
        
    def new_row(self, item):
        row = []
        for key in self.keys:
            row.append( item.get_value(key) )
        row.append(item)
        return row


    def create_treeview(self):
        model = gtk.ListStore(*([object]*(len(self.keys) + 1)))    
        treeview = gtk.TreeView(model)        

        index = 0
        for key in self.keys:
            if self.columns.has_key(key):
                obj = self.columns[key]
                if inspect.isfunction(obj) or inspect.ismethod(obj):
                    c = obj(model, index)
                else:
                    c = obj
            else:
                creator = self.new_column_creator(self.itemclass, key)
                c = creator.create_column(model, index)

            self.columns[key] = c
            treeview.append_column(c)
            index += 1
            
        self.treeview = treeview
        return self.treeview

    
    def check_in(self):
        itemlist = self.listowner.get(self.listkey)
        model = self.treeview.get_model()
        model.clear()
        for item in itemlist:
            row = []
            for key in self.keys:
                row.append(item.get(key))
            model.append( row + [item] )

        self.old_list = itemlist
        

    def check_out(self, undolist=[]):

        ul = UndoList()
        
        def check_out_row(owner, iter, undolist=[]):
            n = 0
            adict = {}
            for key in self.keys:
                adict[key]=model.get_value(iter, n)
                n += 1
            adict['undolist'] = ul
            uwrap.smart_set(owner, **adict)

        new_list = []
        model = self.treeview.get_model()
        iter = model.get_iter_first()
        while iter is not None:
            owner = model.get_value(iter, len(self.keys))
            check_out_row(owner, iter, undolist=ul)
            new_list.append(owner)
            iter = model.iter_next(iter)

        if self.old_list != new_list:        
            uwrap.set(self.listowner, self.listkey, new_list, undolist=ul)
            self.old_list = new_list

        undolist.append(ul)


    def new_column_creator(klass, key):
        keyklass = getattr(klass, key).__class__
        if keyklass == Choice:
            return ColumnCreator_Choice_As_Combobox(klass, key)
        elif keyklass == Mapping:
            return ColumnCreator_Mapping_As_Combobox(klass, key)
        elif keyklass == Bool:
            return ColumnCreator_Bool_As_Checkbutton(klass, key)
        else:
            return ColumnCreator_Anything_As_Entry(klass, key)
    
    new_column_creator = staticmethod(new_column_creator)


    

class Column(object):
    def __init__(self, klass, key):                 
        self.check = getattr(klass, key)
        self.key = key
        self.cell = None # TODO

    def get_column_key(self):
        key = self.check.blurb or self.key
        return key.replace('_', ' ')        



class ColumnCreator_Anything_As_Entry(Column):
    
    def create_column(self, model, index):
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited, model, index)

        column = gtk.TreeViewColumn(self.get_column_key())
        column.pack_start(cell)
        column.set_cell_data_func(cell, self.cell_data_func, index)

        self.column = column
        return column


    def on_edited(self, cell, path, data, model, index):
        try:
            data = self.check(data)
        except ValueError:
            pass
        else:
            model[path][index] = data
            
    def cell_data_func(self, column, cell, model, iter, index):
        value = model.get_value(iter, index)
        if value is None:
            value = ""
        cell.set_property('text', unicode(value))
        


class ColumnCreator_Choice_As_Combobox(Column):
    
    def create_column(self, model, index):
        cell_model = self.new_cell_model()
        
        cell = gtk.CellRendererCombo()                        
        cell.set_property('text-column', 0)
        cell.set_property('model', cell_model)

        # make editable
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited, model, index)
        
        column = gtk.TreeViewColumn(self.get_column_key())
        column.pack_start(cell)
        column.set_cell_data_func(cell, self.cell_data_func, index)

        self.column = column
        return column

    def new_cell_model(self):        
        cell_model = gtk.ListStore(str, object)
        for value in self.check.choices:
            if value is None:
                cell_model.append(('', None))
            else:
                cell_model.append((unicode(value), value))
        return cell_model

    def on_edited(self, cell, path, new_text, model, index):
        if len(new_text) == 0:
            new_text = None
        try:
            model[path][index] = self.check(new_text)            
        except ValueError:
            print "Could not set combo to value '%s', %s" % (new_text, type(new_text))

    def cell_data_func(self, column, cell, model, iter, index):
        user_value = model.get_value(iter, index)
        if user_value is None:
            user_value = ""
        cell.set_property('text', unicode(user_value))


class ColumnCreator_Mapping_As_Combobox(Column):

    def create_column(self, model, index):
        cell_model = self.new_cell_model()
        
        cell = gtk.CellRendererCombo()                        
        cell.set_property('text-column', 0)
        cell.set_property('model', cell_model)

        # make editable
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited, model, index)
        
        column = gtk.TreeViewColumn(self.get_column_key())
        column.pack_start(cell)
        column.set_cell_data_func(cell, self.cell_data_func, index)

        self.column = column
        return column

    def new_cell_model(self):
        self.keys = {}
        cell_model = gtk.ListStore(str, object)
        for key, value in self.check.mapping.iteritems():
            if key is None:
                key = ""            
            cell_model.append((unicode(key), value))
            self.keys[value] = unicode(key) # for reverse mapping
        return cell_model

    def on_edited(self, cell, path, new_text, model, index):
        if len(new_text) == 0:
            new_text = None
        try:
            model[path][index] = self.check(new_text)            
        except ValueError:
            print "Could not set combo to value '%s', %s" % (new_text, type(new_text))

    def cell_data_func(self, column, cell, model, iter, index):
        user_value = model.get_value(iter, index)
        if user_value is None:
            user_value = ""
        cell.set_property('text', self.keys[user_value])



class ColumnCreator_Bool_As_Checkbutton(Column):

    def create_column(self, model, index):
        cell = gtk.CellRendererToggle()

        cell.set_property('activatable', True)
        cell.connect('toggled', self.on_toggled, model, index)

        column = gtk.TreeViewColumn(self.get_column_key())
        column.pack_start(cell)
        column.set_cell_data_func(cell, self.cell_data_func, index)

        self.column = column
        return column


    def cell_data_func(self, column, cell, model, iter, index):
        value = model.get_value(iter, index)
        cell.set_property('active', bool(self.check(value)))


    def on_toggled(self, cell, path, model, index):
        value = not model[path][index]
        try:
            value = self.check(value)
        except ValueError:
            pass
        else:        
            model[path][index] = value








###############################################################################
###############################################################################

def as_class(obj):
    if inspect.isclass(obj):
        return obj
    else:
        return obj.__class__


                
class DisplayFactory:

    def __init__(self, obj):
        # TODO: change arg to klass
        self.obj = obj
        self.klass = as_class(obj)
        self.keys = []
        self.displays = {}
        
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
        
                    
    def check_in(self):
        # TODO: create copy of object and set these as source
        # TODO: for the displays
        for display in self.displays.itervalues():
            display.set_source(self.obj)
    
    def check_out(self, undolist=[]):
        # TODO: merge copy and original back
        pass
    #ul = UndoList()    
     #   for display in self.displays.itervalues():
      #      display.check_out(undolist=ul)
       # undolist.append(ul)


    def new_display(klass, key):
        check = getattr(klass, key)
        if isinstance(check, Bool):
            v = Display_Bool_As_Combobox
        elif isinstance(check, Choice):
            v = Display_Choice_As_Combobox
        elif isinstance(check, Integer):
            v = Display_Integer_As_Spinbutton
        elif isinstance(check, Float):
            v = Display_Number_As_Entry
        elif isinstance(check, RGBColor):
            v = Display_RGBColor_As_Colorbutton
        elif isinstance(check, Mapping):
            v = Display_Mapping_As_Combobox
        else:
            v = Display_Anything_As_Entry

        return v(klass, key)
    
    new_display = staticmethod(new_display)    
        

###############################################################################

    
class Display:
    
    def __init__(self, klass, key):
        self.obj = None
        self.key = None
        self.check = None
        self.key = key
        self.klass = as_class(klass)
        self.check = getattr(self.klass, key)
        self.obj = None
        self.widget = self.create_widget()
        self.prepare_widget(self.widget)

    def set_source(self, obj):        
        self.obj = obj
        self.set_widget_data(obj.get(self.key))

    #----------------------------------------------------------------------
    # UI Stuff

    def use_widget(self, widget):
        self.widget = widget
        self.prepare_widget(widget)



class As_Entry:

    def create_widget(self):                      
        return gtk.Entry()

    def prepare_widget(self, entry):
        entry.connect("focus-in-event", self.on_focus_in_event)

    def on_focus_in_event(self, widget, event):
        self.widget.connect("focus-out-event", self.on_focus_out_event)
        
    def on_focus_out_event(self, widget, event):
        value = self.get_widget_data()
        if self.check.required is False and value == "":
            value = None

        try:
            value = self.check(value)
        except ValueError, msg:
            print "Value Error", msg
            self.set_widget_data(self.obj.get(self.key))
        else:
            self.set_widget_data(value)
            self.obj.set(self.key, value)

        return False
        


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

    

class Display_Bool_As_Combobox(As_Combobox, Display):
            
    def prepare_widget(self, combobox):
        model = gtk.ListStore(str, object)
        combobox.set_model(model)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)
        
        adict = {'True': True, 'False': False}
        if self.check.required is False:
            adict.update({'None': None})
        self.values = adict.values() # for reference

        model = combobox.get_model()
        model.clear()        
        for key, value in adict.iteritems():
            model.append((key, value))

        # TODO: focus-in-event
        
        

class Display_Choice_As_Combobox(As_Combobox, Display):
        
    def prepare_widget(self, cb):
        model = gtk.ListStore(str, object)
        cb.set_model(model)
        cell = gtk.CellRendererText()
        cb.pack_start(cell, True)
        cb.add_attribute(cell, 'text', 0)
        model.clear()
        self.values = []
        for value in self.check.choices:
            model.append((unicode(value), value))
            self.values.append(value)


class Display_Mapping_As_Combobox(As_Combobox, Display):

    def prepare_widget(self, cb):
        model = gtk.ListStore(str, object)
        cb.set_model(model)
        cell = gtk.CellRendererText()
        cb.pack_start(cell, True)
        cb.add_attribute(cell, 'text', 0)
        model.clear()
        self.values = []
        for key, value in self.check.mapping.iteritems():
            model.append((unicode(key), key))
            self.values.append(value)
            

class Display_Anything_As_Entry(As_Entry, Display):

    def get_widget_data(self):
        value = self.widget.get_text()
        if value is Undefined:
            value = ""

        if self.check.required is False and value=="":
            return None

        return value

    def set_widget_data(self, data):
        if data is Undefined or data is None:
            data = u""
        else:
            data = unicode(data)            
        self.widget.set_text(data)

                

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
        print "FOCUS IN"
        self.widget.connect("focus-out-event", self.on_focus_out_event)

    def on_focus_out_event(self, widget, event):
        self.widget.update()
        value = self.get_widget_data()
        if self.check.required is False and value == "":
            value = None

        try:
            value = self.check(value)
        except ValueError, msg:
            print "Value Error", msg
            self.set_widget_data(self.obj.get(self.key))
        else:
            self.set_widget_data(value)
            self.obj.set(self.key, value)

        return False
    
           
        
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
        

Display_Number_As_Entry = Display_Anything_As_Entry
Display_String_As_Entry = Display_Unicode_As_Entry = Display_Anything_As_Entry


class Display_RGBColor_As_Colorbutton(Display):

    def create_widget(self):
        return gtk.ColorButton()

    def prepare_widget(self, colorbutton):
        colorbutton.set_use_alpha(False)
        colorbutton.set_title(self.check.blurb or "Select Color")

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


    class MainObject(HasChecks):
        obj_list = List(Instance(TestObject))


    obj = TestObject(is_valid=False, a_mapping='One')
    obj2 = TestObject(an_integer=5, a_mapping=1)
    main = MainObject(obj_list=[obj, obj2])


    if True:
        df = DisplayFactory(obj)        
        df.add_keys(obj._checks.keys())
        tv = df.create_table()
    else:
        df = ColumnFactory(main, 'obj_list', obj.__class__)
        df.add_keys(obj._checks.keys())
        tv = df.create_treeview()

    df.check_in()

    def quit(sender):
        df.check_out()
        print "VALUES ===>", obj._values
        gtk.main_quit()

    win = gtk.Window()
    win.set_size_request(480,320)
    win.connect('destroy', quit)


    win.add(uihelper.add_scrollbars(tv))
    win.show_all()

    gtk.main()




if __name__ == "__main__":
    test()


    
