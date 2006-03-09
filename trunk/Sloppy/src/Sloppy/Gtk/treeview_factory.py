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


 # TODO: maybe rename Column To ColumnCreator ?



"""

  Both factories should have similar interfaces:
  
  f = DisplayFactory(obj)
  f.add_keys(obj._checks.keys()
  table = f.create_table()
  f.check_in()
  ...
  f.check_out()


  f = ColumnFactory(mainobj, listkey, obj.__class__)
  f.add_keys(..keys()..)
  treeview = f.create_treeview()
  f.check_in()
  ...
  f.check_out()

  Since each factory keeps track of the created Column/Display
  objects, it is also possible to show/hide these:

  f.show(*keys)
  f.hide(*keys) 
  
"""


import gtk, sys, inspect

from Sloppy.Lib.Check import *
from Sloppy.Lib.Signals import *
from Sloppy.Lib.Undo import UndoList
from Sloppy.Base import uwrap

import logging
logger = logging.getLogger('gtk.treeview_factory')


# TODO: For testing
import uihelper


###############################################################################


# TODO ColumnFactory
# ------------------

# set_object
# model should only contain the object, nothing else.
# It doesn't make a difference if we store all values in the model
# or if we create a copy of the object!
# (Well, it does if we don't use all of the object...)

# on_update
   
class ColumnFactory:

    def __init__(self, listowner, listkey, itemclass):
        self.listowner = listowner
        self.itemclass = itemclass
        self.listkey = listkey
        self.keys = []
        self.columns = {}
        self.old_list = []
        
    def add_keys(self, *keys, **kwargs):
        for key in keys:
            if isinstance(key, basestring):
                self.keys.append(key)
            elif isinstance(key, (list, tuple)):
                self.keys.extend(key)
            else:
                raise TypeError("String or tuple required.")

        for key, value in kwargs.iteritems():
            self.columns[key] = value

    def show_keys(self, *keys):           
        if len(keys) == 0:
            keys = self.keys

        for key in keys:
            if key == '_all':
                self.show_keys(*self.keys)
            elif isinstance(key, (list,tuple)):
                self.show_keys(*key)
            else:
                self.columns[key].set_property('visible', True)

    def hide_keys(self, *keys):
        if len(keys) == 0:
            keys = self.keys
        
        for key in keys:
            if key == '_all':
                self.hide_keys(*self.keys)
            elif isinstance(key, (list,tuple)):
                self.hide_keys(*key)
            else:
                self.columns[key].set_property('visible', False)
        
    def new_row(self, item):
        row = []
        for key in self.keys:
            row.append( item.get_value(key) )
        row.append(item)
        return row


    def create_treeview(self):
        model = gtk.ListStore(*([object]*(len(self.keys) + 1)))    
        treeview = gtk.TreeView(model)        

        index = 0
        for key in self.keys:
            if self.columns.has_key(key):
                obj = self.columns[key]
                if inspect.isfunction(obj) or inspect.ismethod(obj):
                    c = obj(model, index)
                else:
                    c = obj
            else:
                creator = self.new_column_creator(self.itemclass, key)
                c = creator.create_column(model, index)

            self.columns[key] = c
            treeview.append_column(c)
            index += 1
            
        self.treeview = treeview
        return self.treeview



    def connect(self, obj):
        # obj is the listowner
        self.obj = obj
        for creator in self.creators.itervalues():
            creator.connect(obj)

        model = self.treeview.get_model()
        model.clear()

        # hmmmm.... maybe this is not enough.
        # I would need to create my own model,
        # which synchronizes with the List
        # object. I know, this is a lot of work,
        # but at the moment I can't think of anything
        # better.
        for item in obj.get(self.listkey):
            row = []
            for key in self.keys:
                row.append(item.get(key))
            model.append( row + [item] )


            
#     def check_in(self):
#         itemlist = self.listowner.get(self.listkey)
#         model = self.treeview.get_model()
#         model.clear()
#         for item in itemlist:
#             row = []
#             for key in self.keys:
#                 row.append(item.get(key))
#             model.append( row + [item] )

#         self.old_list = itemlist
        

    def check_out(self, undolist=[]):

        ul = UndoList()
        
        def check_out_row(owner, iter, undolist=[]):
            n = 0
            adict = {}
            for key in self.keys:
                adict[key]=model.get_value(iter, n)
                n += 1
            adict['undolist'] = ul
            uwrap.smart_set(owner, **adict)

        new_list = []
        model = self.treeview.get_model()
        iter = model.get_iter_first()
        while iter is not None:
            owner = model.get_value(iter, len(self.keys))
            check_out_row(owner, iter, undolist=ul)
            new_list.append(owner)
            iter = model.iter_next(iter)

        if self.old_list != new_list:        
            uwrap.set(self.listowner, self.listkey, new_list, undolist=ul)
            self.old_list = new_list

        undolist.append(ul)


    def new_column_creator(klass, key):
        keyklass = getattr(klass, key).__class__
        if keyklass == Choice:
            return ColumnCreator_Choice_As_Combobox(klass, key)
        elif keyklass == Mapping:
            return ColumnCreator_Mapping_As_Combobox(klass, key)
        elif keyklass == Bool:
            return ColumnCreator_Bool_As_Checkbutton(klass, key)
        else:
            return ColumnCreator_Anything_As_Entry(klass, key)
    
    new_column_creator = staticmethod(new_column_creator)


    

class Column(object):
    def __init__(self, klass, key):                 
        self.check = getattr(klass, key)
        self.key = key
        self.cell = None # TODO

    def get_column_key(self):
        key = self.check.blurb or self.key
        return key.replace('_', ' ')        



class ColumnCreator_Anything_As_Entry(Column):
    
    def create_column(self, model, index):
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited, model, index)

        column = gtk.TreeViewColumn(self.get_column_key())
        column.pack_start(cell)
        column.set_cell_data_func(cell, self.cell_data_func, index)

        self.column = column
        return column


    def on_edited(self, cell, path, data, model, index):
        try:
            data = self.check(data)
        except ValueError:
            pass
        else:
            model[path][index] = data
            
    def cell_data_func(self, column, cell, model, iter, index):
        value = model.get_value(iter, index)
        if value is None:
            value = ""
        cell.set_property('text', unicode(value))
        


class ColumnCreator_Choice_As_Combobox(Column):
    
    def create_column(self, model, index):
        cell_model = self.new_cell_model()
        
        cell = gtk.CellRendererCombo()                        
        cell.set_property('text-column', 0)
        cell.set_property('model', cell_model)

        # make editable
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited, model, index)
        
        column = gtk.TreeViewColumn(self.get_column_key())
        column.pack_start(cell)
        column.set_cell_data_func(cell, self.cell_data_func, index)

        self.column = column
        return column

    def new_cell_model(self):        
        cell_model = gtk.ListStore(str, object)
        for value in self.check.choices:
            if value is None:
                cell_model.append(('', None))
            else:
                cell_model.append((unicode(value), value))
        return cell_model

    def on_edited(self, cell, path, new_text, model, index):
        if len(new_text) == 0:
            new_text = None
        try:
            model[path][index] = self.check(new_text)            
        except ValueError:
            print "Could not set combo to value '%s', %s" % (new_text, type(new_text))

    def cell_data_func(self, column, cell, model, iter, index):
        user_value = model.get_value(iter, index)
        if user_value is None:
            user_value = ""
        cell.set_property('text', unicode(user_value))


class ColumnCreator_Mapping_As_Combobox(Column):

    def create_column(self, model, index):
        cell_model = self.new_cell_model()
        
        cell = gtk.CellRendererCombo()                        
        cell.set_property('text-column', 0)
        cell.set_property('model', cell_model)

        # make editable
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited, model, index)
        
        column = gtk.TreeViewColumn(self.get_column_key())
        column.pack_start(cell)
        column.set_cell_data_func(cell, self.cell_data_func, index)

        self.column = column
        return column

    def new_cell_model(self):
        self.keys = {}
        cell_model = gtk.ListStore(str, object)
        for key, value in self.check.mapping.iteritems():
            if key is None:
                key = ""            
            cell_model.append((unicode(key), value))
            self.keys[value] = unicode(key) # for reverse mapping
        return cell_model

    def on_edited(self, cell, path, new_text, model, index):
        if len(new_text) == 0:
            new_text = None
        try:
            model[path][index] = self.check(new_text)            
        except ValueError:
            print "Could not set combo to value '%s', %s" % (new_text, type(new_text))

    def cell_data_func(self, column, cell, model, iter, index):
        user_value = model.get_value(iter, index)
        if user_value is None:
            user_value = ""
        cell.set_property('text', self.keys[user_value])



class ColumnCreator_Bool_As_Checkbutton(Column):

    def create_column(self, model, index):
        cell = gtk.CellRendererToggle()

        cell.set_property('activatable', True)
        cell.connect('toggled', self.on_toggled, model, index)

        column = gtk.TreeViewColumn(self.get_column_key())
        column.pack_start(cell)
        column.set_cell_data_func(cell, self.cell_data_func, index)

        self.column = column
        return column


    def cell_data_func(self, column, cell, model, iter, index):
        value = model.get_value(iter, index)
        cell.set_property('active', bool(self.check(value)))


    def on_toggled(self, cell, path, model, index):
        value = not model[path][index]
        try:
            value = self.check(value)
        except ValueError:
            pass
        else:        
            model[path][index] = value

