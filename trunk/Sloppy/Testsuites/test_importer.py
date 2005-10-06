
from Sloppy.Base import dataio
from Sloppy.Base.table import Table
from Numeric import array

import unittest


tables = [('./ASCII/1.dat', Table([[1,2,3],[2,4,8],[3,9,27],[4,16,64]]))]


class TestCase(unittest.TestCase):

    def setUp(self):
        self.filelist = ['./ASCII/1.dat']

    def runTest(self):
        for filename, result in tables:
            tbl = dataio.read_table_from_file(filename, 'ASCII')
            print tbl
            print result
            #self.assertEqual(tbl, result)



if __name__ == '__main__':
    unittest.main()
