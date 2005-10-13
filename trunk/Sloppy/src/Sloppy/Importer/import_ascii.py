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


import re

from Sloppy.Base.dataset import *
from Sloppy.Base import dataio
from Sloppy.Base.table import Table

from Sloppy.Lib.Props import *
from Sloppy.Lib.Signals import *


# This must be at the end, because otherwise we might import the
# logger object in the import statements above!
import logging
logger = logging.getLogger('import.ascii')


            
class Importer(dataio.Importer):

    extensions = ['dat', 'txt']
    author = "Niklas Volbers"
    blurb = "ASCII"

    #----------------------------------------------------------------------
    # Properties
    #
    
    delimiter = pString(CheckValid([None,',', '\t',';', '\s*']),
                        blurb ="Delimiter",
                        doc="Column delimiter that separates the columns.")
    
    custom_delimiter = pString(blurb="Custom Delimiter",
                               doc="Custom delimiter used if delimiter is None.")
    
    ncols = pInteger(CheckBounds(min=0), default=None,
                      blurb="Number of columns")

    header_lines = pInteger(CheckBounds(min=0), default=0,
                            blurb="Number of header lines")

    table = Prop(CheckType(Table))
    
    keys = pList()

    labels = pList()
    
    designations = Prop(CheckType(list),
                        default=None)

    typecodes = Prop(CheckType(basestring, list),
                     default='d')

    growth_offset = pInteger(CheckBounds(min=10), default=100)

    public_props = ['delimiter', 'custom_delimiter', 'ncols', 'header_lines']

    

    #----------------------------------------------------------------------
    # Reading in Data
    #
    
    def read_table_from_stream(self, fd):
       
        # determine optional arguments
        typecodes = self.typecodes
        ncols = self.ncols

        # skip header lines if requested
        header_lines = self.header_lines
        while header_lines > 0:
            line = fd.readline()
            header_lines -= 1

        # TODO: use given expression and re
        # skip comments
        line = '#'
        while len(line) > 0 and line[0] == '#':
            rewind = fd.tell()
            line = fd.readline()
        fd.seek(rewind)

        # determine delimiter
        delimiter = self.delimiter or self.custom_delimiter
        if delimiter is None:
            # determine from first non-comment line
            rewind = fd.tell()
            line = fd.readline()
            if line.find(',') != -1:
                delimiter = ','
            else:
                delimiter = '[\s\t]*'
            fd.seek(rewind)

        logger.debug("determined delimiter: %s" % delimiter)
        
        # If a table or a list of designations is given, then we will
        # skip the column count determination and the creation of a
        # new table.
        if self.table is None:
            # if no column count is given, try to
            # determine nr. of ncols from first line
            if ncols is None:
                rewind = fd.tell()
                line = fd.readline()

                # split off comments
                # TODO: This will not work for text entries "Example #Test"
                line = line.split('#')[0]

                cregexp = re.compile(delimiter)
                matches = [match for match in cregexp.split(line) if len(match) > 0]
                logger.debug("MATCHES = %s" % str(matches))
                ncols = len(matches)
               
                fd.seek(rewind)

            # create new Table
            tbl = Table(nrows=self.growth_offset, ncols=ncols, typecodes=typecodes)
        else:
            tbl = self.table

        logger.debug("# of columns to be expected: %d" % ncols)

        
        # make sure existing Table has at least one entry.
        if tbl.nrows == 0:
            tbl.resize(1)
                
        iter = tbl.row(0)
        converters = tbl.converters

        # assign column information from keyword arguments 'keys' & 'label'
        keys = self.keys
        labels = self.labels
        if keys:
            n = 0
            for column in tbl.get_columns():
                column.key = keys[n]
                n +=1
        if labels:
            n = 0
            for column in tbl.get_columns():
                column.label = labels[n]
                n += 1

        # use given designation or if none given, alternate column
        # designations X/Y.
        designations = self.designations
        if designations is None:
            designations = [('X','Y')[i%2] for i in range(tbl.ncols)]
        
        n = 0
        for column in tbl.get_columns():
            column.designation = designations[n]
            n += 1
        
        # Create regular expression used to match the lines.
        cregexp = re.compile(delimiter)


        #
        # read in file line by line
        #
        logger.debug("Start reading ASCII file.")
        skipcount = 0
        row = fd.readline()        
        while len(row) > 0:
            # split off comments
            # TODO: This will not work for text entries "Example #Test"
            row = row.split('#')[0]
            
            matches = [match for match in cregexp.split(row) if len(match) > 0]
            logger.debug("MATCHES = %s" % str(matches))
            if len(matches) == 0:
                skipcount += 1
                if skipcount > 100:
                    Signals.emit("ask-for-confirmation", "Warning: More than 100 lines skipped recently. Should we continue with this file?")
                    skipcount = 0
            else:
                try:
                    values = map(lambda x, c: c(x), matches, converters)
                except ValueError, msg:
                    #logger.warn("Skipped: %s (%s)" % (row,msg))
                    row = fd.readline()
                    continue
                except TypeError, msg:
                    #logger.warn("Skipped: %s (%s)" % (row,msg))
                    row = fd.readline()
                    continue
                else:
                    #logger.info("Read %s" % values)
                    pass
                    
            
                iter.set( values )

                # Move to next row.
                # If this is the last row, then the Table is extended.
                try:
                    iter = iter.next()
                except StopIteration:
                    tbl.extend(tbl.ncols+self.growth_offset)
                    iter = iter.next()

            row = fd.readline()

        logger.info("Finished reading ASCII file.")
        
        # Resize dataset to real size, i.e. the number
        # of rows that have actually been read.
        tbl.resize(nrows=iter.row)

        return tbl



#------------------------------------------------------------------------------
dataio.ImporterRegistry['ASCII'] = Importer

