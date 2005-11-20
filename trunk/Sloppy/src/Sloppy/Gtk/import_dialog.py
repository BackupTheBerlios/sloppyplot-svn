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

# $HeadURL: svn+ssh://niklasv@svn.berlios.de/svnroot/repos/sloppyplot/trunk/Sloppy/src/Sloppy/Gtk/application.py $
# $Id: application.py 284 2005-11-18 11:43:31Z niklasv $


"""
"""

import logging
logger = logging.getLogger('gtk.application')

try:
    import pygtk
    pygtk.require('2.0')
except ImportError:
    pass

import gtk, gtk.glade
import pango

import uihelper
import pwconnect, pwglade

from Sloppy.Base import dataio

#------------------------------------------------------------------------------

class ImportDialog(gtk.Dialog):

    def __init__(self, importer_key, template_key, filenames):
        gtk.Dialog.__init__(self, "%s Import" % "ASCII",
                            None,
                            gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        self.filenames = filenames
        self.importer_key = importer_key
        self.template_key = template_key

        # The importer is fixed
        #self.importer
        

        #
        # Combos for choosing the Template
        #
        label_importer = gtk.Label()
        label_importer.set_markup("<b>ASCII Import</b>")
        label_importer.set_use_markup(True)
#        label_importer.set_alignment(0,0.5)
#        label_importer.show()

        label_template = gtk.Label("Template: ")
#        label_template.show()        
        combo_template = gtk.ComboBox()
        combo_template.show()
        box_template = gtk.VBox()
        box_template.pack_start(label_template,False,True)
        box_template.pack_start(combo_template,True,True)
        box_template.show()

        topbox = gtk.VBox()
        topbox.pack_start(label_importer)
        topbox.pack_end(box_template)
        topbox.show()
        self.topbox = topbox

        #
        # preview widget
        #
        self.preview = self.construct_preview()
        self.preview.show()
        
        #
        # Options
        #
        optionbox = gtk.VBox()
        l = gtk.Label("Test")
        l.show()
        optionbox.pack_start(self.preview,True,True)
        optionbox.pack_start(l,False,True)
        optionbox.show()
        self.optionbox = optionbox
        
        expander = gtk.Expander("Options")
        expander.add(optionbox)
        expander.show()
        self.expander = expander

        #
        # put everything together
        #
        self.vbox.pack_start(self.topbox,False,True)
#        self.vbox.pack_start(self.preview,True,True)        
#        separator = gtk.HSeparator() ; separator.show()
#        self.vbox.pack_start(separator,False,True)
        self.vbox.pack_start(self.expander,False,True)


    def construct_preview(self):
        view = gtk.TextView()
        buffer = view.get_buffer()
        view.set_editable(False)
        view.show()
        
        tag_main = buffer.create_tag(family="Courier")
        tag_linenr = buffer.create_tag(family="Courier", weight=pango.WEIGHT_HEAVY)

        # fill preview buffer with at most 100 lines
        preview_file = self.filenames[0]
        try:
            fd = open(preview_file, 'r')
        except IOError:
            raise RuntimeError("Could not open file %s for preview!" % preview_file)

        iter = buffer.get_start_iter()        
        try:
            for j in range(1,100):
                line = fd.readline()
                if len(line) == 0:
                    break
                buffer.insert_with_tags(iter, u"%3d\t" % j, tag_linenr)
                try:
                    buffer.insert_with_tags(iter, unicode(line), tag_main)
                except UnicodeDecodeError:
                    buffer.insert_with_tags(iter, u"<unreadable line>\n", tag_main)
        finally:
            fd.close()

        return uihelper.add_scrollbars(view)
        
        


if __name__ == "__main__":

    dlg = ImportDialog('ASCII', 'pfc', ['test.dat'])
    dlg.run()
    
    
