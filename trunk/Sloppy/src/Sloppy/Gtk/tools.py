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


try:
    import pygtk
    pygtk.require('2.0')
except ImportError:
    pass

import gtk


from Sloppy.Base import uwrap, error

from Sloppy.Lib.Undo import ulist, UndoList
from Sloppy.Lib.ElementTree.ElementTree import Element, SubElement
from Sloppy.Lib.Props.Gtk import pwconnect
from Sloppy.Lib.Props import pBoolean


import uihelper
from dock import *
from options_dialog import OptionsDialog


#------------------------------------------------------------------------------
import logging
logger = logging.getLogger('Gtk.tools')




#------------------------------------------------------------------------------
# Toolbox
#

class Toolbox(gtk.Window):

    """ The Toolbox holds a dock with a number of Tools.

    Since each Tool refers to a backend and to the backend's active
    layer, the Toolbox has the task to set these two values for all
    of its tools.

    The Toolbox also provides a combobox, so that the user may switch
    the active backend.  The active layer of this backend can not be
    manipulated by the Toolbox.  However, the Toolbox catches any
    change of this active layer and sends it to its tools.
    
    @ivar project: project.
    @ivar backend: currently active backend as displayed in the Toolbox combo.
    @ivar layer: currently active layer.
    """

    def __init__(self, app, project=None):
        gtk.Window.__init__(self)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_UTILITY)
        
        self.app = app

        self.project = project or -1
        self.project_cblist = []
        self.backend_cblist = []

        self.backend = None
        self.layer = None
        
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
            index = entry.get_active()
            if index == -1:                
                self.set_backend(None)
            else:
                model = entry.get_model()
                iter = model.get_iter((index,))
                backend = model.get_value(iter, 0)
                self.set_backend(backend)
        combobox.connect('changed', changed_cb)
        combobox.show()

        self.combobox = combobox

        # create dock
        self.dock = dock = Dock()
        dock.show()

        lt = LayerTool()
        lt.show()
        book = Dockbook()
        book.add(lt)
        book.show()
        dock.add(book)
        
        lt = LabelsTool()
        lt.show()
        book = Dockbook()
        book.add(lt)
        book.show()
        dock.add(book)

        # stuff combo and dock together
        vbox = gtk.VBox()
        vbox.pack_start(combobox,False,True)
        vbox.pack_end(dock,True,True)
        vbox.show()
        self.add(vbox)

        # We add a handler to skip delete-events, i.e. if the
        # user clicks on the close button of his window, the window
        # will only be hidden.        
        def _cb_delete_event(widget, *args):
            self.hide()
            return True # don't continue deletion
        self.connect('delete_event', _cb_delete_event)

        self.set_project(project)

        # for config file
        self.app.sig_connect("write-config", self.write_toolwindow_config)

        # TODO: read config data
        eWindow = app.eConfig.find('Toolbox')
        if eWindow is not None:
            pass

        # move window to top right
        
        # TODO: From my understanding, the following code should be
        #  self.set_gravity(gtk.gdk.GRAVITY_NORTH_EAST)
        #  self.move(gtk.gdk.screen_width(), 0)
        # However, at least with metacity (gnome) this does not work.    
        width, height = self.get_size()
        self.set_gravity(gtk.gdk.GRAVITY_NORTH_EAST)
        self.move(gtk.gdk.screen_width() - width, 0)

                      

    def set_project(self, project):
        if project == self.project:
            return

        for cb in self.project_cblist:
            cb.disconnect()
        self.project_cblist = []

        if project is not None:
            # update combobox again if plots change
            self.project_cblist.extend(
                [project.sig_connect('notify::backends',
                                 (lambda sender: self.update_combobox())),
                 #Signals.connect(project.app, 'backend-changed',
                 #                (lambda sender, backend: self.set_backend(backend)))
                 ])

        self.dock.foreach((lambda tool: tool.set_data('project', project)))
        
        self.project = project
        self.update_combobox()
        


    def set_backend(self, backend):
        """ Set the backend to the new value (implies setting a new layer). """
        if self.backend != backend:
            for cb in self.backend_cblist:
                cb.disconnect()
            self.backend_cblist = []

            self.backend = backend

            if self.backend is not None:
                # If no active layer is set, even though there are layers,
                # then we should set the first layer as being active.
                if self.backend.layer is None and len(self.backend.plot.layers) > 0:
                    self.backend.layer = self.backend.plot.layers[0]
                self.layer = self.backend.layer

                # make sure we keep track of changes to the active layer
                self.backend_cblist.append(
                    backend.sig_connect("notify::layer",
                                    (lambda sender, layer: self.set_layer(layer)))
                    )
            else:
                self.layer = None

            # propagate the new backend to all tools
            self.dock.foreach((lambda tool: tool.set_backend(self.backend)))
            
            # Adjust the active index of the combobox so that the new
            # backend is displayed.
            if self.backend is None:
                index = -1
            else:
                model = self.combobox.get_model()
                index = self.project.backends.index(backend)
            self.combobox.set_active(index)
            

    def set_layer(self, layer):
        """ Set the layer to the new value (implies keeping the old backend). """
        if layer != self.layer:
            self.layer = layer

            # propagate the new layer to all tools
            self.dock.foreach(lambda tool: tool.set_layer(layer))

                              
        
    def update_combobox(self):
        """
        Fill the combobox with all available matplotlib backends.
        This method might change the current backend, e.g. if the former
        current backend does no longer exist in the list.
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
                index = self.project.backends.index(self.backend)
                self.combobox.set_active(index)
            except ValueError:
                self.combobox.set_active(-1)
            
        else:
            self.combobox.set_sensitive(False)

            
    def write_toolwindow_config(self, app):
        eToolbox = app.eConfig.find("Toolbox")
        if eToolbox is None:
            eToolbox = SubElement(app.eConfig, "Toolbox")
        else:
            eToolbox.clear()

        # get information about dockables/dockbooks
        eDock = config.SubElement(eToolbox, "Dock")
        for dockbook in self.dock.dockbooks:
            eDockbook = config.SubElement(eDock, "Dockbook")        
            for dockable in dockbook.get_children():
                eDockable = config.SubElement(eDockbook, "Dockable")
                width, height = dockable.size_request()            
                eDockable.attrib['width'] = str(width)
                eDockable.attrib['height'] = str(height)
                eDockable.text = dockable.__class__.__name__



        
#------------------------------------------------------------------------------
# Tool and derived classes
#

class Tool(Dockable):

    """
    Dockable base class for any tool that edits part of a Plot.

    The project should be set by the top window using

        >>> tool.set_data('project', project)        
    """
    
    
    def __init__(self, label, stock_id):
        Dockable.__init__(self, label, stock_id)

        self.backend = -1
        self.layer = -1
        self.backend_cblist = []
        self.layer_cblist = []

    def set_backend(self, backend):
        if backend == self.backend:
            return

        for cb in self.backend_cblist:
            cb.disconnect()
        self.backend_cblist = []

        self.backend = backend
        self.update_backend()
        
        if backend is not None:            
            self.set_layer(backend.layer)
        else:
            self.set_layer(None)            

    def update_backend(self):
        pass

    def set_layer(self, layer):
        pass

    def update_layer(self):
        pass
    
    

class LayerTool(Tool):

    
    def __init__(self):
        Tool.__init__(self, "Layers", gtk.STOCK_EDIT)
        
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
        #treeview.connect("row-activated", (lambda a,b,c:self.on_edit(a)))
        treeview.connect("cursor-changed", self.on_cursor_changed)
        treeview.show()
        self.add(treeview)        
        
        # remember for further reference
        self.treeview = treeview



    def set_layer(self, layer):
        if layer == self.layer:
            return

        for cb in self.layer_cblist:
            cb.disconnect()
        self.layer_cblist = []

        self.layer = layer
        
        if layer is not None:
            # maybe connect to layer properties: is it visible, position, ...
            pass
        self.update_layer()

        
    def update_backend(self):
        if self.backend is None:
            self.treeview.set_sensitive(False)
            return        
        self.treeview.set_sensitive(True)

        # check_in
        model = self.treeview.get_model()
        model.clear()
        for layer in self.backend.plot.layers:
             model.append((layer,))

        # connect to change of current layer
        self.backend_cblist.append(
            self.backend.sig_connect("notify::layer",
                            (lambda sender, layer: self.set_layer(layer)))
            )
        
             
    def update_layer(self):
        # mark active layer
        model = self.treeview.get_model()
        iter = model.get_iter_first()
        while iter is not None:
            value = model.get_value(iter, 0)
            if value == self.layer:
                self.treeview.get_selection().select_iter(iter)
                break
            iter = model.iter_next(iter)
        else:
            self.treeview.get_selection().unselect_all()

    def on_cursor_changed(self, treeview):
        model, iter = treeview.get_selection().get_selected()
        layer = model.get_value(iter,0)
        if layer is not None:
            self.backend.layer = layer
        
            
        
class LabelsTool(Tool):

    def __init__(self):
        Tool.__init__(self,"Labels", gtk.STOCK_EDIT)
        self.set_size_request(-1,200)
       
        #
        # treeview
        #
        model = gtk.ListStore(object)
        treeview = gtk.TreeView(model)
        treeview.set_headers_visible(False)
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn('label', cell)

        def render_label(column, cell, model, iter):
            label = model.get_value(iter, 0)
            text = "'%s': (%s,%s) %s" % (label.text, label.x, label.y, label.halign)
            cell.set_property('text', text)
        column.set_cell_data_func(cell, render_label)
        
        treeview.append_column(column)
        treeview.connect("row-activated", (lambda a,b,c:self.on_edit(a)))
        treeview.show()

        #
        # buttons
        #

        buttons = [(None, gtk.STOCK_EDIT, self.on_edit),
                   (None, gtk.STOCK_REMOVE, self.on_remove),
                   (None, gtk.STOCK_NEW, self.on_new)]

        btnbox = uihelper.construct_buttonbox(buttons, show_stock_labels=False)
        btnbox.show()        

        # put everything together
        self.pack_start(treeview,True,True)
        self.pack_end(btnbox, False, True)        

        # save variables for reference and update view
        self.treeview = treeview        
        

    def set_layer(self, layer):
        if layer == self.layer:
            return
        
        for cb in self.layer_cblist:
            cb.disconnect()
        self.layer_cblist = []
        self.layer = layer
        
        if layer is not None:
            self.layer_cblist.append(
                self.layer.sig_connect("notify::labels", self.on_notify_labels)
                )
        self.update_layer()
        
    #------------------------------------------------------------------------------
        
    def update_layer(self):       
        model = self.treeview.get_model()        
        model.clear()
            
        if self.layer is None:
            self.treeview.set_sensitive(False)
            return
        else:
            self.treeview.set_sensitive(True)            

        # check_in
        for label in self.layer.labels:
            model.append((label,))


    def edit(self, label):
        dialog = OptionsDialog(label)
        try:           
            response = dialog.run()
            if response == gtk.RESPONSE_ACCEPT:
                return dialog.check_out()
            else:
                raise error.UserCancel

        finally:
            dialog.destroy()
        
    #----------------------------------------------------------------------
    # Callbacks
    #
    
    def on_edit(self, sender):
        (model, pathlist) = self.treeview.get_selection().get_selected_rows()
        if model is None:
            return
        project = self.get_data('project')
            
        label = model.get_value( model.get_iter(pathlist[0]), 0)
        new_label = self.edit(label.copy())
        changeset = label.create_changeset(new_label)
        
        ul = UndoList().describe("Update label.")
        changeset['undolist'] = ul
        uwrap.set(label, **changeset)
        uwrap.emit_last(self.backend.layer, 'notify::labels',
                        updateinfo={'edit' : label},
                        undolist=ul)
        
        logger.info("Updateinfo: documentation = %s" % ul.doc)
        project.journal.append(ul)
        logger.info("Journal text: %s" % project.journal.undo_text())
                

    def on_new(self, sender):
        label = objects.TextLabel(text='newlabel')
        self.edit(label)
        project = self.get_data('project')
            
        ul = UndoList().describe("New label.")
        ulist.append(self.layer.labels, label, undolist=ul)
        uwrap.emit_last(self.layer, "notify::labels",
                        updateinfo={'add' : label},
                        undolist=ul)
        project.journal.append(ul)


    def on_remove(self, sender):
        (model, pathlist) = self.treeview.get_selection().get_selected_rows()
        if model is None:
            return
        project = self.get_data('project')
        label = model.get_value( model.get_iter(pathlist[0]), 0)

        ul = UndoList().describe("Remove label.")
        ulist.remove(self.layer.labels, label, undolist=ul)
        uwrap.emit_last(self.layer, "notify::labels",
                        updateinfo={'remove' : label},
                        undolist=ul)
        project.journal.append(ul)
        
        
    def on_notify_labels(self, layer, updateinfo=None):
        self.update_layer()
        




    
#------------------------------------------------------------------------------

import Sloppy
from Sloppy.Base import const, objects
import application


def test2():
    const.set_path(Sloppy.__path__[0])
    filename = const.internal_path(const.PATH_EXAMPLE, 'example.spj')
    app = application.GtkApplication(filename)
    plot = app.project.get_plot(0)

    win = Toolbox(app, app.project)
    win.connect("destroy", gtk.main_quit)

    win.show()
    gtk.main()

if __name__ == "__main__":
    test2()
