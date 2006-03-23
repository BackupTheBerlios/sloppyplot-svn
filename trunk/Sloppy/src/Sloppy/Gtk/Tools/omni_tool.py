
"""
All-including Tool :-) that lists all objects of a Plot.
"""


import gtk
from Sloppy.Gtk import toolbox, uihelper, checkwidgets
from Sloppy.Base import globals, objects, uwrap, utils
from Sloppy.Lib.Check import List, Dict

import logging
logger = logging.getLogger('Tools.omni_tool')

#------------------------------------------------------------------------------

KLASS_KEYS = {
    objects.Layer: ['title', 'visible', 'grid', 'x', 'y', 'width', 'height'],
    objects.Line: ['label', 'visible', 'style', 'color', 'width', 'marker', 'marker_color', 'marker_size', 'cx', 'cy', 'row_first', 'row_last']

    }


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

        # The edit_cache is a dict where the keys are the classes
        # of the objects that can be edited and the values are
        # tuples (widget, factory), which are the edit widget for this
        # class and the corresponding DisplayFactory object to make 
        # the connection to actual objects. The factory may be None.
        self.edit_cache = {}

        # The currently edited object. Use edit_cache[self.obj.__class__]
        # to get the currently active widget and its factory
        self.obj = None

        # A simple informative label if None is edited.
        self.add_to_cache(None, gtk.Label("--None--"), None)
        self.edit(None)

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
            self.add_list(None, backend.plot, 'layers')

        self.treeview.expand_all()
                
        self.backend = backend


    def add_list(self, parent_node, obj, listkey):
        """ Add items of a List attribute to the model as subnode. """
        model = self.treeview.get_model()
        for item in obj.get(listkey):
            node = model.append(parent_node, (item,))
            # how do we figure out which are the subnodes ?
            # iterate over all checks of the list object,
            for key, check in item._checks.iteritems():
                if isinstance(check, List):
                    self.add_list(node, item, key)
            

    def edit(self, obj):
        logger.debug("%d edit widgets in cache" % len(self.edit_cache))
        
        # 
        if self.edit_cache.has_key(obj.__class__) is False:
            # create factory
            factory = checkwidgets.DisplayFactory(obj)
            try:
                keys = KLASS_KEYS[obj.__class__]
            except KeyError:
                keys = [key for key, check in obj._checks.iteritems() if not isinstance(check, (List,Dict))]                
            factory.add_keys(keys)

            # create widget and add it to the edit area
            tbl = factory.create_table()
            widget = uihelper.add_scrollbars(tbl, viewport=True)
            self.vbox.add(widget)

            # set up undo hooks (needs to be after creation of table, because
            # otherwise there are no displays!)
            for display in factory.displays.itervalues():
                display.set_value = self.set_attribute_value

            self.add_to_cache(obj, widget, factory)           

        # hide last active widget
        if self.edit_cache.has_key(self.obj.__class__):
            widget, factory = self.edit_cache[self.obj.__class__]
            if factory is not None:
                factory.connect(None)
            widget.hide()

        # show new widget        
        widget, factory = self.edit_cache[obj.__class__]
        if factory is not None:
            factory.connect(obj)            
        widget.show_all()
        self.obj = obj        


    def add_to_cache(self, klass, widget, factory):
        """ Add the given widget and factory to the edit cache.
        The given 'klass', which acts as key for the edit cache,
        is automatically converted to a class, if it is an object
        instance. The 'factory' may be None if the edit widget
        is not created by the checkwidgets facility.
        """
        klass = utils.as_class(klass)
        self.edit_cache[klass] = (widget, factory)
        

    def on_cursor_changed(self, sender):
        # if the cursor changes, then we need to refresh
        # the table with the checkwidgets.
        global KLASS_KEYS

        # retrieve selected object
        model, iter = self.treeview.get_selection().get_selected()
        obj = model.get_value(iter,0)

        if obj == self.obj:
            return
                                                
        self.edit(obj)


    def set_attribute_value(self, obj, key, value):
        print
        print "UNDO HOOK"
        print
        # this is used as a hook for undo
        uwrap.set(obj, key, value, undolist=globals.app.project.journal)
        
#------------------------------------------------------------------------------
toolbox.register_tool(OmniTool)
