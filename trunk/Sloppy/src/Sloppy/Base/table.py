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
Table class (list of 1d arrays)
"""


from Numeric import array, ArrayType, zeros, rank, concatenate


from Sloppy.Lib.Signals import HasSignals
from Sloppy.Lib.Props import *



class AsArray(Transformation):

    def __init__(self, _rank):
        self._rank = _rank

    def __call__(self, value):
        # check type
        if isinstance(value, ArrayType):
            pass            
        elif isinstance(value, (tuple,list)):
            value = array(value)
        else:
            raise TypeError("pArray data must be of type array/tuple/list.")

        # check rank
        if rank(value) != self._rank:
            raise TypeError("pArray data must be of rank %d but it is %d." % (_rank, rank(value)))

        return value


class pArray(Prop):

    def __init__(self, rank=1, doc=None, blurb=None):
        Prop.__init__(self, coerce=AsArray(rank), doc=doc, blurb=blurb)
        self.rank = rank

        
        
class Column(HasProps):

    key = pUnicode()
    
    designation = pString(CheckValid(['X','Y','XY','XERR', 'YERR', 'LABEL']),
                          default='X')
    query = pString()
    label = pUnicode()
    data = pArray(rank=1)

    public_props = ['key', 'label', 'designation']

    def __str__(self):
        return "%s (%s): %s" % (self.key, self.designation, self.label)

    def typecode(self):
        return self.data.typecode()
        



class Table(object, HasSignals):

    def __init__(self, data=None, ncols=0, nrows=0, typecodes=None):
        """

        You can either pass a tuple/array as 'data' argument and the
        Table will contain this data.  Any other keyword will simply
        be ignored!

        OR, you can specify some of the other keywords:

        - A single typecode, e.g. 'f', will create a Table with `ncols`
          columns of type 'f'. If `ncols` is unspecified, a Table with
          a single column will be created.

        - A string of typecodes, e.g. 'fdf' specifies the typecode for
          each column.  If `ncols` is provided, the length of the
          string must match the number of requested columns or a
          ValueError is raised.

        - A list of typecodes, e.g. ['f', 'd'] is equivalent to 'fd'.
          Note however that ['f'] is not the same as 'f' since the
          list form will always require the length of the list to be
          the same as the `ncols` given.
          
        """        

        HasSignals.__init__(self)
        self.sig_register('update-columns')
        
        self._columns = []

        if data is not None:
            data = AsArray(_rank=2)(data)
            self._columns = [Column(data=c) for c in data]
            
        else:
            if ncols > 0:
                if isinstance(typecodes, basestring) and len(typecodes) > 1:
                    typecodes = list(typecodes)

                if isinstance(typecodes, (list,tuple)):
                    if len(typecodes) != ncols:
                        raise ValueError("When specifying the number of columns, you may either specify a single typecode or a list with that many entries.")
                elif typecodes is None:
                    tc = 'f'
                    typecodes = list()
                    for i in range(ncols):
                        typecodes.append(tc)
                else:
                    tc = typecodes
                    typecodes = list()
                    for i in range(ncols):
                        typecodes.append(tc)                    

            self._nrows = nrows

            typecodes = typecodes or []
            for tc in typecodes:
                self._columns.append( self.new_column(tc) )

        self.update_cols()        
        self.update_rows()



    def __getitem__(self, i):
        return self.columns[i].data
    
    def __setitem__(self, i, item): 
        # use "set_item" to get undo functionality
        self.columns[i] = self.check_item(item)

    def column(self, index):
        " Return Column object with given `index`. "
        return self.columns[index]
    get_column = column
    
    def set_columns(self, columns):
        self._columns = columns
        self.update_cols()
        self.update_rows()
        
    def set_item(self, i, item):
        self.columns[i] = self.check_item(item)
        
    def new_column(self, typecode=None, **kwargs):
        """        
        Returns a new Column with the given typecode with the number
        of rows that this Table requires, i.e. a Column with a
        one-dimensional array of the length table.rows, with the
        `typecode` and only zeros.  If no typecode is given, then the
        typecode of the first existing column is used, or if there is
        no column yet, 'f'.
        Any keyword argument is passed on to the Column constructor.
        """
        if typecode is None:
            if self.typecodes is not None:
                typecode = self.typecodes[0]
            else:
                typecode = 'f'

        return Column( data = zeros((self.nrows,), typecode), **kwargs)            


    def get_value(self, col, row):
        return self[col][row]

    def set_value(self, col, row, value):
        self[col][row] = value


    def is_equal(self, other_table):
        # compare table sizes and typecodes
        if self.ncols != other_table.ncols:
            return False
        if self.typecodes != other_table.typecodes:
            return False

        # compare column data -- the column keywords are not compared!
        for i in range(self.ncols):
            if self[i] != other_table[i]:
                return False

        return True


    #--- column operations ------------------------------------------------
    
    def append(self, item):
        " Append a column `item`. "
        self.columns.append( self.check_item(item) )
        self.update_cols()

    def insert(self, i, item):
        " Insert a column `item` at index `i`. "
        self.columns.insert(i, self.check_item(item))
        if i < 0: # account for negative indexes
            i = max(0, self.ncols + i - 1)
            print i
        self.update_cols()        

    def remove(self, column):
        " Remove given column from Table. "
        index = self.columns.index(column)
        self.remove_by_index(index)
        
    def remove_by_index(self, i):
        " Remove column with index `i`. "
        self.columns.pop(i)
        self.update_cols()

    def rearrange(self, order):
        """
        Rearrange the columns of the table, that means both the data
        and the infos.

        The new order must be given as a list with each column
        appearing exactly once, i.e. it must be a permuation of the
        column indices.  A Table with 5 columns might be rearranged
        like this:

        >>> tbl.rearrange( [4,3,2,1,0] )  # reverse column order
        >>> tbl.rearrange( [1,0,2,3,4] )  # swap columns 1 and 2
        >>> tbl.rearrange( [3,2,1,4,0] )  # mix columns
        >>> tbl.rearrange( [0,1,2,3,4] )  # identity

        Currently there is no validity check beyond checking the length
        of the list.
        """
        if len(order) != len(self.columns):
            raise TypeError("`order` argument must be a list of the same length as the array; it has a length of %d but it should be %d."
                            % (len(order), len(self.columns))  )

        new_columns = list()
        for n in range(len(order)):
            new_columns.append( self.columns[order[n]] )

        self._columns = new_columns
        self.update_cols()

    #--- row operations ----------------------------------------------------
    
    def resize(self, nrows):
        " Resize all columns to the given number of `nrows`. "
        nrows = max(0, nrows)
        if nrows < self.nrows:
            self.delete_n_rows( nrows, self.nrows - nrows)
        elif nrows > self.nrows:
            self.insert_n_rows( self.nrows, nrows - self.nrows)

    def extend(self, n):
        " Add `n` rows to the end of all columns. "
        self.insert_n_rows( self.nrows, n)

    def insert_n_rows(self, i, n=1):
        " Insert `n` rows into each column at row `i`. "
        rows = list()
        for tc in self.typecodes:
            rows.append( zeros((n,),typecode=tc) )
        self.insert_rows(i, rows)
        self.update_rows()

    def insert_rows(self, i, rows):
        """
        Insert the given `rows` (list of one-dimensional arrays) at row `i`.
        The given arrays must all have the same length and there must be
        exactly as many arrays as there are columns.  Of course the arrays
        must match the Column type or it must be possible to convert
        them to the Column type using astype.
        """
        # [ [all new rows of col1], [all new rows of col2], ...]
        if len(rows) != self.ncols:
            raise ValueError("When adding new rows, you must provide the values in a transposed form: TODO: EXAMPLE.")

        # To make sure that the operation does not fail and leaves invalid
        # data, we first create the new column datas in new_data, and then,
        # if it worked for all columns, we will assign the new data.
        new_data = list()
        j = 0
        first_length = None
        for col in self.columns:
            if first_length is None:
                first_length = len(rows[j])
            else:
                if len(rows[j]) != first_length:
                    raise ValueError("Each column must have the same number of rows inserted. Row %d has not the same length as Row 0" % j )
            new_data.append( concatenate([col.data[0:i], rows[j], col.data[i:]]) )
            j += 1

        # assign new data
        j = 0
        for col in self.columns:
            col.data = new_data[j]
            j += 1            
        self.update_rows()    
        
    def delete_n_rows(self, i, n=1):
        """
        Delete `n` rows, starting at the row with the index `i`.
        Returns the old data.
        """

        n = min(self.nrows-i, n)

        # To make sure that the operation does not fail and leaves invalid
        # data, we first create the new column datas in new_data, and then,
        # if it worked for all columns, we will assign the new data.
        new_data = list()
        rv = list()
        j = 0
        for col in self.columns:
            rv.append( col.data[i:i+n] )
            new_data.append(concatenate( [col.data[0:i], col.data[i+n:]] ))
            j += 1
            
        # assign new data
        j = 0
        for col in self.columns:
            col.data = new_data[j]
            j += 1            
        self.update_rows()

        return rv
                           

        
    #-- data info ----------------------------------------------------------    

    def get_columns(self):
        return self._columns

    columns = property(get_columns)

    def update_cols(self):
        """
        Call this whenever you add/remove a column or when you change
        the type of a column.
        """
        self._ncols = len(self._columns)
        self._typecodes = map(lambda x: x.typecode(), self._columns)

        # TODO: move to types.h
        type_map = {'d': float,
                    'f': float, # scipy.float32
                    'O': str,
                    'l': long,
                    'i': int}
        self._converters = map(lambda tc: type_map[tc], self._typecodes)

        self.sig_emit('update-columns') # FIXME ???
            

    def update_rows(self):
        " Call this whenever you add/remove a row. "
        try:
            self._nrows = len(self._columns[0].data)
        except IndexError:
            self._nrows = 0

    def get_nrows(self): return self._nrows
    nrows = property(get_nrows)
    def get_ncols(self): return self._ncols
    ncols = property(get_ncols)
    def get_typecode(self, i): return self._typecodes[i]
    def get_typecodes(self): return self._typecodes
    typecodes = property(get_typecodes)
    def get_typecodes_as_string(self): return reduce(lambda x,y: x+y, self.typecodes)
    typecodes_as_string = property(get_typecodes_as_string)
    def get_converters(self): return self._converters
    converters = property(get_converters)
    def get_converter(self, i): return self._converters[i]    
    def convert(self, i, value): return self._converters[i](value)

    def col(self, i): return self.columns[i].data
    def row(self, i): return RowIterator(self, i+1)   
    def iterrows(self): return RowIterator(self, 0)

    def __len__(self): return self.ncols
    
    def __str__(self):
        rv = ["\nTable (%d ncols: '%s', %d nrows)" % (self.ncols, self.typecodes_as_string, self.nrows) ]
        j = 0
        for col in self.columns:
            rv.append( "  col %d: %s" % (j, str(col)) )
            j += 1
        rv.append("\n")                

        n = 0
        for row in self.iterrows():
            rv.append( "[%d]  %s" % (n, row) )
            n += 1            


        return "\n".join(rv)

    
    #-- internal use ------------------------------------------------------
    
    def check_item(self, item):

        # check type
        if not isinstance(item, Column):
            item = Column(data=item)

        # check length
        if self.nrows > 0 and self.nrows != len(item.data):
            raise TypeError("Incompatible length %d of new column %s; Table columns must have a length of %d."
                            % (len(item.data), item, self.nrows))        

        return item
        




class RowIterator:

    def __init__(self, table, row):
        self.table = table
        self.row = row - 1
        table.get_columns()

    def __getitem__(self, j): return self.table[j][self.row]
    def __setitem__(self, j, value): self.table[j][self.row] = value
    def __get__(self): return map(lambda col: col[self.row], self.table)    
    def __str__(self):
        return '%s:' % ', '.join( map(lambda col: str(col[self.row]), self.table) )

    def __len__(self): return self.table.ncols
    
    def __getslice__(self, i, j): return map(lambda col: col[self.row], self.table[i:j])
    
    def __iter__(self): return self
    
    def next(self):
        if self.row + 1 < self.table.nrows:
            self.row += 1
            return self
        else:
            raise StopIteration

    def set(self, values):
        j = 0
        for v in values:
            self.table[j][self.row] = v
            j+=1




#--- CONVENIENCE FUNCTIONS ----------------------------------------------------


def table_to_array(tbl, typecode='f'):
    shape = (tbl.ncols, tbl.nrows)
    
    a = zeros( (tbl.ncols, tbl.nrows), typecode)
    for j in range(tbl.ncols):
        a[j] = tbl[j].astype(typecode)

    return transpose(a)


def array_to_table(a):
    if len(a.shape) != 2:
        raise TypeError("Array must be 2-dimensional if you want to convert it to a Table.")
    
    nrows, ncols =a.shape
    a = transpose(a)
    
    tbl = Table(ncols=ncols, nrows=nrows, typecodes=a.typecode)
    for j in range(tbl.ncols):
        tbl[j] = a[j]
        
    return tbl



#------------------------------------------------------------------------------

def setup_test_table():
    # setting up a new table
    tbl = Table()

    col1 = Column(data = [1.0,2,3,4,5], key='First', designation='X', label='some data')
    col2 = Column(data = [1.0,4,9,16,25], key='Second', designation='Y', label='some data')
    col3 = Column(data = [1.0,8,27,64,125], key='Third', designation='Y', label='some data')

    tbl.append(col1)
    tbl.append(col2)
    tbl.append(col3)    

    return tbl

    
def test():
    tbl = setup_test_table()
   
    # moving the new colum to second place
    tbl.rearrange( [0,1,2] )

    # removing the first column
    tbl.remove_by_index(0)

    # resizing the Table to 10 rows
    tbl.resize(10)
    #print tbl

    # resizing the Table to 6 rows
    tbl.resize(6)
    #print tbl

    # extending the Table with 4 rows => 10 rows total
    tbl.extend(4)
    #print tbl

    # delete rows 1-3
    tbl.delete_n_rows(1, 2)
    #print tbl

    # remove second column
    c = tbl.column(1)
    tbl.remove(c)
    #print tbl

    # create an array from the table
    a = table_to_array(tbl)
    #print a

    # create the table from that array
    # of course, the column information is lost
    tbl = array_to_table(a)
    print tbl
    

def test2():
    tbl = Table([[1,2,3,4],[2,4,9,16]])
    tbl2 = Table([[1,2,3,4],[2,4,9,15]])
    print tbl
    print tbl2
    print tbl.is_equal(tbl2)
    
if __name__ == "__main__":
    test2()
    
