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

# $HeadURL$
# $Id$


import logging
logging.basicConfig()

import pygtk # TBR
pygtk.require('2.0') # TBR

import gobject
import gtk


from Sloppy.Base.table import Table
from Sloppy.Lib.Undo import UndoInfo, UndoList, NullUndo


class TableModel(gtk.GenericTreeModel):

    def __init__(self, table=None):
        gtk.GenericTreeModel.__init__(self)
        self.set_table(table)

    def set_table(self, table):

        if not isinstance(table, Table):
            raise TypeError("TableModel needs a Table, not a %s" % type(table))
        
        self.table = table

    #----------------------------------------------------------------------
    # The following are methods from gtk.GenericTreeViewModel that
    # need to be redefined. For a more thorough explanation, take a
    # look at the pygtk tutorial.
    # The model implementation is very straightforward:
    #  iters are RowIterator objects
    #  path has the form (row,col)
    #   -> on_get_iter(path) returns path[0] = row number = iter
    #----------------------------------------------------------------------

    def get_column_names(self):        
        rv =  map(lambda col, n:
                   "%d:\n%s (%s)\n%s" %
                  (n,
                   col.get_value('key', "unnamed"),
                   col.get_value('designation'),
                   col.get_value('label')
                   ),
                  self.table.columns, range(self.table.ncols))
        return rv

    def get_row_from_path(self, path):
        return path[0]
    
    def on_get_flags(self):
        # we don't use gtk.TREE_MODEL_ITERS_PERSIST
        return gtk.TREE_MODEL_LIST_ONLY

    def on_get_n_columns(self):
        return self.table.ncols

    def on_get_column_type(self,index):
        return self.table.get_converter(index)

    def on_get_iter(self, path):
        return self.table.row(path[0])

    def on_get_path(self, iter):
        return (iter.row,)

    def on_get_value(self, iter, column):
        try:
            return iter[column]
        except IndexError:
            return None

    def on_iter_next(self, iter):
        try:
            return iter.next()
        except StopIteration:
            return None

    def on_iter_children(self, iter):
        return None

    def on_iter_has_child(self, iter):
        return False

    def on_iter_n_children(self, iter):
        if iter is not None: 
            return 0
        return self.table.rows

    def on_iter_nth_child(self, iter, n):
        if iter is not None:
            return None
        # ?
        return self.table.row(n)

    def on_iter_parent(self,child):
        return None


    # -- data manipulation --

    def set_value(self, path, value, undolist=[]):
       
        row, col = path
        try:
            value = self.table.convert(col, value)
        except:
            return

        old_value = self.table.get_value(col, row)
        
        if value != old_value:
            self.table.set_value(col, row, value)
            ui = UndoInfo(self.set_value, path, old_value).describe("Set cell value")
        else:
            ui = NullUndo()

        undolist.append(ui)            

        self.row_changed(path, self.get_iter(path))
        

    def insert_row(self, path, data=None, undolist=[]):

        ul = UndoList().describe("Insert row")
        if data is None:
            self.table.insert_n_rows(path[0], 1)
        else:
            self.table.insert_rows(path[0], data)
        ul.append( UndoInfo(self.delete_rows, [path]) )
        self.row_inserted(path, self.get_iter(path))

        undolist.append(UndoInfo(self.delete_rows, [path]))

        
    def delete_rows(self, pathlist, undolist=[]):

        ul = UndoList().describe("Delete rows")
        deleted = 0
        for path in pathlist:
            real_row = path[0]-deleted
            real_path = (real_row,)
            old_data = self.table.delete_n_rows(real_row, 1)
            ul.append( UndoInfo(self.insert_row, real_path, data=old_data) )
            self.row_deleted(real_path)
            deleted += 1
            
        undolist.append(ul)


class TableView(gtk.TreeView):

    __gsignals__ = {
        'column-clicked' : (gobject.SIGNAL_RUN_FIRST,
                            gobject.TYPE_NONE,
                            (gobject.TYPE_OBJECT,))
        }

    
    def __init__(self, app, table=None, model=None):        
        gtk.TreeView.__init__(self)
        self.set_headers_visible(True)
        self.set_headers_clickable(True)
        self.set_property("rules-hint", True)
        self.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.set_fixed_height_mode(True) # PYGTK 2.6

        self.app = app
        
        if table is not None:
            self.set_table(table)
        else:
            self.set_model(model)

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
        if self.app is not None:
            journal = self.app.project.journal
        else:
            journal = list()

        # set up columns
        n = 0
        for name in model.get_column_names():
            cell = gtk.CellRendererText()
            cell.set_property('mode',gtk.CELL_RENDERER_MODE_EDITABLE)            
            cell.set_property('editable',True)
            cell.connect('edited',self.on_value_edited, model, n, journal)
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
    # Table/Model
    #
    
    def set_table(self, table):
        self.set_model( TableModel(table) )

    def get_table(self, table):
        if self.get_model() is not None:
            return self.get_model().table
        else:
            return None
        
    def get_column_index(self, column):
        " Return index of the given column, not counting the first column. "
        return self.get_columns().index(column)
        #return self.get_columns().index(column) - 1


gobject.type_register(TableView)
