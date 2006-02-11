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

from Sloppy.Base import tree, utils

from Sloppy.Lib.Signals import HasSignals
from Sloppy.Lib.Undo import UndoInfo, UndoList, NullUndo
from Sloppy.Lib.Props import HasProperties, String, Unicode, VP

import numpy



#------------------------------------------------------------------------------

class Dataset(tree.Node, HasSignals):

    """
    A Dataset contains an array with the data and some additional
    meta-data, which is stored in the attribute 'node_info'.

    The array can either be a homogeneous or a heterogeneous numpy
    array. In both cases, only two-dimensional arrays are supported
    (rank 2).

    Each Dataset implementation provides a set of basic functions for
    the array manipulation, so that basic plotting and manipulation
    functions can use any kind of Dataset.    
    """
    
    
    def __init__(self, array=None):
        tree.Node.__init__(self)
        HasSignals.__init__(self)
       
        # TBR
        self.key = "" # TODO: should be moved to parent object!    
        self.change_counter = 0
        self.__is_valid = True
        self._table_import = None

        self.sig_register('closed')
        self.sig_register('notify')
        self.sig_register('update-fields')

        self._array = None
        if array is None:
            array = self.get_default_array()
        self.set_array(array)

    def revert_change(self, undolist=[]):
        self.change_counter -= 1
        self.sig_emit('notify')
        undolist.append( UndoInfo(self.notify_change).describe("Notify") )
        
    def notify_change(self, undolist=[]):
        self.change_counter += 1
        self.sig_emit('notify')        
        undolist.append( UndoInfo(self.revert_change).describe("Notify") )

    def has_changes(self, counter):
        return self.change_counter != counter

    def close(self):
        self.sig_emit('closed')        
        self.data = None

    def detach(self):
        self.sig_emit('closed')                

    def is_empty(self):
        " Returns True if the Dataset has no data or if that data is empty. "
        return self._array is None or len(self._array) == 0


    #----------------------------------------------------------------------
    # Any derived classes needs to implement the following functions,
    # that provide some basic functionality for arrays of rank 2.
    #

    def get_array(self):
        " Return internal array. "
        return self._array
    
    def set_array(self, array):
        " Set internal array. "
        raise RuntimeError("not implemented")

    def new_array(self, rows, cols):
        " Return a new array of the given dimensions. "
        raise RuntimeError("not implemented")
    
    def get_default_array(self):
        " Return array that is supposed to be used if no array is given. "
        raise RuntimeError("not implemented")
    
    def get_value(self, row, col):
        " Get value with specifed row and column index. "
        raise RuntimeError("not implemented")
    
    def set_value(self, row, col, value):
        " Set value with specifed row and column index to given value. "
        raise RuntimeError("not implemented")

    def get_row(self, row):
        " Return row vector with given index. "
        return self._array[i]
    
    def get_column(self, col):
        " Return column vector with given index. "
        raise RuntimeError("not implemented")

    # if you redefine get_nrows in derived classes,
    # please redefine 'nrows = property(get_nrows)' as well.
    def get_nrows(self): return len(self._array)
    nrows = property(get_nrows)

    # if you redefine get_ncols in derived classes,
    # please redefine 'ncols = property(get_ncols)' as well.    
    def get_ncols(self): raise RuntimeError("not implemented")
    ncols = property(get_ncols)

    def get_column_type(self, col):
        raise RuntimeError("not implemented")

    pytypemap = {numpy.float32 : float,
                numpy.float64: float,
                numpy.int8: int,
                numpy.int16: int,
                numpy.int32: int,
                numpy.int64: int,
                numpy.string: str
                #numpy.unicode: unicode #?
                }   
    def get_column_pytype(self, col):
        " return python type corresponding to the numpy type of the field. "
        # TODO: The following is a hack. We might need to ask
        # TODO: if the given numpy types can be converted to a numpy-value
        # TODO: by the type directly.
        return self._ptypemap[self.get_column_type(col)]
    
    def dump(self):
        " Diagnostic dump to stdout of the array. "
        print "Dataset (%s)" % self.__class__.__name__
        print self._array
        print
        
    # Row Manipulation ----------------------------------------------------    

    def resize(self, nrows, undolist=[]):
        " Resize array to given number of `nrows`. "        
        current_nrows = self.nrows
        nrows = max(0, nrows)
        if nrows < current_nrows:
            self.delete_n_rows(nrows, current_nrows - nrows, undolist=[])
        elif nrows > self.nrows:
            self.insert_n_rows(current_nrows, nrows - current_nrows, undolist=[])
        else:
            undolist.append(NullUndo())        

    def extend(self, n, undolist=[]):
        " Add `n` rows to the end of all fields. "
        self.resize(self.nrows+n, undolist=undolist)

    def insert_n_rows(self, row, n=1, undolist=[]):
        " Insert `n` empty rows at the given row index. "
        self.insert_rows(row, rows=numpy.zeros((n,), dtype=self._array.dtype), undolist=[])

    def insert_rows(self, i, rows, undolist=[]):
        " Insert the given `rows` (list of one-dimensional arrays) at row `i`. "
        raise RuntimeError("not implemented")

    def delete_n_rows(self, row, n=1, only_zeros=False, undolist=[]):
        """
        Delete `n` rows, starting at the row with the index `row`.
        The keyword arg `only_zeros` is an internal argument needed
        for better undo performance.              
        """
        n = min(self.nrows-row, n)
        if only_zeros is True:
            ui = UndoInfo(self.insert_n_rows, row, )
        else:
            undo_data = numpy.array(self._array[row:row+n])            
            ui = UndoInfo(self.insert_rows, row, undo_data)
            
        self._array = numpy.concatenate([self._array[0:row], self._array[row+n:]])
        undolist.append(ui)


    # Column Manipulation ---------------------------------------------------------
    
    def rearrange(self, order, undolist=[]):
        """ Rearrange Dataset columns.
        
        The list 'order' is a valid permutation of the column indices.
        """
        # Uses _rearrange internally, but adds a check to make sure that
        # the number of fields is preserved.
        if len(order) != self.ncols:
            raise ValueError("Rearrange order must be of the same length as before.")
        self._rearrange(order, undolist=[])
    
    def _rearrange(self, order, undolist=[]):        
        raise RuntimeError("not implemented")

    def remove_column(self, col, undolist=[]):
        " Remove a single column at specified index. "
        self.remove_columns(col, 1, undolist=[])
        
    def remove_columns(self, col, n=1, undolist=[]):
        " Remove 'n' columns starting at column with specified index. "
        index = self.get_index(col)
        order = range(self.ncols)
        for i in range(n):
            order.pop(index)
        self._rearrange(order, undolist=[])

    def append_columns(self, array, undolist=[]):
        " Append the given array to the Dataset array. "        
        self.insert_columns(self.ncols-1, array, undolist=undolist)

    def insert_columns(self, col, array, undolist=[]):
        """ Insert the given 'array' at specified index 'col'.        

        This high-level function accepts not only arrays, but
        also lists/tuples or an integer representing a number
        of empty columns.        
        """
        if isinstance(array, int):
            array = self.new_array(rows=self.nrows, cols=array)
        elif isinstance(array, (list, tuple)):
            array = self.new_array_from_list(array)

        self._insert_columns(col, array, undolist=undolist)

    def _insert_columns(self, col, array, undolist=[]):
        raise RuntimeError("not implemented")



###############################################################################
class Table(Dataset):
    
    """
    A Dataset with a heterogeneous array.

    A Dataset 'column' is mapped to the field of such an heterogeneous array.
    Each field has an Info object which stores additional information
    about it.
    """

    class Info(HasProperties):
        label = Unicode()       
        designation = VP(['X','Y','XERR', 'YERR', 'LABEL', None])
        query = String()


    def __init__(self, array=None):
        self._infos = {}        
        Dataset.__init__(self, array)


    # Array ---------------------------------------------------------------
    
    def set_array(self, array, infos={}, undolist=[]):
        ui = UndoInfo(self.set_array, self._array, self._infos)

        self._array = array
        self._infos = infos
        self.sig_emit('update-fields')
        
        undolist.append(ui)

    def new_array(self, rows, cols, names=None, formats=None):
        raise RuntimeError("Not implemented")

    def get_default_array(self):
        return numpy.array([(0.0,0.0)], dtype='f4,f4')


    # Value Access ---------------------------------------------------------

    def get_value(self, cindex, row):
        return self._array[self.get_name(cindex)][row]
    
    def set_value(self, cindex, row, value, undolist=[]):
        self._array[row][cindex]
        col = self.get_field(cindex)
        old_value = col[row]
        col[row] = value
        undolist.append(UndoInfo(self.set_value, col, row, old_value))


    # for get_column, see get_field

    def get_ncols(self): return len(self._array.dtype.fields) - 1
    ncols = property(get_ncols)

    def get_column_type(self, cindex):
        name = self.get_name(cindex)
        return self._array.dtype.fields[name][0].type


    def dump(self):
        print "Dataset (%s)" % self.__class__.__name__
        print
        fields = self._array.dtype.fields
        print "\t".join(fields[-1])
        print "\t".join([str(fields[key][0]) for key in fields[-1]])
        print
        for row in self._array:
            print "\t".join(str(item) for item in row.item())
        print


    # Row Manipulation ----------------------------------------------------

    def insert_rows(self, i, rows, undolist=[]):        
        self._array = numpy.concatenate([self._array[0:i], rows, self._array[i:]])
        undolist.append(UndoInfo(self.delete_n_rows, i, len(rows), only_zeros=True))


    # Column Manipulation ---------------------------------------------------------

    # TODO: undolist
    def _rearrange(self, order, undolist=[]):
        a = self._array
        
        # Create new descriptor and new infos.
        # The new infos are created because it is possible to
        # specify less fields in the rearrangement.
        descriptor = a.dtype.arrdescr
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

        self._array = new_array
        self._infos = new_infos
        self.sig_emit('update-fields')


    # TODO: undolist
    def _insert_columns(self, col, array, undolist=[]):        
        col = self.get_index(col)

        # We merge in the description of the new array into the
        # existing array 'self.array'. Unfortunately we must
        # make sure that each new added field has a unique name.
        names = self._array.dtype.fields[-1]        
        descriptor = self.array.dtype.arrdescr[:]
        i = 0
        for name,typecode in array.dtype.arrdescr:
            new_name = utils.unique_names([name], names)
            descriptor.insert(i, (new_name, typecode))
            i+=1

        print "new descriptor looks like this:"
        print descriptor
        print
        new_array = numpy.zeros(a.shape, dtype=numpy.dtype(new_descriptor))

        # fill new array with data
        array_names = array.dtype.fields[-1]
        for name in new_array.dtype.fields[-1]:
            if name in array_names:
                new_array[name] = array[name]
            else:
                new_array[name] = self._array[name]

        print "new array looks like this:"
        print new_array
        print
        
        self._array = new_array
        
    

    #----------------------------------------------------------------------
    # SPECIFIC TO TABLE OBJECTS
    
    def get_field(self, cindex):
        " Return a copy of the field with the given name or index `cindex`. "
        if isinstance(cindex, basestring):
            return self.get_field_by_name(cindex)
        elif isinstance(cindex, int):
            return self.get_field_by_index(cindex)
        else:
            raise TypeError("Field must be specified using either a string or a field index.")

    get_column = get_field

    
    def get_field_by_index(self, index):
        " Return a copy of the field with the given `index`. "
        return self._array[ self._array.dtype.fields[-1][index] ]

    def get_field_by_name(self, name):
        " Return a copy of the field with the given `name`. "        
        return self._array[name]
    

    def get_info(self, cindex):
        """
        Retrieve Info object for field with name or index `cindex`.
        If there is no such info, then the info is created.
        """
        name = self.get_name(cindex)
        if not self._infos.has_key(name):
            self._infos[name] = Table.Info()
            
        return self._infos[name]

    def get_infos(self):
        " Return a dictionary with all Info objects. "
        infos = {}
        for name in self.names:
            infos[name] = self.get_info(name)
        return infos
    infos = property(get_infos)

    def get_index(self, cindex):
        " Return index of field with given name or index `cindex`. "
        if isinstance(cindex, int):
            return cindex
        elif isinstance(cindex, basestring):
            return self._array.dtype.fields[-1].index(cindex)
    
    def get_name(self, cindex):
        " Return name of field with given name or index `cindex`. "
        if isinstance(cindex, basestring):
            return cindex
        elif isinstance(cindex, int):
            return self._array.dtype.fields[-1][cindex]

    def get_names(self):
        " Return a list of all field names. "
        return self._array.dtype.fields[-1]
    names = property(get_names)

         
    def get_column_dtype(self, cindex):
        name = self.get_name(cindex)
        return self._array.dtype.fields[name][0]

    def rename(self, cindex, new_name):
        """
        Rename the field with the name or index `cindex` to the new name.        
        """
        a = self._array
        old_name = self.get_name(cindex)
        new = dict(a.dtype.fields)
        new[new_name] = new[old_name]
        del new[old_name]
        del new[-1]
        a.dtype = numpy.dtype(new)

        # keep field infos in sync
        self._infos[new_name] = self._infos[old_name]
        del self._infos[old_name]
        self.sig_register('update-fields')        

    



   

###############################################################################

def setup_test_table():

    a = numpy.array( [ ('Li-I', 7.0, 92.2),                       
                       ('Na', 22.9, 100.0),
                       ('Zn-I', 62.9, 64.0)],
                       dtype = {'formats': ['S10', 'f4', 'f4'],
                                'names': ['element', 'amu', 'abundance']})

    # TODO: allow passing field information 
#    infos = designation='X', label='some data'
#    designation='Y', label='some data'
#    designation='Y', label='some data'

    return Table(a)

    
def test():
    ds = setup_test_table()
    ds.dump()
    
    print "Rearranging"
    ds.rearrange( [1,2,0] )
    ds.dump()

    print "Remove first field"
    ds.remove_column(0)
    ds.dump()

    print "Resizing the Table to 10 rows"
    ds.resize(10)
    ds.dump()

    print "Resizing the Table to 6 rows"
    ds.resize(6)
    ds.dump()

    print "Delete rows 1-3"
    ds.delete_n_rows(1, 2)
    ds.dump()
    raise SystemExit

    # remove second field
    c = ds.field(1)
    ds.remove(c)
    #print ds

    

   
if __name__ == "__main__":
    test()
    
