
import unittest

from Sloppy.Base.dataio import ImporterRegistry
from Sloppy.Base.table import Table

from Numeric import array


class TestCase(unittest.TestCase):

    def setUp(self):
        self.tables = [('./data/1.dat',
                        ImporterRegistry['ASCII'](),
                        Table(array([[1,2,3],[2,4,8],[3,9,27],[4,16,64]],'d'))
                        ),
                       ('./data/2.dat',
                        ImporterRegistry['ASCII'](),
                        Table(array([[1,1,1],[2,2,2],[3,3,3]],'d'))
                        )
                       ]

    def runTest(self):
        for filename, importer, result in self.tables:
            tbl = importer.read_table_from_file(filename)
            try:
                self.assert_(tbl.is_equal(result))
            except AssertionError:
                print ">>>"
                print "File: ", filename
                print tbl
                print "==="
                print result
                print "<<<"
                raise





if __name__ == '__main__':
    unittest.main()
