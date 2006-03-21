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

# $HeadURL: svn+ssh://svn.berlios.de/svnroot/repos/sloppyplot/trunk/Sloppy/src/Sloppy/Gtk/dock.py $
# $Id: dock.py 137 2005-09-18 22:07:32Z niklasv $

import gtk

from Sloppy.Base.objects import SPObject
from Sloppy.Base.backend import Backend
from Sloppy.Base import uwrap, error, globals
from Sloppy.Lib.Check import Instance
from Sloppy.Lib.Undo import ulist, UndoList
from Sloppy.Lib.ElementTree.ElementTree import Element, SubElement
from Sloppy.Gtk import uihelper, dock, checkwidgets


import logging
logger = logging.getLogger('Gtk.toolbox')


#------------------------------------------------------------------------------
# Global Tools Registry
#
ToolRegistry = {}

def register_tool(klass, name=None):
    " Helper functions for plugins. "
    global ToolRegistry
    if name is None:
        name = klass.__name__
    if ToolRegistry.has_key(name):
        logger.error("Tool %s is already registered." % name)
        return
        
    ToolRegistry[name] = klass        
        

#------------------------------------------------------------------------------      
# Toolbox configuration
#
# Todo: maybe use ToolBox as a child of Dock and put these
# config methods into the ToolBox.
#

class ToolBox(dock.Dock):

    def __init__(self, dock_name = "unnamed dock"):
        dock.Dock.__init__(self, dock_name)

        globals.app.sig_connect('write-config',
          lambda sender, eConfig: self.write_config(eConfig))

    def read_config(self, eConfig, default=[]):
        global ToolRegistry
        dock_name = self.get_data('name')

        eDock = eConfig.find(dock_name)
        if eDock is None or len(eDock.findall('Dockbook/Dockable')) == 0:
            logger.debug("Using default Dock configuration")
            default.reverse()
            for item in default:
                book = dock.Dockbook()
                self.add(book)
                tool = ToolRegistry[item]()
                book.add(tool)
            return

        for eDockbook in eDock.findall('Dockbook'):
            book = dock.Dockbook()
            self.add(book)
            for eDockable in eDockbook.findall('Dockable'):
                try:                    
                    tool = ToolRegistry[eDockable.text]()
                    book.add(tool)
                    # TODO: size information is not used                    
                except Exception, msg:
                    logger.error("Could not init tool dock '%s': %s" % (eDockable.text, msg))
                else:
                    print ">>> Tool added", eDockable.text

        self.show_all()

        
    def write_config(self, eConfig):
        dock_name = self.get_data('name')

        eDock = eConfig.find(dock_name)
        if eDock is None:
            eDock = SubElement(eConfig, dock_name)
        else:
            eDock.clear()

        # get information about dockables/dockbooks
        for dockbook in self.dockbooks:
            eDockbook = SubElement(eDock, "Dockbook")        
            for dockable in dockbook.get_children():
                eDockable = SubElement(eDockbook, "Dockable")
                ##width, height = dockable.size_request()            
                ##eDockable.attrib['width'] = str(width)
                ##eDockable.attrib['height'] = str(height)
                eDockable.text = dockable.__class__.__name__



#------------------------------------------------------------------------------
# Tool and derived classes
#
class Tool(dock.Dockable):

    """ Dockable base class for any tool that edits part of a Plot. """

    name = "Unnamed Tool"
    stock_id = gtk.STOCK_EDIT
    
    def __init__(self):
        dock.Dockable.__init__(self)

    def on_menu_button_clicked(self, sender):
        globals.app.popup_info = self        
        uim = globals.app.window.uimanager
        popup = uim.get_widget('/popup_toolconfig')
        popup.popup(None,None,None,3,0)

    def close_button_clicked(self, sender):
        if len(self.dockbook.get_children()) == 1 and len(self.dockbook.dock.dockbooks) == 1:
            return False
        else:
            dock.Dockable.close_button_clicked(self, sender)


    def depends_on(self, obj, *vars):
        # for generic_on_update
        self.signalmap = {}        
        self.dependency_chain = list(vars)
        
        for var in self.dependency_chain:
            setattr(self, var, None)
        obj.sig_connect('update::%s'%vars[0],
          lambda sender, value: self.generic_on_update(vars[0], sender, value))        
        

    def generic_on_update(self, var, sender, value):
        print "GENERIC UPDATE FOR VAR ", var
        print "%s = %s" % (sender, value)

        old_value = getattr(self, var)
        if value == old_value:
            return

        if self.signalmap.has_key(sender):
            signal = self.signalmap.pop(sender)
            # propagate None value before disconnecting
            if value is None and old_value is not None:
                signal(old_value, None)
            signal.disconnect()                

        setattr(self, var, value)                
        if value is not None:
            obj = value # assume this is a Painter/Backend object

            # Connect to the update mechanism of the next dependency.
            # If this is already the last dependency, then we call
            # on_update_object, which then can use the object.
            try:
                next_var = self.dependency_chain[self.dependency_chain.index(var)+1]
            except IndexError:
                pass
            else:
                new_signal = obj.sig_connect('update::%s'%next_var,
                  lambda sender,value: self.generic_on_update(next_var, sender, value))
                self.signalmap[sender] = new_signal            

        # notify if object has changed
        cbname = 'autoupdate_%s'%var
        if hasattr(self, cbname):
            getattr(self, cbname)(sender, value)



    def track(self, key, obj, var):
        " track('backend', globals.app, 'active_backend') "
        if self.tracks.has_key(key):
            signal = self.tracks[key]
            signal.disconnect()
            setattr(self, key) = None

        self.tracks[key] = new_signal
        
