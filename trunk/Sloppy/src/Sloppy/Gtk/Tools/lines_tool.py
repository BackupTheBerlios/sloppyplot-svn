
import gtk
from Sloppy.Gtk import toolbox, uihelper, options_dialog
from Sloppy.Base import globals, error, uwrap
from Sloppy.Lib.Undo import UndoList


class LinesTool(toolbox.Tool):

    name = "Lines"
    stock_id = gtk.STOCK_PROPERTIES


    def __init__(self):
        toolbox.Tool.__init__(self)

        self.depends_on(globals.app, 'active_backend', 'active_layer_painter', 'active_line_painter')

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


    def update_lines(self, updateinfo=None):
        # TODO: partial redraw
        model = self.treeview.get_model()
        model.clear()

        if self.active_layer_painter is None:
            self.treeview.set_sensitive(False)
        else:
            self.treeview.set_sensitive(True)
            layer = self.active_layer_painter.obj
            for line in layer.lines:
                model.append((line,))

        line = self.active_layer_painter.request_active_line()


    def autoupdate_active_backend(self, sender, backend):
        if backend is not None:
            backend.request_active_layer()
        
    def autoupdate_active_layer_painter(self, sender, painter):
        if painter is not None:
            painter.request_active_line()
        self.update_lines()

    def autoupdate_active_line_painter(self, sender, painter):       
        # mark active line
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



    ###############
    def on_cursor_changed(self, treeview):
        model, iter = treeview.get_selection().get_selected()
        line = model.get_value(iter,0)
        if line is not None:
            self.active_layer_painter.set_active_line(line)

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
                ul = UndoList("Edit Line")                                
                dialog.check_out(undolist=ul)
                uwrap.emit_last(self.backend, 'redraw', undolist=ul)
                globals.app.project.journal.append(ul)
                
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
