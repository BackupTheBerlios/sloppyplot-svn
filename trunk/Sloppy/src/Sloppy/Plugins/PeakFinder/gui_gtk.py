
from main import find_peaks

import gtk

from Sloppy.Lib.Check import *
from Sloppy.Gtk import toolbox, checkwidgets, uihelper
from Sloppy.Base import globals, backend, objects

#----------------------------------------------------------------------

# we need to specify a x column and a y column


class Settings(objects.SPObject):
    threshold = Float(init=1.0)
    accuracy = Float(init=1.0)
    
    
class PeakFinder(toolbox.Tool):

    label = "PeakFinder"
    icon_id = gtk.STOCK_EDIT


    def __init__(self):
        toolbox.Tool.__init__(self)
        self.settings = settings = Settings()
        
        self.depends_on(globals.app, 'active_backend', 'active_layer_painter', 'active_line_painter')

        #
        # info label (displaying the active line)
        #
        self.line_label = label = gtk.Label()
        label.set_text("Test")

        #
        # find button
        #
        self.btn_find = btn_find = gtk.Button('Find')
        btn_find.connect('clicked', self.on_btn_find_clicked)

        #
        # Settings
        #
        df = checkwidgets.DisplayFactory(Settings)
        df.add_keys(self.settings._checks.keys())
        self.table = table = df.create_table()
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
        treeview.show()

        #
        # pack everything in a vbox
        #
        vbox = gtk.VBox()
        vbox.pack_start(label, False, True)
        vbox.pack_start(uihelper.add_scrollbars(treeview), True, True)
        vbox.pack_start(table, False, False)
        vbox.pack_start(btn_find, False, True)
        
        vbox.show_all()
        
        self.add(vbox)

    def autoupdate_active_backend(self, sender, backend):
        if backend is not None:
            backend.request_active_layer()
        
    def autoupdate_active_layer_painter(self, sender, painter):
        if painter is not None:
            painter.request_active_line()
    
    def autoupdate_active_line_painter(self, sender, painter):
        self.line_label.set_text(self.get_label_text())

    def get_label_text(self):
        try:
            layer, line = self.active_layer_painter.obj, self.active_line_painter.obj
        except AttributeError:
            return "---"
        
        if line is None:
            return ""
        else:
            return "%02d:%s" % (layer.lines.index(line), line.label or "")


    def on_btn_find_clicked(self, sender):
        try:
            layer, line = self.active_layer_painter.obj, self.active_line_painter.obj
        except AttributeError:
            return

        threshold = self.settings.threshold
        accuracy = self.settings.accuracy
       
        peaklist = find_peaks(line.get_x(), line.get_y(), threshold, accuracy)

        # copy peak list to treeview model
        model = self.treeview.get_model()
        model.clear()
        for x,y in peaklist:
            model.append((x,y,""))

        

def gtk_init(app):
    toolbox.register_tool(PeakFinder, 'PeakFinder')
