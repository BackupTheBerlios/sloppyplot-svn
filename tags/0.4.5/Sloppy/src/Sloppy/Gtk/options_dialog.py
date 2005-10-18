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


from Sloppy.Lib.Props.Gtk import pwconnect
from Sloppy.Lib.Props import pBoolean



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
        self.connectors = construct_connectors(owner)
        if len(self.connectors) == 0:
            raise NoOptionsError
        
        self.tablewidget = construct_table(self.connectors)

        frame = gtk.Frame('Edit')
        frame.add(self.tablewidget)
        frame.show()

        self.vbox.pack_start(frame, False, True)
        self.tablewidget.show()

        
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



#------------------------------------------------------------------------------
# Convenience Methods To Construct Connectors And Container Widgets For Them.
#
       
def construct_table(clist):
    tw = gtk.Table(rows=len(clist), columns=2)
    tooltips = gtk.Tooltips()

    n = 0
    for c in clist:                
        # widget
        tw.attach(c.widget, 1,2,n,n+1,
                  xoptions=gtk.EXPAND|gtk.FILL,
                  yoptions=0, xpadding=5, ypadding=1)

        # label (put into an event box to display the tooltip)
        label = gtk.Label(c.prop.blurb or c.key)
        label.set_alignment(0,0)
        #label.set_justify(gtk.JUSTIFY_LEFT)
        label.show()

        ebox = gtk.EventBox()
        ebox.add(label)
        ebox.show()
        if c.prop.doc is not None:
            tooltips.set_tip(ebox, c.prop.doc)

        tw.attach(ebox, 0,1,n,n+1,
                  yoptions=0, xpadding=5, ypadding=1)

        n += 1
    return tw


def construct_connectors(owner):
    """    
    If owner.public_props is set, then the creation of connectors is limited
    to items of this list.
    """
    if hasattr(owner, 'public_props'):
        proplist = []
        for key in owner.public_props:
            proplist.append(owner.get_prop(key))
    else:
        proplist = owner.get_props().itervalues()
    
    clist = []
    for prop in proplist:
        
        #
        # Determine type of connector from widget type
        # and construct it.
        #
        if prop.get_value_dict() is not None:
            ctype = "ComboBox"
        elif prop.get_value_list() is not None:
            ctype = "ComboBox"
        elif isinstance(prop, pBoolean):
            ctype = "CheckButton"
        else:
            ctype = "Entry"

        connector = pwconnect.connectors[ctype](owner, prop.name)
        connector.create_widget()
        connector.widget.show()        
        clist.append(connector)

    return clist



from Sloppy.Base import dataio

if __name__ == "__main__":
    importer = dataio.ImporterRegistry.new_instance('ASCII')
    dlg = OptionsDialog(importer)
    dlg.run()
    dlg.destroy()
    

        
        
                 
