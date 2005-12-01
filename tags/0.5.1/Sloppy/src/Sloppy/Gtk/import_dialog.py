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
from Sloppy.Lib.Props import pKeyword
       
        

class ImportOptions(gtk.Dialog):
    
    def __init__(self, template_key, previewfile=None, gladefile=None):
        gtk.Dialog.__init__(self, "Importing %s" % template_key, None,
                            gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.set_size_request(520,480)

        # create a new importer based on the template
        self.template = dataio.import_templates[template_key]
        self.importer = self.template.new_instance()
        
        #
        # set up connectors
        #
        self.connectors = pwglade.construct_connectors(self.importer)            
        table_options = pwglade.construct_table(self.connectors)
        widget = uihelper.new_section("Import Options", table_options)
        self.vbox.pack_start(widget,False,True)

        for c in self.connectors:
            c.check_in()

        #
        # add preview widget
        #
        preview = self.construct_preview(previewfile)
        self.vbox.pack_start(preview,True,True)

        hint = gtk.Label()
        hint.set_markup("<i>Hint: These importer settings can later on be retrieved\nas 'recently used' template in the Edit|Preferences dialog.</i>")
        hint.set_use_markup(True)
        self.vbox.pack_start(hint,False,True)
        
        self.vbox.show_all()
        

    def run(self):
        response = gtk.Dialog.run(self)

        if response == gtk.RESPONSE_ACCEPT:
            for c in self.connectors:
                c.check_out()            

        return response            


    def construct_preview(self, filename):
        if filename is None:
            return gtk.Label()           
        
        view = gtk.TextView()
        buffer = view.get_buffer()
        view.set_editable(False)
        view.show()
        
        tag_main = buffer.create_tag(family="Courier")
        tag_linenr = buffer.create_tag(family="Courier", weight=pango.WEIGHT_HEAVY)

        # fill preview buffer with at most 100 lines
        try:
            fd = open(filename, 'r')
        except IOError:
            raise RuntimeError("Could not open file %s for preview!" % filename)

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

        return uihelper.new_section("Preview", uihelper.add_scrollbars(view))

            
        
        
##############################################################################
def test1():
    importer = dataio.importer_registry['ASCII']()
    dlg = ImportDialog(importer, 'ASCII::pfc')
    dlg.run()
    
    print dlg.importer.get_values(include=['header_size'])
    dlg.check_out()
    print
    print dlg.importer.get_values(include=['header_size'])



def test2():
    dlg = SimpleImportDialog('ASCII')
    try:
        dlg.run()
        print "options: ", dlg.modify_options
        print "template key:", dlg.template_key
    finally:
        dlg.destroy()

def test3():
    dlg = ImportOptions("ASCII", gladefile='./Glade/ascii.glade')
    dlg.run()
    print "=> ", dlg.importer.get_values()
    dlg.destroy()    
        
if __name__ == "__main__":
    import Sloppy
    Sloppy.init()

    test3()

