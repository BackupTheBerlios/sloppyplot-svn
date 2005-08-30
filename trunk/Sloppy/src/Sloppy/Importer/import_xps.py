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



# format

# 1  sample name, number of regions
# 2-4 label
# 5-7  1. Bereich
# 8-10 2. Bereich

# 35... data (4 columns)

# binding energy, counts, binding energy, counts
# - possible


import logging
logging.basicConfig()

import re

from Sloppy.Base import dataio
from Sloppy.Lib.Props import Prop, BoolProp


class Importer(dataio.Importer):

    blurb = "XPS Spectra"
    extensions = ["xps"]
    author = "Niklas Volbers"

    ranges = Prop(coerce=int, default=2)    
    split_ranges = BoolProp(default=False)
    sample = Prop(types=basestring, default="")
    
    public_props = []
    
    def __init__(self, **kwargs):
        self.ncols = 0
        self.designations = 0
        self.splitter = None
        
        dataio.Importer.__init__(self, **kwargs)


    def read_header_from_stream(self, fd):

        re_first = '(?P<sample>.*?)\s*(?P<ranges>[0-9]*)\sBereich.*'

        line = fd.readline()
        r = re.compile(re_first)
        matches = r.match(line)
        if matches is None:
            raise RuntimeError("Import Error: First line of data file is invalid.")

        gd = matches.groupdict()
        self.ranges = gd['ranges']
        self.sample = gd['sample']

        
    def read_table_from_stream(self, fd):

        print "READING FILE"
        current_range = 0
        
        def splitter(row):
            rv = row.split(' ')
            rv = [item for item in rv if item != '']
            for n in range(len(rv)):
                if rv[n] == '-':
                    rv[n] = float()
            return rv

        self.read_header_from_stream(fd)

        if self.split_ranges is False:           
            keys = list()
            for n in range(self.ranges):
                keys.extend(["Binding Energy %s:%d" % (self.sample, n),
                             "%s:%d" % (self.sample, n)])
                            
            options = {'delimiter' : ' ',
                       'ncols' : self.ranges * 2,
                       'designations': self.ranges * ['X','Y'],
                       'splitter' : splitter,
                       'keys' : keys,
                       'header_lines' : 33}

            print "Calling ASCII IMPORT"
            importer = dataio.ImporterRegistry.new_instance('ASCII', **options)
            return importer.read_table_from_stream(fd)

        
        else:
            #
            # currently unused
            #            
            pos = fd.seek()
            options = {'delimiter' : ' ',
                       'ncols' : self.ranges * 2,
                       'designations': self.ranges * ['X','Y'],
                       'splitter' : splitter,
                       'header_lines' : 33}            
                       
            importer = dataio.ImporterRegistry.new_instance('ASCII', **options)
            return importer.read_table_from_stream(fd)




#------------------------------------------------------------------------------
dataio.ImporterRegistry.register('XPS', Importer)
