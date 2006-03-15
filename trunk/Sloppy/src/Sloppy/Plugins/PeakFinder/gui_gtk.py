
import main

import gtk

from Sloppy.Lib.Props import *
from Sloppy.Gtk import tools
#----------------------------------------------------------------------

# we need to specify a x column and a y column

# Tool,BasedOnLayer
#

class PeakFinderTool(tools.Tool):

    name = "PeakFinder"
    stock_id = gtk.STOCK_EDIT

    
    def __init__(self):
        tools.Tool.__init__(self)

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

        

        


def gtk_init(app):
    tools.register_tool(PeakFinderTool, 'PeakFinder')
