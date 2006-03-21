
import main

import gtk

from Sloppy.Lib.Props import *
from Sloppy.Gtk import toolbox
from Sloppy.Base import globals, backend

#----------------------------------------------------------------------

# we need to specify a x column and a y column
    
    
class PeakFinder(toolbox.Tool):

    name = "PeakFinder"
    stock_id = gtk.STOCK_EDIT


    def __init__(self):
        toolbox.Tool.__init__(self)
        print ">>> INIT PEAKFINDER"
        
        # for generic_on_update
        self.signalmap = {}        
        self.dependency_chain = ['active_backend',
                                 'active_layer',
                                 'active_line']
        
        for var in self.dependency_chain:
            setattr(self, var, None)
        globals.app.sig_connect('update::active_backend',
          lambda sender, value: self.generic_on_update('active_backend', sender, value))


        # info label (displaying the active line)
        label = self.label = gtk.Label()
        label.set_text("Test")
        
        # model: (object) = (...)
        model = gtk.ListStore(object)        
        treeview = gtk.TreeView(model)
        treeview.set_headers_visible(False)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn('label', cell)

        treeview.append_column(column)
        #treeview.connect("row-activated", self.on_row_activated)
        #treeview.connect("cursor-changed", self.on_cursor_changed)
        treeview.show()
        self.add(treeview)
       

    def generic_on_update(self, var, sender, value):
        print "GENERIC UPDATE FOR VAR ", var
        print "%s = %s" % (sender, value)

        old_value = getattr(self, var)
        if value == old_value:
            return

        if self.signalmap.has_key(sender):
            signal = self.signalmap.pop(sender)
            # propagate None value before disconnecting
            if value is None and old_value is not None:
                signal(old_value, None)
            signal.disconnect()                

        setattr(self, var, value)                
        if value is not None:
            # TODO: this already assumes that we have active_backend
            if not isinstance(value, backend.Backend):
                obj = self.active_backend.get_painter(value)
            else:
                obj = value
            
            # Connect to the update mechanism of the next dependency.
            # If this is already the last dependency, then we call
            # on_update_object, which then can use the object.
            try:
                next_var = self.dependency_chain[self.dependency_chain.index(var)+1]
            except IndexError:
                self.on_update_object(sender, value)
            else:
                new_signal = obj.sig_connect('update::%s'%next_var,
                  lambda sender,value: self.generic_on_update(next_var, sender, value))
                self.signalmap[sender] = new_signal            

    def on_update_object(self, sender, value):
        print "------------- UPDATE -----------------"



def gtk_init(app):
    toolbox.register_tool(PeakFinder, 'PeakFinder')
