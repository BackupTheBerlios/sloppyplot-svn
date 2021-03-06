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
from Sloppy.Lib.Undo import UndoInfo, UndoList, NullUndo, Journal
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
        self._import = None

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

    # what is the difference btw. close and detach?
    def close(self):
        print "CLOSING"
        self.sig_emit('closed')
    detach = close
    

    def is_empty(self):
        " Returns True if the Dataset has no data or if that data is empty. "
        return self._array is None or len(self._array) == 0


    #----------------------------------------------------------------------
    # Any derived classes needs to implement the following functions,
    # that provide some basic functionality for arrays of rank 2.
    #
        
    def get_array(self):
        " Return internal array. "
        if self._import is not None:
            self._import(self)
            self._import = None        
        return self._array
    
    def set_array(self, array):
        " Set internal array. "
        raise RuntimeError("not implemented")

    array = property(get_array, set_array)
    
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

    # Get/Set of values or of array chunks --------------------------------
    
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

    def set_column(self, col, array, undolist=[]):
        " Set column to given value. "
        raise RuntimeError("not implemented")

    def get_region(self, row, col, height, width, cut=False):
        " Return an array containing the given data range. "
        raise RuntimeError("not implemented")

    def set_region(self, row, col, array, coerce=True, undolist=[]):
        " Insert the given array into the dataset at specified row and col. "
        raise RuntimeError("not implemented")
    

    # Information ---------------------------------------------------------
    
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

    _pytypemap = {numpy.float32 : float,
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
        return self._pytypemap[self.get_column_type(col)]
    
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
            self.remove_n_rows(nrows, current_nrows - nrows, undolist=undolist)
        elif nrows > self.nrows:
            self.insert_n_rows(current_nrows, nrows - current_nrows, undolist=undolist)
        else:
            undolist.append(NullUndo())        

    def extend(self, n, undolist=[]):
        " Add `n` rows to the end of all fields. "
        self.resize(self.nrows+n, undolist=undolist)

    def insert_n_rows(self, row, n=1, undolist=[]):
        " Insert `n` empty rows at the given row index. "
        self.insert_rows(row, rows=numpy.zeros((n,), dtype=self._array.dtype), undolist=undolist)

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
        return self.remove_n_columns(col, 1, undolist=undolist)
        
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
        elif isinstance(array, self.__class__):
            ds = array
        else:
            raise ValueError("invalid value for insert_columns: %s" % array)
            
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

        public_props=['label', 'designation']


    def __init__(self, array=None, infos={}):
        self._infos = {}
        Dataset.__init__(self, array)
        self._infos = infos


    # Array ---------------------------------------------------------------

    def set_array(self, array, infos={}, undolist=[]):
        ui = UndoInfo(self.set_array, self._array, self._infos)
        self._array = array
        self._infos = infos
        undolist.append(ui)
        
        self.sig_emit('update-fields')    

    array = property(Dataset.get_array, set_array)

    
    def new_array(self, rows, cols):
        names = ['f%d'%i for i in range(cols)]
        formats = ['f4']*cols
        return numpy.zeros((rows,), dtype={'names':names,'formats':formats})

    def new_array_from_list(self, alist):
        # assume a list of rank 2, e.g. [[1,2,3], [4,5,6]]
        names = ['f%d'%i for i in range(len(alist))]
        formats = ['f4']*len(alist)        
        return numpy.array(alist, dtype={'names':names,'formats':formats})
                            
    def new_array_from_columns(self, col, n):
        atype = {'names': self.names[col:col+n],
                 'formats': self.formats[col:col+n]}
        print atype
        a = numpy.zeros((self.nrows,), atype)

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
        col = self.get_column(cindex)
        old_value = col[row]
        col[row] = value
        undolist.append(UndoInfo(self.set_value, col, row, old_value))


    # for get_column, see get_column

    def get_region(self, row, col, height, width, cut=False):        
        formats = ','.join(self.formats[col:col+width])
        a = numpy.zeros( (height,), formats)

        i = 0
        names = a.dtype.fields[-1]
        for name in self.names[col:col+width]:
            a[names[i]] = self._array[name][row:row+height].copy()
            if cut is True:
                self._array[name][row:row+height] = numpy.zeros((height,), self.formats[col+i])
            i += 1

        return a
    

    def set_region(self, row, col, array, coerce=True, undolist=[]):
        undo_data = self.get_region(row, col, len(array), len(array.dtype.fields[-1]))
        ul = UndoList()
        ul.append(UndoInfo(self.set_region, row, col, undo_data))

        try:
            names = array.dtype.fields[-1]
            i = 0
            for name in self.names[col:col+len(array)]:
                if coerce is True:
                    z = self.get_column_type(col+i)(array[names[i]])
                else:
                    z = array[names[i]]
                self._array[name][row:row+len(array)] = z
                i += 1
        except Exception, msg:
            print "set_region failed: %s.  undoing." % msg
            ul.execute()
        else:            
            undolist.append(ul)
                   
    # Information ---------------------------------------------------------

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
        descriptor = a.dtype.descr
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
        # existing array 'self._array'. Unfortunately we must
        # make sure that each new added field has a unique name.
        new_names = self.names[:]
        descriptor = self._array.dtype.descr[:]
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
        ul = UndoList()
        self.update_infos(infos, undolist=ul)        
        ul.append(UndoInfo(self.remove_n_columns, col, table.ncols))
        undolist.append(ul)

        self._array = new_array
        self.sig_emit('update-fields')        
        


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
                undo_infos[name] = self._infos[name].copy()
        undo_table = self.__class__(undo_array, undo_infos)
        self._rearrange(order)
        undolist.append(UndoInfo(self.insert_columns, col, undo_table))

        self.sig_emit("update-fields")
        
        return undo_table


    #----------------------------------------------------------------------
    # SPECIFIC TO TABLE OBJECTS
    
    def get_column(self, cindex):
        " Return a copy of the field with the given name or index `cindex`. "
        if isinstance(cindex, basestring):
            return self.get_column_by_name(cindex)
        elif isinstance(cindex, int):
            return self.get_column_by_index(cindex)
        else:
            raise TypeError("Field must be specified using either a string or a field index.")

    def get_column_by_index(self, index):
        " Return a copy of the field with the given `index`. "
        return self._array[ self._array.dtype.fields[-1][index] ]

    def get_column_by_name(self, name):
        " Return a copy of the field with the given `name`. "        
        return self._array[name]

    def set_column(self, col, array, undolist=[]):
        name = self.get_name(col)        
        old_data = self._array[name].copy()
        self._array[name] = array
        undolist.append(UndoInfo(self.set_column, col, old_data))
        self.sig_emit('notify')

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
        """ Update the Table's info dict with the given dict.

        Besides providing an undo, the method differs from
        the update method of a python dictionary in the followin
        way: A value of None implies that the info object
        is to be deleted (after all any value in the info dict
        should be a Table.Info object).
        """
        undo_dict = {}
        for name, info in adict.iteritems():
            if self._infos.has_key(name) is True:
                undo_dict[name] = self._infos[name]
            else:
                undo_dict[name] = None
                
            if info is None:
                try:
                    self._infos.pop(name)
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
        return list(self._array.dtype.fields[-1])
    names = property(get_names)

         
    def get_column_dtype(self, cindex):
        name = self.get_name(cindex)
        return self._array.dtype.fields[name][0]

    def rename_column(self, col, new_name, undolist=[]):
        """
        Rename the field with the name or index `cindex` to the new name.        
        """
        index = self.get_index(col)
        new_names = self.names[:]
        old_name = new_names[index]
        new_names[index] = new_name
        self._array.dtype = numpy.dtype({'formats': self.formats, 'names': new_names})

        print "NEW DTYPE", self._array.dtype

        # keep field infos in sync
        if self._infos.has_key(old_name):
            self._infos[new_name] = self._infos.pop(old_name)

        undolist.append(UndoInfo(self.rename_column, col, old_name))
        self.sig_register('update-fields')        

    



   

###############################################################################




    
def test():
    a = numpy.array( [(1,2,3), (4,5,6), (7,8,9)], dtype='f4,i2,f4' )
    ds = Table(a)
    ds.get_info(0)
    ds.get_info(1).designation = 'Y'

    journal = Journal()
    ds.insert_n_rows(0, 10, undolist=journal)
    ds.dump()
    journal.undo()
    ds.dump()
    raise SystemExit
    # cut_info = ds.remove_n_rows(1,1)
#     ds.dump()
#     print "cut = ", cut_info
#     ds.insert_rows(1,cut_info)
#     ds.dump()


#     ds.dump()
#     cut_info = ds.remove_column(1)
#     print "Cut column 1"
#     ds.dump()
#     print "cut = ", cut_info._infos
#     cut_info.dump()
#     print "Changing a designation of last column"
#     ds.get_info(1).designation = 'XERR'
#     print "re-inserting the column again"
#     ds.insert_(1, cut_info)
#     ds.dump()
    ds.dump()
    r = ds.get_region(0,0,2,2, cut=True)
    ds.dump()
    print ds._array, r
    ds.set_region(0,1,r, coerce=False)
    ds.dump()
    raise SystemExit
    print 
    print "Rearranging"
    ds.rearrange( [1,2,0] )
    ds.dump()
    raise SystemExit

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
    
