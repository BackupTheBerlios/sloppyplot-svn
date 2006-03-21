
import gtk
from Sloppy.Gtk import toolbox
from Sloppy.Base import globals

class LayersTool(toolbox.Tool):

    name = "Layers"
    stock_id = gtk.STOCK_EDIT
    
    def __init__(self):
        toolbox.Tool.__init__(self)
        
        self.layer = None

        self.depends_on(globals.app, 'active_backend', 'active_layer_painter')
        
        # model: (object) = (layer object)
        model = gtk.ListStore(object)        
        treeview = gtk.TreeView(model)
        treeview.set_headers_visible(False)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn('label', cell)

        def render_label(column, cell, model, iter):
            layer = model.get_value(iter, 0)
            visible = ('','V')[layer.visible]
            title = layer.title or "<untitled layer>"
            index = model.get_path(iter)[0]
            cell.set_property('text', "[%d - %s]: %s" % (index, visible, title))
        column.set_cell_data_func(cell, render_label)
        
        treeview.append_column(column)
        treeview.connect("row-activated", self.on_row_activated)
        treeview.connect("cursor-changed", self.on_cursor_changed)
        treeview.show()
        self.add(treeview)        
        self.treeview = treeview

        self.update_layers()

    def autoupdate_active_backend(self, sender, backend):
        self.update_layers()
        

    def autoupdate_active_layer_painter(self, sender, painter):
        # mark active layer
        model = self.treeview.get_model()
        iter = model.get_iter_first()
        while iter is not None:
            value = model.get_value(iter, 0)
            if value == painter.obj:
                self.treeview.get_selection().select_iter(iter)
                break
            iter = model.iter_next(iter)
        else:
            self.treeview.get_selection().unselect_all()
        
        
    def update_layers(self, updateinfo=None):
        # TODO: partial redraw
        model = self.treeview.get_model()
        model.clear()
        
        if self.active_backend is None:
            self.treeview.set_sensitive(False)
        else:
            self.treeview.set_sensitive(True)
            for layer in self.active_backend.plot.layers:
                model.append((layer,))

        if self.active_backend is not None:
            layer = self.active_backend.request_active_layer()


    ########
    def on_cursor_changed(self, treeview):
        model, iter = treeview.get_selection().get_selected()
        layer = model.get_value(iter,0)
        if layer is not None:
            self.active_backend.active_layer_painter = self.active_backend.get_painter(layer)


    def on_row_activated(self, treeview, *udata):
        model, iter = treeview.get_selection().get_selected()
        layer = model.get_value(iter, 0)               
        globals.app.edit_layer(self.active_backend.plot, layer)
        


#------------------------------------------------------------------------------
toolbox.register_tool(LayersTool)
