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


import os.path

from Sloppy.Base.table import table_to_array, array_to_table, Table
from Sloppy.Lib.Props import *

from Numeric import ArrayType


#------------------------------------------------------------------------------
DC={\

'IOTemplate:extensions':
"""File extensions for which this template should be used,
e.g. 'dat' for files ending in '.dat'.
You can specify multiple extensions by separating them with
commas, e.g. 'dat,csv' if the template should be valid for
both files ending in '.dat' or files ending in '.csv'.""",

'IOTemplate:skip_options':
""" Whether to ask the user for options. Set this to false
if you specify a template for a fixed file format and you
don't want to confirm the import options every time.""",

'IOTemplate:blurb':
"""One-line description."""

}

#------------------------------------------------------------------------------


class ImportError(Exception):
    pass

class ExportError(Exception):
    pass



class Importer(HasProps):

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
    
    >>> importer_registry.register('QTP', MyImporter)

    """
    
    author = "your name"       
    filemode = '' # set to 'b' for binary objects

    # Still experimental:
    # These two properties can be used to interact with the application
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



class Exporter(HasProps):

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
importer_registry = {}
import_templates = {}

exporter_registry = {}
export_templates = {}


class IOTemplate(HasProps):

    extensions = pString(\
        default="",
        blurb="File extensions",
        doc=DC['IOTemplate:extensions']
        )
    
    blurb = pUnicode(\
        blurb="Description",
        doc=DC['IOTemplate:blurb']
        )

    skip_options = pBoolean(\
        default=False,
        blurb="Skip Options",
        doc=DC['IOTemplate:skip_options']
        ) 

    defaults = pDict()    
    importer_key = pString()
    is_internal = pBoolean(default=False) #
    

    def new_instance(self):
        return importer_registry[self.importer_key](**self.defaults.data)




#------------------------------------------------------------------------------
# convenience methods

def read_table_from_file(filename, importer_key='ASCII', **kwargs):
    global importer_registry
    importer = importer_registry[importer_key](**kwargs)
    return importer.read_table_from_file(filename)

def read_table_from_stream(fd, importer_key='ASCII', **kwargs):
    global importer_registry
    importer = importer_registry[importer_key](**kwargs)
    return importer.read_table_from_stream(fd)
    

def read_array_from_file(filename, importer_key='ASCII', **kwargs):
    global importer_registry
    importer = importer_registry[importer_key](**kwargs)
    return importer.read_array_from_file(filename)


def importer_template_from_filename(filename):
    """    
    Return a list of templates that matches the given filename based
    on the extension.
    """
    global import_templates
    
    path, ext = os.path.splitext(filename)
    if len(ext) > 1: ext = ext[1:].lower()
    else: return matches

    matches = []
    for key, template in import_templates.iteritems():
        if ext in template.extensions.split(','):
            matches.append(key)

    return matches
    
