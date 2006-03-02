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

from Sloppy.Lib.Check import HasChecks
from uihelper import add_scrollbars

import gtk

import logging
logger = logging.getLogger('Gtk.dlg_metadata')

"""
A very simple implementation of a dialog to browse the attributes of
a HasChecks object. Nothing fancy.
"""

# TODO: implement support for lists and dictionaries!


class PropertyBrowser(gtk.TreeView):

    """ The PropertyBrowser allows (read-only)
    browsing through an object's Properties. """
    
    def __init__(self, obj):

        # model: object, key, label
        # if key is None, then we have a node
        model = gtk.TreeStore(object, str, str)        
        gtk.TreeView.__init__(self, model)

        def add_item(item, key=None, iter=None):

            if key is None:                
                # add item itself
                iter = model.append(iter, (item, key, item.__class__.__name__))

                if hasattr(item, 'browser_keylist'):
                    keys = item.browser_keylist.keys(item)
                else:
                    keys = item._checks.keys()
                    
                # add properties
                for key in keys:
                    add_item(item, key, iter)
            else:
                # add property by key
                model.append(iter, (item, key, key))

        add_item(obj)

        # key column        
        column = gtk.TreeViewColumn('key')
        cell = gtk.CellRendererText()
        column.pack_start(cell)
        column.set_attributes(cell, text=2)
        self.append_column(column)

        # value column
        column = gtk.TreeViewColumn('value')
        cell = gtk.CellRendererText()
        column.pack_start(cell)
        column.set_cell_data_func(cell, self.cell_data_func_value)
        self.append_column(column)

    def cell_data_func_value(self, column, cell, model, iter):
        obj = model.get_value(iter, 0)
        key = model.get_value(iter, 1)
        if key is None:
            text = ""
        else:
            text = obj.get(key)

        cell.set_property('text', unicode(text))

            
        

class PropertyBrowserDialog(gtk.Dialog):

    def __init__(self, dataset, parent=None):
        gtk.Dialog.__init__(self, "Metadata", parent,
                            gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        self.set_size_request(480,320)
        
        pb = PropertyBrowser(dataset)
        pb.expand_all()
        self.vbox.add(add_scrollbars(pb))

        self.show_all()
        

if __name__ == "__main__":

    from Sloppy.Base.dataset import Dataset
    from Sloppy.Base.objects import Plot, Layer

#    ds = Dataset(key="DS1724", label="a sample dataset",
#                 metadata={'Whatever':42, 'However': 24},
#                 data = None)


    #ds = Plot(layers=[Layer(), Layer()])

    ds = Layer()
    dlg = PropertyBrowserDialog(ds)
    try:
        dlg.run()
    finally:
        dlg.destroy()



    
