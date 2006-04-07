
from main import find_peaks, match_patterns

import gtk
import numpy

from Sloppy.Lib.Check import *
from Sloppy.Gtk import toolbox, checkwidgets, uihelper
from Sloppy.Base import globals, backend, objects

#----------------------------------------------------------------------

class DisplayLine(checkwidgets.Display):

    def __init__(self):
        checkwidgets.Display.__init__(self)
        self.backend = None
        self.values = []
        self.cblist = []
        
    def _create(self):
        return gtk.ComboBox()

    def _prepare(self, cb):
        # model = (line, layer)
        model = gtk.ListStore(object, object)
        cb.set_model(model)
        cell = gtk.CellRendererText()
        cb.pack_start(cell, True)

        def render_linename(column, cell, model, iter):
            line = model.get_value(iter, 0)
            if line is None:
                line_descr = "NONE"
            else:
                line_descr = line.get_description()

            layer = model.get_value(iter, 1)
            if layer is None:
                layer_descr = "NONE"
            else:
                layer_descr = layer.get_description()
                
            cell.set_property('text', '%s: %s' % (layer_descr, line_descr))
        cb.set_cell_data_func(cell, render_linename)
        cb.connect("changed", self.on_changed)
        
        self.update_model()

    def update_model(self):
        # first disconnect all old signals
        for cb in self.cblist:
            cb.disconnect()
        self.cblist = []

        # now repopulate the treeview and add callbacks
        # If the old selection still exists, make sure it stays selected.
        model = self.widget.get_model()         
        iter = self.widget.get_active_iter()
        if iter is not None:
            old_value = model.get_value(iter, 0)
        else:
            old_value = None

        model.clear()
        self.values = []        
        if self.backend is not None:
            for layer in self.backend.plot.layers:
                cb = layer.sig_connect('update::lines', lambda sender, key, updateinfo: self.update_model())
                self.cblist.append(cb)
                for line in layer.lines:
                    iter = model.append((line, layer))
                    self.values.append(line)
                    if line is old_value:
                        self.widget.set_active_iter(iter)
                        

    def set_backend(self, backend):
        if backend is not self.backend:
            self.backend = backend
            self.update_model()
        

    def get_widget_data(self):
        index = self.widget.get_active()      
        if index < 0:
            return Undefined
        else:
            model = self.widget.get_model()        
            return self.values[index]

    def set_widget_data(self, data):
        try:
            index = self.values.index(data)
        except:
            index = -1
        self.widget.set_active(index)

    def on_changed(self, widget):
        print "ON CHANGED"
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


#----------------------------------------------------------------------
class Settings(objects.SPObject):
    threshold = Float(init=1.0)
    accuracy = Float(init=1.0)
    line = Instance(objects.Line, init=None)

       
    
class PeakFinder(toolbox.Tool):

    label = "PeakFinder"
    icon_id = gtk.STOCK_EDIT


    def __init__(self):
        toolbox.Tool.__init__(self)
        self.settings = settings = Settings()
        
        self.depends_on(globals.app, 'active_backend')

        #
        # find button
        #
        self.btn_find = btn_find = gtk.Button('Find')
        btn_find.connect('clicked', self.on_btn_find_clicked)

        #
        # Settings
        #
        df = checkwidgets.DisplayFactory(Settings)
        self.display_line = DisplayLine()
        df.add_keys(self.settings._checks.keys(), line=self.display_line)
        self.table = table = df.create_sections(['Settings', 'line','threshold','accuracy'])
        df.connect(self.settings)
            
        #
        # Treeview (displaying the found peaks)
        #
        
        # model: (float, float, str) = (x,y, symobl)
        model = gtk.ListStore(float, float, str)        
        self.treeview = treeview = gtk.TreeView(model)
        treeview.set_headers_visible(False)

        cell = gtk.CellRendererText()        
        column = gtk.TreeViewColumn('X', cell)
        column.set_attributes(cell, text=0)
        cell = gtk.CellRendererText()
        treeview.append_column(column)
        
        cell = gtk.CellRendererText()        
        column = gtk.TreeViewColumn('Y', cell)
        column.set_attributes(cell, text=1)
        cell = gtk.CellRendererText()
        treeview.append_column(column)

        cell = gtk.CellRendererText()        
        column = gtk.TreeViewColumn('Symbol', cell)
        column.set_attributes(cell, text=2)
        cell = gtk.CellRendererText()
        treeview.append_column(column)

        #treeview.connect("row-activated", self.on_row_activated)
        #treeview.connect("cursor-changed", self.on_cursor_changed)

        # results is the section containing the treeview
        results = uihelper.new_section('Results:', uihelper.add_scrollbars(treeview))

        #
        # pack everything in a vbox
        #
        vbox = gtk.VBox()
        vbox.pack_start(results, True, True)
        vbox.pack_start(table, False, False)
        vbox.pack_start(btn_find, False, True)
        
        vbox.show_all()
        
        self.add(vbox)

    def autoupdate_active_backend(self, sender, backend):
        print
        print "-- updating backend --"

        self.display_line.set_backend(backend)
        
        print
        


    def on_btn_find_clicked(self, sender):
        line = self.settings.line
        threshold = self.settings.threshold
        accuracy = self.settings.accuracy
       
        peaklist = find_peaks(line.get_x(), line.get_y(), threshold, accuracy)

        # copy peak list to treeview model
        model = self.treeview.get_model()
        model.clear()
        for x,y in peaklist:
            model.append((x,y,""))

        # TESTING: find patterns as well!
        # The match_patterns function should interpret values that are
        # too high as o.k.
        patterns = {
            'Li': [(7.0, 1)],
            'Zn': [(63.9291466, 0.4863),
                   (65.9260368, 0.2790),
                   (66.9271309, 0.0410),
                   (67.9248476, 0.1875)]
            }


        a = numpy.array(peaklist)
        match_patterns(a[:,0], a[:,1], patterns)
        

def gtk_init(app):
    toolbox.register_tool(PeakFinder, 'PeakFinder')
