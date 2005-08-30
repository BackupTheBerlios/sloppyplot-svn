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

""" I have been using the propwidgets.py module to automate the
creation of widgets and corresponding labels for Props.  From a user's
point of view, this worked fine, even though it did not look so nice.
This module aims to be a reimplementation of such a mechanism, but it
needs to be different in some ways.  We need to be able to use a UI
designed by a glade file, specify a Container and its Props, and have
this module automagically find the corresponding input widgets, fill
in the data (e.g. the Prop's value_list for a ComboBox and attach
callbacks!
"""

import logging
logger = logging.getLogger('Gtk.pwglade')

try:
    import pygtk
    pygtk.require('2.0')
except ImportError:
    pass

import gtk

import pwconnect

from Sloppy.Lib.Props import Container,Prop, BoolProp


def test():
    import gtk.glade

    filename = "./Glade/example.glade"
    widgetname = 'main_box'
 
    win = gtk.Window()
    win.connect("destroy", gtk.main_quit)
    tree = gtk.glade.XML(filename, widgetname)    
    widget = tree.get_widget(widgetname)
    win.add(widget)

    # set up container
    class Options(Container):
        filename = Prop(coerce=unicode)
        mode = Prop(coerce=unicode,
                    value_list=[None, u'read-only', u'write-only', u'read-write'])
        include_header = BoolProp(default=None)
        
    options = Options(filename="test.dat", mode=u'read-only')
    print options.values
    print options.props

    def wrap(container, key, wrapper_class):
        wrapper = wrapper_class(container, key)
        widget_key = 'pw_%s' % key
        widget = tree.get_widget(widget_key)
        if widget is not None:
            wrapper.use_widget(widget)
        else:
            raise RuntimeError("Could not find widget '%s'" % widget_key)
        wrapper.check_in()
        return wrapper

    to_be_wrapped = {'filename' : pwconnect.Entry,
                     'mode' : pwconnect.ComboBox,
                     'include_header' : pwconnect.CheckButton}

    wrapped = {}
    for k,v in to_be_wrapped.iteritems():
        wrapped[k] = wrap(options, k, v)    
        
    def finish_up(sender):
        for wrapper in wrapped.itervalues():
            wrapper.check_out()
        
        # display props
        print 
        for k,v in options.values.iteritems():            
            print "%s = %s" % (k,v)
        print
        
        gtk.main_quit()
    signals = {"on_button_ok_clicked": finish_up}
    tree.signal_autoconnect(signals)

    win.show()
    gtk.main()


if __name__ == "__main__":
    test()

        
