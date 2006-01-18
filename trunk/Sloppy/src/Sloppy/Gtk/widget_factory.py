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


from Sloppy.Gtk.pwconnect import *
import gtk

from Sloppy.Lib.Props import *
from Sloppy.Lib.Undo import UndoList
from Sloppy.Base.properties import *
from Sloppy.Gtk.proprenderer import *

class CTreeViewFactory:

    def __init__(self, listowner, listkey):
        self.listowner = listowner 
        self.listkey = listkey

        prop = listowner.get_prop(listkey)
        validators = [v for v in prop.validator.vlist if isinstance(v, VList)]
        if len(validators) == 0:
            raise TypeError("%s.%s must be a List.",
                            (listowner.__class__.__name__, listkey))        
        else:
            vlist = validators[0]
        item_validators = [v for v in vlist.item_validator.vlist if isinstance(v, VInstance)]
        if len(item_validators) == 0:
            raise TypeError("%s.%s must be limited to a certain class instance (VInstance)." %
                            (listowner.__class__.__name__, listkey))
        else:
            self.container = item_validators[0].instance()

        self.keys = []
        self.columns = {}
        
        self.model = None
        self.treeview = None



    def add_columns(self, *keys, **kwargs):
        for key in keys:
            if isinstance(key, basestring):
                self.keys = key
            elif isinstance(key, (list,tuple)):
                self.keys.extend(key)
            elif isinstance(key, dict):
                self.columns.update(key)
            else:
                raise TypeError("String, tuple or dict required.")

        if len(kwargs) > 0:
            self.add_columns(kwargs)

          
    def create_treeview(self):
        model = gtk.ListStore(*([object]*(len(self.keys) + 1)))    
        treeview = gtk.TreeView(model)        

        index = 1
        for key in self.keys:
            if self.columns.has_key(key):
                column = self.columns[key]
            else:
                column = gtk.TreeViewColumn(key)
                cname = get_cname(self.container, key)
                renderer = renderers[cname](self.container, key)
                column = renderer.create(model, index)
                self.columns[key] = column
                
            treeview.append_column(column)

            index += 1
            
        self.treeview = treeview
        return self.treeview


    def check_in(self):
        itemlist = self.listowner.get_value(self.listkey)
        model = self.treeview.get_model()
        for item in itemlist:
            row = []
            for key in self.keys:
                row.append( item.get_value(key) )
            model.append( [item] + row )

        self.old_list = itemlist
        

    def check_out(self, undolist=[]):

        def check_out_row(owner, iter, undolist=[]):
            n = 1
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
            owner = model.get_value(iter, 0)
            check_out_row(owner, iter, undolist=ul)
            new_list.append(owner)
            iter = model.iter_next(iter)
        
        if self.old_list != new_list:        
            uwrap.set(self.listowner, listkey, new_list, undolist=ul)
            self.old_list = new_list


#------------------------------------------------------------------------------

class CWidgetFactory:

    def __init__(self, container):
        self.container = container
        self.keys = []

    def add_keys(self, *keys):
        for key in keys:
            if isinstance(key, basestring):
                self.keys.append(key)
            elif isinstance(key, (list,tuple)):
                self.keys.extend(key)
            else:
                raise TypeError("String or tuple required.")
    
    def create_vbox(self):
        vbox = gtk.VBox()

        clist = []
        for key in self.keys:
            connector = new_connector(self.container, key)
            vbox.add(connector.create_widget())
            clist.append(connector)
        self.clist = clist

        return vbox

    def check_in(self):
        for connector in self.clist:
            connector.check_in()

    def check_out(self, undolist=[]):
        ul = UndoList()    
        for c in clist:
            c.check_out(undolist=ul)
        undolist.append(ul)       
