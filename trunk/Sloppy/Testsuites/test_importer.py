
import unittest

import Sloppy
Sloppy.init()

from Sloppy.Base.dataio import import_templates
from Sloppy.Base.table import Table

from Numeric import array


class TestCase(unittest.TestCase):

    def setUp(self):
        self.tables = [('./data/1.dat', 'ASCII',
                        Table(array([[1,2,3],[2,4,8],[3,9,27],[4,16,64]],'d'))
                        ),
                       ('./data/2.dat', 'ASCII',
                        Table(array([[1,1,1],[2,2,2],[3,3,3]],'d'))
                        ),
                       ('./data/3.dat', 'ASCII',
                        Table(array([[1,1,1],[2,2,2],[3,3,3]],'d'))
                        )
                       ]

    def runTest(self):
        for filename, template_key, result in self.tables:
            importer = import_templates[template_key].new_instance()
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
