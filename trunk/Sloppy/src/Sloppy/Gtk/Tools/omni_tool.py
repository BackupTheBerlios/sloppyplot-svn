
import gtk
from Sloppy.Gtk import toolbox, uihelper
from Sloppy.Base import globals


"""
All-including Tool :-) that lists all objects of a Plot.
"""


class OmniTool(toolbox.Tool):

    label = "Omni"
    icon_id = gtk.STOCK_PREFERENCES

    def __init__(self):
        toolbox.Tool.__init__(self)

        self.depends_on(globals.app, 'active_backend')

        # model (object)
        model = gtk.TreeStore(object)

        self.treeview = treeview = gtk.TreeView(model)
        treeview.set_headers_visible(False)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn('label', cell)

        def render_label(column, cell, model, iter):
            obj = model.get_value(iter, 0)
            if hasattr(obj, 'label') and obj.label is not None:
                label = obj.label
            else:
                label = "<%s>" % obj.__class__.__name__
            cell.set_property('text', label)
        column.set_cell_data_func(cell, render_label)

        treeview.append_column(column)
        #treeview.connect("row-activated", self.on_row_activated)
        #treeview.connect("cursor-changed", self.on_cursor_changed)
        treeview.show()
        
        self.add(uihelper.add_scrollbars(treeview))

        self.backend = -1
        #self.dock.connect('backend', ...)
        sender = globals.app
        sender.sig_connect('update::active_backend', self.on_update_backend)
        self.on_update_backend(sender, sender.active_backend)



    def on_update_backend(self, sender, backend):
        if backend == self.backend:
            return

        model = self.treeview.get_model()
        model.clear()

        if backend is None:
            self.treeview.set_sensitive(False)
        else:
            self.treeview.set_sensitive(True)
            for layer in backend.plot.layers:
                model.append(None, (layer,))
                
        self.backend = backend
        

#------------------------------------------------------------------------------
toolbox.register_tool(OmniTool)
