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

from Sloppy.Base import objects
from Sloppy.Base import pdict, uwrap

from propwidgets import *


import config, pwglade, uihelper



class LayerWindow(gtk.Window):

    """
    The LayerWindow allows to edit the properties of a plot layer.
    Different aspects of the layer are grouped as tabs in a notebook
    widget.  Changes are not applied immediately but only when you
    confirm your changes.
    
    """
    
    def __init__(self, app, plot, layer, current_page=None):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_default_size(550, 500)
        self.set_title("[Edit Plot Layer]")
        
        self.plot = plot
        self.app = app
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
        
        for tab in [NewLayerTab(app, layer),
                    NewLegendTab(app, layer.legend),
                    NewAxesTab(app, layer.axes),
                    LineTab(app, layer)]:
                    #NewLinesTab(app, layer)]:
            nb.append_page(tab)
            nb.set_tab_label_text(tab, tab.title)
            tab.check_in()
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
            
        self.app.project.journal.add_undo(ul)
        
        
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

        


class GroupBox(gtk.HBox, PWContainer):

    """    
    A group of widgets for so called 'Group' properties.
    See Base.objects.Group for details.
    """

    def __init__(self, layer, propname):

        gtk.HBox.__init__(self)
        
        self.layer = layer
        self.propname = propname        
        self.prop = layer.get_prop(propname)
        
        #
        # create widgets and put them into a horizontal box
        #

        # combo box
        liststore = gtk.ListStore(str, int)
        cbox_type = gtk.ComboBox(liststore)
        cell = gtk.CellRendererText()
        cbox_type.pack_start(cell, True)
        cbox_type.add_attribute(cell, 'text', 0)
        cbox_type.show()

        # populate combo box
        map_group_type = {'cycle value': objects.GROUP_TYPE_CYCLE,
                          'fixed value': objects.GROUP_TYPE_FIXED,
                          'increment value': objects.GROUP_TYPE_INCREMENT}
        for k,v in map_group_type.iteritems():
            liststore.append( (k,v) )

        # entries
        entry_value = gtk.Entry()
        #entry_value.show()

        entry_increment = gtk.Entry()
        entry_increment.show()

        # check button
        cbutton_allow_override = gtk.CheckButton("allow override")
        cbutton_allow_override.show()


        self.add(cbox_type)
        self.add(entry_value)
        self.add(entry_increment)
        self.add(cbutton_allow_override)
        self.show()

        PWContainer.__init__(self)
        
    def check_in(self):
        pass
        #allow_override = self.prop.allow_override
        #cbutton_allow_override.set_active(allow_override)

    def check_out(self):
        pass
        #allow_override = cbutton_allow_override.get_active()
        #self.prop.allow_override = allow_override
        
    


###############################################################################
#
# REPLACEMENTS FOR THE ABOVE CLASSES
#


class AbstractTab(gtk.VBox):

    def __init__(self, app):
        gtk.VBox.__init__(self)
        self.app = app
        self.clist = []
        
    def check_in(self):
        for c in self.clist:
            c.check_in()

    def check_out(self, undolist=[]):
        ul = UndoList().describe("Multiple actions")
        for c in self.clist:
            uwrap.smart_set(c.container, c.key, c.get_data(), undolist=ul)
            c.check_out() # why not put in the undolist here?
        undolist.append(ul)


class NewLayerTab(AbstractTab):

    title = "Layer"

    def __init__(self, app, layer):
        AbstractTab.__init__(self, app)        

        keys = ['title', 'visible', 'grid']

        clist = pwglade.smart_construct_connectors(layer, include=keys)
        table = pwglade.construct_table(clist)
        frame = uihelper.new_section("Layer", table)
        self.add(frame)

        self.clist = clist
        self.layer = layer
        self.show_all()        





class NewLegendTab(AbstractTab):

    title = "Legend"

    def __init__(self, app, legend):
        AbstractTab.__init__(self, app)

        keys = ['label', 'position', 'visible', 'border', 'x', 'y']
        
        clist = pwglade.smart_construct_connectors(legend, include=keys)
        table = pwglade.construct_table(clist)
        frame = uihelper.new_section("Legend", table)
        self.add(frame)

        self.clist = clist

        self.show_all()



class NewAxesTab(AbstractTab):

    title = "Axes"
    
    def __init__(self, app, axesdict):
        AbstractTab.__init__(self, app)

        keys = ['label', 'start', 'end', 'scale', 'format']

        self.clist = []
        for key, axis in axesdict.iteritems():
            connectors = pwglade.smart_construct_connectors(axis, include=keys)
            table = pwglade.construct_table(connectors)
            frame = uihelper.new_section(key, table)
            self.pack_start(frame, False, True)
            self.clist += connectors

        self.axesdict = axesdict
        self.show_all()


# TODO:
#
# Create a new Treeview that holds generic objects,
# for now Label, Line, ...
# These objects might be grouped, but for now a flat list
# should be sufficient.
#
# Double-clicking will open an edit window for that object.
# The button box on the right should contain the standard
# elements (edit,add,remove) as well as (move up, move down),
# because order is important.
#

#
# I could generalize the concept of a 'Drawing Element',
# so that it would be possible to define new drawing elements
# in a plugin.
#
#


class LineTab(AbstractTab):

    title = "Lines"

    def __init__(self, app, layer):
        AbstractTab.__init__(self, app)

        self.layer = layer

        self.treeview = ObjectTreeView()

        tv = self.treeview

        buttons = [(gtk.STOCK_EDIT, None),
                   (gtk.STOCK_ADD, None),
                   (gtk.STOCK_REMOVE, None),
                   (gtk.STOCK_GO_UP, None),
                   (gtk.STOCK_GO_DOWN, None)]
        btnbox = uihelper.construct_vbuttonbox(buttons)        

        hbox = gtk.HBox()
        hbox.pack_start(tv,True,True)
        hbox.pack_start(btnbox,False,True)

        self.add(hbox)
        self.show_all()
        

class ObjectTreeView(gtk.TreeView):

    def __init__(self):
        gtk.TreeView.__init__(self)
        
        
        
class NewLinesTab(AbstractTab):

    title = "Lines (old)"
    
    (COL_LINE,
     COL_VISIBLE,
     COL_LABEL,
     COL_STYLE,
     COL_MARKER,
     COL_WIDTH,
     COL_SOURCE_KEY,
     COL_CX, COL_CY,
     COL_ROW_FIRST, COL_ROW_LAST,
     COL_CXERR, COL_CYERR) = range(13)
    
    def __init__(self, app, layer):
        AbstractTab.__init__(self, app)
        self.layer = layer
                
        lines = layer.lines.copy()

        # Set up treeview
        sw = self.construct_treeview()

        # Set up button box
        buttons=[#(gtk.STOCK_EDIT, (lambda btn: self._cb_btn_),
                 (gtk.STOCK_ADD, (lambda btn: self.on_btn_add_clicked)),
                 (gtk.STOCK_DELETE, (lambda btn: self.on_btn_delete_clicked))]

        btnbox = uihelper.construct_vbuttonbox(buttons)

        # Construct an hbox with the line treeview on the left
        # and a buttonbox to add/remove lines on the right.
        hbox = gtk.HBox()        
        hbox.pack_start(sw, True, True)
        hbox.pack_start(btnbox, False, True)
        
        frame = uihelper.new_section("Lines", hbox)
        self.add(frame)
        self.show_all()
        

    #--- GUI CONSTRUCTION -------------------------------------------------        

    def construct_treeview(self):
        tv = gtk.TreeView()
        tv.set_headers_visible(True)
        tv.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

        model = gtk.TreeStore(object, 'gboolean',str,str,str,str,str,str,str,str,str,str,str)
        tv.set_model(model)

        # self.COL_VISIBLE
        cell = gtk.CellRendererToggle()
        cell.set_property('activatable', True)
        cell.connect("toggled", self._cb_toggled_bool,
                     model, self.COL_VISIBLE)
        column = gtk.TreeViewColumn('visible', cell)
        column.set_attributes(cell, active=self.COL_VISIBLE)
        tv.append_column(column)

        # self.COL_LABEL
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self._cb_edited_text, 
                     model, self.COL_LABEL, 'label')
        column = gtk.TreeViewColumn('label', cell)
        column.set_attributes(cell, text=self.COL_LABEL)
        tv.append_column(column)

        # self.COL_WIDTH
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self._cb_edited_text,
                     model, self.COL_WIDTH, 'width')
        column = gtk.TreeViewColumn('width', cell)
        column.set_attributes(cell, text=self.COL_WIDTH)
        tv.append_column(column)

        # self.COL_STYLE
        
        # set up model with all available line styles
        linestyle_model = gtk.ListStore(str)
        value_list = [None] + objects.Line.style.valid_values()
        for style in value_list:
            linestyle_model.append( (style or "",) )

        cell = gtk.CellRendererCombo()
        cell.set_property('editable', True)
        cell.connect('edited', self._cb_edited_source,
                     model, self.COL_STYLE)
        cell.set_property('text-column', 0)
        cell.set_property('model', linestyle_model)
        column = gtk.TreeViewColumn('style', cell)
        column.set_attributes(cell, text=self.COL_STYLE)
        tv.append_column(column)

        # self.COL_MARKER

        # set up model with all available markers
        marker_model = gtk.ListStore(str)
        value_list = [None] + objects.Line.marker.valid_values()
        for marker in value_list:
            marker_model.append( (marker or "",) )

        cell = gtk.CellRendererCombo()
        cell.set_property('editable', True)
        cell.connect('edited', self._cb_edited_source,
                     model, self.COL_MARKER)
        cell.set_property('text-column', 0)
        cell.set_property('model', marker_model)
        column = gtk.TreeViewColumn('marker', cell)
        column.set_attributes(cell, text=self.COL_MARKER)
        tv.append_column(column)
        
        
        # self.COL_SOURCE_KEY

        # set up model with all available datasets
        dataset_model = gtk.ListStore(str)        
        def refresh_dataset_model(sender, project, model):
            model.clear()
            for ds in self.app.project.datasets:
                model.append( (ds.key,) )
        refresh_dataset_model(self, self.app.project, dataset_model)

        self.app.project.sig_connect("notify::datasets", refresh_dataset_model,
                                         self.app.project, dataset_model)
        
        cell = gtk.CellRendererCombo()
        cell.set_property('editable', True)
        cell.connect('edited', self._cb_edited_source,
                     model, self.COL_SOURCE_KEY)
        cell.set_property('text-column', 0)
        cell.set_property('model', dataset_model)
        column = gtk.TreeViewColumn('source', cell)
        column.set_attributes(cell, text=self.COL_SOURCE_KEY)
        tv.append_column(column)

        # self.COL_CX
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self._cb_edited_text, 
                     model, self.COL_CX, 'cx')
        column = gtk.TreeViewColumn('cx', cell)
        column.set_attributes(cell, text=self.COL_CX)
        tv.append_column(column)

        # self.COL_CY
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self._cb_edited_text, 
                     model, self.COL_CY, 'cy')
        column = gtk.TreeViewColumn('cy', cell)
        column.set_attributes(cell, text=self.COL_CY)
        tv.append_column(column)

        # self.COL_ROW_FIRST
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self._cb_edited_text, 
                     model, self.COL_ROW_FIRST, 'row_first')
        column = gtk.TreeViewColumn('row_first', cell)
        column.set_attributes(cell, text=self.COL_ROW_FIRST)
        tv.append_column(column)

        # self.COL_ROW_LAST
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self._cb_edited_text, 
                     model, self.COL_ROW_LAST, 'row_last')
        column = gtk.TreeViewColumn('row_last', cell)
        column.set_attributes(cell, text=self.COL_ROW_LAST)
        tv.append_column(column)


        # error bars are not yet implemented, so I disabled the next two
#         # self.COL_CXERR
#         cell = gtk.CellRendererText()
#         cell.set_property('editable', True)
#         cell.connect('edited', self._cb_edited_text, 
#                      model, self.COL_CXERR, 'cxerr')
#         column = gtk.TreeViewColumn('cxerr', cell)
#         column.set_attributes(cell, text=self.COL_CXERR)
#         tv.append_column(column)

#         # self.COL_CYERR
#         cell = gtk.CellRendererText()
#         cell.set_property('editable', True)
#         cell.connect('edited', self._cb_edited_text, 
#                      model, self.COL_CYERR, 'cyerr')
#         column = gtk.TreeViewColumn('cyerr', cell)
#         column.set_attributes(cell, text=self.COL_CYERR)
#         tv.append_column(column)

        # put treeview 'tv' in a scrolled window 'sw'
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(tv)
        tv.show()        
        sw.show()    

        #
        # Below the scrolled window, we add some boxes for group
        # properties.
        #
        self.gblist = [GroupBox(self.layer, 'group_linestyle'),
                       GroupBox(self.layer, 'group_linemarker'),
                       GroupBox(self.layer, 'group_linewidth'),
                        GroupBox(self.layer, 'group_linecolor')]

        # TODO: we re-think the whole layerwin implementation before
        # actually displaying the table with the group boxes.
        for gb in self.gblist:
            gb.show()
        
        # Wrap group boxes into a table
        table = gtk.Table(rows=len(self.gblist), columns=3)

#         n = 0
#         for widget in gblist:
#             label = gtk.Label(widget.propname)
#             label.show()
            
#             table.attach(label, 0, 1, n, n+1,
#                          xoptions=gtk.FILL,
#                          yoptions=0,
#                          xpadding=5,
#                          ypadding=1)            
#             table.attach(widget, 1, 2, n, n+1,
#                          xoptions=gtk.EXPAND|gtk.FILL,
#                          yoptions=0,
#                          xpadding=5,
#                          ypadding=1)
#             n += 1
#         table.show()
        
         
#         frame = gtk.Frame('Grouped Properties')
#         frame.add(table)
#         frame.show()        

        #
        # Put everything in a vertical box...
        #
        vbox = gtk.VBox()
        vbox.pack_start(sw, expand=True, fill=True)
#         vbox.pack_start(frame, expand=False, fill=True)
        vbox.show()

        # for further reference        
        self.widget = vbox
        self.label = gtk.Label("None")
        self.treeview = tv        
        return vbox
    

    #--- CHECK IN/CHECK OUT -----------------------------------------------    

#     def check_in(self):
#         for c in self.clist:
#             self.check_in()

            
    def check_out(self, undolist=[]):

        return # TODO TODO TODO TODO
    
        # TOOD: make sure we are finished with editing the treeview
        
        ul = UndoList().describe("Set Line Property")

        model = self.treeview.get_model()
        model_lines = []

        def get_column(column, default=None):
            """
            Returns the value of the specified column from the model, or if
            it is an empty string, returns the default value given.
            """
            rv = model.get_value(treeiter, column)
            if isinstance(rv, basestring) and len(rv) == 0:
                return default
            else:
                return rv
        
        n=0        
        treeiter = model.get_iter_first()
        while treeiter:
            # Is this row an existing line or a new one?
            line = model.get_value(treeiter, self.COL_LINE)
            if line in self.layer.lines:
                # existing line
                source_key = model.get_value(treeiter, self.COL_SOURCE_KEY)
                if not source_key:
                    source = None
                else:
                    source = self.app.project.get_dataset(source_key, default=None)
                        
                uwrap.smart_set(line,
                          'visible', get_column(self.COL_VISIBLE),
                         'label', get_column(self.COL_LABEL),
                         'style', get_column(self.COL_STYLE),
                         'marker', get_column(self.COL_MARKER),
                         'width', get_column(self.COL_WIDTH),
                         'source', source,
                         'cx', get_column(self.COL_CX),
                         'cy', get_column(self.COL_CY),
                         'row_first', get_column(self.COL_ROW_FIRST),
                         'row_last', get_column(self.COL_ROW_LAST),
                         'cxerr', get_column(self.COL_CXERR),
                         'cyerr', get_column(self.COL_CYERR),
                         undolist=ul)
            else:
                ulist.append( self.layer.lines, line, undolist=ul )

            model_lines.append(line)
            treeiter = model.iter_next(treeiter)
            n+=1

        # now we need to check if we have removed any lines
        for line in self.layer.lines:
            if line not in model_lines:
                ulist.remove( self.layer.lines, line, undolist=ul)

        # group boxes
        for gb in self.gblist:
            print "CHECKING OUT"
            #gb.check_out()
        
        undolist.append(ul)

            
    def check_in(self):
        model = self.treeview.get_model()
        model.clear()

        lines = self.layer.lines
        for line in lines:            
            model.append(None, self.model_row_from_line(line))

        # group boxes
        for gb in self.gblist:
            gb.check_in()

    def model_row_from_line(self, line):
        source = line.source
        if source is not None: source_key = source.key
        else: source_key = ""
        return [line,
                line.visible,
                line.label or "",
                line.rget('style', ""),
                line.rget('marker', ""),
                line.rget('width', ""),
                source_key,
                str(line.rget('cx',"")),
                str(line.rget('cy',"")),
                str(line.rget('row_first',"")),
                str(line.rget('row_last',"")),                
                str(line.rget('cxerr',"")),
                str(line.rget('cyerr',""))]


    #----------------------------------------------------------------------
    # GUI Callbacks
    #

    def _cb_edited_text(self, cell, path, new_text, model, column, prop_key):
        # check if the new_text is appropriate for the property
        prop = objects.Line().get_prop(prop_key)
        try:
            if new_text == "": new_text = None
            new_text = prop.check(new_text)
        except (TypeError, ValueError):
            print "Invalid value"
        else:
            if new_text is None: new_text=""
            model[path][column] = str(new_text)

    def _cb_toggled_bool(self, cell, path, model, column):
        model[path][column] = not model[path][column]
        
    def _cb_edited_source(self, cell, path, new_text, model, column):
        model[path][column] = new_text

    def on_btn_add_clicked(self, sender):        
        selection = self.treeview.get_selection()
        model, pathlist = selection.get_selected_rows()

        if model is None:
            model = self.treeview.get_model()
            
        if len(pathlist) > 0:
            source_key = model.get_value(model.get_iter(pathlist[0]), self.COL_SOURCE_KEY)
            source = self.app.project.get_dataset(source_key, default=None)
        else:
            source = None

        new_line = objects.Line(source=source)
        
        iter = model.append(None, self.model_row_from_line(new_line))

        selection.unselect_all()
        selection.select_iter(iter)

    def on_btn_delete_clicked(self, sender):
        selection = self.treeview.get_selection()
        model, pathlist = selection.get_selected_rows()

        n = 0
        for path in pathlist:
            iter = model.get_iter((path[0] - n,))
            model.remove(iter)
            n += 1

        
        

        
