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
DEPRECATED.  Will be replaced by pwconnect.
"""

import logging
logging.basicConfig()

#import pygtk
#pygtk.require('2.0')
import gtk

from Sloppy.Lib.Props import BoolProp, Container
from Sloppy.Lib.Undo import UndoList

from Sloppy.Base import uwrap


_all__ = ["PWContainer", "PWTableBox",
          "PW", "PWString", "PWComboBox", "PWComboBox",
          "PWToggleButton", "PWAlternateToggleButton",
          "construct_pw", "construct_pw_in_box", "construct_pw_table"]


class PWContainer:

    def __init__(self):
        self.pwdict = dict()
        self.construct_pwdict()
        
    def check_in(self):
        for key, pw in self.pwdict.iteritems():
            pw.check_in()


    def check_out(self, undolist=[]):
        ul = UndoList()
        for key, pw in self.pwdict.iteritems():
            pw.check_out(undolist=ul)
        undolist.append(ul)


    def construct_pwdict(self):
        pass



class PWTableBox(gtk.ScrolledWindow, PWContainer):
    
    def __init__(self, container, props):
        self.props = props
        self.container = container
        gtk.ScrolledWindow.__init__(self)
        PWContainer.__init__(self)

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
    def construct_pwdict(self):
        pwlist = list()
        for key in self.props:
            pw = construct_pw(self.container, key)
            self.pwdict[key] = pw
            pwlist.append(pw)

        tooltips = gtk.Tooltips()
        tablewidget = construct_pw_table(pwlist, tooltips=tooltips)
        tablewidget.show()    

        self.add_with_viewport(tablewidget)

    

class PW(object):

    """
    A wrapper class that connects a property (P) with a graphical
    widget(W).  Required initialization parameters are the property
    container and the key, i.e. the name of the property.  
    """
        
    def __init__(self, container, key, **kwargs):
        self.container = container
        self.key = key
        self.widget = self.label = None
        self.init(**kwargs)

    def init(self):
        pass

    #--- ACCESSORS --------------------------------------------------------

    def get_value(self):
        return getattr( self.container, self.key)
    def get_prop(self):
        return self.container.get_prop(self.key)
    prop = property(get_prop)


    #--- CHECK IN/OUT -----------------------------------------------------
    
    def check_in(self):
        " Retrieve value from container "
        raise RuntimeError("check_in() needs to be implemented.")

    def check_out(self, undolist=[]):
        " Set value in container "
        raise RuntimeError("check_out() needs to be implemented.")

    def get_label(self):
        return self.label
    
    def get_widget(self):
        return self.widget

    #--- GUI CONSTRUCTION -------------------------------------------------
    
    def construct_hbox(self, tooltips=None):
        box = gtk.HBox()
        if self.get_label() is not None:
            if tooltips is not None and self.prop.doc is not None:
                eb = gtk.EventBox()
                eb.add(self.get_label())
                eb.show()
                tooltips.set_tip(eb, self.prop.doc)
                box.pack_start(eb)
            else:
                box.pack_start(self.get_label())
        box.pack_end(self.get_widget())
        box.show()
        return box

    def construct_vbox(self, tooltips=None):
        box = gtk.VBox()
        if self.get_label() is not None:
            if tooltips is not None and self.prop.doc is not None:
                eb = gtk.EventBox()
                eb.add(self.get_label())
                eb.show()
                tooltips.set_tip(eb, self.prop.doc)
                box.pack_start(eb)
            else:
                box.pack_start(self.get_label())
        box.pack_end(self.get_widget())
        box.show()
        return box
    
    

    
class PWString(PW):

    def init(self):

        blurb = self.prop.blurb or self.prop.doc or self.key

        self.label = gtk.Label(blurb)
        self.label.show()

        self.widget = gtk.Entry()
        self.widget.show()

        self.widget.connect("focus-in-event", self.cb_focus_in_event)
        self.widget.connect("focus-out-event", self.cb_focus_out_event)
        
        self.last_value = None


    def check_in(self):
        self.old_value = self.get_value()
        
        if self.old_value is not None:
            value = unicode(self.old_value)
        else:
            value = ""        
        self.widget.set_text(value)

    def check_out(self, undolist=[]):           
        val = self.widget.get_text()
        if len(val) == 0:
            val = None
        else:
            val = self.prop.check_value(val)

        if val != self.old_value:
            uwrap.set(self.container, self.key, val, undolist=undolist)
            #self.container.set(self.key, val, undolist=undolist)
            self.old_value = val
    
    def cb_focus_in_event(self, sender, event):
        self.last_value = self.widget.get_text()

    def cb_focus_out_event(self, sender, event):
        val = self.widget.get_text()
        if len(val) == 0: val = None
        try:
            self.prop.check_value(val)
        except (TypeError, ValueError):
            print "Value is wrong, resetting"
            self.widget.set_text(self.last_value)
        

        

class PWComboBox(PW):

    def init(self):

        blurb = self.prop.blurb or self.prop.doc or self.key
        self.label = gtk.Label(blurb)
        self.label.show()

        liststore = gtk.ListStore(str, object)
        combobox = gtk.ComboBox(liststore)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)
  
        self.widget = combobox        
        self.widget.show()
                   
        self.fill_combo()


    def check_in(self):
        try:
            index = self.prop.value_list.index(self.get_value())
        except:
            print "Failed to retrieve value ", self.get_value(), self.prop.doc
            raise
        self.widget.set_active(index)

        self.old_value = index

    def check_out(self, undolist=[]):
        index = self.widget.get_active()
        print "combobox: ", self.key,
        if index != self.old_value:
            if index < 0:
                val = None
            else:
                model = self.widget.get_model()
                val = model[index][1]
            uwrap.smart_set(self.container, self.key, val, undolist=undolist)
            self.old_value = index

    def fill_combo(self):
        model = self.widget.get_model()
        model.clear()
        for value in self.prop.value_list:
            model.append( (value or "<None>", value) )
        


class PWToggleButton(PW):

    def init(self):

        blurb = self.prop.blurb or self.prop.doc or self.key
        self.label = gtk.Label(blurb)
        self.label.show()

        self.widget = gtk.ToggleButton(label=blurb)
        self.widget.connect("toggled", self.cb_toggled)
        #self.widget.set_mode(False)
        self.widget.show()
        
        
    def check_in(self):
        self.old_value = self.get_value()
        if self.old_value is None:
            self.widget.set_inconsistent(True)
        else:
            self.widget.set_active(self.old_value)
        self.correct_label()

    def check_out(self, undolist=[]):
        if self.widget.get_inconsistent() is True:
            val = None
        else:
            val = self.widget.get_active()
        if val != self.old_value:
            uwrap.set( self.container, self.key, val, undolist=undolist)
            self.old_value = val


    def cb_toggled(self, button):
        if self.widget.get_inconsistent() is True:
            self.widget.set_inconsistent(False)
        self.correct_label()

    def correct_label(self):
        if self.widget.get_inconsistent() is True:
            self.widget.set_label("---")
        elif self.widget.get_active() is True:
            self.widget.set_label("True")
        else:
            self.widget.set_label("False")

class PWAlternateToggleButton(PW):

    def init(self):

        blurb = self.prop.blurb or self.prop.doc or self.key
        self.label = gtk.Label(blurb)
        self.label.show()

        model = gtk.ListStore(str, object)
        combobox = gtk.ComboBox(model)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)

        for entry in [("Default",None), ("True",True), ("False",False)]:
            model.append( (entry) )

        self.widget = combobox        
        self.widget.show()

    def check_in(self):
        index_map = {None: 0, True: 1, False: 2}
        index = index_map[self.get_value()]
        
        self.widget.set_active(index)
        self.old_value = index

    def check_out(self, undolist=[]):
        index = self.widget.get_active()
        if index != self.old_value:
            model = self.widget.get_model()
            value = model[index][1]
            uwrap.smart_set(self.container, self.key, value, undolist=undolist)
            self.old_value = index

class PWCheckButton(PW):

    def init(self):

        blurb = self.prop.blurb or self.prop.doc or self.key

        self.widget = gtk.CheckButton(label=blurb)
        self.widget.connect("toggled", self.cb_toggled)
        #self.widget.set_mode(False)
        self.widget.show()

        #self.label = gtk.Label(blurb)
        #self.label.show()
        
        
    def check_in(self):
        self.old_value = self.get_value()
        if self.old_value is None:
            self.widget.set_inconsistent(True)
            print "Setting inconsistent to True"
        else:
            #self.widget.set_inconsistent(False)
            self.widget.set_active(self.old_value)

    def check_out(self, undolist=[]):
        print "=>", self.widget.get_inconsistent()
        if self.widget.get_inconsistent() is True:
            val = None
        else:
            val = self.widget.get_active()
        if val != self.old_value:
            uwrap.set( self.container, self.key, val, undolist=undolist)
            self.old_value = val


    def cb_toggled(self, button):
        if self.widget.get_inconsistent() is True:
            self.widget.set_inconsistent(False)
            


#------------------------------------------------------------------------------
# CONVENIENCE METHODS

def construct_pw(container, key):
    prop = container.get_prop(key)
    
    if prop.value_list is not None:
        pw = PWComboBox(container, key)
    elif isinstance(prop, BoolProp):
        pw = PWAlternateToggleButton(container, key)
    else:
        pw = PWString(container, key)

    pw.check_in()
    return pw



def construct_pw_in_box(container, key, tooltips=None):
    pw = construct_pw(container, key)
    hbox = pw.construct_hbox(tooltips=tooltips)
    hbox.show()

    return (pw, hbox)
    
def construct_pw_table(pwlist, tooltips=None):
    tw = gtk.Table(rows=len(pwlist), columns=2)
    n = 0            
    for pw in pwlist:
        # widget
        tw.attach(pw.widget, 1,2,n,n+1, xoptions=gtk.EXPAND|gtk.FILL, yoptions=0, xpadding=5, ypadding=1)

        # associated label
        if tooltips is None:
            label = pw.label
        else:
            label = gtk.EventBox()
            tooltips.set_tip(label, pw.prop.doc or pw.prop.blurb or "(no documentation avaiable)")
            label.add(pw.label)
            label.show()

        tw.attach(label, 0,1,n,n+1, xoptions=0, yoptions=0, xpadding=5, ypadding=1)
        #label.set_alignment(-1.0, 0.0)        
            
        n += 1                                    
    return tw



#------------------------------------------------------------------------------
# TESTING

import uihelper

def test():

    class TestContainer(Container):
        test = BoolProp()

    tc = TestContainer(test=True)

    pw = PWAlternateToggleButton(tc, 'test')
    pw.check_in()
    
    win = uihelper.setup_test_window(pw.widget)
    gtk.main()

    
if __name__ == "__main__":
    test()
