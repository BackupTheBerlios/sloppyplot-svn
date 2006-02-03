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

# $HeadURL: svn+ssh://niklasv@svn.berlios.de/svnroot/repos/sloppyplot/trunk/Sloppy/src/Sloppy/Exporter/export_ascii.py $
# $Id: export_ascii.py 158 2005-09-23 20:44:14Z niklasv $


import logging
logger = logging.getLogger("exporter.export_ascii")

from Sloppy.Base import dataio


class Exporter(dataio.Exporter):

    extensions = ['csv']
    author = "Niklas Volbers"
    blurb = "CSV (comma separated values)"
   
    def write_dataset_to_stream(self, fd, dataset):
        e = dataio.exporter_registry['ASCII'](delimiter=',')
        e.write_dataset_to_stream(fd, dataset)
        
#------------------------------------------------------------------------------
dataio.exporter_registry["CSV"] = Exporter
