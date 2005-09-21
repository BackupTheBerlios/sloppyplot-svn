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
logger = logging.getLogger('gtk.importer_options_dlg')

import pygtk # TBR
pygtk.require('2.0') # TBR

import gtk, gobject

from propwidgets import *


class NoOptionsError(Exception):
    pass

class OptionsDialog(gtk.Dialog):

    def __init__(self, container, parent=None):
            
        gtk.Dialog.__init__(self, "Options", parent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        self.container = container

        if hasattr(container, 'public_props'):
            props = container.public_props
        else:
            props = self.container.get_props().keys()

        if len(props) == 0:
            raise NoOptionsError

        self.pwbox = PWTableBox(self.container, props)
        self.pwbox.show()
        
        frame = gtk.Frame("Options")
        frame.add(self.pwbox)
        frame.show()

        self.vbox.add(frame)
        self.vbox.show()


    def run(self):
        self.pwbox.check_in()
        response = gtk.Dialog.run(self)
        if response == gtk.RESPONSE_ACCEPT:
            self.pwbox.check_out()
        return response    



from Sloppy.Base import dataio

if __name__ == "__main__":
    importer = dataio.ImporterRegistry.new_instance('ASCII')
    dlg = OptionsDialog(importer)
    dlg.run()
    dlg.destroy()
    

        
        
                 
