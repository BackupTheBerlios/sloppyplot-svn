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



#------------------------------------------------------------------------------

class ConnectorFactory:

    def create_from_glade_tree(self, container, tree, prefix='pw_'):
        """
        Find the widgets in the glade file that match the props
        of the given Container.  If e.g. the prop key is 'filename',
        and the prefix is 'pw_', then we are looking for a widget
        called 'pw_filename'.        

        If the widget is found, then a Connector that matches the
        widget's type is created.  This is based on the class name
        of the widget.

        Currently there is no way to specify a certain Connector for a
        certain widget.  I guess it would be better to put this into a
        separate method that creates Connectors based on a dictionary
        of widget names.

        Returns the created connectors.
        """
        
        connectors = {}
        keys = container.get_props().keys()
        for key in keys:
            widget_key = prefix + key
            widget = tree.get_widget(widget_key)
            if widget is None:
                logger.error("No widget found for prop '%s'" % key)
                continue
            try:
                connector = pwconnect.connectors[widget.__class__.__name__](container, key)
            except KeyError:
                raise RuntimeError("No matching Connector available for widget '%s' of %s" % (widget_key, widget.__class__.__name__))
            connector.use_widget(widget)
            connectors[key] = connector

        return connectors

        

#------------------------------------------------------------------------------

def check_in(connectors):
    " Check in multiple Connectors. "
    for connector in connectors.itervalues():
        connector.check_in()

def check_out(connectors):
    " Check out multiple Connectors. "
    for connector in connectors.itervalues():
        connector.check_out()


def create_changeset(container, working_copy):
    """ Find differences between old container and the working copy.
    Returns a 'changeset' dictionary with the names of the props
    that have been changed as keys and the new value as values.
    """
    changeset = {}
    for key, value in working_copy.get_values().iteritems():
        old_value = container.get_value(key)
        if value != old_value:
            changeset[key] = value
    return changeset


#------------------------------------------------------------------------------        
# Testing Area
#

from Sloppy.Lib.Props import HasProps,Prop, pBoolean, pUnicode, CheckValid

# set up container
    
class Options(HasProps):
    filename = pUnicode()
    mode = pUnicode(CheckValid([None, u'read-only', u'write-only', u'read-write']))
    include_header = pBoolean(default=None)



def test():
    import gtk.glade

    filename = "./Glade/example.glade"
    widgetname = 'main_box'
    myoptions = Options(filename="test.dat", mode=u'read-only')
    options = myoptions.copy()

    # create window and add widget created by libglade
    win = gtk.Window()
    win.connect("destroy", gtk.main_quit)

    # This is the actual wrapping 
    tree = gtk.glade.XML(filename, widgetname)    
    widget = tree.get_widget(widgetname)
    win.add(widget)
    cf = ConnectorFactory()
    connectors = cf.create_from_glade_tree(options, tree)
    check_in(connectors)
       
    def finish_up(sender):
        check_out(connectors)
        changeset = create_changeset(myoptions, options)
        myoptions.set_values(**changeset)
        print "CHANGES: ", changeset        
        print "MYOPTIONS: ", myoptions.get_values()
        gtk.main_quit()
    signals = {"on_button_ok_clicked": finish_up}
    tree.signal_autoconnect(signals)


        

    win.show()
    gtk.main()


if __name__ == "__main__":
    test()

        
