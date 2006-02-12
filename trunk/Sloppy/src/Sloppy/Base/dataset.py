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
logger = logging.getLogger("Base.dataset")

from Sloppy.Base import tree, utils

from Sloppy.Lib.Signals import HasSignals
from Sloppy.Lib.Undo import UndoInfo, UndoList, NullUndo
from Sloppy.Lib.Props import HasProperties, String, Unicode, VP

import numpy


# TODO: check if info objects are copied or not.

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

    def new_array_from_list(self, rows, cols):
        " Return a new array from a list of arrays. "
        raise RuntimeError("not implemented")

    def new_array_from_columns(self, cols, n):
        " Return a new array from the columns of the existing array"
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
        return self._array[row]
    
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
            self.remove_n_rows(nrows, current_nrows - nrows, undolist=[])
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

    def remove_n_rows(self, row, n=1, only_zeros=False, undolist=[]):
        """
        Delete `n` rows, starting at the row with the index `row`.
        The keyword arg `only_zeros` is an internal argument needed
        for better undo performance.

        Returns array with removed rows.
        """
        n = min(self.nrows-row, n)
        if only_zeros is True:
            undo_data = numpy.zeros((n,),dtype=self.formatstring)
            ui = UndoInfo(self.insert_n_rows, row, )
        else:
            undo_data = numpy.array(self._array[row:row+n])            
            ui = UndoInfo(self.insert_rows, row, undo_data)
            
        self._array = numpy.concatenate([self._array[0:row], self._array[row+n:]])
        undolist.append(ui)

        return undo_data


    # Column Manipulation ---------------------------------------------------------
    
    def rearrange(self, order, undolist=[]):
        """ Rearrange Dataset columns.
        
        The list 'order' is a valid permutation of the column indices.
        """
        # Uses _rearrange internally, but adds a check to make sure that
        # the number of fields is preserved.
        if len(order) != self.ncols:
            raise ValueError("Rearrange order must be of the same length as before.")

        # create reverse mapping for undo information
        reverse_order = []
        for i in range(self.ncols):
            reverse_order.append(order.index(i))
        ui = UndoInfo(self.rearrange, reverse_order)
        
        self._rearrange(order)
        undolist.append(ui)
    
    def _rearrange(self, order):
        # Undoing a rearrange is not trivial, because _rearrange
        # can also be used to remove columns by providing a new 'order'
        # list with less entries than before. This is why the calling
        # function needs to take care of undoing the operation.
        raise RuntimeError("not implemented")

    def remove_column(self, col, undolist=[]):
        " Remove a single column at specified index. "
        return self.remove_n_columns(col, 1, undolist=[])
        
    def remove_n_columns(self, col, n=1, undolist=[]):
        " Remove 'n' columns starting at column with specified index. "
        raise RuntimeError("not implemented")

    def append_columns(self, array, undolist=[]):
        " Append the given array to the Dataset array. "        
        self.insert_columns(self.ncols-1, array, undolist=undolist)

    def insert_columns(self, col, array, undolist=[]):
        """ Insert the given 'array' at specified index 'col'.        

        This high-level function accepts not only arrays, but also
        lists/tuples, Datasets or an integer representing a number of
        empty columns.        
        """
        if isinstance(array, int):
            ds = self.__class__(self.new_array(rows=self.nrows, cols=array))
        elif isinstance(array, (list, tuple)):
            ds = self.__class__(self.new_array_from_list(array))
        elif isinstance(array, numpy.ndarray):
            ds = self.__class__(array)
            
        self.insert_(col, ds, undolist=undolist)

    def insert_(self, col, ds, undolist=[]):
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


    def __init__(self, array=None, infos={}):
        self._infos = infos
        Dataset.__init__(self, array)


    # Array ---------------------------------------------------------------
    
    def set_array(self, array, infos={}, undolist=[]):
        ui = UndoInfo(self.set_array, self._array, self._infos)

        self._array = array
        self._infos = infos
        self.sig_emit('update-fields')
        
        undolist.append(ui)

    def new_array(self, rows, cols):
        return numpy.zeros( (rows,), dtype='f4'*cols)

    def new_array_from_list(self, alist):
        # assume a list of rank 2, e.g. [[1,2,3], [4,5,6]]
        return numpy.array( alist, dtype='f4'*len(alist) )
                            
    def new_array_from_columns(self, col, n):
        atype = {'names': self.names[col:col+n],
                 'formats': self.formats[col:col+n]}
        print atype
        a = numpy.zeros( (self.nrows,), atype)

        for name in a.dtype.fields[-1]:
            a[name] = self._array[name]
            
        return a
        
    def get_default_array(self):
        return numpy.array([(0.0,0.0)], dtype='f4,f4')


    def copy(self):
        a = self._array.copy()
        infos = self.infos.copy()
        return self.__class__(a, infos=infos)
        
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
        fields = self._array.dtype.fields
        field_descr = "  ".join(fields[-1])
        format_descr = "  ".join(self.formats)

        length = max(len(format_descr), len(field_descr))
        
        print "-"*length
        print field_descr
        print format_descr
        print "infos = "
        for key, info in self._infos.iteritems():
            print "   ", key, "= ", info.get_values()
        print "-"*length
        for row in self._array:
            print "  ".join(str(item) for item in row.item())

        print "-"*length

    # Row Manipulation ----------------------------------------------------

    def insert_rows(self, i, rows, undolist=[]):        
        self._array = numpy.concatenate([self._array[0:i], rows, self._array[i:]])
        undolist.append(UndoInfo(self.remove_n_rows, i, len(rows), only_zeros=True))


    # Column Manipulation ---------------------------------------------------------

    def _rearrange(self, order):
        a = self._array

        # Create new descriptor and new infos.
        # The new infos are created because it is possible to
        # specify less fields in the rearrangement.
        descriptor = a.dtype.arrdescr
        names = a.dtype.fields[-1]

        new_descriptor = []
        for index in order:
            if isinstance(index, basestring):
                name = index
                index = names.index(index)
            else:
                name = names[index]
            new_descriptor.append(descriptor[index])

        new_array = numpy.zeros(a.shape, dtype=numpy.dtype(new_descriptor))       
        for name in new_array.dtype.fields[-1]:
            new_array[name] = a[name]

        self._array = new_array
        self.sig_emit('update-fields')


    def insert_(self, col, table, undolist=[]):
        
        col = self.get_index(col)
       
        # We merge in the description of the new array into the
        # existing array 'self.array'. Unfortunately we must
        # make sure that each new added field has a unique name.
        new_names = self.names[:]
        descriptor = self._array.dtype.arrdescr[:]
        infos = {}
        i = 0
        for name in table.names:
            typecode = table.get_column_type(name)
            new_name = utils.unique_names([name], new_names)[0]
            new_names.insert(i+col, new_name)
            descriptor.insert(i+col, (new_name, typecode))
            
            if table._infos.has_key(name):
                infos[new_name] = table._infos[name].copy()
            i+=1

        new_array = numpy.zeros( (self.nrows,), dtype=numpy.dtype(descriptor))

        # fill new array with data
        # copy data from existing dataset
        for name in self.names:
            new_array[name] = self._array[name]

        # ..and then copy data from table object.
        # Because the names might have changed, we refer
        # to the columns by their index!    
        i = 0
        for name in table.names:
            new_array[new_names[col+i]] = table._array[name]
            i += 1
            
        # undo information
        undolist.append(UndoInfo(self.remove_n_columns, col, table.ncols))
        undolist.append(UndoInfo(self.update_infos, infos))
        
        self._array = new_array
        


    def remove_n_columns(self, col, n=1, undolist=[]):
        index = self.get_index(col)
        order = range(self.ncols)
        for i in range(n):
            order.pop(index)

        # create undo information
        ul = UndoList().describe("remove columns")        
        old_names = self.names[col:col+n]
        undo_array = self.new_array_from_columns(col, n)
        undo_infos = {}
        for name in old_names:
            if self._infos.has_key(name):
                print "COPYING INFO ", name
                undo_infos[name] = self._infos[name].copy()
        undo_table = self.__class__(undo_array, undo_infos)
        print "BEFORE REARRANGE", self._infos
        self._rearrange(order)
        print "AFTER REARRANGE", self._infos
        undolist.append(UndoInfo(self.insert_columns, col, undo_table))
        return undo_table


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

    def update_infos(self, adict, undolist=[]):
        " TODO . Value of None => delete Info"
        undo_dict = {}
        for name, info in adict.iteritems():
            if self._infos.has_key(name) is True:
                undo_dict[name] = self._infos
            else:
                undo_dict[name] = None
                
            if info is None:
                try:
                    del self._infos[name]
                except KeyError:
                    logger.warn("update_infos: info with name %s did not exist" % name)
            else:
                self._infos[name] = info

        undolist.append(UndoInfo(self.update_infos, undo_dict))
                
    infos = property(get_infos)

    def get_formats(self):
        " Return a list with the column formats, e.g. ['f4','f4'] "
        rv = []
        fields = self._array.dtype.fields
        for name in self.names:
            dt = fields[name][0]
            rv.append( '%s%d' % (dt.kind,dt.itemsize) )
        return rv
    formats = property(get_formats)
    
    def get_formatstring(self):
        " Return a string with the column formats, e.g. 'f4,f4' "
        return ','.join(self.formats)
    formatstring = property(get_formatstring)
    
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




    
def test():
    a = numpy.array( [(1,2,3), (4,5,6), (7,8,9)], dtype='f4,i2,f4' )
    ds = Table(a)

    # cut_info = ds.remove_n_rows(1,1)
#     ds.dump()
#     print "cut = ", cut_info
#     ds.insert_rows(1,cut_info)
#     ds.dump()

    ds.get_info(0)
    ds.get_info(1).designation = 'Y'
    ds.dump()
    cut_info = ds.remove_column(1)
    print "Cut column 1"
    ds.dump()
    print "cut = ", cut_info._infos
    cut_info.dump()
    print "Changing a designation of last column"
    ds.get_info(1).designation = 'XERR'
    print "re-inserting the column again"
    ds.insert_(1, cut_info)
    ds.dump()
    raise SystemExit

    ds.dump()

    print 
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
    ds.remove_n_rows(1, 2)
    ds.dump()
    raise SystemExit

    # remove second field
    c = ds.field(1)
    ds.remove(c)
    #print ds

    
    

   
if __name__ == "__main__":
    test()
    
