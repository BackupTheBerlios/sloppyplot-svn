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

"""
Table class (heterogeneous numpy array).
"""


import numpy # requires 0.9.4.SVN as of February 1st 2006

from Sloppy.Lib.Signals import HasSignals
from Sloppy.Lib.Props import *
from Sloppy.Lib.Undo import UndoList, UndoInfo, NullUndo


class ColumnInfo(HasProperties):    
    designation = VP(['X','Y','XY','XERR', 'YERR', 'LABEL'])
    query = String()
    label = Unicode()



class Table(object, HasSignals):

    def __init__(self, _array):
        HasSignals.__init__(self)
        self.sig_register('update-columns')
        
        self.array = _array        
        self.infos = {}


    # Item Access -------------------------------------------------------------

    def get_value(self, cindex, row):
        return self.array[self.get_name(cindex)][row]
    
    def set_value(self, cindex, row, value, undolist=[]):
        col = self.get_column(cindex)
        old_value = col[row]
        col[row] = value
        undolist.append(UndoInfo(self.set_value, col, row, old_value))


    # Column Access -----------------------------------------------------------
    
    def get_column(self, cindex):
        " Return a copy of the column with the given name or index `cindex`. "
        if isinstance(cindex, basestring):
            return self.get_column_by_name(cindex)
        elif isinstance(cindex, int):
            return self.get_column_by_index(cindex)
        else:
            raise TypeError("Column must be specified using either a string or a column index.")

    def get_column_by_index(self, index):
        " Return a copy of the column with the given `index`. "
        return self.array[ self.array.dtype.fields[-1][index] ]

    def get_column_by_name(self, name):
        " Return a copy of the column with the given `name`. "        
        return self.array[name]

    def get_index(self, cindex):
        " Return index of column with given name or index `cindex`. "
        if isinstance(cindex, int):
            return cindex
        elif isinstance(cindex, basestring):
            return self.array.dtype.fields[-1].index(cindex)

    def get_name(self, cindex):
        " Return name of column with given name or index `cindex`. "
        if isinstance(cindex, basestring):
            return cindex
        elif isinstance(cindex, int):
            return self.array.dtype.fields[-1][cindex]
        
        
    # Column Manipulation -----------------------------------------------------


    def append(self, cols):
        self.insert(cindex, self.get_ncols() - 1)
                    
    # TODO
    def insert(self, cindex, cols, names=[]):
        # make sure names is a list of names, not a single name
        if not isinstance(names, (list,tuple)):
            names = [names]
        
        # cols might be ...
        if isinstance(cols, (list,tuple)):
            # ...a list of 1-d arrays or of lists

            # This wraps scalar lists like [1,2,3] to the form [[1,2,3]]
            # as expected by _insert.
            if len(cols) > 0:
                first_item = cols[0]
                if not isinstance(first_item, (list,tuple,numpy.ndarray)):
                    cols = [cols]
                    
            self._insert(cindex, cols, names)

        elif isinstance(cols, numpy.ndarray):
            # ... an array of void-type
            fields = cols.dtype.fields
            if fields is None:
                if len(names) == 0:
                    names = [''] * len(cols)
                self._insert(cindex, [cols[i] for i in range(len(cols))], names)
            else:
                if len(names) == 0:
                    names = fields[-1]
                self._insert(cindex, [cols[name] for name in fields[-1]], names)
                
            
    # TODO    
    def _insert(self, cindex, cols, names):
        """
        Append a list of columns `cols` with a list of names `names`
        at position `cindex`. 
        """
        a = self.array
        insert_at = self.get_index(cindex)

        descriptor = a.dtype.descr[:]
        new_names = a.dtype.fields[-1]

        for index in range(len(cols)):
            # make sure we have an array
            col = cols[index]
            if isinstance(col, (list,tuple)):
                col = cols[index] = numpy.array(col)

            # Make sure we have a unique name.
            # If we have no name, suggest C%d where %d is the index.
            # If the name is already in use, replace the numeric suffix
            # until the name is unique.
            name = names[index] or 'C%d' % index
            j = index                                        
            while (not name) or (name in new_names):
                rpos = name.rfind(str(j))
                if rpos == -1:
                    name += str(j+1)
                else:
                    name = name[:rpos] + str(j+1)
                j += 1
            names[index] = name

            new_names.insert(insert_at + index, name)
            descriptor.insert(insert_at + index, (name, col.dtype.str))


        # create new array
        new_descriptor = [descriptor[new_names.index(name)] for name in new_names]        
        new_array = numpy.zeros(a.shape, dtype=numpy.dtype(new_descriptor))

        # fill new array with data
        for name in new_array.dtype.fields[-1]:
            if name in names:
                new_array[name] = cols[names.index(name)]
            else:
                new_array[name] = a[name]
        
        self.array = new_array
        


    # TODO
    def rearrange(self, order):
        """
        Rearrangement of columns.

        Uses _rearrange internally, but adds a check to make sure that
        the number of columns is preserved.
        """        
        # validity check 
        if len(order) != len(self.array.dtype.fields[-1]):
            raise ValueError("Rearrange order must be of the same length as before.")

        self._rearrange(order)


    # TODO
    def _rearrange(self, order):
        a = self.array
        
        # Create new descriptor and new infos.
        # The new infos are created because it is possible to
        # specify less columns in the rearrangement.
        descriptor = a.dtype.descr
        names = a.dtype.fields[-1]

        new_infos = {}
        new_descriptor = []
        for index in order:
            if isinstance(index, basestring):
                name = index
                index = names.index(index)
            else:
                name = names[index]
            new_descriptor.append(descriptor[index])
            new_infos[name] = self.get_info(name)

        new_array = numpy.zeros(a.shape, dtype=numpy.dtype(new_descriptor))       
        for name in new_array.dtype.fields[-1]:
            new_array[name] = a[name]

        self.array = new_array
        self.infos = new_infos
        self.sig_register('update-columns')        
        
        
    # TODO
    def rename(self, cindex, new_name):
        """
        Rename the column with the name or index `cindex` to the new name.        
        """
        a = self.array
        old_name = self.get_name(cindex)
        new = dict(a.dtype.fields)
        new[new_name] = new[old_name]
        del new[old_name]
        del new[-1]
        a.dtype = numpy.dtype(new)

        # keep column infos in sync
        self.infos[new_name] = self.infos[old_name]
        del self.infos[old_name]
        self.sig_register('update-columns')        


    # TODO
    def remove(self, cindex, n=1):
        """
        Remove n columns starting at column with name or index `cindex`.
        """
        index = self.get_index(cindex)
        order = range(len(self.array.dtype.fields[-1]))
        for i in range(n):
            order.pop(index)
        self._rearrange(order)
        

    # Row Manipulation --------------------------------------------------------

    def insert_n_rows(self, i, n=1, undolist=[]):
        """
        Insert `n` empty rows into each column at row `i`.
        """
        self.insert_rows(i, rows=numpy.zeros((n,), dtype=self.array.dtype), undolist=[])

    def insert_rows(self, i, rows, undolist=[]):
        """
        Insert the given `rows` (list of one-dimensional arrays) at row `i`.
        """
        self.array = numpy.concatenate([self.array[0:i], rows, self.array[i:]])
        undolist.append(UndoInfo(self.delete_n_rows, i, len(rows), only_zeros=True))

    def extend(self, n, undolist=[]):
        """
        Add `n` rows to the end of all columns.
        """
        self.insert_n_rows(len(self.array), n, undolist=undolist)

    def delete_n_rows(self, i, n=1, only_zeros=False, undolist=[]):
        """
        Delete `n` rows, starting at the row with the index `i`.
        The keyword arg `only_zeros` is an internal argument needed
        for better undo performance.              
        """
        n = min(len(self.array)-i, n)

        if only_zeros is True:
            ui = UndoInfo(self.insert_n_rows, i, )
        else:
            undo_data = numpy.array(self.array[i:i+n])            
            ui = UndoInfo(self.insert_rows, i, undo_data)
            
        self.array = numpy.concatenate([self.array[0:i], self.array[i+n:]])
        undolist.append(ui)
        
        # TODO: return cut data ??

    def resize(self, nrows, undolist=[]):
        """
        Resize array to given number of `nrows`.
        """
        current_nrows = self.array.shape[0]
        nrows = max(0, nrows)        
        if nrows < current_nrows:
            self.delete_n_rows( nrows, current_nrows - nrows, undolist=[])
        elif nrows > current_nrows:
            self.insert_n_rows( current_nrows, nrows - current_nrows, undolist=[])
        else:
            undolist.append(NullUndo())

            
    # Diagnostics -------------------------------------------------------------

    def dump(self):
        """
        Diagnostic dump to stdout of the array.
        """
        a = self.array
        print
        fields = a.dtype.fields
        print "\t".join(fields[-1])
        print "\t".join([str(fields[key][0]) for key in fields[-1]])
        print
        for row in a:
            print "\t".join(str(item) for item in row.item())
        print


    # Information -------------------------------------------------------------
    
    def get_nrows(self):
        return len(self.array)
    nrows = property(get_nrows)
    def get_ncols(self):
        return len(self.array.dtype.fields) - 1
    ncols = property(get_ncols)
    
    def get_info(self, cindex):
        """
        Retrieve ColumnInfo object for column with name or index `cindex`.
        If there is no such info, then the info is created.
        """
        name = self.get_name(cindex)
        if not self.infos.has_key(name):
            self.infos[name] = ColumnInfo()
            
        return self.infos[name]


#     def get_typecode(self, i): return self._typecodes[i]
#     def get_typecodes(self): return self._typecodes
#     typecodes = property(get_typecodes)
#     def get_typecodes_as_string(self): return reduce(lambda x,y: x+y, self.typecodes)
#     typecodes_as_string = property(get_typecodes_as_string)

#     def get_converters(self): return self._converters
#     converters = property(get_converters)
#     def get_converter(self, i): return self._converters[i]    
#     def convert(self, i, value): return self._converters[i](value)
   


# #--- CONVENIENCE FUNCTIONS ----------------------------------------------------


# def table_to_array(tbl, typecode='f'):
#     shape = (tbl.ncols, tbl.nrows)
    
#     a = zeros( (tbl.ncols, tbl.nrows), typecode)
#     for j in range(tbl.ncols):
#         a[j] = tbl[j].astype(typecode)

#     return transpose(a)


# def array_to_table(a):
#     if len(a.shape) != 2:
#         raise TypeError("Array must be 2-dimensional if you want to convert it to a Table.")
    
#     nrows, ncols =a.shape
#     a = transpose(a)
    
#     tbl = Table(ncols=ncols, nrows=nrows, typecodes=a.typecode)
#     for j in range(tbl.ncols):
#         tbl[j] = a[j]
        
#     return tbl



#------------------------------------------------------------------------------

def setup_test_table():

    a = numpy.array( [ ('Li-I', 7.0, 92.2),                       
                       ('Na', 22.9, 100.0),
                       ('Zn-I', 62.9, 64.0)],
                       dtype = {'formats': ['S10', 'f4', 'f4'],
                                'names': ['element', 'amu', 'abundance']})

    # TODO: allow passing column information 
#    infos = designation='X', label='some data'
#    designation='Y', label='some data'
#    designation='Y', label='some data'

    return Table(a)

    
def test():
    tbl = setup_test_table()
    tbl.dump()
    
    print "Rearranging"
    tbl.rearrange( [1,2,0] )
    tbl.dump()

    print "Remove first column"
    tbl.remove(0)
    tbl.dump()

    print "Resizing the Table to 10 rows"
    tbl.resize(10)
    tbl.dump()

    print "Resizing the Table to 6 rows"
    tbl.resize(6)
    tbl.dump()

    print "Delete rows 1-3"
    tbl.delete_n_rows(1, 2)
    tbl.dump()
    raise SystemExit

    # remove second column
    c = tbl.column(1)
    tbl.remove(c)
    #print tbl

    

   
if __name__ == "__main__":
    test()
    
