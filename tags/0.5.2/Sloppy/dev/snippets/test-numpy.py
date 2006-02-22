import numpy

# TODO-list:

# column-operations: append, insert, remove, remove_by_index, rearrange
# row-operations: resize, extend, insert_n_rows, insert_rows, delete_n_rows
# data-info: get_converter, column access

# some built in data types and their characters:
#  bool_ ?, short h, int l, uint L, float d, complex D, object_ O   !!!
#  str_ S, unicode_ U#

dtype = numpy.dtype( {'names': ['name', 'age', 'weight'],
                      'formats': ['U30', 'i2', numpy.float32]} )

a = numpy.array( [(u'Bill', 31, 260),
                  ('Fred', 15, 135)], dtype=dtype )

print a

# specify column by key
print a ['name']
print a['age']
print a['weight']
#print a['object']

# specify row by number
print a[0]
print a[1]

# first item of row 1 (Fred's age)
print a[1]['age']

# first item of name column (name 'Bill')
print a['name'][0]

# create a new array based on the old one?


# --- DIAGNOSTICS ---

def dump(a):
    print "-"*80
    fields = a.dtype.fields
    print "\t".join(fields[-1])
    print "\t".join([str(fields[key][0]) for key in fields[-1]])
    print
    for row in a:
        print "\t".join(str(item) for item in row.item())
    print "-"*80


# --- COLUMN OPERATIONS ---

def rename(a, old_name, new_name):
    new = dict(a.dtype.fields) # get a writeable dictionary.
    new[new_name] = new[old_name]
    del new[old_name]
    del new[-1]  # get rid of the special ordering entry
    a.dtype = numpy.dtype(new)

#def rearrange(a, order):
#    fields = a.dtype.fields

    


# --- ROW OPERATIONS ---

def insert_n_rows(a, i, n=1):
    return insert_rows(a, i, rows=numpy.zeros((n,), dtype=a.dtype))

def insert_rows(a, i, rows):
    return numpy.concatenate([a[0:i], rows, a[i:]])

def extend(a, n):
    return insert_n_rows(a, len(a), n)

def delete_n_rows(a, i, n=1):
    n = min(len(a)-i, n)
    return numpy.concatenate([a[0:i], a[i+n:]])




 ###############################################################################
print "Original version"    
dump(a)
rename(a, 'name', 'whatever_name')

print "Renamed name to whatever_name"
dump(a)

print "Inserted five empty rows"
b = insert_n_rows(a, 1, 5)
dump(b)

print "Inserted one specific row instead"
b = insert_rows(a, 1, [('Waldemar', 42, 127.5)])
dump(b)

print "Extending the array instead"
b = extend(a, 3)
dump(b)

print "From this extended array, remove two rows"
b = delete_n_rows(b, 1, 2)
dump(b)


# first column
print b[::]


b = n
#print numpy.concatenate( [b['age'][:,], b['weight']] )
#b1 = b['weight']
#print b1
#print b1.transpose()

#c1 = numpy.array( b1 )
#print c1.dtype
#print b1.dtype
#print numpy.concatenate( [[b1], [b['age']]] )


