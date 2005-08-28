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

import tempfile, os


from Sloppy.Base.error import NoData
from Sloppy.Base.dataio import ImporterRegistry, read_table_from_stream, read_table_from_file
from Sloppy.Base.table import Table

from Sloppy.Lib import Signals
from Sloppy.Lib.Undo import UndoInfo, UndoList
from Sloppy.Lib.Props import DictProp, Prop, Container, KeyProp

from Numeric import ArrayType


#------------------------------------------------------------------------------

class Dataset(Container):

    """
    A Dataset is a wrapper for any data used for plotting.

    Attributes are:

    key - string that identifies the Dataset

    label - descriptive label

    metadata - additional meta info

    data - the actual data, either a Table or a numeric array.  Note
      that the numeric array should be 2-dimensional, even though this
      is not checked.

    To create a Dataset from scratch:

    >>> ds = Dataset(key='dataset01', label='Recent data on weather',
    >>>              metadata={'ImportSource': 'Local Weather TV'},
    >>>              data=array([[1,2,3,4],[5,6,7,8]])

    If you use the Dataset's data, then always make sure that you are
    dealing with the right kind of data.  The recommended way to do so
    is

    >>> data = ds.data  # ds is the Dataset
    >>> if not isinstance(data, Table):
    >>>     ....

    or alternatively

    >>> if not isinstance(data, ArrayType):
    >>>     ....

    where ArrayType must have been imported from `numeric`.

    If you add a Dataset to a Project, then you must make sure that
    its key is unique.

    TODO: implement some function in Project that does that.
    
    """
    
    key = KeyProp()

    label = Prop(coerce=unicode)
    metadata = DictProp(coerce=unicode)
    data = Prop(types=(Table, ArrayType,None))

    def __init__(self, **kwargs):
        Container.__init__(self, **kwargs)
        self.change_counter = 0
        self.__is_valid = True
        self._table_import = None

    #----------------------------------------------------------------------
    def revert_change(self, undolist=[]):
        self.change_counter -= 1
        Signals.emit(self, 'changed')
        undolist.append( UndoInfo(self.notify_change).describe("Notify") )
        
    def notify_change(self, undolist=[]):
        self.change_counter += 1        
        Signals.emit(self, 'changed')
        undolist.append( UndoInfo(self.revert_change).describe("Notify") )

    def has_changes(self, counter):
        return self.change_counter != counter

    #----------------------------------------------------------------------
        
    def close(self):
        Signals.emit(self, 'closed')
        self.data = None

    def detach(self):
        Signals.emit(self, 'closed')

    def is_empty(self):
        " Returns True if the Dataset has no data or if that data is empty. "
        return self.get_data() is None or len(self.data) == 0
        
    #----------------------------------------------------------------------

    def get_data(self):
        if self._table_import is not None:
            self.import_table(*self._table_import)
            self._table_import = None
        return self.data

    def import_table(self, project, filename, typecodes, column_props, importer_key):
        dir = tempfile.mkdtemp('spj')
        name = os.path.join(dir, filename)
        project._archive.extract(filename, dir)
        
        try:
            table = read_table_from_file(name, importer_key, column_props=column_props)
        finally:
            os.remove(name)
            os.rmdir(os.path.join(dir, 'datasets'))
            os.rmdir(dir)
        
        self.data = table
        
        
    def set_table_import(self, *args):
        self._table_import = args

    #----------------------------------------------------------------------
    
