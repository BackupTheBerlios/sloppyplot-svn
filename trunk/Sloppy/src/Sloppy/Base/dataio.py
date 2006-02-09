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

from Sloppy.Base import globals, dataset
from Sloppy.Lib.Props import *



#------------------------------------------------------------------------------
DS={\

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



class Importer(HasProperties):

    """

    `Importer` is a base class for any import extension.

    A sample implementation for the import of the well-known and
    extremly popular HQT format would start like this:
    
    >>> class MyImporter(Importer):
    >>>     extensions = ['HQT']
    >>>     blurb = 'High Quality Table'
    >>>     author = 'Fridolin Smurf'

    You must only implement the method `read_dataset_from_stream` which
    constructs a new Dataset object from a given file descriptor.    

    """
    
    author = "your name"       
    filemode = '' # set to 'b' for binary objects

    # Still experimental:
    # These two properties can be used to interact with the application
    app = VP(object)
    progress_indicator = VP(object)
    
    def read_dataset_from_stream(self,fd):
        return None
        
    def read_dataset_from_file(self,filename):

        try:
            fd = open(filename, 'r%s' % self.filemode)
        except IOError:
            raise ImportError("File not found %s" % filename)

        try:
            ds = self.read_dataset_from_stream(fd)
            ds.node_info.metadata['_import_filename'] = unicode(filename)            
            if ds.nrows == 0:
                raise ImportError("File %s:\nResulting Dataset is empty!" % filename )
            return ds
        finally:
            fd.close()



class Exporter(HasProperties):

    filemode = '' # set to 'b' for binary objects
    
    def write_dataset_to_stream(self, fd, tbl):
        pass

    
    def write_to_stream(self, fd, data):
        if isinstance(data, dataset.Dataset):
            self.write_dataset_to_stream(fd, data)
        else:
            raise TypeError("Unknown type of data.")

    def write_to_file(self, file, tbl):
        try: fd = open(file,'w%s' % self.filemode )
        except: raise IOError("Could not write file %s" % file)

        try: self.write_to_stream(fd, tbl)
        finally: fd.close()
        

#------------------------------------------------------------------------------

class IOTemplate(HasProperties):

    extensions = String(\
        default="",
        blurb="File extensions",
        doc=DS['IOTemplate:extensions']
        )
    
    blurb = Unicode(\
        blurb="Description",
        doc=DS['IOTemplate:blurb']
        )

    skip_options = Boolean(\
        default=False,
        blurb="Skip Options",
        doc=DS['IOTemplate:skip_options']
        ) 

    defaults = Dictionary()    
    importer_key = String()
    is_internal = Boolean(False) #
    

    def new_instance(self):
        return globals.importer_registry[self.importer_key](**self.defaults.data)




#------------------------------------------------------------------------------
# convenience methods

def read_dataset_from_file(filename, importer_key='ASCII', **kwargs):
    importer = globals.importer_registry[importer_key](**kwargs)
    return importer.read_dataset_from_file(filename)

def read_dataset_from_stream(fd, importer_key='ASCII', **kwargs):
    importer = globals.importer_registry[importer_key](**kwargs)
    return importer.read_dataset_from_stream(fd)
    

def importer_template_from_filename(filename):
    """    
    Return a list of templates that matches the given filename based
    on the extension.
    """   
    path, ext = os.path.splitext(filename)
    if len(ext) > 1: ext = ext[1:].lower()
    else: return matches

    matches = []
    for key, template in globals.import_templates.iteritems():
        if ext in template.extensions.split(','):
            matches.append(key)

    return matches
    
