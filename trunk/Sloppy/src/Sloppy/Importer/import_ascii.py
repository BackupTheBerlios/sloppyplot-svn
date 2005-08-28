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
logger = logging.getLogger('Importer.import_ascii')

import csv

from Sloppy.Base.dataset import *
from Sloppy.Base import dataio
from Sloppy.Base.table import Table

from Sloppy.Lib.Props import *


STEP_ROWS = 100
            
class Importer(dataio.Importer):

    extensions = ['dat', 'txt']
    author = "Niklas Volbers"
    blurb = "ASCII"

    delimiter = Prop(types=basestring, value_list=[None,',', '\t',';', ' '], default=None, doc="Delimiter")
    custom_delimiter = Prop(types=basestring, doc="Custom delimiter")
    ncols = RangeProp(coerce=int,min=0, steps=1, default=None,
                         doc="# Columns")
    skip = RangeProp(coerce=int, min=0, default=0,
                doc="# Skipped lines")
    table = Prop(types=Table)
    keys = Prop(types=list, default=None)
    designations = Prop(types=list, default=None)

    typecodes = Prop(types=(basestring, list), default='f')
    splitter = Prop(types=object)

    public_props = ['delimiter', 'custom_delimiter', 'ncols', 'skip']
    
        
    def read_table_from_stream(self, fd):

        # determine optional arguments
        typecodes = self.typecodes
        ncols = self.ncols

        # skip lines if requested
        skip = self.skip
        while skip > 0:
            line = fd.readline()
            skip -= 1

        # skip comments
        line = '#'
        while line[0] == '#':
            rewind = fd.tell()
            line = fd.readline()
        fd.seek(rewind)

        # Delimiter
        delimiter = self.delimiter or self.custom_delimiter
        if delimiter is None:
            # Determine from the first non-comment line    
            rewind = fd.tell()
            line = fd.readline()
            if line.find(',') != -1:
                delimiter = ','
            elif line.find('\t')!= -1:
                delimiter = '\t'
            else:
                raise dataio.ImportError("Could not determine delimiter.")
            fd.seek(rewind)
        print "ASCII MARK"
                
        logging.debug("determined delimiter: %s" % delimiter)
        
        # If a table or a list of designations is given, then we will
        # skip the column count determination and the creation of a
        # new table.
        if self.table is None:
            # if no column count is given, try to
            # determine nr. of ncols from first line
            if ncols is None:
                rewind = fd.tell()
                line = fd.readline()
                ncols = len(line.split(delimiter))
                fd.seek(rewind)
                logger.debug("# of columns to be expected: %d" % ncols)


            # create new Table
            self.table = Table(nrows=STEP_ROWS, ncols=ncols, typecodes=typecodes)
        
        # make sure existing Table has at least one entry.
        tbl = self.table
        if tbl.nrows == 0:
            tbl.resize(1)
                
        iter = tbl.row(0)
        converters = tbl.converters

        # assign column information from keyword arguments 'keys' and
        # 'designations'
        keys = self.keys
        if keys is not None:
            n = 0
            for column in tbl.get_columns():
                column.key = keys[n]
                n +=1

        # use given designation or if none given, alternate column
        # designations X/Y.
        designations = self.designations
        if designations is None:
            designations = [('X','Y')[i%2] for i in range(tbl.ncols)]
        
        n = 0
        for column in tbl.get_columns():
            column.designation = designations[n]
            n += 1

        # default line splitting method
        def split(row):
            return row.split(delimiter)
        split = self.splitter or split

        # read in file line by line
        row = fd.readline()
        while len(row) > 0:
            try:
                values = map(lambda x, c: c(x), split(row[:-2]), converters)
            except ValueError, msg:
                logger.warn("Skipped: %s (%s)" % (row,msg))
                row = fd.readline()
                continue
            except TypeError, msg:
                logger.warn("Skipped: %s (%s)" % (row,msg))
                row = fd.readline()
                continue
            
            iter.set( values )

            try:
                iter = iter.next()
            except StopIteration:
                tbl.extend(STEP_ROWS)
                iter = iter.next()

            row = fd.readline()
        
        # Resize dataset to real size, i.e. the number
        # of rows that have actually been read.
        tbl.resize(nrows=iter.row)

        return tbl



#------------------------------------------------------------------------------
dataio.ImporterRegistry.register("ASCII", Importer)

