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


""" Dataset is a wrapper object for a one-dimensional numpy array.

A Dataset can be a heterogeneous array like this

 [ ('one', 1),
   ('two', 2) ]

or a homogeneous array like this

 [ [1.2, 1.0],
   [2.1, 2.0] ]


A Dataset can be created by simply writing

>>> ds = Dataset(an_array)

and it provides a multitude of basic functions to simplify typical
operations, such as renaming, removing, inserting or rearranging
columns, or insert and removing rows.

You can have raw access to the array by using Dataset.data

"""

import numpy
from Sloppy.Lib.Undo import UndoList,UndoInfo,NullUndo


# The Dataset _is_ the wrapper!

# TODO: to_matrix, to_table ?

# TODO: regression tests

# TODO: change column type somehow _or_ replace column!!!



class Dataset:

    def __init__(self, _array):
        self.data = _array


    # Item Access -------------------------------------------------------------

    def get_value(self, cindex, row):
        return self.col(cindex)[row]

    def set_value(self, cindex, row, value, undolist=[]):
        col = self.col(cindex)
        old_value = col[row]
        col[row] = value
        undolist.append(UndoInfo(self.set_value, col, row, old_value))


    # Array Information -------------------------------------------------------

    # OK
    def is_homogeneous(self):
        return len(self.data.dtype.descr) == 1

    # OK
    def is_heterogeneous(self):
        return len(self.data.dtype.descr) != 1
    

    # Column Access -----------------------------------------------------------
    
    def col(self, cindex):
        " Return the column with the given name or index `cindex`. "
        if isinstance(cindex, basestring):
            return self.get_column_by_name(cindex)
        elif isinstance(cindex, int):
            return self.get_column_by_index(cindex)
        else:
            raise TypeError("Column must be specified using either a string or a column index.")

    def get_column_by_index(self, index):
        " Return a copy of the column with the given `index`. "
        if self.is_homogeneous() is True:
            return self.data[:,index]
        else:
            return self.data[ self.data.dtype.fields[-1][index] ]            


    def get_column_by_name(self, name):
        " Return a copy of the column with the given `name`. "
        if self.is_homogeneous():
            raise TypeError("Column access by name is only valid for heterogeneous Datasets.")
        return self.data[name]

    def index(self, cindex):
        " Return index of column with given name or index `cindex`. "
        if isinstance(cindex, int):
            return cindex
        elif isinstance(cindex, basestring):
            return self.data.dtype.fields[-1].index(cindex)

    def name(self, cindex):
        " Return name of column with given name or index `cindex`. "
        if self.is_homogeneous():
            raise TypeError("Column access by name is only valid for heterogeneous Datasets.")        
        if isinstance(cindex, basestring):
            return cindex
        elif isinstance(cindex, int):
            return self.data.dtype.fields[-1][cindex]
        
        
    # Column Manipulation -----------------------------------------------------

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
        a = self.data
        insert_at = self.index(cindex)

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
        b = numpy.zeros(a.shape, dtype=numpy.dtype(new_descriptor))

        # fill new array with data
        for name in b.dtype.fields[-1]:
            if name in names:
                b[name] = cols[names.index(name)]
            else:
                b[name] = a[name]
        
        self.data = b


    # TODO
    def rearrange(self, order):
        """
        Rearrangement of columns.

        Uses _rearrange internally, but adds a check to make sure that
        the number of columns is preserved.
        """        
        # validity check 
        if len(order) != len(self.data.dtype.fields[-1]):
            raise ValueError("Rearrange order must be of the same length as before.")

        self._rearrange(order)


    # TODO
    def _rearrange(self, order):
        a = self.data
        
        # create new descriptor
        descriptor = a.dtype.descr
        names = a.dtype.fields[-1]
        
        new_descriptor = []
        for i in order:
            if isinstance(i, basestring):
                i = names.index(i)
            new_descriptor.append(descriptor[i])

        b = numpy.zeros(a.shape, dtype=numpy.dtype(new_descriptor))
       
        for name in b.dtype.fields[-1]:
            b[name] = a[name]

        self.data = b
        
    # TODO
    def rename(self, cindex, new_name):
        """
        Rename the given `cindex` to the new name.
        """
        a = self.data
        old_name = self.name(cindex)
        new = dict(a.dtype.fields)
        new[new_name] = new[old_name]
        del new[old_name]
        del new[-1]
        a.dtype = numpy.dtype(new)


    # TODO
    def remove(self, cindex, n=1):
        """
        Remove n columns starting at column with name or index `cindex`.
        """
        index = self.index(cindex)
        order = range(len(self.data.dtype.fields[-1]))
        for i in range(n):
            order.pop(index)
        self._rearrange(order)
        

    # Row Manipulation --------------------------------------------------------

    def insert_n_rows(self, i, n=1, undolist=[]):
        """
        Insert `n` empty rows into each column at row `i`.
        """
        self.insert_rows(i, rows=numpy.zeros((n,), dtype=self.data.dtype), undolist=[])

    def insert_rows(self, i, rows, undolist=[]):
        """
        Insert the given `rows` (list of arrays) at row `i`.
        """
        self.data = numpy.concatenate([self.data[0:i], rows, self.data[i:]])
        undolist.append(UndoInfo(self.delete_n_rows, i, len(rows), only_zeros=True))

    def extend(self, n, undolist=[]):
        """
        Add `n` rows to the end of all columns.
        """
        self.insert_n_rows(len(self.data), n, undolist=undolist)

    def delete_n_rows(self, i, n=1, only_zeros=False, undolist=[]):
        """
        Delete `n` rows, starting at the row with the index `i`.
        The keyword arg `only_zeros` is an internal argument needed
        for better undo performance.              
        """
        n = min(len(self.data)-i, n)

        if only_zeros is True:
            ui = UndoInfo(self.insert_n_rows, i, )
        else:
            undo_data = numpy.array(self.data[i:i+n])            
            ui = UndoInfo(self.insert_rows, i, undo_data)
            
        self.data = numpy.concatenate([self.data[0:i], self.data[i+n:]])
        undolist.append(ui)
        
        # TODO: return cut data ??

    def resize(self, nrows, undolist=[]):
        """
        Resize array to given number of `nrows`.
        """
        current_nrows = self.data.shape[0]
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
        a = self.data
        print "-"*80
        fields = a.dtype.fields
        print "\t".join(fields[-1])
        print "\t".join([str(fields[key][0]) for key in fields[-1]])
        print
        for row in a:
            print "\t".join(str(item) for item in row.item())
        print "-"*80    







#------------------------------------------------------------------------------
def test():

    #
    # heterogeneous array
    #
    dtype = numpy.dtype( {'names': ['name', 'age', 'weight'],
                          'formats': ['U30', 'i2', numpy.float32]} )
    a = numpy.array( [(u'Bill', 31, 260),
                      ('Fred', 15, 135)], dtype=dtype )

    ds = Dataset(a)

    # column access
    print ds.col('name')
    print ds.col('age')

    print ds.col(1) # heterogeneous only
    
#     print dataset.rearrange( ['name','weight', 'age'] )
#     dataset.dump()

#     col = dataset.col(1)
#     col = numpy.sin(dataset.col(1))
#     print col
#     dataset.dump()


#     dataset.data['weight'] = numpy.sin(dataset.data['weight'])
#     dataset.rename('weight', 'sin of weight')
#     dataset.dump()


#     # dataset.remove(1)
#     # dataset.dump()

#     # dataset.remove('age')
#     # dataset.dump()


#     dataset.resize(3)
#     dataset.dump()

#     dataset.remove('name',2)
#     dataset.dump()

#     dataset.insert(1, [0.1,0.2,0.4], 'floaties')
#     dataset.dump()

#     print dataset.col(-1)
#     z = numpy.array( ['one', 'two', 'three'] )
#     dt = numpy.dtype( {'names':['age','numberasint'],
#                        'formats': ['U30', 'i2']} )
#     b = numpy.array([('one', 1),('two', 2),('three',3)], dtype=dt)
#     dataset.insert(1, b)
#     dataset.dump()

#     print a



if __name__ == '__main__':
    test()





