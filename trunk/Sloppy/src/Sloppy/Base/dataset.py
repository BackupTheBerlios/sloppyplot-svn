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

from Sloppy.Base.tree import Node
from Sloppy.Base.error import NoData

from Sloppy.Lib.Signals import HasSignals
from Sloppy.Lib.Undo import UndoInfo, UndoList, NullUndo
from Sloppy.Lib.Props import HasProperties, String, Unicode, VP


import numpy

##import tempfile, os
##from Sloppy.Base.dataio import read_table_from_stream, read_table_from_file


#------------------------------------------------------------------------------

class FieldInfo(HasProperties):
    label = Unicode()       
    designation = VP(['X','Y','XY','XERR', 'YERR', 'LABEL'])
    query = String()


class Dataset(Node, HasSignals):
    
    def __init__(self, array=None):
        Node.__init__(self)
        HasSignals.__init__(self)
       
        self.key = "" # TODO: should be moved to parent object!    
        self.change_counter = 0
        self.__is_valid = True
        self._table_import = None

        self.sig_register('closed')
        self.sig_register('notify')
        self.sig_register('update-fields')
        
        if array is None:
            array = numpy.array([(0.0,0.0)],
                                dtype={'names':['col1','col2'],
                                       'formats':['f4','f4']})                   
        self._array = array
        self._infos = {}


    # Item Access -------------------------------------------------------------

    def get_value(self, cindex, row):
        return self._array[self.get_name(cindex)][row]
    
    def set_value(self, cindex, row, value, undolist=[]):
        col = self.get_field(cindex)
        old_value = col[row]
        col[row] = value
        undolist.append(UndoInfo(self.set_value, col, row, old_value))


    # Field Access -----------------------------------------------------------
    
    def get_field(self, cindex):
        " Return a copy of the field with the given name or index `cindex`. "
        if isinstance(cindex, basestring):
            return self.get_field_by_name(cindex)
        elif isinstance(cindex, int):
            return self.get_field_by_index(cindex)
        else:
            raise TypeError("Field must be specified using either a string or a field index.")

    def get_field_by_index(self, index):
        " Return a copy of the field with the given `index`. "
        return self.array[ self._array.dtype.fields[-1][index] ]

    def get_field_by_name(self, name):
        " Return a copy of the field with the given `name`. "        
        return self.array[name]

    # Row Access -------------------------------------------------------------

    def get_row(self, i):
        return self.array[i]
        
    # Field Manipulation -----------------------------------------------------


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
        Append a list of fields `cols` with a list of names `names`
        at position `cindex`. 
        """
        a = self._array
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
        
        self._array = new_array
        


    # TODO
    def rearrange(self, order):
        """
        Rearrangement of fields.

        Uses _rearrange internally, but adds a check to make sure that
        the number of fields is preserved.
        """        
        # validity check 
        if len(order) != len(self._array.dtype.fields[-1]):
            raise ValueError("Rearrange order must be of the same length as before.")

        self._rearrange(order)


    # TODO
    def _rearrange(self, order):
        a = self._array
        
        # Create new descriptor and new infos.
        # The new infos are created because it is possible to
        # specify less fields in the rearrangement.
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

        self._array = new_array
        self._infos = new_infos
        self.sig_register('update-fields')        
        
        
    # TODO
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


    # TODO
    def remove(self, cindex, n=1):
        """
        Remove n fields starting at field with name or index `cindex`.
        """
        index = self.get_index(cindex)
        order = range(len(self._array.dtype.fields[-1]))
        for i in range(n):
            order.pop(index)
        self._rearrange(order)
        

    # Row Manipulation --------------------------------------------------------

    def insert_n_rows(self, i, n=1, undolist=[]):
        """
        Insert `n` empty rows into each field at row `i`.
        """
        self.insert_rows(i, rows=numpy.zeros((n,), dtype=self._array.dtype), undolist=[])

    def insert_rows(self, i, rows, undolist=[]):
        """
        Insert the given `rows` (list of one-dimensional arrays) at row `i`.
        """
        self._array = numpy.concatenate([self._array[0:i], rows, self._array[i:]])
        undolist.append(UndoInfo(self.delete_n_rows, i, len(rows), only_zeros=True))

    def extend(self, n, undolist=[]):
        """
        Add `n` rows to the end of all fields.
        """
        self.insert_n_rows(len(self._array), n, undolist=undolist)

    def delete_n_rows(self, i, n=1, only_zeros=False, undolist=[]):
        """
        Delete `n` rows, starting at the row with the index `i`.
        The keyword arg `only_zeros` is an internal argument needed
        for better undo performance.              
        """
        n = min(len(self._array)-i, n)

        if only_zeros is True:
            ui = UndoInfo(self.insert_n_rows, i, )
        else:
            undo_data = numpy.array(self._array[i:i+n])            
            ui = UndoInfo(self.insert_rows, i, undo_data)
            
        self._array = numpy.concatenate([self._array[0:i], self._array[i+n:]])
        undolist.append(ui)
        
        # TODO: return cut data ??

    def resize(self, nrows, undolist=[]):
        """
        Resize array to given number of `nrows`.
        """
        current_nrows = self._array.shape[0]
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
        a = self._array
        print
        fields = a.dtype.fields
        print "\t".join(fields[-1])
        print "\t".join([str(fields[key][0]) for key in fields[-1]])
        print
        for row in a:
            print "\t".join(str(item) for item in row.item())
        print


    # Information -------------------------------------------------------------

    def get_array(self):
        if self._array is None:
            raise NoData
        return self._array

    def set_array(self, array, infos={}, undolist=[]):
        ui = UndoInfo(self.set_array, self._array, self._infos)

        self._array = array
        self._infos = infos
        self.sig_emit('update-fields')
        
        undolist.append(ui)
        
    array = property(get_array, set_array)

            
    def get_nrows(self):
        return len(self._array)
    nrows = property(get_nrows)

    def get_ncols(self):
        return len(self._array.dtype.fields) - 1
    ncols = property(get_ncols)
    
    def get_info(self, cindex):
        """
        Retrieve FieldInfo object for field with name or index `cindex`.
        If there is no such info, then the info is created.
        """
        name = self.get_name(cindex)
        if not self._infos.has_key(name):
            self._infos[name] = FieldInfo()
            
        return self._infos[name]

    def get_infos(self):
        " Return a dictionary with all FieldInfo objects. "
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
        return self.array.dtype.fields[-1]
    names = property(get_names)

    
    #######################################################################
    # Everything below this point is subject to dismissal

    #----------------------------------------------------------------------
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

    #----------------------------------------------------------------------
        
    def close(self):
        self.sig_emit('closed')        
        self.data = None

    def detach(self):
        self.sig_emit('closed')                

    def is_empty(self):
        " Returns True if the Dataset has no data or if that data is empty. "
        return self.array is None or len(self.array) == 0
        
    #----------------------------------------------------------------------

    # I guess these access things should go into the main object, i.e.
    # into the tree object ???
    
#     def get_data(self):
#         if self._table_import is not None:
#             self.import_table(*self._table_import)
#             self._table_import = None
#         return self.data

#     def import_table(self, project, filename, typecodes, field_props, importer_key):
#         dir = tempfile.mkdtemp('spj')
#         name = os.path.join(dir, filename)
#         project._archive.extract(filename, dir)
        
#         try:
#             table = read_table_from_file(name, importer_key, field_props=field_props)
#         finally:
#             os.remove(name)
#             os.rmdir(os.path.join(dir, 'datasets'))
#             os.rmdir(dir)
        
#         self.data = table
        
        
#     def set_table_import(self, *args):
#         self._table_import = args


    def get_field_type(self, cindex):
        name = self.get_name(cindex)
        return self.array.dtype.fields[name][0].type
         




###############################################################################

def setup_test_dataset():

    a = numpy.array( [ ('Li-I', 7.0, 92.2),                       
                       ('Na', 22.9, 100.0),
                       ('Zn-I', 62.9, 64.0)],
                       dtype = {'formats': ['S10', 'f4', 'f4'],
                                'names': ['element', 'amu', 'abundance']})

    # TODO: allow passing field information 
#    infos = designation='X', label='some data'
#    designation='Y', label='some data'
#    designation='Y', label='some data'

    return Dataset(a)

    
def test():
    ds = setup_test_dataset()
    ds.dump()
    
    print "Rearranging"
    ds.rearrange( [1,2,0] )
    ds.dump()

    print "Remove first field"
    ds.remove(0)
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
    
