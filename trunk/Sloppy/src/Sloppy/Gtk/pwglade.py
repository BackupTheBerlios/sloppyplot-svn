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

""" Helper module to use Connector objects from pwconnect along with glade.

Note: I have been using the propwidgets.py module to automate the
creation of widgets and corresponding labels for Props.  From a user's
point of view, this worked fine, even though it did not look so nice.
This module aims to be a reimplementation of such a mechanism, but it
needs to be different in some ways.  We need to be able to use a UI
designed by a glade file, specify a Container and its Props, and have
this module automagically find the corresponding input widgets, fill
in the data (e.g. the Prop's value_list for a ComboBox) and attach
callbacks!
"""

import logging
logger = logging.getLogger('pwglade')

try:
    import pygtk
    pygtk.require('2.0')
except ImportError:
    pass

import gtk

import pwconnect


from Sloppy.Lib.Props import *
from Sloppy.Base.properties import *


#------------------------------------------------------------------------------

# def construct_connectors_from_glade_tree(container, tree, prefix='pw_'):
#     """
#     Find the widgets in the glade file that match the props
#     of the given Container.  If e.g. the prop key is 'filename',
#     and the prefix is 'pw_', then we are looking for a widget
#     called 'pw_filename'.        

#     If the widget is found, then a Connector that matches the
#     widget's type is created.  This is based on the class name
#     of the widget.

#     Currently there is no way to specify a certain Connector for a
#     certain widget.  I guess it would be better to put this into a
#     separate method that creates Connectors based on a dictionary
#     of widget names.

#     Returns the created connectors.
#     """

#     connectors = []
#     keys = container.get_props().keys()
#     for key in keys:
#         widget_key = prefix + key
#         widget = tree.get_widget(widget_key)
#         if widget is None:
#             logger.error("No widget found for prop '%s'" % key)
#             continue
#         try:
#             connector = pwconnect.connectors[widget.__class__.__name__](container, key)
#         except KeyError:
#             raise RuntimeError("No matching Connector available for widget '%s' of %s" % (widget_key, widget.__class__.__name__))
#         connector.use_widget(widget)
#         connectors.append(connector)

#     return connectors

       
def construct_table(clist):
    """
    Returns a table widget, based on a given list of connectors.
    """
    
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

