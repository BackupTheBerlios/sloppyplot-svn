
import gtk
from Sloppy.Gtk import toolbox, uihelper, options_dialog
from Sloppy.Base import globals, error

class LinesTool(toolbox.BackendTool):

    name = "Lines"
    stock_id = gtk.STOCK_PROPERTIES


    def init(self):
        self.layer = None
        self.layer_signals = []
        self.line = None
        self.line_signals = []

        # GUI: treeview with buttons below
        
        # model: (object) = (layer object)
        model = gtk.ListStore(object)        
        treeview = gtk.TreeView(model)
        treeview.set_headers_visible(False)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn('line', cell)

        def render_label(column, cell, model, iter):
            line = model.get_value(iter, 0)
            title = line.label or "<untitled line>"
            index = model.get_path(iter)[0]
            cell.set_property('text', "%d: %s" % (index, title))
        column.set_cell_data_func(cell, render_label)
        
        treeview.append_column(column)
        treeview.connect("row-activated", self.on_row_activated)
        treeview.connect("cursor-changed", self.on_cursor_changed)
        
        buttons = [(gtk.STOCK_ADD, lambda sender: None),
                   (gtk.STOCK_REMOVE, lambda sender: None),
                   (gtk.STOCK_GO_UP, lambda sender: None),#self.on_move_selection, -1),
                   (gtk.STOCK_GO_DOWN, lambda sender: None)]#self.on_move_selection, +1)]        
        buttonbox = uihelper.construct_hbuttonbox(buttons, labels=False)

        box = gtk.VBox()
        box.pack_start(treeview, True, True)
#        box.pack_start(buttonbox, False, True)
        self.add(box)
        self.show_all()

        self.treeview = treeview
        self.buttonbox = buttonbox
        self.box = box


            
    def on_update_active_backend(self, sender, backend):
        if backend == self.backend:
            return

        for signal in self.backend_signals:
            signal.disconnect()
        if backend is not None:
            s1 = backend.sig_connect('update::active_layer', self.on_update_active_layer)
            backend_signals = [s1]            
            
        self.backend = backend
        try:
            layer = self.backend.active_layer
        except:
            layer = None
        self.update_active_layer(layer)

    def on_update_active_layer(self, painter, layer):
        self.update_active_layer(layer)                       

    def on_update_lines(self, sender, updateinfo):
        self.update_lines(updateinfo)

    def on_update_active_line(self, sender, line):
        self.update_active_line(line)


    def update_active_layer(self, layer):
        if layer == self.layer:
            return       

        try:
            painter = self.backend.get_painter(layer)
        except:
            painter = None
            
        for signal in self.layer_signals:
            signal.disconnect()
            #layer = self.painter.active_layer
            #if layer is not None:
            #    layer.sig_disconnect('update::lines', self.on_update_lines)
        if painter is not None:
            s1 = painter.sig_connect('update::active_line', self.on_update_active_line)
            layer_signals = [s1]
            #layer = painter.active_layer
            #if layer is not None:
            #    layer.sig_connect('update::lines', self.on_update_lines)            

        self.layer = layer
        self.update_lines()
        

    def update_lines(self, updateinfo=None):
        # TODO: partial redraw
        model = self.treeview.get_model()
        model.clear()

        if self.layer is None:
            self.treeview.set_sensitive(False)
        else:
            self.treeview.set_sensitive(True)
            for line in self.layer.lines:
                model.append((line,))

        try:
            line = self.backend.get_painter(self.layer).active_line
        except:
            line = None

        if line is None and self.layer is not None and len(self.layer.lines) > 0:
            self.backend.get_painter(self.layer).active_line = self.layer.lines[0]
        else:
            self.update_active_line(line)

    def update_active_line(self, line):
        if line == self.line:
            return
        
        # mark active layer
        model = self.treeview.get_model()
        iter = model.get_iter_first()
        while iter is not None:
            value = model.get_value(iter, 0)
            if value == line:
                self.treeview.get_selection().select_iter(iter)
                break
            iter = model.iter_next(iter)
        else:
            self.treeview.get_selection().unselect_all()                      



    ###############
    def on_cursor_changed(self, treeview):
        model, iter = treeview.get_selection().get_selected()
        line = model.get_value(iter,0)
        if line is not None:
            try:
                painter = self.backend.get_painter(self.layer)
            except:
                pass
            else:
                painter.active_line = line

    def on_row_activated(self, treeview, *udata):
        model, iter = treeview.get_selection().get_selected()
        line = model.get_value(iter, 0)
        self.edit(line)        
        # TODO: edit line  (maybe put this function somewhere else?)

    ########
    def edit(self, line):
        dialog = options_dialog.OptionsDialog(line)
        try:           
            response = dialog.run()
            if response == gtk.RESPONSE_ACCEPT:
                dialog.check_out()
                return dialog.owner
            else:
                raise error.UserCancel

        finally:
            dialog.destroy()

#         win = gtk.Window()
#         self.factory = checkwidgets.DisplayFactory(line)
#         self.factory.add_keys(line._checks.keys())
#         table = self.factory.create_table()
#         frame = uihelper.new_section("Line", table)
#         self.factory.check_in(line)


#------------------------------------------------------------------------------
toolbox.register_tool(LinesTool)
