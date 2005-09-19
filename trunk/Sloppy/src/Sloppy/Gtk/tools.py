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


import uihelper
from Sloppy.Lib import Signals
from dock import *



#------------------------------------------------------------------------------
# ToolWindow
#

class ToolWindow(gtk.Window):

    """
    A window containing a combo box to indicate and select the active plot,
    along with a Dock that holds the tools to manipulate the plot or its
    active layer.

    @ivar project: project.
    @ivar plot: currently active plot as displayed in the ToolWindow combo.
    """

    def __init__(self, project):
        gtk.Window.__init__(self)
       
        self.plot = None
        self.project = -1 

        #
        # create gui
        #
        model = gtk.ListStore(object, str) # object := Plot, Plot.title
        combobox = gtk.ComboBox(model)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 1)

        def changed_cb(entry):
            index = entry.get_active()
            if index == -1:                
                self.set_plot(None)
            else:
                model = entry.get_model()
                iter = model.get_iter((index,))
                plot = model.get_value(iter, 0)
                self.set_plot(plot)                
        combobox.connect('changed', changed_cb)
        combobox.show()

        self.combobox = combobox

        self.dock = dock = Dock()
        dock.show()
        
        vbox = gtk.VBox()
        vbox.pack_start(combobox,False,True)
        vbox.pack_end(dock,True,True)
        vbox.show()
        self.add(vbox)

        lt = LabelsTool(project)
        lt.show()

        dock.add(lt)

        self.set_project(project)


                      

    def set_project(self, project):
        if project == self.project:
            return

        if project is not None:
            # update combobox again if plots change
            Signals.connect(project.plots, 'notify',
                            (lambda sender: self.update_combobox()))
            Signals.connect(project.app, 'notify::current_plot',
                            (lambda sender, plot: self.set_plot(plot)))

        self.project = project
        self.update_combobox()
        self.update_plot()


    def set_plot(self, plot):
        if self.plot != plot:
            self.plot = plot
            self.update_plot()

            if self.plot is None:
                index = -1
            else:
                model = self.combobox.get_model()
                index = self.project.plots.index(plot)
            self.combobox.set_active(index)

    def update_plot(self):
        if self.plot is not None and \
               (self.plot.current_layer is None and len(self.plot.layers) > 0):
            self.plot.current_layer = self.plot.layers[0]
        self.dock.foreach((lambda tool: tool.set_plot(self.plot)))

    def update_combobox(self):
        model = self.combobox.get_model()

        # remember last selected Plot in combobox
        index = self.combobox.get_active()
        if index == -1:
            old_object = None
        else:
            iter = model.get_iter((index,))
            old_object = model.get_value(iter,0)

        # fill model with Plot objects and their keys
        model.clear()
        if self.project is not None:
            for plot in self.project.plots:
                model.append((plot, plot.key))
            self.combobox.set_sensitive(True)
            
            # reset old Plot object
            try:
                index = self.project.plots.index(old_object)
                self.combobox.set_active(index)                
            except ValueError:
                self.combobox.set_active(-1)
            
        else:
            self.combobox.set_sensitive(False)

            



        
#------------------------------------------------------------------------------
# Tool and derived classes
#

class Tool(Dockable):

    """
    Dockable base class for any tool that edits part of a Plot.
    """
    
    
    def __init__(self, project, label, stock_id):
        Dockable.__init__(self, label, stock_id)

        self.project = project
        self.layer = -1
        self.plot = -1


    def set_plot(self, plot):
        if plot == self.plot:
            return        
        self.plot = plot

        if plot is not None:
            self.layer = plot.current_layer
            Signals.connect(plot, "notify::current_layer", self.on_notify_layer)
        else:
            self.layer = None

        self.set_sensitive(plot is not None)

        # TODO: connect properly on change of plot
        self.update_plot()
       

    def update_plot(self):
        self.update_layer()

    def update_layer(self):
        pass

    

class LayerTool(Tool):

    def __init__(self, project):
        Tool.__init__(self, project, "Layers", gtk.STOCK_EDIT)
       
        # model: (object) = (layer object)
        model = gtk.ListStore(object)        
        treeview = gtk.TreeView(model)
        treeview.set_headers_visible(False)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn('label', cell)

        def render_label(column, cell, model, iter):
            layer = model.get_value(iter, 0)
            cell.set_property('text', layer.title)
        column.set_cell_data_func(cell, render_label)
        
        treeview.append_column(column)
        #treeview.connect("row-activated", (lambda a,b,c:self.on_edit(a)))
        treeview.show()
        self.add(treeview)
        
        # remember for further reference
        self.treeview = treeview


    def on_notify_layer(self, sender, layer):
        print "Change combo to ..."
        # mark active layer

        
    def update_plot(self):
        if self.plot is None:
            self.treeview.set_sensitive(False)
            return
        self.treeview.set_sensitive(True)

        # check_in
        model = self.treeview.get_model()
        model.clear()
        for layer in self.plot.layers:
            model.append((layer,))

        # mark active layer

            
        
class LabelsTool(Tool):

    def __init__(self, project):
        Tool.__init__(self, project, "Labels", gtk.STOCK_EDIT)
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
                   (None, gtk.STOCK_REMOVE, (lambda sender: self.on_remove())),
                   (None, gtk.STOCK_NEW, self.on_new)]

        btnbox = uihelper.construct_buttonbox(buttons, show_stock_labels=False)
        btnbox.show()        

        # put everything together
        self.pack_start(treeview,True,True)
        self.pack_end(btnbox, False, True)        

        # save variables for reference and update view
        self.treeview = treeview        
        #self.update_plot()
        

    #------------------------------------------------------------------------------
        
    def update_layer(self):
        if self.layer is None:
            self.treeview.set_sensitive(False)
            return
        else:
            self.treeview.set_sensitive(True)            

        # check_in
        model = self.treeview.get_model()        
        model.clear()
        for label in self.layer.labels:
            model.append((label,))


    def edit(self, label):
        dialog = ModifyHasPropsDialog(label)
        try:
            response = dialog.run()
            if response == gtk.RESPONSE_ACCEPT:                
                dialog.check_out()

            Signals.emit(self.project, 'update-sobject', label, self.layer) # add changeset

            def assign_changes(treeview, owner, changeset):
                pass
            
        finally:
            dialog.destroy()
            
    #----------------------------------------------------------------------
    # Callbacks
    #
    
    def on_edit(self, sender):
        (model, pathlist) = self.treeview.get_selection().get_selected_rows()
        if model is None:
            return
        label = model.get_value( model.get_iter(pathlist[0]), 0)
        self.edit(label)
        self.treeview.grab_focus()
                

    def on_new(self, sender):        
        label = objects.TextLabel(text='newlabel')
        self.layer.labels.append(label)
        self.treeview.get_model().append((label,))
        self.edit(label)
        self.treeview.grab_focus()


    def on_notify_layer(self, sender, layer):
        # no change ?        
        if layer == self.layer:
            return
        self.layer = layer
        self.update_layer()

        



import propwidgets
from Sloppy.Lib.Undo import UndoList
class ModifyHasPropsDialog(gtk.Dialog):

    def __init__(self, owner):

        gtk.Dialog.__init__(self, "Edit Properties", None,
                            gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        self.owner = owner
        
        self.pwdict = dict()
        
        pwlist = list()
        keys = owner.get_props().keys()
        for key in keys:
            pw = propwidgets.construct_pw(owner, key)
            self.pwdict[key] = pw
            pwlist.append(pw)

        self.tablewidget = propwidgets.construct_pw_table(pwlist)

        frame = gtk.Frame('Edit')
        frame.add(self.tablewidget)
        frame.show()

        self.vbox.pack_start(frame, False, True)
        self.tablewidget.show()
                    
        
    def check_in(self):
        for pw in self.pwdict.itervalues():
            pw.check_in()

    def check_out(self, undolist=[]):
        ul = UndoList().describe("Set Properties")
        for pw in self.pwdict.itervalues():
            pw.check_out(undolist=ul)
        undolist.append(ul)            

    def run(self):
        self.check_in()
        return gtk.Dialog.run(self)

    

#------------------------------------------------------------------------------
import Sloppy
from Sloppy.Base import const, objects
import application


def test2():
    const.set_path(Sloppy.__path__[0])
    filename = const.internal_path(const.PATH_EXAMPLE, 'example.spj')
    app = application.GtkApplication(filename)
    plot = app.project.get_plot(0)

    win = ToolWindow(app.project)
    win.connect("destroy", gtk.main_quit)

    win.show()
    gtk.main()

if __name__ == "__main__":
    test2()
