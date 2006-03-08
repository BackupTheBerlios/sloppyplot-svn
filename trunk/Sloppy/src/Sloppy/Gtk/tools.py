# This file is part of SloppyPlot, a scientific plotting tool.
# Copyright (C) 2005 Niklas Volbers
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# $HeadURL: svn+ssh://svn.berlios.de/svnroot/repos/sloppyplot/trunk/Sloppy/src/Sloppy/Gtk/dock.py $
# $Id: dock.py 137 2005-09-18 22:07:32Z niklasv $

import gtk

from Sloppy.Base.objects import SPObject
from Sloppy.Base.backend import Backend
from Sloppy.Base import uwrap, error, globals
from Sloppy.Lib.Check import Instance
from Sloppy.Lib.Undo import ulist, UndoList
from Sloppy.Lib.ElementTree.ElementTree import Element, SubElement
from Sloppy.Gtk import uihelper, dock, options_dialog


import logging
logger = logging.getLogger('Gtk.tools')

#------------------------------------------------------------------------------
# Toolbox
#

class Toolbox(gtk.Window, SPObject):

    """ The Toolbox holds a dock with a number of Tools.

    Each Tool refers to a backend and the Toolbox has the task to set
    these two values for all of its tools.

    The Toolbox provides a combobox, so that the user may switch the
    active backend.
    
    @ivar project: project.
    @ivar backend: currently active backend as displayed in the Toolbox combo.    
    """

    active_backend = Instance(Backend)
    

    def __init__(self, project=None):
        SPObject.__init__(self)
        gtk.Window.__init__(self)


        self.project = project or -1
        self.project_cblist = []
        self.backend_cblist = []
        
        #
        # create gui
        #

        # create combobox
        model = gtk.ListStore(object, str) # object := Backend, Plot-Title
        combobox = gtk.ComboBox(model)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 1)

        def changed_cb(entry):
            backend = uihelper.get_active_combobox_item(entry)
            self.set_backend(backend)
        combobox.connect('changed', changed_cb)
        combobox.show()

        self.combobox = combobox

        # create dock
        self.dock = dock.Dock()    

        # stuff combo and dock together
        vbox = gtk.VBox()
        vbox.pack_start(self.combobox,False,True)
        vbox.pack_end(self.dock,True,True)
        self.add(vbox)
        self.vbox = vbox

        # We add a handler to skip delete-events, i.e. if the
        # user clicks on the close button of the toolbox, then
        # it is only hidden.
        def _cb_delete_event(widget, *args):
            self.hide()
            return True # don't continue deletion
        self.connect('delete_event', _cb_delete_event)

        # on hide => remember position
        # on show => reset position
        #self.position_x, self.position_y = 0,0
        #def on_hide(widget, *args):
        #    print "ON HIDE", self.get_position()
        #    widget.position_x, widget.position_y = widget.get_position()
        #def on_show(widget, *args):
        #    print "ON SHOW"
        #    widget.move(widget.position_x, widget.position_y)
        #self.connect('hide', on_hide)
        #self.connect('show', on_show)

        ######
            
        self.set_project(project)

        # move window to top right        
        # TODO: From my understanding, the following code should be
        #  self.set_gravity(gtk.gdk.GRAVITY_NORTH_EAST)
        #  self.move(gtk.gdk.screen_width(), 0)
        # However, at least with metacity (gnome) this does not work.    
        width, height = self.get_size()
        self.set_gravity(gtk.gdk.GRAVITY_NORTH_EAST)
        self.move(gtk.gdk.screen_width() - width, 0)


        self.vbox.show_all()
                      

    def set_project(self, project):
        if project == self.project:
            return

        for cb in self.project_cblist:
            cb.disconnect()
        self.project_cblist = []

        if project is not None:
            cb1 = project.sig_connect('update::backends', self.on_update_backends)
            cb2 = project.sig_connect('update::active_backend', lambda sender, value: self.set_backend(value))                    
            self.project_cblist.extend([cb1,cb2])

        self.project = project
        self.update_combobox()
        

    def set_backend(self, backend):
        """ Set the backend to the new value. """
        if self.active_backend != backend:
            for cb in self.backend_cblist:
                cb.disconnect()
            self.backend_cblist = []

            self.active_backend = backend
            
            # Adjust the active index of the combobox so that the new
            # backend is displayed.
            if self.active_backend is None:
                index = -1
            else:
                model = self.combobox.get_model()
                index = self.project.backends.index(backend)
            self.combobox.set_active(index)
                              

    
    def update_combobox(self):
        """
        Fill the combobox with all available matplotlib backends.
        This method might change the current backend, e.g. if the former
        current backend no longer exists in the list.
        """

        model = self.combobox.get_model()

        # fill model with Backend objects and their keys
        model.clear()
        if self.project is not None:
            for backend in self.project.find_backends(key='matplotlib'):
                model.append((backend, backend.plot.key))
            self.combobox.set_sensitive(True)
            
            # make current Backend the active one
            try:
                index = self.project.backends.index(self.active_backend)
                self.combobox.set_active(index)
            except ValueError:
                self.combobox.set_active(-1)
            
        else:
            self.combobox.set_sensitive(False)

    def on_update_backends(self, sender, updateinfo):
        self.update_combobox()




        
#------------------------------------------------------------------------------
# Tool and derived classes
#


class Tool(dock.Dockable):

    """ Dockable base class for any tool that edits part of a Plot. """
        
    def __init__(self, toolbox):
        dock.Dockable.__init__(self)
        self.toolbox = None
        self.toolbox_cb = None
        self.backend = None        
        self.init()
        self.set_toolbox(toolbox)

    def set_toolbox(self, toolbox):
        if self.toolbox is not None:
            self.toolbox.sig_disconnect('update::active_backend', self.on_update_active_backend)        
        toolbox.sig_connect('update::active_backend', self.on_update_active_backend)
        self.toolbox = toolbox        
        
    def init(self): pass
    def on_update_active_backend(self, sender, backend): pass
    

class LayerTool(Tool):

    name = "Layers"
    stock_id = gtk.STOCK_EDIT
    
    def init(self):       
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

    def update_layers(self):
        model = self.treeview.get_model()
        model.clear()
        
        if self.backend is None:
            self.treeview.set_sensitive(False)
        else:
            self.treeview.set_sensitive(True)
            for layer in self.backend.plot.layers:
                model.append((layer,))                   

    def on_update_layers(self, sender, updateinfo):
        self.update_layers()

    def on_update_active_backend(self, sender, backend):
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

#     def set_layer(self, layer):
#         if layer == self.layer:
#             return

#         for cb in self.layer_cblist:
#             cb.disconnect()
#         self.layer_cblist = []

#         self.layer = layer
        
#         if layer is not None:
#             # maybe connect to layer properties: is it visible, position, ...
#             pass
#         self.on_update_active_layer()
                    
    def on_update_active_layer(self, sender, layer):
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


    def on_cursor_changed(self, treeview):
        model, iter = treeview.get_selection().get_selected()
        layer = model.get_value(iter,0)
        if layer is not None:
            self.backend.active_layer = layer


    def on_row_activated(self, treeview, *udata):
        model, iter = treeview.get_selection().get_selected()
        layer = model.get_value(iter, 0)               
        globals.app.edit_layer(self.backend.plot, layer)
        



class LinesTool(Tool):

    name = "Lines"
    stock_id = gtk.STOCK_PROPERTIES


    def init(self):
        self.painter = None

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
        ##treeview.connect("row-activated", self.on_row_activated)
        ##treeview.connect("cursor-changed", self.on_cursor_changed)
        treeview.show()
        self.add(treeview)        
        self.treeview = treeview

    def on_update_active_backend(self, sender, backend):
        if backend == self.backend:
            return

        if self.backend is not None:
            self.backend.sig_disconnect('update::active_layer', self.on_update_active_layer)
        if backend is not None:
            backend.sig_connect('update::active_layer', self.on_update_active_layer)            
        self.backend = backend
        
        self.update_lines()            

    def on_update_active_layer(self, sender, layer):
        print "ACTIVE LAYER HAS CHANGED", layer
        
        try:
            painter = self.backend.get_painter(layer)
        except KeyError:
            painter = None

        if self.painter is not None:
            self.painter.sig_disconnect('update::active_line', self.on_update_active_line)
        if painter is not None:
            painter.sig_connect('update::active_line', self.on_update_active_line)
        self.painter = painter

        print "PAINTER OBJECT IS ", self.painter
        self.update_lines()
        
        
    def update_lines(self):
        model = self.treeview.get_model()
        model.clear()

        if self.painter is None:
            self.treeview.set_sensitive(False)
        else:
            self.treeview.set_sensitive(True)
            for line in self.painter.obj.lines:
                model.append((line,))                   

    def on_update_lines(self, sender, updateinfo):
        self.update_lines()


    def on_update_active_line(self, sender, value):
        print "update active line"
        pass

        
class LabelsTool(Tool):

    name = "Labels"
    stock_id = gtk.STOCK_EDIT



#     def __init__(self):
#         Tool.__init__(self)
#         self.set_size_request(-1,200)
       
#         #
#         # treeview
#         #
#         model = gtk.ListStore(object)
#         treeview = gtk.TreeView(model)
#         treeview.set_headers_visible(False)
        
#         cell = gtk.CellRendererText()
#         column = gtk.TreeViewColumn('label', cell)

#         def render_label(column, cell, model, iter):
#             label = model.get_value(iter, 0)
#             text = "'%s': (%s,%s) %s" % (label.text, label.x, label.y, label.halign)
#             cell.set_property('text', text)
#         column.set_cell_data_func(cell, render_label)
        
#         treeview.append_column(column)
#         treeview.connect("row-activated", (lambda a,b,c:self.on_edit(a)))
#         treeview.show()

#         #
#         # buttons
#         #

#         buttons = [(gtk.STOCK_ADD, self.on_new),
#                    (gtk.STOCK_REMOVE, self.on_remove),
#                    (gtk.STOCK_EDIT, self.on_edit)]

#         btnbox = uihelper.construct_buttonbox(buttons, labels=False)
#         btnbox.show()        

#         # put everything together
#         self.pack_start(treeview,True,True)
#         self.pack_end(btnbox, False, True)        

#         # save variables for reference and update view
#         self.treeview = treeview        
        

#     def set_layer(self, layer):
#         if layer == self.layer:
#             return
        
#         for cb in self.layer_cblist:
#             cb.disconnect()
#         self.layer_cblist = []
#         self.layer = layer
        
#         if layer is not None:
#             self.layer_cblist.append(
#                 self.layer.sig_connect("update::labels", self.on_update_labels)
#                 )
#         self.on_update_layer()
        
#     #------------------------------------------------------------------------------
        
#     def on_update_layer(self):       
#         model = self.treeview.get_model()        
#         model.clear()
            
#         if self.layer is None:
#             self.treeview.set_sensitive(False)
#             return
#         else:
#             self.treeview.set_sensitive(True)            

#         # check_in
#         for label in self.layer.labels:
#             model.append((label,))


#     def edit(self, label):
#         dialog = options_dialog.OptionsDialog(label)
#         try:           
#             response = dialog.run()
#             if response == gtk.RESPONSE_ACCEPT:
#                 dialog.check_out()
#                 return dialog.owner
#             else:
#                 raise error.UserCancel

#         finally:
#             dialog.destroy()
        
#     #----------------------------------------------------------------------
#     # Callbacks
#     #
    
#     def on_edit(self, sender):
#         self.check_layer()
        
#         (model, pathlist) = self.treeview.get_selection().get_selected_rows()
#         if model is None or len(pathlist) == 0:
#             return
#         project = self.get_data('project')
            
#         label = model.get_value( model.get_iter(pathlist[0]), 0)
#         new_label = self.edit(label.copy())
#         print "new label", new_label, label
#         changeset = label.create_changeset(new_label)
        
#         ul = UndoList().describe("Update label.")
#         changeset['undolist'] = ul
#         uwrap.set(label, **changeset)
#         uwrap.emit_last(self.backend.layer, 'update::labels',
#                         updateinfo={'edit' : label},
#                         undolist=ul)
        
#         logger.info("Updateinfo: documentation = %s" % ul.doc)
#         project.journal.append(ul)
#         logger.info("Journal text: %s" % project.journal.undo_text())

#         self.on_update_layer()
                

#     def on_new(self, sender):
#         self.check_layer()
        
#         label = objects.TextLabel(text='newlabel')
#         self.edit(label)
#         project = self.get_data('project')
            
#         ul = UndoList().describe("New label.")
#         ulist.append(self.layer.labels, label, undolist=ul)
#         uwrap.emit_last(self.layer, "update::labels",
#                         updateinfo={'add' : label},
#                         undolist=ul)
#         project.journal.append(ul)


#     def on_remove(self, sender):
#         self.check_layer()
        
#         (model, pathlist) = self.treeview.get_selection().get_selected_rows()
#         if model is None:
#             return
#         project = self.get_data('project')
#         label = model.get_value( model.get_iter(pathlist[0]), 0)

#         ul = UndoList().describe("Remove label.")
#         ulist.remove(self.layer.labels, label, undolist=ul)
#         uwrap.emit_last(self.layer, "update::labels",
#                         updateinfo={'remove' : label},
#                         undolist=ul)
#         project.journal.append(ul)
        
        
#     def on_update_labels(self, layer, updateinfo=None):
#         self.on_update_layer()
