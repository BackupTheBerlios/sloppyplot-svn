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

# $HeadURL: file:///home/nv/sloppysvn/trunk/Sloppy/src/Sloppy/Base/utable.py $
# $Id: utable.py 384 2005-07-03 12:11:00Z nv $


"""
Undo wrappers for table.py
"""


from Sloppy.Base.table import table
from Sloppy.Lib.Undo import UndoInfo, UndoList, NullUndo


def set_item(self, i, item, undolist=[]):
    " Undoable __setitem__ method. "
    old_item = self.columns[i]
    self.set_item(i, item)    
    undolist.append( UndoInfo(set_item, self, i, old_item) )

def set_value(self, col, row, value, undolist=[]):
    old_value = self[col][row]
    self.set_value(col, row, value)
    undolist.append( UndoInfo(set_value, self, col, row, old_value) )

def append(self, item, undolist=[]):    
    self.append(item)
    undolist.append( UndoInfo(remove_by_index, self, len(self.columns) - 1) )

def insert(self, i, item, undolist=[]):
    self.insert(i, self.check_item(item))
    undolist.append( UndoInfo(remove_by_index, self, i) )
    
def remove(self, column, undolist=[]):
    index = self.columns.index(column)
    remove_by_index(self, index, undolist=undolist)
        
def remove_by_index(self, i, undolist=[]):
    old_item = self.columns(i)
    self.remove_by_index(i)
    undolist.append( UndoInfo(insert, self, i, old_item) )    

def rearrange(self, order, undolist=[]):
    old_order = range(len(order))
    for n in range(len(order)):
        old_order[order[n]] = n

    self.rearrange(order)
    undolist.append( UndoInfo(rearrange, self, old_order) )

#--- row operations ----------------------------------------------------

# TODO: this is not a highlevel undo wrapper but rather a replacement
def resize(self, rowcount, undolist=[]):    
    rowcount = max(0, rowcount)
    if rowcount < self.rowcount:
        delete_n_rows(self, rowcount, self.rowcount - rowcount, undolist=undolist)
    elif rowcount > self.rowcount:
        insert_n_rows(self, self.rowcount, rowcount - self.rowcount, undolist=undolist)
    else:
        undolist.append( NullUndo() )


def extend(self, n, undolist=[]):
    insert_n_rows( self.rowcount, n, undolist=undolist)


# TODO: no highlevel undo wrapper
def insert_n_rows(self, i, n=1, undolist=[]):
    rows = list()
    for tc in self.typecodes:
        rows.append( zeros((n,),typecode=tc) )
    insert_rows(self, i, rows, undolist=undolist)
    self.update_rows()


def insert_rows(self, i, rows, undolist=[]):
    self.insert_rows(i, rows)
    undolist.append( UndoInfo(delete_n_rows, self, i, len(rows[0]), only_zeros=True) )

        
def delete_n_rows(self, i, n=1, only_zeros=False, undolist=[]):
    """
    The keyword arg `only_zeros` is an internal argument needed
    for better undo performance.
    """
    
    n = min(self.rowcount-i, n)
    undo_data = list()
    for col in self.columns:
        undo_data.append( col.data[i:i+n].copy() )                

    # fix undo information
    if only_zeros is True:
        ui = UndoInfo(insert_n_rows, self, i, n)
    else:
        ui = UndoInfo(insert_rows, self, i, undo_data)

    rv = self.delete_n_rows(i, n)
    undolist.append(ui)
    return rv

