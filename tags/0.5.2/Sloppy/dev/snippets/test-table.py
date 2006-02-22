import numpy


# TODO: the table could even have a reference to the Dataset and
# TODO: make sure that the keys and their metadata are in sync.

# TODO: table_to_array, array_to_table 

# TODO: regression tests

# TODO: change column type somehow _or_ replace column!!!



class TableProxy:

    def __init__(self, _array):
        self.array = _array


    # Column Access -----------------------------------------------------------
    
    def col(self, cindex):
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

    def index(self, cindex):
        " Return index of column with given name or index `cindex`. "
        if isinstance(cindex, int):
            return cindex
        elif isinstance(cindex, basestring):
            return self.array.dtype.fields[-1].index(cindex)

    def name(self, cindex):
        " Return name of column with given name or index `cindex`. "
        if isinstance(cindex, basestring):
            return cindex
        elif isinstance(cindex, int):
            return self.array.dtype.fields[-1][cindex]
        
        
    # Column Manipulation -----------------------------------------------------

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
                
            
    
    def _insert(self, cindex, cols, names):
        """
        Append a list of columns `cols` with a list of names `names`
        at position `cindex`.
        """
        a = self.array
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
        
        self.array = b

    def rearrange(self, order):
        """
        Rearrangement of columns.

        Uses _rearrange internally, but adds a check to make sure that
        the number of columns is preserved.
        """        
        # validity check 
        if len(order) != len(a.dtype.fields[-1]):
            raise ValueError("Rearrange order must be of the same length as before.")

        self._rearrange(order)
        
    def _rearrange(self, order):
        a = self.array
        
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

        self.array = b
        

    def rename(self, cindex, new_name):
        """
        Rename the given `cindex` to the new name.
        """
        a = self.array
        old_name = self.name(cindex)
        new = dict(a.dtype.fields) # get a writeable dictionary.
        new[new_name] = new[old_name]
        del new[old_name]
        del new[-1]  # get rid of the special ordering entry
        a.dtype = numpy.dtype(new)


    def remove(self, cindex, n=1):
        """
        Remove n columns starting at column with name or index `cindex`.
        """
        index = self.index(cindex)
        order = range(len(self.array.dtype.fields[-1]))
        for i in range(n):
            order.pop(index)
        self._rearrange(order)
        

    # Row Manipulation --------------------------------------------------------

    def insert_n_rows(self, i, n=1):
        """
        Insert `n` empty rows into each column at row `i`.
        """
        self.insert_rows(i, rows=numpy.zeros((n,), dtype=self.array.dtype))

    def insert_rows(self, i, rows):
        """
        Insert the given `rows` (list of one-dimensional arrays) at row `i`.
        """
        self.array = numpy.concatenate([self.array[0:i], rows, self.array[i:]])

    def extend(self, n):
        """
        Add `n` rows to the end of all columns.
        """
        self.insert_n_rows(len(self.array), n)

    def delete_n_rows(self, i, n=1):
        """
        Delete `n` rows, starting at the row with the index `i`.
        """
        n = min(len(self.array)-i, n)
        self.array = numpy.concatenate([self.array[0:i], self.array[i+n:]])

    def resize(self, nrows):
        """
        Resize array to given number of `nrows`.
        """
        current_nrows = self.array.shape[0]
        nrows = max(0, nrows)        
        if nrows < current_nrows:
            self.delete_n_rows( nrows, current_nrows - nrows)
        elif nrows > current_nrows:
            self.insert_n_rows( current_nrows, nrows - current_nrows)
            
    # Diagnostics -------------------------------------------------------------

    def dump(self):
        """
        Diagnostic dump to stdout of the array.
        """
        a = self.array
        print "-"*80
        fields = a.dtype.fields
        print "\t".join(fields[-1])
        print "\t".join([str(fields[key][0]) for key in fields[-1]])
        print
        for row in a:
            print "\t".join(str(item) for item in row.item())
        print "-"*80    


#------------------------------------------------------------------------------
dtype = numpy.dtype( {'names': ['name', 'age', 'weight'],
                      'formats': ['U30', 'i2', numpy.float32]} )

a = numpy.array( [(u'Bill', 31, 260),
                  ('Fred', 15, 135)], dtype=dtype )

table = TableProxy(a)

print table.col('name')
print table.col(1)

print table.array

print table.rearrange( ['name','weight', 'age'] )
table.dump()

col = table.col(1)
col = numpy.sin(table.col(1))
print col
table.dump()


table.array['weight'] = numpy.sin(table.array['weight'])
table.rename('weight', 'sin of weight')
table.dump()


# table.remove(1)
# table.dump()

# table.remove('age')
# table.dump()


table.resize(3)
table.dump()

table.remove('name',2)
table.dump()

table.insert(1, [0.1,0.2,0.4], 'floaties')
table.dump()

print table.col(-1)
z = numpy.array( ['one', 'two', 'three'] )
dt = numpy.dtype( {'names':['age','numberasint'],
                   'formats': ['U30', 'i2']} )
b = numpy.array([('one', 1),('two', 2),('three',3)], dtype=dt)
table.insert(1, b)
table.dump()



