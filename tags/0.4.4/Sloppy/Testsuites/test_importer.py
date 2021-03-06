
import unittest

from Sloppy.Base.dataio import ImporterRegistry
from Sloppy.Base.table import Table



class TestCase(unittest.TestCase):

    def setUp(self):
        self.tables = [('./ASCII/1.dat',
                        ImporterRegistry['ASCII'](),
                        Table([[1,2,3],[2,4,8],[3,9,27],[4,16,64]])
                        ),
                       ('./ASCII/2.dat',
                        ImporterRegistry['ASCII'](),
                        Table([[1,1,1],[2,2,2],[3,3,3]])
                        ),
                       ('./ASCII/3.dat',
                        ImporterRegistry['ASCII'](),
                        Table([[1,3],[2,8],[3,27],[4,64]])
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
                print "<<<"
                raise





if __name__ == '__main__':
    unittest.main()
