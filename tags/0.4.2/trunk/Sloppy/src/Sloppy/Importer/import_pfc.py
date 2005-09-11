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
logging.basicConfig()

import re

from Sloppy.Base import dataio



class Importer(dataio.Importer):

    blurb = "SIMS Profiles (converted)"
    extensions = ["pfc"]
    author = "Niklas Volbers"

    public_props = []
    
    def read_header_from_stream(self, fd):
        # first line is header line, delimited by ','
        line = fd.readline()[:-2]
        self.labels = line.split(',')                    

           
    def read_table_from_stream(self, fd):

        self.read_header_from_stream(fd)
        ncols = len(self.labels)
        
        if ncols == 0 or (ncols%2 != 0):
            raise ImportError("Invalid header line for PFC.")        

        options = {'ncols' : ncols,
                   'typecodes' : 'f',
                   'designations' : ['X','Y'] * (ncols/2),
                   'header_lines' : 1,
                   'labels': self.labels,
                   'delimiter' : None,
                   'custom_delimiter' : ',\s*'}
                           
        importer = dataio.ImporterRegistry.new_instance('ASCII', **options)
        return importer.read_table_from_stream(fd)

#------------------------------------------------------------------------------
dataio.ImporterRegistry.register('PFC', Importer)


