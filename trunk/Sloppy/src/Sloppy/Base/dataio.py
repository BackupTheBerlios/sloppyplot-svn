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

import os.path

from Sloppy.Base import klassregistry
from Sloppy.Base.table import table_to_array, array_to_table, Table
from Sloppy.Lib.Props import *

from Numeric import ArrayType




class ImportError(Exception):
    pass

class ExportError(Exception):
    pass



class Importer(Container):

    """

    `Importer` is a base class for any import extension.

    A sample implementation for the import of the well-known and
    extremly popular HQT format would start like this:
    
    >>> class MyImporter(Importer):
    >>>     extensions = ['HQT']
    >>>     blurb = 'High Quality Table'
    >>>     author = 'Fridolin Smurf'

    You must only implement the method `read_table_from_stream` which
    constructs a new Table object from a given file descriptor.    

    Finally you must register your Importer class like this:
    
    >>> ImporterRegistry.register('QTP', MyImporter)

    """
    
    # additional meta-information
    extensions = ['foo']
    blurb = "Sample Import Format"
    author = "your name"       
    filemode = '' # set to 'b' for binary objects

    app = Prop(CheckType(object))
    progress_indicator = Prop(CheckType(object))
    
    def read_table_from_stream(self,fd):
        return None

    def read_array_from_stream(self,fd):
        tbl = self.read_table_from_stream(fd, **kwargs)
        return table_to_array(tbl)

        
    def read_table_from_file(self,file):
        try:
            fd = open(file, 'r%s' % self.filemode)
        except IOError:
            raise ImportError("File not found %s" % file)

        try:
            table = self.read_table_from_stream(fd)
            if table.nrows == 0:
                raise ImportError("File %s:\nResulting Table is empty!" % file )
            return table
        finally:
            fd.close()

    def read_array_from_file(self, file):
        try:
            fd = open(file, 'r%s' % self.filemode)
        except:
            raise ImportError("File not found %s" % file)

        try:
            array = self.read_array_from_stream(fd)
            if len(array.shape == 0):
                raise ImportError("Empty Array.")
            return array        
        finally:
            fd.close()



class Exporter(Container):

    filemode = '' # set to 'b' for binary objects
    
    def write_table_to_stream(self, fd, tbl):
        pass

    def write_array_to_stream(self, fd, a):
        a = array_to_table(a)
        self.write_table_to_stream(fd, tbl)

    
    def write_to_stream(self, fd, data):
        if isinstance(data, ArrayType):
            self.write_array_to_stream(fd, data)
        elif isinstance(data, Table):
            self.write_table_to_stream(fd, data)
        else:
            raise TypeError("Unknown type of data.")

    def write_to_file(self, file, tbl):
        try: fd = open(file,'w%s' % self.filemode )
        except: raise IOError("Could not write file %s" % file)

        try: self.write_to_stream(fd, tbl)
        finally: fd.close()
        

#------------------------------------------------------------------------------
ImporterRegistry = klassregistry.Registry("Importer")
ExporterRegistry = klassregistry.Registry("Exporter")


#------------------------------------------------------------------------------
# convenience methods

def read_table_from_file(filename, importer_key='ASCII', **kwargs):
    importer = ImporterRegistry.new_instance(importer_key, **kwargs)
    return importer.read_table_from_file(filename)

def read_table_from_stream(fd, importer_key='ASCII', **kwargs):
    importer = ImporterRegistry.new_instance(importer_key, **kwargs)
    return importer.read_table_from_stream(fd)
    

def read_array_from_file(filename, importer_key='ASCII', **kwargs):
    importer = ImporterRegistry.new_instance(importer_key, **kwargs)
    return importer.read_array_from_file(filename)

def importer_from_filename(filename):
   
    path, ext = os.path.splitext(filename)
    if len(ext) > 1: ext = ext[1:].lower()
    else: return matches

    matches = []
    for key, classwrapper in ImporterRegistry.iteritems():
        importer = classwrapper.klass
        if ext in importer.extensions:
            matches.append(key)

    return matches
    


