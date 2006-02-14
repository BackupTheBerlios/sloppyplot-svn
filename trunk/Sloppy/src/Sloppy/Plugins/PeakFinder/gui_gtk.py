
import main

import gtk

from Sloppy.Lib.Props import *
from Sloppy.Gtk.tools import Tool
#----------------------------------------------------------------------

class PeakFinderTool(Tool):
    
    def __init__(self):
        Tool.__init__(self, "PeakFinder", gtk.STOCK_EDIT)

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

        


def gtk_init(app):
    app.register_tool(PeakFinderTool, 'PeakFinder')

    
        



        

