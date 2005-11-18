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

# $HeadURL: svn+ssh://niklasv@svn.berlios.de/svnroot/repos/sloppyplot/trunk/Sloppy/src/Sloppy/Importer/import_ascii.py $
# $Id: import_ascii.py 234 2005-11-07 05:01:37Z niklasv $

from Sloppy.Base.dataset import *
from Sloppy.Base import dataio
from Sloppy.Base.table import Table

from Sloppy.Lib.Props import *

import import_ascii

# This must be at the end, because otherwise we might import the
# logger object in the import statements above!
import logging
logger = logging.getLogger('import.ascii')



class Importer(dataio.Importer):

    extensions = ['csv']
    author = "Niklas Volbers"
    blurb = "Comma Separated Value"

    #----------------------------------------------------------------------
    # Properties
    #

    header_size = pInteger(CheckBounds(min=0), default=0,
                            blurb="Number of header lines")

    column_props = pList(types=dict)

    def read_table_from_stream(self, fd):

        table = Table(nrows=0, ncols=len(self.column_props))

        j = 0
        for column in table.columns:
            for k,v in self.column_props[j].iteritems():
                column.set_value(k,v)
            j += 1

        kwargs = {'delimiter' : ',',
                  'header_size' : self.header_size,
                  'table' : table}

        importer = import_ascii.Importer(**kwargs)
        return importer.read_table_from_stream(fd)


#------------------------------------------------------------------------------
dataio.ImporterRegistry['CSV'] = Importer
