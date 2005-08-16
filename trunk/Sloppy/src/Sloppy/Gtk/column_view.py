

from Sloppy.Base.table import Table, setup_test_table
from Sloppy.Lib.Undo import UndoInfo

from uihelper import setup_test_window
from tableview import TableView
import gtk




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

        # set up columns
        cell = gtk.CellRendererText()            
        column = gtk.TreeViewColumn('Table Columns', cell)
        column.set_cell_data_func(cell, self.render_column_name)
        self.append_column(column)
        


    def update(self):

        # fill with data
        model = self.get_model()
        model.clear()
        for column in self.table.get_columns():
            model.append( (column,) )


    def set_table(self, table):
        self.table = table

        # set up model
        if table is None:
            return self.set_model(None)
                    
        model = gtk.ListStore( object )            
        self.set_model(model)

        self.update()

        
    def render_column_name(self, column, cell, model, iter):
        value = model.get_value(iter, 0)
        cell.set_property('text', value.key)


###############################################################################
if __name__ == "__main__":

    table = setup_test_table()
    print table
    hbox = gtk.HPaned()
    
    cview = TableColumnView(table)
    tview = TableView(None, table)
    hbox.add1(cview)
    hbox.add2(tview)
    cview.show()
    tview.show()
    hbox.show()

    #buttons
    # add buttons for adding/removing columns
    remove_column(table, 1)
    cview.update()
    tview.update()
    
    win = setup_test_window(hbox)
    gtk.main()

    
    
