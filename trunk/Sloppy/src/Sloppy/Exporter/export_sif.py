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
logger = logging.getLogger("exporter.export_sif")

from pycdf import *

from Sloppy.Base.dataset import *
from Sloppy.Base import dataio
from Sloppy.Base.table import Table, table_to_array

from Sloppy.Lib.Props import *



class Exporter(dataio.Exporter):

    extensions = ['sif']
    author = "Niklas Volbers"
    blurb = "SloppyPlot Internal Format"
    filemode = 'b'


    def write_to_file(self, file, tbl):
        try: fd = CDF(file, NC.WRITE|NC.CREATE)
        except: raise dataio.ExportError("Could not write file %s" % file)

        try: self.write_to_stream(fd, tbl)
        finally: fd.close()

    def write_table_to_stream(self, fd, table):
        fd.automode()

        rows = table.rowcount
       
        # column => vars
        j = 0
        for column in table.get_columns():
            key = "column_%d" % j

            dim = fd.def_dim(key, rows)

            # TODO: move to types.py
            type_mappings = {'d' : NC.DOUBLE,
                             'f' : NC.FLOAT,
                             'l' : NC.INT}
            try:
                nc_type = type_mappings[column.data.typecode()]
            except KeyError:
                raise dataio.ExportError("Column type '%s' is not supported. Can't save the column." % column.data.typecode())
                
            var = fd.def_var(key, nc_type, dim)
            var[:] = column.data

            # add Column properties as attributes
            for key in ['key', 'designation', 'label', 'query']:
                value = column.get_value(key)
                if value is not None:
                    if isinstance(value, unicode):
                        value = 'invalid encoding'
                    try:
                        setattr(var, key, value)
                    except CDFError:
                        logger.error("Error while setting key '%s' to '%s'" % (key,value))
                        raise

            j += 1        

#------------------------------------------------------------------------------
dataio.ExporterRegistry.register("SIF", Exporter)
