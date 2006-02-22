
import unittest

import Sloppy
Sloppy.init()

from Sloppy.Base.dataio import import_templates
from Sloppy.Base.dataset import Dataset

import numpy


# FOR ASCII

class TestCaseASCII(unittest.TestCase):

    def setUp(self):
        a1 = numpy.array([(1,2,3),(2,4,8),(3,9,27),(4,16,64)],
                         dtype={'names':['a','b','c'],
                                'formats':['i2','i2','i2']})

        self.datasets = {}
        self.datasets['1.dat'] = Dataset(a1)
#                           ),
#                          ('./data/2.dat', 'ASCII',
#                           Dataset(numpy.array([[1,1,1],[2,2,2],[3,3,3]],'d'))
#                           ),
#                        ('./data/3.dat', 'ASCII',
#                         Dataset(numpy.array([[1,1,1],[2,2,2],[3,3,3]],'d'))
#                         )
#                          ]

    def runTest(self):
        
        for filename, ds in self.datasets.iteritems():
            filename = './data/%s' % filename
            print "Reading file ", filename
            importer = import_templates['ASCII'].new_instance()
            # TODO: copy the dataset w/o the data and then read the
            # TODO: dataset into it. This way we will have the
            # TODO: same field types.
            new_ds = importer.read_dataset_from_file(filename)
            ds.dump()            
            new_ds.dump()

            # TODO: compare the datasets
#             try:
#                 self.assert_(tbl.is_equal(result))
#             except AssertionError:
#                 print ">>>"
#                 print "File: ", filename
#                 print tbl
#                 print "==="
#                 print result
#                 print "<<<"
#                 raise





if __name__ == '__main__':
    unittest.main()
