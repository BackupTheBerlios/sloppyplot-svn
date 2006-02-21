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


import gtk
import inspect


from Sloppy.Lib.Props import *
from Sloppy.Lib.Undo import UndoList
from Sloppy.Base.properties import *
from Sloppy.Base import uwrap

import logging
logger = logging.getLogger('gtk.widget_factory')
#------------------------------------------------------------------------------

# - Make CTreeFactory, CWidgetFactory similar in functionality, so that 
#   you can have the same comfort in adding widgets as in adding renderers.

# - Implement some kind of sub-connector: a connector that itself is a vbox
#   with other connectors (this is why I need a proper CWidgetFactory)
#   -> CLimits aka CInlineInstance
#   there might be a way to tell the widget_factory that the instance is supposed
#   to be displayed inline (=> a Keylist or view?)

# - gui for cycle list... (=> widget_factory)

# - RendererUnicodeReadOnly for non-implemented properties

# - Why can't I have get_keys() of HasProperties as classmethod?
#   It is risky to initiate a new instance just to get the names
#   of the keys.  I know that the problem is that the keys are collected
#   from the base classes, but maybe we could have a static alternative
#   that takes more time but collects this information on the fly?

#   Or maybe we can initiate the keys not in __init__ but in __new__ ?
#   Or is __new__ for the instance instantiation. I need some method
#   for the class instantiation!


# (F2) Implement Group Properties

# - Group Properties: if each get_xxx method needs exactly one property
#   to be defined, then we could arrange the widgets likewise: one button
#   per mode: fixed, cycle_list, range

#------------------------------------------------------------------------------

class CTreeViewFactory:

    def __init__(self, listowner, listkey):
        self.listowner = listowner 
        self.listkey = listkey

        prop = listowner.get_prop(listkey)
        validators = [v for v in prop.validator.vlist if isinstance(v, VList)]
        if len(validators) == 0:
            raise TypeError("%s.%s must be a List.",
                            (listowner.__class__.__name__, listkey))        
        else:
            vlist = validators[0]
        item_validators = [v for v in vlist.item_validator.vlist if isinstance(v, VInstance)]
        if len(item_validators) == 0:
            raise TypeError("%s.%s must be limited to a certain class instance (VInstance)." %
                            (listowner.__class__.__name__, listkey))
        else:
            self.container = item_validators[0].instance()

        self.keys = []
        self.columns = {}
        
        self.model = None
        self.treeview = None


    def add_columns(self, *keys, **kwargs):
        for key in keys:            
            if isinstance(key, basestring):
                self.keys = key
            elif isinstance(key, (list,tuple)):
                self.keys.extend(key)
            elif isinstance(key, dict):
                self.columns.update(key)
            else:
                raise TypeError("String, tuple or dict required.")

        if len(kwargs) > 0:
            self.add_columns(kwargs)


    def show_columns(self, *keys):           
        if len(keys) == 0:
            keys = self.keys

        for key in keys:
            if key == '_all':
                self.show_columns(*self.keys)
            elif isinstance(key, (list,tuple)):
                self.show_columns(*key)
            else:                
                self.columns[key].set_property('visible', True)

    def hide_columns(self, *keys):
        if len(keys) == 0:
            keys = self.keys
        
        for key in keys:
            if key == '_all':
                self.show_columns(*self.keys)
            elif isinstance(key, (list,tuple)):
                self.show_columns(*key)
            else:
                self.columns[key].set_property('visible', False)
        
    def new_row(self, item):
        row = []
        for key in self.keys:
            row.append( item.get_value(key) )
        row.append(item)
        return row

 
    def create_treeview(self):
        model = gtk.ListStore(*([object]*(len(self.keys) + 1)))    
        treeview = gtk.TreeView(model)        

        index = 0
        for key in self.keys:
            if self.columns.has_key(key):
                obj = self.columns[key]
                if inspect.isfunction(obj) or inspect.ismethod(obj):
                    column = obj(model, index)                    
                else:
                    column = obj
            else:
                cname = get_cname(self.container, key)
                renderer = renderers[cname](self.container, key)
                column = renderer.create(model, index)

            self.columns[key] = column                
            treeview.append_column(column)

            index += 1
            
        self.treeview = treeview
        return self.treeview

    
    def check_in(self):
        itemlist = self.listowner.get_value(self.listkey)
        model = self.treeview.get_model()
        model.clear()
        for item in itemlist:
            row = []
            for key in self.keys:
                row.append( item.get_value(key) )
            model.append( row + [item] )

        self.old_list = itemlist
        

    def check_out(self, undolist=[]):

        ul = UndoList()
        
        def check_out_row(owner, iter, undolist=[]):
            n = 0
            adict = {}
            for key in self.keys:
                adict[key]=model.get_value(iter, n)
                n += 1
            adict['undolist'] = ul
            uwrap.smart_set(owner, **adict)

        new_list = []
        model = self.treeview.get_model()
        iter = model.get_iter_first()
        while iter is not None:
            owner = model.get_value(iter, len(self.keys))
            check_out_row(owner, iter, undolist=ul)
            new_list.append(owner)
            iter = model.iter_next(iter)

        if self.old_list != new_list:        
            uwrap.set(self.listowner, self.listkey, new_list, undolist=ul)
            self.old_list = new_list

        undolist.append(ul)

###############################################################################


class Renderer(object):

   
    def __init__(self, container, key):
        self.prop = container.get_prop(key)
        self.key = key

        self.cell = None # TODO

    def create(self):
        raise RuntimeError("create() needs to be implemented.")

    def get_column_key(self):
        key = self.prop.blurb or self.key
        return key.replace('_', ' ')        


class RendererUnicode(Renderer):

    """ Suitable for VUnicode. """

    def create(self, model, index):
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited, model, index)

        column = gtk.TreeViewColumn(self.get_column_key())
        column.pack_start(cell)
        column.set_cell_data_func(cell, self.cell_data_func, index)

        self.column = column
        return column


    def on_edited(self, cell, path, new_text, model, index):    
        try:
            value = self.prop.check(new_text)
            
            # If the property accepts None as valid value,
            # then we interpret an empty value as None.
            if len(new_text) == 0:
                try: self.prop.check(None)
                except PropertyError: pass
                else: value = None
                    
        except PropertyError:
            pass
        else:
            model[path][index] = value

    def cell_data_func(self, column, cell, model, iter, index):
        value = model.get_value(iter, index)
        if value is None:
            value = ""
        cell.set_property('text', unicode(value))


#------------------------------------------------------------------------------

class RendererChoice(Renderer):

    """ Suitable for VChoice. """

    def create(self, model, index):

        cell_model = self.new_cell_model()
        
        cell = gtk.CellRendererCombo()                        
        cell.set_property('text-column', 0)
        cell.set_property('model', cell_model)

        # make editable
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited, model, index)
        
        column = gtk.TreeViewColumn(self.get_column_key())
        column.pack_start(cell)
        column.set_cell_data_func(cell, self.cell_data_func, index)

        self.column = column
        return column

    def new_cell_model(self):        
        vchoices = [v for v in self.prop.validator.vlist if isinstance(v, VChoice)]
        if len(vchoices) == 0:
            raise TypeError("Property for renderer 'RendererChoice' has no fitting validator!")
        vchoice = vchoices[0]

        cell_model = gtk.ListStore(str, object)
        for value in vchoice.choices:
            if value is None: cell_model.append(('', None))
            else: cell_model.append((unicode(value), value))

        return cell_model

    def on_edited(self, cell, path, new_text, model, index):
        if len(new_text) == 0:
            new_text = None
        try:
            model[path][index] = self.prop.check(new_text)            
        except PropertyError:
            print "Could not set combo to value '%s', %s" % (new_text, type(new_text))

    def cell_data_func(self, column, cell, model, iter, index):
        user_value = model.get_value(iter, index)
        if user_value is None: user_value = ""
        cell.set_property('text', unicode(user_value))


#------------------------------------------------------------------------------

class RendererBoolean(Renderer):

    """ Suitable for VBoolean. """
   
    def create(self, model, index):
        cell = gtk.CellRendererToggle()

        cell.set_property('activatable', True)
        cell.connect('toggled', self.on_toggled, model, index)

        column = gtk.TreeViewColumn(self.get_column_key())
        column.pack_start(cell)
        column.set_cell_data_func(cell, self.cell_data_func, index)

        self.column = column
        return column


    def cell_data_func(self, column, cell, model, iter, index):
        value = model.get_value(iter, index)
        cell.set_property('active', bool(self.prop.check(value)))


    def on_toggled(self, cell, path, model, index):
        value = not model[path][index]
        try:
            value = self.prop.check(value)
        except PropertyError:
            pass
        else:        
            model[path][index] = value

renderers = {'Unicode': RendererUnicode,
             'Choice': RendererChoice,
             'Boolean': RendererBoolean,
             'Instance': RendererUnicode, # TODO
             'Limits': RendererUnicode
             }


###############################################################################

class CWidgetFactory:

    def __init__(self, container):
        self.container = container
        self.keys = []

    def add_keys(self, *keys):
        for key in keys:
            if isinstance(key, basestring):
                self.keys.append(key)
            elif isinstance(key, (list,tuple)):
                self.keys.extend(key)
            else:
                raise TypeError("String, list or tuple required.")


    def _create_connectors(self):
        clist = []
        for key in self.keys:
            connector = new_connector(self.container, key)
            connector.create_widget()
            clist.append(connector)
        self.clist = clist

        
    def create_vbox(self):
        self._create_connectors()
        
        vbox = gtk.VBox()
        for c in self.clist:
            vbox.add(c.widget)
        return vbox

    def create_table(self):
        self._create_connectors()
        
        tw = gtk.Table(rows=len(self.keys), columns=2)
        tooltips = gtk.Tooltips()

        n = 0
        for c in self.clist:
            # widget
            tw.attach(c.widget, 1,2,n,n+1,
                      xoptions=gtk.EXPAND|gtk.FILL,
                      yoptions=0, xpadding=5, ypadding=1)

            # label (put into an event box to display the tooltip)
            label = gtk.Label(c.get_widget_key())
            label.set_alignment(0,0)
            #label.set_justify(gtk.JUSTIFY_LEFT)
            label.show()

            ebox = gtk.EventBox()
            ebox.add(label)
            ebox.show()
            if c.prop.doc is not None:
                tooltips.set_tip(ebox, c.prop.doc)

            tw.attach(ebox, 0,1,n,n+1,
                      yoptions=0,
                      xpadding=5, ypadding=1)

            n += 1

        return tw


    def set_container(self, container):
        self.container = container
        for connector in self.clist:
            connector.container = container
            
    def check_in(self):
        for connector in self.clist:
            connector.check_in()

    def check_out(self, undolist=[]):
        ul = UndoList()    
        for c in self.clist:
            c.check_out(undolist=ul)
        undolist.append(ul)       




###############################################################################

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
        return self.container.get_value(self.key)
    def set_value(self, value):
        if value != self.last_value:
            self.container.set_value(self.key, value)
            self.last_value = value
    def get_prop(self):
        return self.container.get_prop(self.key)
    prop = property(get_prop)


    def get_widget_key(self):
        key = self.prop.blurb or self.key
        return key.replace('_', ' ')
    
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
        raise RuntimeError("create_widget() needs to be implemented.")




class ConnectorUnicode(Connector):

    """ Suitable for VUnicode. """

    def create_widget(self):                      
        # create entry
        self.entry = gtk.Entry()

        entry = self.entry        
        entry.connect("focus-in-event", self.on_focus_in_event)
        entry.connect("focus-out-event", self.on_focus_out_event)

        # create checkbutton if requested
        try:
            prop = self.container.get_prop(self.key)
            prop.check(None)
        except PropertyError:
            self.allow_none = False
        else:
            self.allow_none = True


        # TODO: disabled for now, until better solution is found.
        if self.allow_none is False or 1:
            self.checkbutton = None
        else:
            self.checkbutton = gtk.CheckButton()
            self.checkbutton.connect("toggled",
              (lambda sender: entry.set_sensitive(sender.get_active())))




        # pack everything together
        self.widget = gtk.HBox()

        widget = self.widget
        widget.pack_start(entry,True,True)
        if self.checkbutton is not None:
            widget.pack_start(self.checkbutton,False,True)                    
        widget.show_all()

        return self.widget


    def on_focus_in_event(self, widget, event):
        self.last_value = widget.get_text()
        
        
    def on_focus_out_event(self, widget, event):
        value = widget.get_text()
        if value == self.last_value:
            return

        try:
            self.prop.check(value)
        except PropertyError:
            widget.set_text(self.last_value)
            
                
        return False
            

    #----------------------------------------------------------------------

    def check_in(self):
        value = self.get_value()
        if value is Undefined:
            value = None
            
        if self.checkbutton is not None:
            state = value is not None
            self.checkbutton.set_active(state)
            self.entry.set_sensitive(state)            

        if value is None:
            value = ""

        self.entry.set_text(unicode(value))            
        self.last_value = value


    def get_data(self):
        value = self.entry.get_text()
        if self.allow_none is False:
            value = ""
            
        if self.checkbutton is not None:
            state = self.checkbutton.get_active()
            if state is False:
                return None       

        try:
            return self.prop.check(value)
        except:
            return self.last_value



###############################################################################

class ConnectorRange(Connector):

    """ Suitable for VRange. """
    
    def create_widget(self):
        # create spinbutton
        self.spinbutton = gtk.SpinButton()

        #
        # create checkbutton, if None is a valid value.
        #
        try:
            prop = self.container.get_prop(self.key)
            prop.check(None)
        except PropertyError:
            self.checkbutton = None
        else:
            self.checkbutton = gtk.CheckButton()
            self.checkbutton.connect("toggled",\
              (lambda sender: self.spinbutton.set_sensitive(sender.get_active())))
            
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

        return self.widget
    
        
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


###############################################################################

class ConnectorRGBColor(Connector):

    def create_widget(self):       
        self.colorbutton = gtk.ColorButton()
        self.widget = self.colorbutton

        widget = self.widget
        
        return self.widget

    def create_renderer(self, model, index):
        cell = gtk.CellRenderer
        return self.widget

    
    def to_gdk_color(self, color):
        return gtk.gdk.Color(int(color[0]*65535), int(color[1]*65535), int(color[2]*65535))

    def to_rgb(self, color):
        return (color.red/65535.0, color.green/65535.0, color.blue/65535.0)

    def get_data(self):
        gdk_color = self.colorbutton.get_color()
        print "Comparing ", gdk_color, self.last_value
        if (gdk_color.red == self.last_value.red) and \
               (gdk_color.blue == self.last_value.blue) and \
               (gdk_color.green == self.last_value.green):
            return self.container.get_mvalue(self.key)
        
        return self.to_rgb(gdk_color)

    def check_in(self):
        rgb_color = self.container.get_mvalue(self.key) or (0.0,0.0,0.0)
        gdk_color = self.to_gdk_color(rgb_color)
        self.colorbutton.set_color(gdk_color)
        self.last_value = gdk_color



###############################################################################

class ConnectorChoice(Connector):

    """ Suitable for VChoice. """
    
    def init(self):
        self.vchoice = None
        self.last_index = -1
        
    def create_widget(self):
        # create combobox
        self.combobox = gtk.ComboBox()

        # create combobox model
        combobox = self.combobox
        model = gtk.ListStore(str, object)
        combobox.set_model(model)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)

        # fill model
        prop = self.container.get_prop(self.key)
        vchoices = [v for v in prop.validator.vlist if isinstance(v, VChoice)]
        if len(vchoices) == 0:
            raise TypeError("Property for connector 'Choice' has no choice validator!")
        self.vchoice = vchoice = vchoices[0]
        
        model.clear()
        for value in vchoice.choices:
            model.append((unicode(value), value))

        # pack everything together
        self.widget = gtk.HBox()

        widget = self.widget
        widget.pack_start(combobox,True,True)
        widget.show_all()

        return self.widget
        
    #----------------------------------------------------------------------

    def check_in(self):
        value = self.get_value()
        if value != Undefined:
            try:
                index = self.vchoice.choices.index(value)
            except:
                raise ValueError("Connector for %s.%s failed to retrieve prop value '%s' in list of available values '%s'" % (self.container.__class__.__name__, self.key, real_value, values))

            model = self.combobox.get_model()
            iter = model.get_iter((index,))
            self.combobox.set_active_iter(iter)
            self.last_index = index
            
        self.last_value = value


    
    def get_data(self):
        index = self.combobox.get_active()
        if index == self.last_index:
            return self.get_value()
        elif index < 0:
            return Undefined            
        else:
            model = self.combobox.get_model()
            prop = self.container.get_prop(self.key)
            return model[index][1]




###############################################################################

class ConnectorBoolean(Connector):

    def init(self):
        self.values = []
        self.last_index = -1
        
    def create_widget(self):

        # create combobox
        self.combobox = gtk.ComboBox()

        # create model
        combobox = self.combobox        
        model = gtk.ListStore(str, object)
        combobox.set_model(model)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)

        # fill combo
        try:
            self.prop.check(None)
        except:
            value_dict = {}
        else:
            value_dict = {'None': None}

        value_dict.update({'True': True, 'False': False})
        self.values = value_dict.values()
        
        model.clear()        
        for key, value in value_dict.iteritems():
            model.append((key, value))
        
        #
        # pack everything together
        #
        self.widget = gtk.HBox()

        widget = self.widget
        widget.pack_start(combobox,True,True)
        widget.show_all()

        return self.widget


    def check_in(self):
        value = self.get_value()

        if value is not Undefined:            
            index = self.values.index(value)

            model = self.combobox.get_model()
            iter = model.get_iter((index,))
            self.combobox.set_active_iter(iter)
        else:
            index = -1
            
        self.last_value = value
        self.last_index = index

    def get_data(self):
        index = self.combobox.get_active()
        if index == self.last_index:
            return self.get_value()
        elif index < 0:
            return Undefined            
        else:
            model = self.combobox.get_model()
            prop = self.container.get_prop(self.key)
            return model[index][1]


###############################################################################

class ConnectorInstance(Connector):

    def init(self):
        self.data = None
    
    def create_widget(self):
        # find VInstance
        prop = self.container.get_prop(self.key)
        vinstances = [v for v in prop.validator.vlist if isinstance(v, VInstance)]
        if len(vinstances) == 0:
            raise TypeError("Property for connector 'Instance' has no instance validator!")
        self.vinstance = vinstance = vinstances[0]

        # create button widget
        button = gtk.Button()

                            
        self.widget = button
        return self.widget

    def check_in(self):        
        value = self.get_value()

        self.widget.set_label('%s' % (self.vinstance.instance.__name__))

        self.data = value
        self.last_value = value
        
    def get_data(self):
        return self.data



###############################################################################

class ConnectorLimits(Connector):

    def init(self):
        self.data = None
    
    def create_widget(self):
        # find VInstance
        prop = self.container.get_prop(self.key)
        vinstances = [v for v in prop.validator.vlist if isinstance(v, VInstance)]
        if len(vinstances) == 0:
            raise TypeError("Property for connector 'Instance' has no instance validator!")
        self.vinstance = vinstance = vinstances[0]

        # create vbox with connectors
        vbox = gtk.VBox()

        pseudo_instance = vinstance.instance()
        keys = pseudo_instance.get_keys()
        self.factory = CWidgetFactory(pseudo_instance)
        self.factory.add_keys(keys)
        self.widget = self.factory.create_table()
      
        return self.widget

    def check_in(self):
        value = self.get_value()

        self.factory.set_container(value)
        self.factory.check_in()        

        self.data = value
        self.last_value = value
        
    def get_data(self):
        return self.data

        
connectors ={'Choice': ConnectorChoice,
             'RGBColor': ConnectorRGBColor,
             'Range': ConnectorRange,
             'Unicode': ConnectorUnicode,
             'Boolean': ConnectorBoolean,
             'Instance': ConnectorInstance,
             'Limits': ConnectorLimits}



###############################################################################

def get_cname(owner, key):
    prop = owner.get_prop(key)
    vlist = prop.validator.vlist[:] # create copy of list, because we pop it!
    while len(vlist) > 0:
        v = vlist[0]
        if isinstance(v, VRange):
            return'Range'
        elif isinstance(v, VInstance):
            # TEMPORARY
            if v.instance.__name__ == 'Limits':
                return 'Limits'
            return 'Instance'        
        #elif isinstance(v, VRGBColor):
        #    return 'RGBColor'
        elif isinstance(v, VChoice):
            return 'Choice'
        elif isinstance(v, VBoolean):
            return 'Boolean'
        elif isinstance(v, (VUnicode,VInteger,VFloat,VString,VRegexp)):
            return 'Unicode'
        
        vlist.pop(0)

    logger.warning("No connector found for property %s.%s. Using default (Unicode)." % (owner.__class__.__name__, key))
    return 'Unicode'


def new_connector(owner, key):  
    cname = get_cname(owner, key)
    if connectors.has_key(cname) is False:
        cname = 'Unicode'
    connector = connectors[cname](owner, key)
    return connector


def new_connectors(owner, include=None, exclude=None):
    keys = owner.get_keys(include=include,exclude=exclude)
    clist = []
    for key in keys:
        clist.append(new_connector(owner, key))
    return clist
