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

# $HeadURL: file:///home/nv/sloppysvn/trunk/Sloppy/src/Sloppy/Gtk/gnuplot_export_dlg.py $
# $Id: gnuplot_export_dlg.py 429 2005-08-03 06:04:10Z nv $


import logging
logger = logging.getLogger('gtk.ascii_wizard')

import pygtk # TBR
pygtk.require('2.0') # TBR

import gtk, gobject

import uihelper
import propwidgets

from Sloppy.Base.dataio import ImporterRegistry


class ImportWizard(gtk.Dialog):
    
    def __init__(self, filenames):

        gtk.Dialog.__init__(self, "Import Wizard", None,
                            gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.set_size_request(480,320)
        
        self.treeview = self.construct_treeview()        
        self.populate_preview(filenames[0])

        sw = uihelper.add_scrollbars(self.treeview)
        self.treeview.show()

        self.vbox.pack_end(sw, True, True)
        sw.show()

        self.importer = ImporterRegistry.new_instance('ASCII')

        frame = gtk.Frame()


        def redisplay(sender, event, treeview):
            treeview.queue_draw()
            
        pw_skip, box_skip = propwidgets.construct_pw_in_box(self.importer, 'skip')
        pw_skip.widget.connect('focus-out-event', redisplay, self.treeview)
        self.pw_skip = pw_skip        
        box_skip.show()

        
        pw_designations, box_designations = propwidgets.construct_pw_in_box(self.importer, 'designations')
        #pw_designations.connect('
        box_designations.show()

        hbox = gtk.HBox()
        hbox.pack_start(box_skip)
        hbox.pack_start(box_designations)
        hbox.show()
        
        frame.add(hbox)

        self.vbox.pack_start(frame, False, True)
        frame.show()
        
        
        # properties to determine:
        # skip
        # designations (=repeating pattern)
        # delimiter | custom_delimiter
        # nr of columns

    def construct_treeview(self):
       
        def render_line(column, cell, model, iter):
            linenr = model.get_value(iter, 0)
            value = model.get_value(iter, 1)
            
            cell.set_property('text', value)

            print "==>", self.pw_skip.get_value()
            foreground = ('blue', 'black')[not linenr < self.pw_skip.get_value()]
            cell.set_property('foreground', foreground)
                

        model = gtk.ListStore(int, str) # linenr, line
        treeview = gtk.TreeView(model)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn('linenr', cell, text=0)
        treeview.append_column(column)

        column = gtk.TreeViewColumn('line', cell)
        column.set_cell_data_func(cell, render_line)
        treeview.append_column(column)
        return treeview


    def populate_preview(self, filename):
        
        try:
            fd = open(filename, 'r')
        except IOError:
            raise

        model = self.treeview.get_model()
        model.clear()
        
        try:
            for j in range(1,99):
                line = fd.readline()
                if len(line) == 0:
                    break

                try:
                    contents = unicode(line[:-1])
                except UnicodeDecodeError:
                    contents = u"<unreadable line>"

                model.append( (j, contents) )
        finally:
            fd.close()

        


if __name__ == "__main__":

    dlg = ImportWizard( ["test.dat"] )
    dlg.run()

    
