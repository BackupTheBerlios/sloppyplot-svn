
""" The Property Editor allows you to edit any attribute of the Plot
objects on-the-fly. """


import gtk
from Sloppy.Gtk import toolbox, uihelper, checkwidgets
from Sloppy.Base import globals, objects, uwrap, utils
from Sloppy.Lib.Undo import UndoList, ulist
from Sloppy.Lib.Check import List, Dict, Instance

import logging
logger = logging.getLogger('Gtk.Tools.property_editor')
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

       

class PropertyEditor(toolbox.Tool):

    label = "PropertyEditor"
    icon_id = gtk.STOCK_PREFERENCES

    actions = [
        ('PE_DeleteLine', gtk.STOCK_DELETE, 'Delete Line', None, 'Delete', 'action_DeleteLine'),
        ('PE_AddLine', gtk.STOCK_ADD, 'Add Line', None, 'Add', 'action_AddLine')        
        ]


    def __init__(self):
        toolbox.Tool.__init__(self)

        self.depends_on(globals.app, 'active_backend')
        self.popup_info = None
        
        #
        # Treeview
        #
        
        # model (object)
        model = gtk.TreeStore(object, str)

        self.treeview = treeview = gtk.TreeView(model)
        treeview.set_headers_visible(False)
        treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        
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
                try:
                    label = obj.get_description()
                except:
                    for attr in ['label', 'title', 'key']:
                        if hasattr(obj, attr):
                            label = getattr(obj, attr)
                            break
                    else:
                        label = "<%s>" % obj.__class__.__name__                        

            cell.set_property('text', label)
            
        column.set_cell_data_func(cell, render_label)
        treeview.append_column(column)

        treeview.connect("button-press-event", self.on_button_press_event)
        treeview.connect("cursor-changed", self.on_cursor_changed)
        treeview.connect("popup-menu", self.on_popup_menu, 3, 0)
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
        self.on_update_backend(sender, 'backend', sender.active_backend)

        # ui manager
        uimanager = globals.app.window.uimanager        
        uihelper.add_actions(uimanager, "PropertyEditor", self.actions, self)
        uimanager.add_ui_from_string(globals.app.get_uistring('property_editor'))              


    def on_update_backend(self, sender, key, backend):
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

    def on_update_list(self, sender, key, updateinfo):
        logger.debug("on update list: %s, %s, %s" % (sender, key, updateinfo))

        # find the corresponding sender
        model = self.treeview.get_model()

        def find_obj(iter, obj):
            item = model.get_value(iter, 0)
            if item is obj:
                return iter

            child = model.iter_children(iter)
            while child is not None:
                result = find_obj(child, obj)
                if result is not None:
                    return result
                child = model.iter_next(child)

            return None

        iter = find_obj(model.get_iter_first(), sender.get(key))
        if iter is None:
            return # TODO: then maybe disconnect by returning False?

        #
        # Analyze updateinfo
        #

        if updateinfo.has_key('removed'):
            first_index = updateinfo['removed'][0]
            count = updateinfo['removed'][1]
            indices = range(first_index, first_index+count)            
            indices.reverse()
            for index in indices:
                child = model.iter_nth_child(iter, index)
                print "child = ", child
                model.remove(child)

        if updateinfo.has_key('added'):
            index = updateinfo['added'][0] - 1
            new_items = updateinfo['added'][2]
            sibling = model.iter_nth_child(iter, index)
            for item in new_items:
                print "iter, sibling =" , iter, sibling
                sibling = model.insert_after(iter, sibling, (item, None))

        if updateinfo.has_key('reordered'):
            raise RuntimeError("Reordering of lists is too complicated for me")          

        

    
            
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
                    obj.sig_connect('update::%s'%key, self.on_update_list)
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
        model, pathlist = self.treeview.get_selection().get_selected_rows()

        # If we have multiple objects selected, then we currently gray
        # out the displays. The goal is an implementation where fields
        # common to all controls can be set, e.g. if you have three lines
        # selected, then you should be able to set the widht to 3.0 for
        # all of the lines.
        if len(pathlist) == 0:
            obj = None
        elif len(pathlist) == 1:
            obj = model.get_value(model.get_iter(pathlist[0]), 0)
        else:
            obj = None

        def set_sensitive(sensitive):
            child2 = self.paned.get_child2()
            if child2 is not None:
                child2.set_sensitive(sensitive)

        if isinstance(obj, objects.SPObject):            
            #if obj == self.obj:
            #    return                                                
            self.edit(obj)

        set_sensitive(isinstance(obj, objects.SPObject))

    def on_button_press_event(self, widget, event):
        """
          RMB: Display popup menu.
          LMB, double-click: expand/collapse item.
        """
      
        # LMB and double click -> expand/collapse item
        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            try:
                path, col, cellx, celly = widget.get_path_at_pos(int(event.x), int(event.y))
            except TypeError:
                return False # double-click on empty space causes no action
            else:
                if widget.row_expanded(path) is False:
                    widget.expand_row(path, open_all=False)
                    widget.queue_draw()
                else:
                    widget.collapse_row(path)
                    widget.queue_draw()
                return True

        
        # RMB has been clicked -> popup menu
        if event.button == 3:
            # Different cases are possible
            # - The user has not yet selected anything.
            #   In this case, we select the row on which the cursor
            #   resides.
            # - The user has made a selection.
            #   In this case, we will leave it as it is.

            # get mouse coords and corresponding path
            try:
                path, col, cellx, celly = widget.get_path_at_pos(int(event.x), int(event.y))
            except TypeError:
                # => user clicked on empty space -> offer creation of objects
                pass                
            else:
                # If user clicked on a row, then select it.
                selection = widget.get_selection()
                if selection.count_selected_rows() == 0:              
                    widget.grab_focus()
                    widget.set_cursor( path, col, 0)

            return self.on_popup_menu(widget,event.button,event.time)            

        return False

    
    def on_popup_menu(self, widget, button, time):
        " Returns True if a popup has been popped up. "

        self.popup_info = None # holds the model and the pathlist
        uim = globals.app.window.uimanager
        
        # create popup menu according to object type
        model, pathlist = self.treeview.get_selection().get_selected_rows()
        if len(pathlist) == 0:
            popup = None
        elif len(pathlist) == 1:
            # The popup name is (in lowercase) popup_property_editor_xxx,
            # where xxx is either the object's class, e.g. 'line'
            # or 'layer', or in case of List and Dict objects (which
            # have a key given in the treemodel), it is formed from
            # their parent's class and their key, e.g. 'layer_lines'
            # or 'plot_labels'
            path = pathlist[0]
            object, key = model.get(model.get_iter(path), 0, 1)                                    
            if key is None:
                key = object.__class__.__name__
            else:
                parent = model.get_value(model.get_iter(path[:-1]), 0)
                key = "%s_%s" %( parent.__class__.__name__, key)
            key = key.lower()
            popup = uim.get_widget('/popup_property_editor_%s'%key)
            self.popup_info = (model, pathlist)
        else:
            # selection of more than one object is currently not supported.
            popup = None

        if popup is not None:
            popup.popup(None,None,None,button,time)
            return True
        else:
            return False

        
    def find_parent(self, model, path, parent_class):
        """ Find the parent object to the object given by 'path'
        in the treeview, where the parent is an instance of
        'parent_class'. """            
        while 1:
            path = path[:-1]            
            obj = model.get_value(model.get_iter(path), 0)
            if isinstance(obj, objects.Layer):
                return obj
        return None

    def action_DeleteLine(self, action):
        logger.debug("action: DeleteLine")

        model, pathlist = self.popup_info
        for path in pathlist:
            line = model.get_value(model.get_iter(path), 0)            
            layer = self.find_parent(model, path, objects.Layer)

            ul = UndoList("Remove Line")
            ulist.remove(layer.lines, line, undolist=ul)
            globals.app.project.journal.append(ul)            
            
        
    def action_AddLine(self, action):
        logger.debug("action: AddLine")

        model, pathlist = self.popup_info
        for path in pathlist:
            obj, key = model.get(model.get_iter(path), 0, 1)
            layer = self.find_parent(model, path, objects.Layer)            
            if isinstance(obj, objects.Line):
                index = layer.lines.index(obj)+1
                line = objects.Line(label="fresh line", color="red",
                                source=obj.source, cx=obj.cy, cy=obj.cx)                
            else:
                index = 0
                line = objects.Line(label="fresh line", color="red")
                

            ul = UndoList("Insert Line")
            ulist.insert(layer.lines, index, line, undolist=ul)
            globals.app.project.journal.append(ul)            
                
        
#------------------------------------------------------------------------------
toolbox.register_tool(PropertyEditor)
