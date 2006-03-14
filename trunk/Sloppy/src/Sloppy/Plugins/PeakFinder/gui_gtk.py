
import main

import gtk

from Sloppy.Lib.Props import *
from Sloppy.Gtk import tools
#----------------------------------------------------------------------

# we need to specify a x column and a y column
# => we are not necessarily acting on a specific layer,
#    but even on a specific line!

#    Maybe we can stay independent of the layer stuff ?
#    If this Tool is some kind of history window, where you
#    can see the results of the find_peak operation, then we must
#    make sure, that this history is not cleared, when the layer
#    changes.


class PeakFinderTool(tools.Tool):

    name = "PeakFinder"
    stock_id = gtk.STOCK_EDIT

    
    def __init__(self):
        tools.Tool.__init__(self)

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
