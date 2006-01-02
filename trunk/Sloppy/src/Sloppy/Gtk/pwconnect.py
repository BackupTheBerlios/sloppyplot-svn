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

"""Create widgets (or use existing widgets) to enter values for Props.

>>> # Get a Connector instance
>>> c = connectors['ComboBox'](container, 'propname')

>>> # create a widget
>>> c.create_widget()
>>> w = c.widget

>>> # check in / check out data into the container
>>> c.check_in()
>>> c.check_out()
"""

import logging
logger = logging.getLogger('pwconnect')

try:
    import pygtk
    pygtk.require('2.0')
except ImportError:
    pass

import gtk

from Sloppy.Base import uwrap
import sys


from Sloppy.Lib.Props.main import Undefined, VRange


__all__ = ['Connector', 'connectors',
           #
           'Entry', 'ComboBox', 'CheckButton', 'SpinButton'
           ]


class Connector(object):

    """ Abstract base class for all wrappers.  
    
    Derived class must implement 'create_widget'.  Of course, for the
    widget to be useful, it should also implement 'check_in' and
    'check_out'.  The default 'check_out' method relies on 'get_data',
    so it might make more sense to implement this instead.

    """
    
    def __init__(self, container, key):
        self.container = container
        self.key = key
        self.widget = None
        self.last_value = None
        self.init()

    def init(self):
        pass

    #----------------------------------------------------------------------
    # Helper Functions
    
    def get_value(self):
        return self.container.get_value(self.key, default=None)
    def set_value(self, value):
        if value != self.last_value:
            self.container.set_value(self.key, value)
            self.last_value = value
    def get_prop(self):
        return self.container.get_prop(self.key)
    prop = property(get_prop)

    def set_container(self, container):
        self.container = container

    #----------------------------------------------------------------------
    # Check In/Out
    
    def check_in(self):
        " Retrieve value from container "
        raise RuntimeError("check_in() needs to be implemented.")

    def get_data(self):
        """
        Return checked value from widget, so it can be passed on to
        the container.
        """        
        raise RuntimeError("get_data() needs to be implemented.")
    
    def check_out(self, undolist=[]):
        " Set value in container "
        new_value = self.get_data()
        if new_value != self.last_value:
            uwrap.smart_set(self.container, self.key, new_value, undolist=undolist)
            self.last_value = new_value

    #----------------------------------------------------------------------
    # UI Stuff

    def create_widget(self):
        raise RuntimeError("crete_widget() needs to be implemented.")


connectors = {}



    
class Entry(Connector):

    def create_widget(self, use_checkbutton=False):

        # create entry
        self.entry = gtk.Entry()

        entry = self.entry        
        entry.connect("focus-in-event", self.on_focus_in_event)
        entry.connect("focus-out-event", self.on_focus_out_event)

        # create checkbutton if requested
        if use_checkbutton is True:            
            self.checkbutton = gtk.CheckButton()
            self.checkbutton.connect("toggled",
              (lambda sender: entry.set_sensitive(sender.get_active())))
        else:
            self.checkbutton = None

        # pack everything together
        self.widget = gtk.HBox()

        widget = self.widget
        widget.pack_start(entry,True,True)
        if self.checkbutton is not None:
            widget.pack_start(self.checkbutton,False,True)                    
        widget.show_all()
        
        
    def on_focus_in_event(self, widget, event):
        self.last_value = widget.get_text()
        
        
    def on_focus_out_event(self, widget, event):
        value = widget.get_text()
        if value == self.last_value:
            return
        
        try:
            self.prop.check(value)
        except (TypeError, ValueError):
            print "Entry Value is wrong, resetting." # TODO: user notice
            widget.set_text(self.last_value)
            

    #----------------------------------------------------------------------

    def check_in(self):
        value = self.get_value()

        if self.checkbutton is not None:
            state = value is not None
            self.checkbutton.set_active(state)
            self.entry.set_sensitive(state)            
        else:
            if value is None:
                value = ""
            
        if value is not None:
            self.entry.set_text(unicode(value))
        self.last_value = value


    def get_data(self):
        value = self.entry.get_text()

        if self.checkbutton is not None:
            state = self.checkbutton.get_active()
            if state is False:
                return None
        else:
            if len(value) == 0:
                return None
            
        try:                    
            return self.prop.check(value)
        except:
            print "Entry Value is wrong, resetting." # TODO: user notice                    
            return None # TODO: what if the entry does not allow None?                            


connectors['Entry'] = Entry



class ComboBox(Connector):
    
    def init(self):
        self.value_dict = {}

        # The value_list is a list of all values in value_dict
        # and is created for caching purposes.
        self.value_list = []
        
    def create_widget(self, use_checkbutton=False):

        #
        # create combobox
        #
        self.combobox = gtk.ComboBox()

        # create combobox model
        combobox = self.combobox
        model = gtk.ListStore(str, object)
        combobox.set_model(model)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)

        # fill model
        model.clear()

        mapping = self.prop.get_mapping()
        if mapping is not None:
            for key, value in mapping.dict.iteritems():
                model.append((key or "<None>", value))
                self.value_dict[value] = value
                self.value_list.append(value)                
        else:
            # if no Mapping was found, try ValueList
            value_list = self.prop.get_value_list()
            if value_list is not None:
                for value in value_list.values:
                    model.append((value or "<None>", value))
                    self.value_dict[value] = value
                    self.value_list.append(value)                    


        # create checkbutton if requested
        if use_checkbutton is True:
            self.checkbutton = gtk.CheckButton()
            self.checkbutton.connect("toggled",\
              (lambda sender: combobox.set_sensitive(sender.get_active())))
        else:
            self.checkbutton = None
            if self.value_dict.has_key(None) is False \
                   and self.prop.on_default() is not None:
                model.append(("default [%s]" % self.prop.on_default(), None))
                self.value_dict[None] = None
                self.value_list.append(None)
        

        # pack everything together
        self.widget = gtk.HBox()

        widget = self.widget
        widget.pack_start(combobox,True,True)
        if self.checkbutton is not None:
            widget.pack_start(self.checkbutton,False,True)
        widget.show_all()


        
    #----------------------------------------------------------------------

    
    def check_in(self):
        value = self.get_value()

        if self.checkbutton is not None:
            active = value is not None
            self.checkbutton.set_active(active)
            self.combobox.set_sensitive(active)
            if (active is False):
                self.last_value = value
                return                
            
        try:
            index = self.value_list.index(value)
        except:
            raise ValueError("Connector for %s.%s failed to retrieve prop value '%s' in list of available values '%s'" % (self.container, self.key, self.get_value(), self.value_list))

        model = self.combobox.get_model()
        iter = model.get_iter((index,))
        self.combobox.set_active_iter(iter)

        self.last_value = value
        
    
    def get_data(self):
        if (self.checkbutton is not None) \
               and (self.checkbutton.get_active() is False):
            return None

        index = self.combobox.get_active()
        if index < 0:
            return None
        else:
            model = self.combobox.get_model()
            return model[index][1]        


connectors['ComboBox'] = ComboBox



class TrueFalseComboBox(ComboBox):

    def create_widget(self, use_checkbutton=False):

        #
        # create combobox
        #
        self.combobox = gtk.ComboBox()

        # create model
        combobox = self.combobox        
        model = gtk.ListStore(str, object)
        combobox.set_model(model)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)

        # fill combo
        model.clear()
        if use_checkbutton is False:
            self.value_dict[Undefined] = Undefined
            self.value_list.append(Undefined)
            model.append(('undefined', Undefined))
        
        value_dict = {'True': True, 'False': False}
        for key, value in value_dict.iteritems():
            model.append((key, value))
            self.value_dict[value] = value
            self.value_list.append(value)

        #
        # create checkbutton
        #
        if use_checkbutton is True:
            self.checkbutton = gtk.CheckButton()
            self.checkbutton.connect("toggled",\
              (lambda sender: self.combobox.set_sensitive(sender.get_active())))
        else:
            self.checkbutton = None

        #
        # pack everything together
        #
        self.widget = gtk.HBox()

        widget = self.widget
        widget.pack_start(combobox,True,True)
        if self.checkbutton is not None:
            widget.pack_start(self.checkbutton,False,True)
        widget.show_all()
        

        
        
connectors['TrueFalseComboBox'] = TrueFalseComboBox
            

class CheckButton(Connector):

    def create_widget(self):
        widget = gtk.CheckButton()
        widget.connect('toggled', self.on_toggled)
        self.widget = widget
        
    def on_toggled(self, widget):
        if self.widget.get_inconsistent() is True:
            self.widget.set_inconsistent(False)

    def check_in(self):
        value = self.get_value()
        self.last_value = value

        if value is None:
            self.widget.set_inconsistent(True)
        else:
            self.widget.set_inconsistent(False)
            self.widget.set_active(value is True)

    def get_data(self):
        # determine value (None,False,True)
        if self.widget.get_inconsistent() is True:
            return None
        else:
            return self.widget.get_active()


connectors['CheckButton'] = CheckButton




class SpinButton(Connector):

    def create_widget(self, use_checkbutton=True):
        #
        # create spinbutton
        #
        self.spinbutton = gtk.SpinButton()


        #
        # create checkbutton
        #
        if use_checkbutton is True:
            self.checkbutton = gtk.CheckButton()
            self.checkbutton.connect("toggled",\
              (lambda sender: self.spinbutton.set_sensitive(sender.get_active())))
        else:
            self.checkbutton = None
            
        #
        # pack everything together
        #
        self.widget = gtk.HBox()

        widget = self.widget
        widget.pack_start(self.spinbutton,True,True)
        if self.checkbutton is not None:
            widget.pack_start(self.checkbutton,False,True)
        widget.show_all()


        #
        # set spinbutton values
        #

        sb = self.spinbutton
        sb.set_numeric(True)

        vranges = [v for v in self.prop.validator.vlist if isinstance(v, VRange)]
        if len(vranges) > 0:
            vrange = vranges[0]
            lower,upper = vrange.min, vrange.max
        else:
            lower,upper = None,None

        if lower is None:
            lower = -sys.maxint

        if upper is None:
            upper = +sys.maxint

        sb.set_range(float(lower), float(upper))
        sb.set_increments(1,1)
        sb.set_digits(0)


        
    def check_in(self):
        value = self.get_value()
        if value is not None:
            value = float(value)        
        
        if self.checkbutton is not None:
            state = value is not None
            self.checkbutton.set_active(state)
            self.spinbutton.set_sensitive(state)
        if value is not None:
            self.spinbutton.set_value(value)

        self.last_value = value
            


        

    def get_data(self):
        if (self.checkbutton is not None) and \
               (self.checkbutton.get_active() is not True):
            return None


        try:
            return self.prop.check(self.spinbutton.get_value())
        except:
            raise ValueError("Invalid value %s in spinbutton." % self.spinbutton.get_value())

        
connectors['SpinButton'] = SpinButton




class List(Connector):

    def init(self):
        # The value_display widget only holds a string
        # representation of the list, so an additional
        # variable is needed to hold the current value.
        self.current_value = []
        
    def create_widget(self, use_checkbutton=False):

        vd = self.value_display = gtk.Entry()
        eb = self.edit_button = gtk.Button(stock=gtk.STOCK_EDIT)
        widget = self.widget = gtk.HBox()

        vd.set_property('editable', False)
        eb.connect("clicked", self.on_edit_button_clicked)        
        widget.pack_start(vd,False,True)
        widget.pack_start(eb,False,True)

    def check_in(self):
        self.current_value = self.get_value()
        self.update_display()
        self.last_value = self.current_value

    def get_data(self):
        return self.current_value
    
    def update_display(self):
        self.value_display.set_text(unicode(self.current_value))

    def on_edit_button_clicked(self, sender):
        dialog = ListWizardDialog()        
        try:
            dialog.run()
        finally:
            dialog.destroy()


class ListWizardDialog(gtk.Dialog):
    # similar to ModifyTable Dialog.

    def __init__(self):
        gtk.Dialog.__init__(self, "Edit List", None,
                            gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.set_size_request(320,400)
    
        tv = gtk.TreeView()
        self.vbox.add(tv)


connectors['List'] = List

