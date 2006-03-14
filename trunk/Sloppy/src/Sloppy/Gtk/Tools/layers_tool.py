
import gtk
from Sloppy.Gtk import tools


class LayerTool(tools.Tool):

    name = "Layers"
    stock_id = gtk.STOCK_EDIT
    
    def init(self):
        self.layer = None
        
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


    def update_active_backend(self, backend):
        if backend == self.backend:
            return

        if self.backend is not None:
            self.backend.sig_disconnect('update::active_layer', self.on_update_active_layer)
            self.backend.plot.sig_disconnect('update::layers', self.on_update_layers)

        if backend is not None:
            backend.sig_connect('update::active_layer', self.on_update_active_layer)
            backend.plot.sig_connect('update::layers', self.on_update_layers)

        self.backend = backend
        self.update_layers()
        
    def update_layers(self, updateinfo=None):
        # TODO: partial redraw
        model = self.treeview.get_model()
        model.clear()
        
        if self.backend is None:
            self.treeview.set_sensitive(False)
        else:
            self.treeview.set_sensitive(True)
            for layer in self.backend.plot.layers:
                model.append((layer,))

        try:
            layer = self.backend.active_layer
        except:
            layer = None
            
        if layer is None and self.backend is not None and len(self.backend.plot.layers) > 0:
            self.backend.active_layer = self.backend.plot.layers[0]
        else:
            self.update_active_layer(layer)

    def update_active_layer(self, layer):
        # mark active layer
        model = self.treeview.get_model()
        iter = model.get_iter_first()
        while iter is not None:
            value = model.get_value(iter, 0)
            if value == layer:
                self.treeview.get_selection().select_iter(iter)
                break
            iter = model.iter_next(iter)
        else:
            self.treeview.get_selection().unselect_all()
        self.layer = layer
        
    def on_update_active_layer(self, sender, layer):
        self.update_active_layer(layer)      

    def on_update_layers(self, sender, updateinfo):
        self.update_layers(updateinfo)


    ########
    def on_cursor_changed(self, treeview):
        model, iter = treeview.get_selection().get_selected()
        layer = model.get_value(iter,0)
        if layer is not None:
            self.backend.active_layer = layer


    def on_row_activated(self, treeview, *udata):
        model, iter = treeview.get_selection().get_selected()
        layer = model.get_value(iter, 0)               
        globals.app.edit_layer(self.backend.plot, layer)
        


#------------------------------------------------------------------------------
tools.register_tool(LayerTool, 'LayerTool')
