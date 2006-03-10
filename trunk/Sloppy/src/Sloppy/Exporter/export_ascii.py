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
logger = logging.getLogger("exporter.export_ascii")

from Sloppy.Base import dataio, globals
from Sloppy.Lib.Check import *

import numpy



class Exporter(dataio.Exporter):

    extensions = ['dat', 'txt']
    author = "Niklas Volbers"
    blurb = "ASCII"

    delimiter = String(default='\t')
    
    def write_dataset_to_stream(self, fd, dataset):
        a = dataset._array

        type_map = {numpy.float32: "%f",
                    numpy.int16: "%d",
                    numpy.int32: "%d",
                    numpy.string: '"%s"'}

        # TODO: if we have Matrix, check if we really need different
        # TODO: types or just one for all columns
        types  = [dataset.get_column_type(i) for i in range(dataset.ncols)]
        types = [type_map[t] for t in types]
        exp = self.delimiter.join(types) + '\n'

        for row in a:
            fd.write(exp % row.item())
            


#------------------------------------------------------------------------------
globals.exporter_registry["ASCII"] = Exporter
