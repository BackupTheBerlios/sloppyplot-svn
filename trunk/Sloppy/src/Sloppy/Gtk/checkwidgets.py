
import gtk
import inspect


from Sloppy.Lib.Check import *
from Sloppy.Lib.Undo import UndoList
from Sloppy.Base import uwrap

import logging
logger = logging.getLogger('gtk.checkwidgets')
#------------------------------------------------------------------------------



# - create widget(s)
# - check in data (from object into widget)
# - check out data (from widget to object)


class BoolCombobox:

    def __init__(self, obj, key):
        self.obj = obj
        self.key = key
        self.last_value = None
        self.last_index = None
        self.widget = self.create_widget()

        self.connect()

    def create_widget(self):
        cb = gtk.ComboBox()
        model = gtk.ListStore(str, object)
        cb.set_model(model)
        cell = gtk.CellRendererText()
        cb.pack_start(cell, True)
        cb.add_attribute(cell, 'text', 0)
        return cb
    
    def connect(self):
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

    def get_data(self):
        index = self.widget.get_active()
        if index == self.last_index:
            return self.last_value
        elif index < 0:
            return Undefined            
        else:
            model = self.widget.get_model()
            return model[index][1]

    def check_out(self, undolist=[]):
        new_value = self.get_data()
        if new_value != self.last_value:
            uwrap.smart_set(self.obj, self.key, new_value, undolist=undolist)
            self.last_value = new_value


#class BoolCheckButton:

    

#------------------------------------------------------------------------------

class TestObject(HasChecks):
    is_valid = Bool()
    is_valid_or_none = Bool(required=False)

obj = TestObject(is_valid=False)

cdict = {'is_valid': BoolCombobox, 'is_valid_or_none': BoolCombobox}
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
    
