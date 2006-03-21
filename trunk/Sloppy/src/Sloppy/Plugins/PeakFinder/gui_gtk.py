
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
        
        self.depends_on(globals.app, 'active_backend', 'active_layer_painter', 'active_line_painter')

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

    def autoupdate_active_line_painter(self, sender, painter):
        print
        print "PAINTER UPDATED"
        print



def gtk_init(app):
    toolbox.register_tool(PeakFinder, 'PeakFinder')
