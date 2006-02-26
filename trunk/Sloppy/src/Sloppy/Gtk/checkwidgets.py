
import gtk


from Sloppy.Lib.Check import *
from Sloppy.Lib.Undo import UndoList
from Sloppy.Base import uwrap

import logging
logger = logging.getLogger('gtk.checkwidgets')
#------------------------------------------------------------------------------

# TODO:

# Display_Mapping_As_Combobox (!)
# Display_RGBColor (!!!)
# Display_Number_As_SpinButton
# Display_Bool_As_Checkbutton => boring

#------------------------------------------------------------------------------

class Display:
    
    def __init__(self, obj, key):
        self.obj = None
        self.key = None
        self.check = None
        self.set_source(obj, key)

        self.widget = None
        self.last_value = None
        self.init()

        self.create_widget()
        self.prepare_widget()

    def set_source(self, obj, key):        
        self.obj = obj
        self.key = key
        self.check = obj._checks[key]
                
    def init(self):
        pass

   
    #----------------------------------------------------------------------
    # Check In/Out
    
    def check_in(self):
        " Retrieve value from object. "
        raise RuntimeError("check_in() needs to be implemented.")

    def widget_data(self):
        """ Data that can be passed on to the object. """
        raise RuntimeError("widget_data() needs to be implemented.")
    
    def check_out(self, undolist=[]):
        " Set value in object. "
        new_value = self.widget_data()
        if new_value != self.last_value:
            uwrap.smart_set(self.obj, self.key, new_value, undolist=undolist)
            self.last_value = new_value

    #----------------------------------------------------------------------
    # UI Stuff

    def create_widget(self):
        raise RuntimeError("create_widget() needs to be implemented.")

    def use_widget(self, widget):
        self.widget = widget
        self.prepare_widget()
        

class Display_Bool_As_Combobox(Display):

    def init(self):
        self.last_index = None

    def create_widget(self):
        cb = gtk.ComboBox()
        model = gtk.ListStore(str, object)
        cb.set_model(model)
        cell = gtk.CellRendererText()
        cb.pack_start(cell, True)
        cb.add_attribute(cell, 'text', 0)
        self.widget = cb
        return cb
    
    def prepare_widget(self):
        adict = {'True': True, 'False': False}
        if self.obj._checks[self.key].required is False:
            adict.update({'None': None})
        self.values = adict.values() # for reference

        model = self.widget.get_model()
        model.clear()        
        for key, value in adict.iteritems():
            model.append((key, value))            
        
    def check_in(self):
        value = self.obj.get(self.key)
        if value is not Undefined:
            index = self.values.index(value)
            model = self.widget.get_model()
            iter = model.get_iter((index,))
            self.widget.set_active_iter(iter)
        else:
            index = -1
            
        self.last_value = value
        self.last_index = index

    def widget_data(self):
        index = self.widget.get_active()
        if index == self.last_index:
            return self.last_value
        elif index < 0:
            return Undefined            
        else:
            model = self.widget.get_model()
            return model[index][1]

    def check_out(self, undolist=[]):
        new_value = self.widget_data()
        if new_value != self.last_value:
            uwrap.smart_set(self.obj, self.key, new_value, undolist=undolist)
            self.last_value = new_value


class Display_Choice_As_Combobox(Display):

    def init(self):
        self.last_index = -1

    def create_widget(self):
        self.widget = gtk.ComboBox()
        return self.widget
        
    def prepare_widget(self):
        cb = self.widget
        model = gtk.ListStore(str, object)
        cb.set_model(model)
        cell = gtk.CellRendererText()
        cb.pack_start(cell, True)
        cb.add_attribute(cell, 'text', 0)

        model.clear()
        for value in self.check.choices:
            model.append((unicode(value), value))

    def check_in(self):
        value = self.obj.get(self.key)
        if value != Undefined:
            index = self.check.choices.index(value)
            model = self.widget.get_model()
            iter = model.get_iter((index,))
            self.widget.set_active_iter(iter)
            self.last_index = index
            
        self.last_value = value

    
    def widget_data(self):
        index = self.widget.get_active()
        if index == self.last_index:
            return self.obj.get(self.key)
        elif index < 0:
            return Undefined            
        else:
            model = self.widget.get_model()
            return model[index][1]


class Display_Anything_As_Entry(Display):

    def create_widget(self):                      
        self.widget = gtk.Entry()
        return self.widget

    def prepare_widget(self):
        entry = self.widget        
        entry.connect("focus-in-event", self.on_focus_in_event)
        entry.connect("focus-out-event", self.on_focus_out_event)

    def on_focus_in_event(self, widget, event):
        self.last_value = widget.get_text()
        
    def on_focus_out_event(self, widget, event):
        value = widget.get_text()
        if value == self.last_value:
            return

        if self.check.required is False and value == "":
            return
            
        try:
            value = self.check(value)
            widget.set_text(unicode(value))
        except ValueError:
            widget.set_text(self.last_value)
                            
        return False
            

    def check_in(self):
        value = self.obj.get(self.key)
        if value is Undefined:
            value = None
            
        if value is None:
            value = ""

        self.widget.set_text(unicode(value))
        self.last_value = value


    def widget_data(self):
        value = self.widget.get_text()
        if self.check.required is False and value=="":
            return None
            
        try:
            return self.check(value)
        except Exception, msg:
            return self.last_value


Display_Number_As_Entry = Display_Anything_As_Entry
Display_String_As_Entry = Display_Unicode_As_Entry = Display_Anything_As_Entry

#------------------------------------------------------------------------------

class TestObject(HasChecks):
    is_valid = Bool()
    is_valid_or_none = Bool(required=False)
    choices = Choice(['One', 'Two', 'Three'])

    an_integer = Integer()
    a_float = Float()
    another_float = Float(max=27.0)
    a_third_float = Float(min=-5, max=12.874)
    

obj = TestObject(is_valid=False)

cdict = {'is_valid': Display_Bool_As_Combobox,
         'is_valid_or_none': Display_Bool_As_Combobox,
         'choices': Display_Choice_As_Combobox,
         'an_integer': Display_Number_As_Entry,
         'a_float': Display_Number_As_Entry,
         'another_float': Display_Number_As_Entry,
         'a_third_float': Display_Number_As_Entry}
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
    vbox.pack_start(c.widget, False, True)

win.add(vbox)
win.show_all()

gtk.main()
    
