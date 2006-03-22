
import gtk
from Sloppy.Gtk import toolbox, uihelper, checkwidgets
from Sloppy.Base import globals, objects, uwrap


"""
All-including Tool :-) that lists all objects of a Plot.
"""


KLASS_KEYS = {objects.Layer: ['title', 'visible', 'grid', 'x', 'y', 'width', 'height', 'type']}


class OmniTool(toolbox.Tool):

    label = "Omni"
    icon_id = gtk.STOCK_PREFERENCES

    def __init__(self):
        toolbox.Tool.__init__(self)

        self.depends_on(globals.app, 'active_backend')

        #
        # Treeview
        #
        
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
        treeview.connect("cursor-changed", self.on_cursor_changed)
        treeview.show()    

        #
        # Edit Area
        #
        self.edit_area = None
        self.obj = None # no active object to begin with

        #
        # Both the treeview and the table are stuffed into
        # a vbox; but there is no no table to begin with.
        # It is created in the on_cursor_changed event.
        #
        self.vbox = vbox = gtk.VBox()
        vbox.add(uihelper.add_scrollbars(treeview))
        self.add(vbox)
        
        # Connect to Backend.
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


    def on_cursor_changed(self, sender):
        # if the cursor changes, then we need to refresh
        # the table with the checkwidgets.
        global KLASS_KEYS

        # retrieve selected object
        model, iter = self.treeview.get_selection().get_selected()
        obj = model.get_value(iter,0)

        if obj == self.obj:
            return
        
        # TODO: if the object is different, but the class is the
        # TODO: same, then we don't rebuild the table, but simply
        # TODO: connect the new object.
        
        # remove any existing edit area
        if self.edit_area is not None:
            self.vbox.remove(self.attr_table)

        print "OBJECT IS ", obj
        
        # create new widget
        if obj is not None:            
            df = checkwidgets.DisplayFactory(obj)
            try:
                keys = KLASS_KEYS[obj.__class__]
            except KeyError:
                key = obj._checks.keys()
            df.add_keys(keys)
            tbl = df.create_table()
            # undo hooks
            for display in df.displays.itervalues():
                display.set_value = self.set_attribute_value
            df.connect(obj)                        
            widget = uihelper.add_scrollbars(tbl, viewport=True)
            widget.show_all()            
            self.vbox.add(widget)
        else:
            widget = None

        self.edit_area = widget
        self.obj = obj


    def set_attribute_value(self, obj, key, value):
        # this is used as a hook for undo
        uwrap.set(obj, key, value, undolist=globals.app.project.journal)
        
#------------------------------------------------------------------------------
toolbox.register_tool(OmniTool)
