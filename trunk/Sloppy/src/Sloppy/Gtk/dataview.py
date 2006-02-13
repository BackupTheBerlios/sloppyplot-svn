
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

# $HeadURL: svn+ssh://niklasv@svn.berlios.de/svnroot/repos/sloppyplot/trunk/Sloppy/src/Sloppy/Gtk/tableview.py $
# $Id: tableview.py 431 2006-01-04 23:04:29Z niklasv $

"""
TreeView to display a Dataset.
"""

import gtk, gobject, numpy

from Sloppy.Base import globals
from Sloppy.Base.dataset import Dataset, Table
from Sloppy.Lib.Undo import UndoInfo, UndoList, NullUndo
from Sloppy.Lib.Signals import HasSignals


class DatasetModel(gtk.GenericTreeModel):

    def __init__(self, dataset=None):
        gtk.GenericTreeModel.__init__(self)
        self.set_dataset(dataset)

    def set_dataset(self, dataset):
        self.dataset = dataset

    #----------------------------------------------------------------------
    # The following are methods from gtk.GenericTreeViewModel that
    # need to be redefined. For a more thorough explanation, take a
    # look at the pygtk tutorial.
    # The model implementation is very straightforward:
    #  iters are row numbers
    #  path has the form (row,col)
    #   -> on_get_iter(path) returns path[0] = row number = iter
    #----------------------------------------------------------------------

    def get_column_names(self):

        rv = []
        if isinstance(self.dataset, Table):        
            n = 0
            for name in self.dataset.names:
                info = self.dataset.get_info(name)
                if info.designation is not None:
                    designation = "(%s)" % info.designation
                else:
                    designation = ""
                rv.append("%d: %s %s\n%s" % (n, name, designation, info.label))
                n+=1
        else:
            rv = [str(n) for n in range(self.dataset.ncols)]
            
        return rv

    def get_row_from_path(self, path):
        return path[0]
    
    def on_get_flags(self):
        # we don't use gtk.TREE_MODEL_ITERS_PERSIST
        return gtk.TREE_MODEL_LIST_ONLY

    def on_get_n_columns(self):
        return self.dataset.ncols

    def on_get_column_type(self, index):
        return str
    
    def on_get_iter(self, path):
        return path[0]

    def on_get_path(self, iter):
        return (iter,)

    def on_get_value(self, iter, column):
        try:
            v = self.dataset.get_value(column, iter)
            if numpy.isnan(v):
                return "-"
            else:
                return v
        except IndexError:
            return None

    def on_iter_next(self, iter):
        if iter+1 < self.dataset.nrows:
            return iter+1
        else:
            return None

    def on_iter_children(self, iter):
        return None

    def on_iter_has_child(self, iter):
        return False

    def on_iter_n_children(self, iter):
        if iter is not None: 
            return 0
        return self.dataset.rows

    def on_iter_nth_child(self, iter, n):
        if iter is not None:
            return None
        # ?
        return n

    def on_iter_parent(self,child):
        return None


    # -- data manipulation --

    def set_value(self, path, value, undolist=[]):

        row, col = path

        if value == '-':
            value = numpy.nan
        else:
            try:
                converter = self.dataset.get_column_pytype(col)
                value = converter(value)
            except Exception, msg:
                print "Not ok: ", msg
                return

        old_value = self.dataset.get_value(col, row)
        
        if value != old_value:
            self.dataset.set_value(col, row, value)
            ui = UndoInfo(self.set_value, path, old_value).describe("Set cell value")
        else:
            ui = NullUndo()

        undolist.append(ui)            

        self.row_changed(path, self.get_iter(path))


    def remove_rows_by_path(self, pathlist, undolist=[]):
        ul = UndoList().describe("Remove rows")       
        ds = self.dataset
        deleted = 0
        real_pathlist = []
        for path in pathlist:
            real_path = (path[0]-deleted,)
            ds.remove_n_rows(real_path[0], 1, undolist=ul)
            real_pathlist += real_path
            deleted += 1
        self.undoable_rows_deleted(real_pathlist, undolist=ul)
        ds.notify_change()
        undolist.append(ul)


    def insert_rows_by_path(self, pathlist, offset=0, undolist=[]):
        ul = UndoList().describe("Insert row")
        ds = self.dataset
        added = offset
        real_pathlist = []
        for path in pathlist:
            real_path = (path[0]+added,)
            ds.insert_n_rows(real_path[0], 1, undolist=ul)
            real_pathlist += real_path
            added += 1
        self.undoable_rows_inserted(pathlist, undolist=ul)
        ds.notify_change(undolist=ul)
        undolist.append(ul)

    def undoable_rows_deleted(self, pathlist, undolist=[]):
        for path in pathlist:
            self.row_deleted(path)
        undolist.append(UndoInfo(self.undoable_rows_inserted, pathlist))

    def undoable_rows_inserted(self, pathlist, undolist=[]):
        for path in pathlist:
            self.row_inserted(path, self.get_iter(path))
        undolist.append(UndoInfo(self.undoable_rows_deleted, pathlist))

        
        

class DatasetView(gtk.TreeView, HasSignals):

    __gsignals__ = {
        'column-clicked' : (gobject.SIGNAL_RUN_FIRST,
                            gobject.TYPE_NONE,
                            (gobject.TYPE_OBJECT,))
        }

    
    def __init__(self, dataset=None, model=None):        
        gtk.TreeView.__init__(self)
        self.set_headers_visible(True)
        self.set_headers_clickable(True)
        self.set_property("rules-hint", True)
        self.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.set_fixed_height_mode(True) # PYGTK 2.6
      
        if dataset is not None:
            self.set_dataset(dataset)
        else:
            self.set_model(model)

        HasSignals.__init__(self)
        
    def set_model(self, model):
        if model is not None:
            gtk.TreeView.set_model(self, model)
            self.setup_columns()

    def setup_columns(self):

        model = self.get_model()
        if model is None: return
        
        # Remove all old columns...
        for col in self.get_columns():
            self.remove_column(col)

        # For testing purposes, we might not have an Application object.
        # In this case, we will simply use a plain list as undo journal.
        if globals.app is not None:
            journal = globals.app.project.journal
        else:
            journal = list()

        # set up columns
        n = 0
        for name in model.get_column_names():
            cell = gtk.CellRendererText()
            cell.set_property('mode',gtk.CELL_RENDERER_MODE_EDITABLE)            
            cell.set_property('editable',True)
            cell.connect('edited',self.on_value_edited, model, n, journal)
            name = name.replace('_','__')
            column = gtk.TreeViewColumn(name,cell,text=n)            
            column.set_property('resizable',True)
            column.set_property('clickable',True)
            column.set_property('sizing', gtk.TREE_VIEW_COLUMN_FIXED) # PYGTK 2.6
            column.set_fixed_width(100)
            column.set_expand(False)

            ## create custom label widget
            #widget = gtk.Button()
            #widget.show()
            #column.set_widget(widget)

            column.connect("clicked", self.on_column_clicked)
            
            self.append_column(column)
            n += 1
                
    update = setup_columns


    #----------------------------------------------------------------------
    # Callbacks
    #
    
    def on_column_clicked(self, tvcolumn):
        self.emit('column-clicked', tvcolumn)
        
    def on_value_edited(self, cell, path, new_text, model, column, undolist=[]):
        " model, column, undolist must be provided by the connect call. "
        # Since the first column is not a data column (and not editable),
        # we need to subtract 1 from the column number.
        #column -= 1 
        path = (int(path), column)
        model.set_value(path, new_text, undolist=undolist)        

    def on_render_rownr(self,column,cell,model,iter):
        rownr = model.get_row_from_path(model.get_path(iter))
        cell.set_property('text',str(rownr))
        return


    #----------------------------------------------------------------------
    # Dataset/Model
    #
    
    def set_dataset(self, dataset):
        self.set_model(DatasetModel(dataset))
        dataset.sig_connect('update-fields', lambda sender: self.setup_columns())
        # TODO: remove callbacks

    def get_dataset(self, dataset):
        if self.get_model() is not None:
            return self.get_model().dataset
        else:
            return None
        
    def get_column_index(self, column):
        " Return index of the given column, not counting the first column. "
        return self.get_columns().index(column)
        #return self.get_columns().index(column) - 1



# register only for pygtk < 2.8
if gtk.pygtk_version[1] < 8:
    gobject.type_register(DatasetView)




###############################################################################

if __name__ == "__main__":

    win = gtk.Window()
    win.connect("destroy", gtk.main_quit)

    ds = Table( numpy.array([(1,2,3),(4,5,6)]) )
#    ds = setup_test_dataset()
#    ds.remove(0)
    ds.dump()
    print ds.nrows

    dsview = DatasetView(None,ds)
    win.add(dsview)
    
    win.show_all()
    gtk.main()
