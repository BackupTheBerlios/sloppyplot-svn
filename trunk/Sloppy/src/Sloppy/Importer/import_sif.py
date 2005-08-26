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
logger = logging.getLogger('Importer.import_sif')

from pycdf import *
from Numeric import *

from Sloppy.Base.dataset import *
from Sloppy.Base import dataio
from Sloppy.Base.table import Table, array_to_table, Column


class Importer(dataio.Importer):

    extensions = ['sif']
    author = "Niklas Volbers"
    blurb = "SloppyPlot Internal Format"
    filemode = 'b'

    def read_table_from_stream(self, fd):
        raise RuntimeError("Please call 'read_table_from_file'.")

    
    def read_table_from_file(self, fd):
        if not isinstance(fd, basestring):
            raise RuntimeError("You must supply a filename.")

        nc = CDF(fd)
        
        # global attributes
        #attr = nc.attributes(full=1) # unused

        dims = nc.dimensions(full=1)
        ncols = len(nc.variables())

        # create new table according to dimension information
        self.table = Table(nrows=0, ncols=ncols)

        # vars => columns
        j = 0
        for column in self.table.get_columns():           
            v = nc.var(j)
            column.data = array(v[:])

            attributes = v.attributes(full=1)
            for k,v in attributes.iteritems():
                column.set_value(k, v[0])
            j += 1

        nc.close()

        self.table.update_cols()
        self.table.update_rows()
        
        return self.table

#------------------------------------------------------------------------------
dataio.ImporterRegistry.register("SIF", Importer)
        

