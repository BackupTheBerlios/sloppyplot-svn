
"""
All-including Tool :-) that lists all objects of a Plot.
"""


import gtk
from Sloppy.Gtk import toolbox, uihelper, checkwidgets
from Sloppy.Base import globals, objects, uwrap, utils
from Sloppy.Lib.Check import List, Dict, Instance

import logging
logger = logging.getLogger('Tools.omni_tool')
#------------------------------------------------------------------------------



KLASS_KEYS = {
    objects.Plot: ['key', 'title', 'comment'],
    objects.Layer: ['title', 'visible', 'grid', 'x', 'y', 'width', 'height'],
    objects.Line: ['label', 'visible', 'style', 'color', 'width', 'marker', 'marker_color', 'marker_size', 'cx', 'cy', 'row_first', 'row_last'],
    objects.Axis: ['label', 'start', 'end', 'scale']
    }

KLASS_DESCR = {
    objects.Plot:
      {'nodes': ['layers'],
       'attrs': ['key', 'title', 'comment'],
       'label': 'Plot %(key)s'},
    objects.Layer:
      {'nodes': ['axes', 'lines', 'legend'],
       'attrs': ['title', 'visible', 'grid', 'x', 'y', 'width', 'height'],
       'label': 'Layer'},
    objects.Line:
      {'nodes': [],
       'attrs': ['label', 'visible', 'style', 'color', 'width', 'marker', 'marker_color', 'marker_size', 'cx', 'cy'],
       'label': 'Line %(key)s'},
    objects.Axis:
      {'nodes': [],
       'attrs': ['label', 'start', 'end', 'scale'],
       'label': '%(key)s-Axis'},
    objects.Legend:
      {'nodes': [],
       'attrs': ['visible', 'position', 'x', 'y', 'border'],
       'label': 'Legend'}
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
        model = gtk.TreeStore(object, str)

        self.treeview = treeview = gtk.TreeView(model)
        treeview.set_headers_visible(False)

        column = gtk.TreeViewColumn('label')

        cell = gtk.CellRendererPixbuf()                        
        column.pack_start(cell,expand=False)
        def render_icon(column, cell, model, iter):
            obj = model.get_value(iter, 0)
            key = model.get_value(iter, 1)
            if key is not None:
                stock_id = 'sloppy-%s'%key.lower()
            else:
                stock_id = 'sloppy-%s'%obj.__class__.__name__.lower()
            cell.set_property('stock_id', stock_id)        
        column.set_cell_data_func(cell, render_icon)
        treeview.append_column(column)
        
        cell = gtk.CellRendererText()
        column.pack_start(cell)
        def render_label(column, cell, model, iter):
            obj = model.get_value(iter, 0)
            key = model.get_value(iter, 1)

            if key is None:
                for attr in ['label', 'title', 'key']:
                    if hasattr(obj, attr):
                        key = getattr(obj, attr)

            label = key
            cell.set_property('text', label)

            
            label = None
            if key is not None:
                label = key
            else:
                for attr in ['label', 'title', 'key']:
                    if hasattr(obj, attr):
                        label = getattr(obj, attr)
            if label is None:
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

        #
        # Both the treeview and the table are stuffed into
        # a vbox; but there is no no table to begin with.
        # It is created in the on_cursor_changed event.
        #
        self.paned = gtk.VPaned()
        self.paned.pack1(uihelper.add_scrollbars(treeview),True,True)
        self.add(self.paned)
               
        #self.vbox = vbox = gtk.VBox()
        #vbox.add(uihelper.add_scrollbars(treeview))
        #self.add(vbox)
        
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
            self.refresh(backend.plot)

        self.treeview.expand_all()
                
        self.backend = backend

    def refresh(self, obj):
        model = self.treeview.get_model()
            
                                
        def add_list(obj, parent_iter=None, key=None):
            iter = model.append(parent_iter, (obj,key))
            for item in obj:
                if isinstance(item, objects.SPObject):
                    add_spobject(item, iter, key=None)

        def add_dict(obj, parent_iter=None, key=None):
            iter = model.append(parent_iter, (obj,key))
            for subkey, item in obj.iteritems():
                if isinstance(item, objects.SPObject):
                    add_spobject(item, iter, key=subkey)

        def add_spobject(obj, parent_iter=None, key=None):              
            iter = model.append(parent_iter, (obj,key))
            
            try:
                nodes = KLASS_DESCR[obj.__class__]['nodes']
            except KeyError:
                nodes = obj._checks.keys()
                
            for key in nodes:
                check = obj._checks[key]
                if isinstance(check, List):
                    add_list(obj.get(key), iter, key)
                elif isinstance(check, Dict):
                    add_dict(obj.get(key), iter, key)
                elif isinstance(check, Instance):
                    add_spobject(obj.get(key), iter, key)

        add_spobject(obj, key=None)
        
            

    def edit(self, obj):

        # create new widget (unless we don't have a SPObject, e.g. a List)
        if self.edit_cache.has_key(obj.__class__) is False:
            # create factory
            factory = checkwidgets.DisplayFactory(obj)
            try:
                #keys = KLASS_KEYS[obj.__class__]
                keys = KLASS_DESCR[obj.__class__]['attrs']
            except KeyError:
                keys = [key for key, check in obj._checks.iteritems() if not isinstance(check, (List,Dict))]                
            factory.add_keys(keys)

            # create widget and add it to the edit area
            tbl = factory.create_table()
            widget = uihelper.add_scrollbars(tbl, viewport=True)
            self.paned.pack2(widget)

            # set up undo hooks (needs to be after creation of table, because
            # otherwise there are no displays!)
            undo_hook = lambda obj, key, value: uwrap.set(obj, key, value, undolist=globals.app.project.journal)
            for display in factory.displays.itervalues():
                display.set_value = undo_hook

            self.add_to_cache(obj, widget, factory)           

        # show widget
        widget, factory = self.edit_cache[obj.__class__]
        if factory is not None:
            factory.connect(obj)
        child = self.paned.get_child2()
        if child is not None and child is not widget:
            self.paned.remove(child)
            self.paned.pack2(widget)
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


        def set_sensitive(sensitive):
            child2 = self.paned.get_child2()
            if child2 is not None:
                child2.set_sensitive(sensitive)

        if isinstance(obj, objects.SPObject):            
            #if obj == self.obj:
            #    return                                                
            self.edit(obj)

        set_sensitive(isinstance(obj, objects.SPObject))

                

        
        
#------------------------------------------------------------------------------
toolbox.register_tool(OmniTool)
