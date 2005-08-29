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
logger = logging.getLogger('gtk.ascii_wizard')

import pygtk # TBR
pygtk.require('2.0') # TBR

import gtk, gobject, gtk.glade

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
        
        awp = AsciiWizardPage(filenames[0])
        awp.show()        
        self.vbox.pack_end(awp, True, True)


#------------------------------------------------------------------------------
#
#

class WizardPage(gtk.VBox):
    pass


class AsciiWizardPage(WizardPage):

    gladefile = './Glade/ascii_wizard.glade'
    
    def __init__(self, filename):
        WizardPage.__init__(self)
        
        self.treeview = self.construct_treeview()
        self.treeview.show()
        
        self.populate_preview(filename)


        self.importer = ImporterRegistry.new_instance('ASCII')

        frame = gtk.Frame()


        def redisplay(sender, event, treeview):
            treeview.queue_draw()


        # construct property widgets
        pwdict = {}
        for key in ['header_lines', 'designations']:
            print "Creating propwidget %s" % key
            pwdict[key] = propwidgets.construct_pw(self.importer, key)        
            
        # construct ui from glade file
        print "Setting up GUI"
        self.tree = gtk.glade.XML(self.gladefile, 'wizard_page_1')
        page = self.tree.get_widget('wizard_page_1')
        page.show()
        self.add(page)

        # fill in property widgets
        print dir(self.tree)
        for key, pw in pwdict.iteritems():
            print "Filling in property widget %s" % key
            widget = self.tree.get_widget('pw_%s' % key)
            print "..Found %s" % widget
            if widget is not None:
                widget.destroy()
            
#         pw_skip, box_skip = propwidgets.construct_pw_in_box(self.importer, 'header_lines')
#         pw_skip.widget.connect('focus-out-event', redisplay, self.treeview)
#         self.pw_skip = pw_skip        
#         box_skip.show()

        
#         pw_designations, box_designations = propwidgets.construct_pw_in_box(self.importer, 'designations')
#         #pw_designations.connect('
#         box_designations.show()

#         hbox = gtk.HBox()
#         hbox.pack_start(box_skip)
#         hbox.pack_start(box_designations)
#         hbox.show()
        
#         frame.add(hbox)
#         frame.show()
        
#         self.pack_start(frame, False, True)
#         self.pack_start(uihelper.add_scrollbars(self.treeview), True, True)
        
        
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

            #print "==>", self.pw_skip.get_value()
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

    
