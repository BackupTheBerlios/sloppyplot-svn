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

from Sloppy.Lib.Undo import UndoList, UndoInfo, NullUndo, ulist
from Sloppy.Base import objects, globals, pdict, uwrap
from Sloppy.Gtk import config, uihelper, widget_factory



class LayerWindow(gtk.Window):

    """
    The LayerWindow allows to edit the properties of a plot layer.
    Different aspects of the layer are grouped as tabs in a notebook
    widget.  Changes are not applied immediately but only when you
    confirm your changes.
    
    """
    
    def __init__(self, plot, layer, current_page=None):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_default_size(550, 500)
        self.set_title("[Edit Plot Layer]")
        
        self.plot = plot
        self.layer = layer       

        #
        # frame above notebook that holds the current tab name
        #        
        self.tab_label= gtk.Label()

        label = self.tab_label
        label.set_use_markup(True)
        topframe = gtk.Frame()
        topframe.add(label)

        def on_switch_page(notebook, page, page_num, tab_label):
            tab = notebook.get_nth_page(page_num)
            text = "\n<big><b>%s</b></big>\n" % tab.title
            tab_label.set_markup(text)
        
        #
        # populate notebook with tabs
        #
        self.tabdict = {} # list of tabs with a check_in/check_out method
        self.notebook = gtk.Notebook()

        nb = self.notebook        
        nb.set_property('tab-pos', gtk.POS_LEFT)
        nb.connect("switch-page", on_switch_page, self.tab_label)
        
        for tab in [LayerTab(layer),
                    AxesTab(layer.axes),
                    LegendTab(layer.legend),                    
                    LineTab(layer)]:
            nb.append_page(tab)
            nb.set_tab_label_text(tab, tab.title)
            self.tabdict[tab.title] = tab


        # if requested, set the page with the name `tab` as current page
        if current_page is not None:
            try:
                index = self.tablabels.index(current_page)                
            except ValueError:
                raise KeyError("There is no Tab with the label %s" % current_page)
            nb.set_current_page(index)        

        
        #
        # button box
        #
        buttons=[(gtk.STOCK_REVERT_TO_SAVED, self.on_btn_revert),
                 (gtk.STOCK_CANCEL, self.on_btn_cancel),
                 (gtk.STOCK_APPLY, self.on_btn_apply),
                 (gtk.STOCK_OK, self.on_btn_ok)]
        
        btnbox = uihelper.construct_hbuttonbox(buttons)

        #
        # put everything together
        #
        separator = gtk.HSeparator()
             
        vbox = gtk.VBox()
        vbox.pack_start(topframe, False, True)
        vbox.pack_start(nb, True, True)
        vbox.pack_start(separator, False, False, padding=4)
        vbox.pack_end(btnbox, False, False)
        self.add(vbox)
        self.show_all()

        # After we have shown everything, we check in.
        for tab in self.tabdict.itervalues():
            tab.check_in()

        self.notebook = nb
        

    def apply_changes(self):
        """ Apply all changes in all tabs.

        The method calls 'check_in' of every tab in the dialog's
        notebook. The created undolists are unified into a single
        undolist, which is appended to the project's journal.
        """
        
        ul = UndoList().describe("Edit Plot Properties")

        for tab in self.tabdict.itervalues():
            ui = UndoList()            
            tab.check_out(undolist=ui)
            ul.append(ui.simplify())

        ul = ul.simplify(preserve_list=True)

        if len(ul) > 0:
            uwrap.emit_last(self.plot, "changed", undolist=ul)            
        else:
            ul = NullUndo()
            
        globals.app.project.journal.add_undo(ul)
        
        
    #----------------------------------------------------------------------
    # Callbacks
    #

    def on_btn_cancel(self, sender):
        self.destroy()

    def on_btn_revert(self, sender):
        for tab in self.tabdict.itervalues():
            tab.check_in()

    def on_btn_apply(self, sender):
        sender.grab_focus()
        self.apply_changes()
            
    def on_btn_ok(self, sender):
        sender.grab_focus()
        self.apply_changes()
        self.destroy()            

        


class GroupBox(gtk.HBox):

    """    
    A group of widgets for so called 'Group' properties.
    See Base.objects.Group for details.
    """

    # we have basically a widget_type and
    # then we have some extra widgets which determine
    # the extra information for that specific type:
    
    # type == GROUP_TYPE_FIXED:
    #   widget_value

    # type == GROUP_TYPE_RANGE:
    #   widget.range_start
    #   widget.range_stop
    #   widget.range_step

    # type  == GROUP_TYPE_CYCLE:
    #   widget_cycle_list

    # As one can see, the last two types are rather complicated...
    #  - I will start with the first one, widget_value ! -- OK
    #  - Next one is range_xxx.
    
    def __init__(self, layer, propname):

        gtk.HBox.__init__(self)

        
#         self.layer = layer
#         self.propname = propname        
#         self.prop = layer.get_prop(propname)
#         self.group = layer.get_value(propname)
        
#         # create widgets and put them into a horizontal box
#         self.widget_allow_override = pwconnect.CheckButton(self.group,'allow_override')
#         self.widget_type = pwconnect.ComboBox(self.group, 'type')
#         self.widget_value = pwconnect.new_connector(self.group, 'value')
#         self.widget_range_start = pwconnect.SpinButton(self.group, 'range_start')
#         self.widget_range_stop = pwconnect.SpinButton(self.group, 'range_stop')
#         self.widget_range_step = pwconnect.SpinButton(self.group, 'range_step')        
#         self.widget_cycle_list = pwconnect.List(self.group, 'cycle_list')
        
#         self.clist = [
#             self.widget_allow_override,            
#             self.widget_type,
#             self.widget_value,
#             self.widget_range_start,
#             self.widget_range_stop,
#             self.widget_range_step,
#             self.widget_cycle_list
#             ]
        
#         # TODO: cycle_list        

#         for connector in self.clist:
#             connector.create_widget()
#             self.pack_start(connector.widget,False,True)
            
#         self.show_all()

#         # add special signals        
#         self.widget_type.combobox.connect('changed', self.on_type_changed)   
    
        
#     def check_in(self):        
#         for container in self.clist:
#             container.check_in()
#         self.refresh_widget_visibility(self.group.type)
        
#     def check_out(self, undolist=[]):
#         for container in self.clist:
#             container.check_out(undolist=undolist)


#     def on_type_changed(self, sender):
#         new_type = uihelper.get_active_combobox_item(sender, 1)
#         self.refresh_widget_visibility(new_type)

#     def refresh_widget_visibility(self, new_type):
#         self.widget_value.widget.set_property('visible',
#                                               new_type==objects.GROUP_TYPE_FIXED)

#         self.widget_range_start.widget.set_property('visible', new_type==objects.GROUP_TYPE_RANGE)
#         self.widget_range_stop.widget.set_property('visible', new_type==objects.GROUP_TYPE_RANGE)
#         self.widget_range_step.widget.set_property('visible', new_type==objects.GROUP_TYPE_RANGE) 
        
#         self.widget_cycle_list.widget.set_property('visible', new_type==objects.GROUP_TYPE_CYCLE)        


###############################################################################
#
# REPLACEMENTS FOR THE ABOVE CLASSES
#


class AbstractTab(gtk.VBox):

    def __init__(self):
        gtk.VBox.__init__(self)
        self.factory = None
        
    def check_in(self):
        self.factory.check_in()

    def check_out(self, undolist=[]):
        ul = UndoList().describe("Multiple actions")
        self.factory.check_out(undolist=undolist)
        undolist.append(ul)


class LayerTab(AbstractTab):

    title = "Layer"

    def __init__(self, layer):
        AbstractTab.__init__(self)        

        keys = ['title', 'visible', 'grid']

        self.factory = widget_factory.CWidgetFactory(layer)
        self.factory.add_keys(keys)
        table = self.factory.create_table()
        frame = uihelper.new_section("Layer", table)
        self.add(frame)

        self.layer = layer
        self.show_all()        



class LegendTab(AbstractTab):

    title = "Legend"

    def __init__(self, legend):
        AbstractTab.__init__(self)

        keys = ['label', 'position', 'visible', 'border', 'x', 'y']
        self.factory = widget_factory.CWidgetFactory(legend)
        self.factory.add_keys(keys)
        table = self.factory.create_table()
        frame = uihelper.new_section("Legend", table)
        self.add(frame)

        self.show_all()



class AxesTab(AbstractTab):

    title = "Axes"
    
    def __init__(self, axesdict):
        AbstractTab.__init__(self)

        keys = ['label', 'start', 'end', 'scale', 'format']

        self.factorylist = []
        
        for key, axis in axesdict.iteritems():
            factory = widget_factory.CWidgetFactory(axis)        
            factory.add_keys(keys)          
            table = factory.create_table()            
            frame = uihelper.new_section(key, table)
            self.pack_start(frame, False, True)
            self.factorylist.append(factory)

        self.show_all()

    def check_in(self):
        for factory in self.factorylist:
            factory.check_in()

    def check_out(self, undolist=[]):
        for factory in self.factorylist:
            factory.check_out(undolist=undolist)



class LineTab(AbstractTab):

    title = "Lines"

    def __init__(self, layer):
        AbstractTab.__init__(self)
        self.layer = layer

        #
        # Construct TreeView and ButtonBox
        #

        keys = ['visible', 'label', 'style', 'width', 'color', 'marker', 'marker_color', 'marker_size', 'source', 'cx', 'cy', 'row_first', 'row_last']
        self.factory = widget_factory.CTreeViewFactory(layer, 'lines')
        self.factory.add_columns(keys, source=self.create_source_column)
        self.treeview = self.factory.create_treeview()
        sw = uihelper.add_scrollbars(self.treeview)

        #
        # keybox = label + key_combo 
        #
        model = gtk.ListStore(str, object)
        key_combo = gtk.ComboBox(model)
        cell = gtk.CellRendererText()
        key_combo.pack_start(cell, True)
        key_combo.add_attribute(cell, 'text', 0)
        key_combo.connect('changed', lambda cb: self.limit_columns())
        self.key_combo = key_combo # for use in limit_columns()
        
        viewdict = {'all' : ['_all'],
                    'style' : ['visible', 'label', 'style', 'width', 'color', 'marker', 'marker_color', 'marker_size'],
                    'data' : ['visible', 'label', 'source', 'cx', 'cy', 'row_first', 'row_last']}
        for key, alist in viewdict.iteritems():
            model.append((key, alist))

        keybox = gtk.HBox(False, 5)
        keybox.pack_start(gtk.Label("Display:"), False, False)
        keybox.pack_start(key_combo, False, False)
        keybox.pack_start(gtk.Label(), True, True)

        self.key_combo.set_active(0)        
        self.limit_columns()

        
        buttons = [(gtk.STOCK_ADD, self.on_insert_new),
                   (gtk.STOCK_REMOVE, self.on_remove_selection),
                   (gtk.STOCK_GO_UP, self.on_move_selection, -1),
                   (gtk.STOCK_GO_DOWN, self.on_move_selection, +1)]        
        buttonbox = uihelper.construct_vbuttonbox(buttons, labels=False)

        hbox = gtk.HBox(False, 5)
        hbox.pack_start(sw, True, True)
        hbox.pack_start(buttonbox, False, True)

        vbox = gtk.VBox(False, 5)
        vbox.pack_start(keybox, False, False)
        vbox.pack_start(hbox)
        
        frame1 = uihelper.new_section('Lines', vbox)
        
        #
        # Construct Group Boxes
        #
        #self.gblist = [GroupBox(self.layer, 'group_linestyle'),
        #               GroupBox(self.layer, 'group_linemarker'),
        #               GroupBox(self.layer, 'group_linewidth'),
        #               GroupBox(self.layer, 'group_linecolor')]
        self.gblist = []

        # DISABLE GROUP BOXES RIGHT NOW!
        self.gblist = []

#         # Wrap group boxes into a table       
#         table = gtk.Table(rows=len(self.gblist), columns=3)

#         n = 0
#         for widget in self.gblist:
#             # label (put into an event box to display the tooltip)
#             label = gtk.Label(widget.prop.blurb or widget.propname)
#             ebox = gtk.EventBox()
#             ebox.add(label)
#             if widget.prop.doc is not None:
#                 tooltips.set_tip(ebox, widget.prop.doc)
            
#             table.attach(ebox, 0, 1, n, n+1,
#                          xoptions=gtk.FILL, yoptions=0,
#                          xpadding=5, ypadding=1)            
#             table.attach(widget, 1, 2, n, n+1,
#                          xoptions=gtk.EXPAND|gtk.FILL, yoptions=0,
#                          xpadding=5, ypadding=1)
#             n += 1       

#         frame2 = uihelper.new_section('Group Properties', table)

        #
        # Put everything together!
        #
        self.pack_start(frame1,True,True)

        # DISABLE GROUP BOXES RIGHT NOW
        #self.pack_start(frame2,False,True)

        self.show_all()
            
        
    def create_source_column(self, model, index):
        " Set up model with all available datasets. "

        def cell_data_func(column, cell, model, iter, index):
            dataset = model.get_value(iter, index)
            if dataset is None:
                cell.set_property('text', "")
            else:
                cell.set_property('text', unicode(dataset.key))
            
        def on_edited(cell, path, new_text, model, index):
            if new_text == "":
                ds = None
            else:
                ds = globals.app.project.get_dataset(new_text)

            model[path][index] = ds

        dataset_model = gtk.ListStore(object, str)        
        def refresh_dataset_model(sender, project, model):
            model.clear()
            model.append((None, ""))
            for ds in globals.app.project.datasets:
                model.append( (ds, ds.key) )
        refresh_dataset_model(self, globals.app.project, dataset_model)
       
        cell = gtk.CellRendererCombo()
        cell.set_property('text-column', 1)
        cell.set_property('editable', True)
        cell.connect('edited', on_edited, model, index)
        cell.set_property('model', dataset_model)
        
        column = gtk.TreeViewColumn('source')
        column.pack_start(cell)
        column.set_cell_data_func(cell, cell_data_func, index)
        return column
        
        
    #--- CHECK IN/CHECK OUT -----------------------------------------------
    
    def check_in(self):
        self.factory.check_in()

        for gb in self.gblist:
            gb.check_in()

            
    def check_out(self, undolist=[]):
        self.factory.check_out(undolist=undolist)
        for gb in self.gblist:
            gb.check_out(undolist=undolist)
        

    #----------------------------------------------------------------------
    # Callbacks
    #
    
    def on_insert_new(self, sender):
        selection = self.treeview.get_selection()
        model, pathlist = selection.get_selected_rows()

        if model is None:
            model = self.treeview.get_model()
            
        if len(pathlist) > 0:
            source_key = model.get_value(model.get_iter(pathlist[0]), self.factory.keys.index('source'))
            source = globals.app.project.get_dataset(source_key, default=None)
            sibling = model.get_iter(pathlist[-1])
        else:
            source = None
            sibling = None

        new_line = objects.Line(source=source)
        new_row = self.factory.new_row(new_line)
        iter = model.insert_after(sibling, new_row)

        selection.unselect_all()
        selection.select_iter(iter)


    def on_remove_selection(self, sender):
        selection = self.treeview.get_selection()
        model, pathlist = selection.get_selected_rows()        
        n = 0
        for path in pathlist:
            iter = model.get_iter((path[0] - n,))
            model.remove(iter)
            n += 1


    def on_move_selection(self, sender, direction):
        (model, pathlist) = self.treeview.get_selection().get_selected_rows()
        if model is None or len(pathlist) == 0:
            return

        new_row = max(0, pathlist[0][0] + direction)
        iter = model.get_iter(pathlist[0])        
        second_iter = model.iter_nth_child(None, new_row)

        if second_iter is not None:
            model.swap(iter, second_iter)
            self.treeview.grab_focus()


    def on_toggle_view(self, sender):
        self.column_view = (self.column_view+1) % len(self.column_views)
        self.limit_columns()

    def limit_columns(self):
        model = self.key_combo.get_model()
        index = self.key_combo.get_active()
        if index > -1:
            keys = model[index][1]
            self.factory.hide_columns()
            self.factory.show_columns(keys)                   





        

        
