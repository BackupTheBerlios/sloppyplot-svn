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


from Sloppy.Lib.Props import pBoolean
import pwconnect, pwglade, uihelper


class NoOptionsError(Exception):
    pass


class OptionsDialog(gtk.Dialog):

    """
    Note: run() does not check out the values, you have to do that yourself.
    """

    def __init__(self, owner, title="Edit Options", parent=None):
        """
        owner: instance of HasProps that owns the properties
        parent: parent window
        @note: 'parent' is currently ignored, since it produces a silly window placement!
        """
        gtk.Dialog.__init__(self, title, None,
                            gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))


        self.owner = owner
        self.connectors = pwglade.construct_connectors(owner)
        if len(self.connectors) == 0:
            raise NoOptionsError
        
        table = pwglade.construct_table(self.connectors)
        frame = uihelper.new_section(title, table)
        self.vbox.pack_start(frame, False, True)
        self.show_all()

        
    def check_in(self):
        for c in self.connectors:
            c.check_in()

    def check_out(self):
        for c in self.connectors:
            c.check_out()
        return self.owner
           
    def run(self):
        self.check_in()
        return gtk.Dialog.run(self)
