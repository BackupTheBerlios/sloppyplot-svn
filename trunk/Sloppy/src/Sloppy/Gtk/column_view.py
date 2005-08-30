

from Sloppy.Base.table import Table, setup_test_table

from Sloppy.Lib.Undo import UndoInfo, UndoList
from Sloppy.Base import uwrap

from uihelper import setup_test_window
import gtk


import propwidgets



# stolen from tablewin.py
# need to use this for tablewin.py. It is an improved version.

class ColumnPropertiesDialog(gtk.Dialog):

    def __init__(self, column):

        gtk.Dialog.__init__(self, "Column Properties", None,
                            gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        self.column = column
        
        self.pwdict = dict()
        
        pwlist = list()
        keys = ['key', 'designation', 'label']
        for key in keys:
            pw = propwidgets.construct_pw(column, key)
            self.pwdict[key] = pw
            pwlist.append(pw)

        self.tablewidget = propwidgets.construct_pw_table(pwlist)

        frame = gtk.Frame('Edit Column')
        frame.add(self.tablewidget)
        frame.show()

        self.vbox.pack_start(frame, False, True)
        self.tablewidget.show()
                    
        
    def check_in(self):
        for pw in self.pwdict.itervalues():
            pw.check_in()

    def check_out(self, undolist=[]):
        ul = UndoList().describe("Set Column Properties")
        for pw in self.pwdict.itervalues():
            pw.check_out(undolist=ul)

        #uwrap.emit_last(self.table, 'update-columns', undolist=ul)

        undolist.append(ul)
            

    def run(self):
        self.check_in()
        response = gtk.Dialog.run(self)
        if response == gtk.RESPONSE_ACCEPT:
            self.check_out()
        return response



#------------------------------------------------------------------------------
def insert_column(table, index, column, undolist=[]):
    table.insert(index, column)
    #self.dataset.notify_change()

    ui = UndoInfo(remove_column, table, index).describe("Insert Column")
    undolist.append(ui)

def remove_column(table, index, undolist=[]):
    old_column = table.column(index)
    table.remove_by_index(index)
    #self.dataset.notify_change()

    ui = UndoInfo(insert_column, table, index, old_column).describe("Remove Column")        
    undolist.append(ui)    

#------------------------------------------------------------------------------

class TableColumnView(gtk.TreeView):

    def __init__(self, table):        
        gtk.TreeView.__init__(self)
        self.set_table(table)

        #
        # set up columns
        #
        def add_column(key):
            cell = gtk.CellRendererText()            
            column = gtk.TreeViewColumn(key, cell)
            column.set_cell_data_func(cell, self.render_column_prop, key)
            self.append_column(column)

        for key in ['key', 'label', 'designation']:
            add_column(key)


    def set_table(self, table):
        self.table = table

        # set up model
        if table is None:
            return self.set_model(None)
                    
        model = gtk.ListStore( object )            
        self.set_model(model)

    def check_in(self):
        # create copies of columns (except for the data)
        model = self.get_model()
        model.clear()
        for column in self.table.get_columns():
            new_column = column.copy(data=False)
            model.append( (new_column,) )

    def check_out(self, undolist=[]):        
        model = self.get_model()
        iter = model.get_iter_first()
        n = 0
        while iter:
            column = model.get_value(iter, 0)
            # copy all properties except for the actual data
            kwargs = column.values.copy()
            kwargs.pop('data')
            uwrap.set(self.table.get_column(n), **kwargs)             # ADD Undo
            iter = model.iter_next(iter)
            n += 1
                    
        
    def render_column_prop(self, column, cell, model, iter, propkey):
        column = model.get_value(iter, 0)
        cell.set_property('text', column.get_value(propkey) or "")



class ModifyTableDialog(gtk.Dialog):

    # This is actually something like a PW.
    # We check in a table, keep the copy of the new values in memory
    # and if we like the changes, we check out the new values.
    
    def __init__(self, table, parent=None):

        self.table = table

        gtk.Dialog.__init__(self, "Modify Table", parent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        cview = TableColumnView(table)
        cview.show()
        
        self.vbox.add(cview)

        # connect
        cview.connect( "row-activated", self.on_row_activated )
        
        # for reference
        self.cview = cview


    def on_row_activated(self, treeview, *udata):
        (model, pathlist) = self.cview.get_selection().get_selected_rows()
        column = model.get_value( model.get_iter(pathlist[0]), 0)
        dialog = ColumnPropertiesDialog(column)
        try:
            response = dialog.run()
        finally:
            dialog.destroy()
        self.cview.queue_draw()


    def check_out(self, undolist=[]):
        self.cview.check_out(undolist=undolist)
        
    def run(self):
        self.cview.check_in()
        return gtk.Dialog.run(self)
            
        

###############################################################################
if __name__ == "__main__":

    table = setup_test_table()
    print table

    dlg = ModifyTableDialog(table)
    response = dlg.run()
    if response == gtk.RESPONSE_ACCEPT:
        ul = UndoList().describe("Update Columns")
        dialog.check_out(undolist=ul)
        uwrap.emit_last(table, 'update-columns', undolist=ul)
        #self.project.journal.append(ul)

    print table
    
