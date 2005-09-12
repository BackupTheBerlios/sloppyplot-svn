

import gtk
import uihelper


class GenericTool(gtk.VBox):

    def __init__(self):
        gtk.VBox.__init__(self)

    def add_buttons(self, buttons):
        btnbox = uihelper.construct_buttonbox(buttons)
        btnbox.show()        
        self.pack_end(btnbox,False,True)


class LabelsTool(GenericTool):

    def __init__(self):
        
        GenericTool.__init__(self)
        
        self.layer = None

        # construct GUI
        frame = gtk.Frame("Labels")
        frame.show()
        self.add(frame)

        model = gtk.ListStore(object)
        treeview = gtk.TreeView(model)
        treeview.set_headers_visible(False)
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn('label', cell)
        column.set_cell_data_func(cell, self.render_label)
        treeview.append_column(column)
        treeview.show()
        frame.add(treeview)       

        # buttons
        buttons = [(None, gtk.STOCK_EDIT, (lambda sender: self.on_edit())),
                   (None, gtk.STOCK_REMOVE, (lambda sender: self.on_remove())),
                   (None, gtk.STOCK_NEW, (lambda sender: self.on_new()))]
        self.add_buttons(buttons)


        self.treeview = treeview        
        self.update()


    def render_label(self, column, cell, model, iter):
        label = model.get_value(iter, 0)
        text = "'%s': (%f,%f) %s" % (label.text, label.x, label.y, label.align)
        cell.set_property('text', text)
        
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

        model = self.treeview.get_model()

        # check_in
        model.clear()
        for label in self.layer.labels:
            print ":added ", label
            model.append((label,))

    def on_edit(self, sender):
        print "EDIT!"

    

win = gtk.Window()
win.connect("destroy", gtk.main_quit)
win.set_size_request(320,200)

class PseudoLabel:
    def __init__(self, text,x,y,align):
        self.text = text
        self.x, self.y = x,y
        self.align = align
        
class PseudoLayer:
    def __init__(self):
        self.labels = [PseudoLabel('x',0.2,0.3,1)]
        
l = PseudoLayer()

lt = LabelsTool()
lt.set_layer(l)
lt.show()

win.add(lt)

win.show()
gtk.main()
