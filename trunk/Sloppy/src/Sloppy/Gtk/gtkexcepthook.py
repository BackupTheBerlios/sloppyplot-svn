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


"""
Helper module which redirects exceptions to a nice GTK window,
allowing the user to see exceptions even if no terminal is opened.

Just import the module to obtain the functionality.

Taken from pygtk FAQ 20.10
Credits go to Gustavo Carneiro.
"""

import logging
logger = logging.getLogger('Gtk.gtkexcepthook')


import gtk, pango

import sys
from cStringIO import *
import traceback
from gettext import gettext as _


from Sloppy.Base import error


def _info(type, value, tb):


    # Check for Sloppy-specific errors.  These indicate that
    # a certain kind of error message is requested.  All other
    # errors should display a generic error dialog.


    if isinstance(value, error.SloppyError):
        msg = "<big><b>SloppyPlot Error:</b></big>\n\n"
        msg += '\n'.join(value.args)

        dialog = gtk.MessageDialog(parent=None,flags=0,
                                   type=gtk.MESSAGE_ERROR,
                                   buttons=(gtk.BUTTONS_CLOSE),
                                   message_format=msg)
        dialog.vbox.get_children()[0].get_children()[1].get_children()[0].set_property("use-markup", True)
        
        dialog.set_position(gtk.WIN_POS_CENTER)
        dialog.set_gravity(gtk.gdk.GRAVITY_CENTER)    
        
        try:
            dialog.run()
        finally:
            dialog.destroy()

    elif isinstance(value, KeyboardInterrupt):
        # for testing versions, allow keyboard interrupt
        pass
    else:
        msg = _("<big><b>A programming error has been detected during the execution of this program.</b></big>"
                "\n\nIt probably isn't fatal, but should be reported to the developers nonetheless.")        
        dialog = gtk.MessageDialog(parent=None,
                                   flags=0,
                                   type=gtk.MESSAGE_WARNING,
                                   buttons=gtk.BUTTONS_NONE,
                                   message_format=msg)
        
        dialog.set_title(_("Bug Detected"))        
        dialog.set_property("has-separator", False)
        dialog.vbox.get_children()[0].get_children()[1].get_children()[0].set_property("use-markup", True)

        dialog.add_button(_("Show Details"), 1)
        dialog.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)

        # Details
        textview = gtk.TextView(); textview.show()
        textview.set_editable(False)
        textview.modify_font(pango.FontDescription("Monospace"))
        sw = gtk.ScrolledWindow(); sw.show()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(textview)
        frame = gtk.Frame();
        frame.set_shadow_type(gtk.SHADOW_IN)
        frame.add(sw)
        frame.set_border_width(6)
        dialog.vbox.add(frame)
        textbuffer = textview.get_buffer()
        trace = StringIO()
        traceback.print_exception(type, value, tb, None, trace)
        logger.critical("%s" % trace.getvalue())
        textbuffer.set_text(trace.getvalue())
        textview.set_size_request(gtk.gdk.screen_width()/2, gtk.gdk.screen_height()/3)

        dialog.details = frame
        dialog.set_position(gtk.WIN_POS_CENTER)
        dialog.set_gravity(gtk.gdk.GRAVITY_CENTER)

        # TODO: This is turned off during development!
        if True:
            try:
                while 1:
                    resp = dialog.run()
                    if resp == 1:
                        dialog.details.show()
                        dialog.action_area.get_children()[1].set_sensitive(0)
                    else:
                        break
                        
            finally:
                dialog.destroy()
        
        
    

sys.excepthook = _info


