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

try:
    import pygtk
    pygtk.require('2.0')
except ImportError:
    pass

import gtk, gtk.glade

import uihelper
import pwconnect, pwglade

from Sloppy.Base.dataio import importer_registry


#------------------------------------------------------------------------------

class Wizard(gtk.Dialog):

    def __init__(self):
        gtk.Dialog.__init__(self, "Import Wizard", None,
                            gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        self.set_size_request(480,320)
       
        self.nb = gtk.Notebook()
        self.nb.show()        
        self.vbox.pack_start(self.nb,True,True)

        self.init()
        

    def add_page(self, wizardpage):
        self.nb.append_page(wizardpage)

    def run(self):
        pages = self.nb.get_children()
        if len(pages) > 0:
            page = pages[0]
            page.show()

        gtk.Dialog.run(self)                



class AsciiWizard(Wizard):

    def init(self):
        self.add_page(AsciiWizardPage('test.dat'))
        self.set_size_request(640,480)

    def run(self):
        Wizard.run(self)
        for page in self.nb.get_children():
            pwglade.check_out(page.connectors)
            print page.importer.get_values()
        

class WizardPage(gtk.VBox):
    pass


class AsciiWizardPage(WizardPage):

    gladefile = './Glade/ascii_wizard.glade'
    
    def __init__(self, filename):
        WizardPage.__init__(self)

        # construct ui from glade file
        tree = gtk.glade.XML(self.gladefile, 'wizard_page_1')
        page = tree.get_widget('wizard_page_1')
        page.show()
        self.add(page)
       
        # Set up import object which hold the options and
        # create the connection to the GUI.
        self.importer = importer_registry['ASCII']()
        self.connectors = pwglade.construct_connectors_from_glade_tree(self.importer, tree)
        pwglade.check_in(self.connectors)


        self.header_lines = 0

        def update_header_lines(sender, event):
            try: self.header_lines = int(sender.get_text())
            except: self.header_lines = 0
            self.treeview.queue_draw()

        widget = self.connectors['header_lines'].widget
        widget.connect('focus-out-event', update_header_lines)
        
        # populate treeview
        self.treeview = tree.get_widget('treeview_preview')
        self.prepare_treeview()
        self.populate_preview(filename)
        


    def prepare_treeview(self):
       
        def render_line(column, cell, model, iter):
            linenr = model.get_value(iter, 0)
            value = model.get_value(iter, 1)
            
            cell.set_property('text', value)
            foreground = ('blue', 'black')[not linenr <= self.header_lines]
            cell.set_property('foreground', foreground)
                

        model = gtk.ListStore(int, str) # linenr, line
        self.treeview.set_model(model)
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn('linenr', cell, text=0)
        self.treeview.append_column(column)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn('line', cell)
        column.set_cell_data_func(cell, render_line)
        self.treeview.append_column(column)


    def populate_preview(self, filename):
        # we try to include the first N lines into the preview
        N = 99
        
        try: fd = open(filename, 'r')
        except IOError:  raise
        
        model = self.treeview.get_model()
        model.clear()
        
        try:
            for j in range(1,N):
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

    import Sloppy
    Sloppy.init()
    
    dlg = AsciiWizard()
    dlg.run()

    
