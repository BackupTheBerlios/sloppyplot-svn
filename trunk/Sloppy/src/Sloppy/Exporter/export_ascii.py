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

import csv

from Sloppy.Base import dataio

from Sloppy.Lib.Props import *

import numpy

class Exporter(dataio.Exporter):

    extensions = ['dat', 'txt']
    author = "Niklas Volbers"
    blurb = "ASCII"

    delimiter = VP(basestring, default='\t')
    
    def write_dataset_to_stream(self, fd, dataset):
        a = dataset.get_array()

        type_map = {numpy.float32: "%f",
                    numpy.int16: "%d",
                    numpy.int32: "%d",
                    numpy.string: '"%s"'}
        
        types  = [dataset.get_column_type(name) for name in dataset.names]
        
        exp = ''
        for type in types:
            exp += type_map[type]
            exp += self.delimiter
        exp += '\n'
        
        for row in a:
            fd.write(exp % row.item())
            


#------------------------------------------------------------------------------
dataio.exporter_registry["ASCII"] = Exporter
