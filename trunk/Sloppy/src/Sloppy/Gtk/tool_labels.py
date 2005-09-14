


try:
    import pygtk
    pygtk.require('2.0')
except ImportError:
    pass


import gtk
import uihelper

from Sloppy.Lib import Signals
from dock import *


class LayerTool(gtk.VBox):

    def __init__(self, project):
        gtk.VBox.__init__(self)
        self.project = project


class LabelsTool(LayerTool):

    def __init__(self, project):
        LayerTool.__init__(self, project)
        self.layer = None

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

        btnbox = uihelper.construct_buttonbox(buttons)
        btnbox.show()        

        # put everything together
        self.pack_start(treeview,True,True)
        self.pack_end(btnbox, False, True)        

        # save variables for reference and update view
        self.treeview = treeview        
        self.update()



        
    def set_layer(self, layer):
        if layer == self.layer:
            return
        
        self.layer = layer
        self.update()


    def update(self):

        if self.layer is None:
            self.treeview.set_sensitive(False)
            return
        self.treeview.set_sensitive(True)


        # check_in
        model = self.treeview.get_model()        
        model.clear()
        for label in self.layer.labels:
            print ":added ", label
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
from dock import *

def test():
    win = gtk.Window()
    win.connect("destroy", gtk.main_quit)
    win.set_size_request(320,200)

    const.set_path(Sloppy.__path__[0])
    filename = const.internal_path(const.PATH_EXAMPLE, 'example.spj')
    app = application.GtkApplication(filename)
    plot = app.project.get_plot(0)

    l = plot.layers[0]
    l.labels.append(objects.TextLabel(text='x', x=0.2, y=0.3, halign=1))

    lt = LabelsTool(app.project)
    lt.set_layer(l)
    lt.show()  

    lt2 = LabelsTool(app.project)
    lt2.set_layer(l)
    lt2.show()
    
    dockable = Dockable("Label", gtk.STOCK_EDIT)
    dockable.add(lt)
    dockable.show()

    dockable2 = Dockable("Label2", gtk.STOCK_EDIT)
    dockable2.add(lt2)
    dockable2.show()

    dockbook = Dockbook()
    dockbook.add(dockable)
    dockbook.add(dockable2)    
    dockbook.show()

    dock = Dock()
    dock.show()
    dock.add_book(dockbook)
    win.add(dock)
    
    win.show()
    gtk.main()


if __name__ == "__main__":
    test()
