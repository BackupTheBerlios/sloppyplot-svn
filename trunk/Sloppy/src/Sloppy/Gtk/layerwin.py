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



class LineTab(AbstractTab):

    title = "Lines"

    def __init__(self, app, layer):
        AbstractTab.__init__(self, app)

        self.layer = layer
        self.treeview = LinesTreeView(app, layer)
                
        buttons = [
            (gtk.STOCK_ADD, (lambda sender: self.treeview.insert_new())),
            (gtk.STOCK_REMOVE, (lambda sender: self.treeview.remove_selection())),
            (gtk.STOCK_GO_UP, (lambda sender: self.treeview.move_selection(-1))),
            (gtk.STOCK_GO_DOWN, (lambda sender: self.treeview.move_selection(+1)))
            ]        
        self.buttonbox = uihelper.construct_vbuttonbox(buttons, labels=False)

        hbox = gtk.HBox()
        hbox.pack_start(self.treeview, True, True)
        hbox.pack_start(self.buttonbox, False, True)

        self.add(hbox)
        self.show_all()



    #--- CHECK IN/CHECK OUT -----------------------------------------------
    
    def check_in(self):
        self.treeview.check_in()

            
    def check_out(self, undolist=[]):

        # TOOD: make sure we are finished with editing the treeview
        self.treeview.check_out(undolist=undolist)



        

class LinesTreeView(gtk.TreeView):

    (MODEL_OBJECT,
     MODEL_VISIBLE,     
     MODEL_LABEL,
     MODEL_WIDTH,
     MODEL_COLOR,     
     MODEL_STYLE,
     MODEL_MARKER,
     MODEL_MARKER_COLOR,
     #
     MODEL_SOURCE_KEY,
     MODEL_CX,
     MODEL_CY,
     MODEL_ROW_FIRST,
     MODEL_ROW_LAST,
     MODEL_CXERR,
     MODEL_CYERR
     ) = range(15)

    
    def __init__(self, app, layer):

        self.app = app
        self.layer = layer
        self.lines = layer.lines

        # model: see MODEL_XXX
        model = gtk.TreeStore(object, bool, str, str, str, str, str, str, str, str,
                              str, str, str, str, str)
        gtk.TreeView.__init__(self, model)
        self.set_headers_visible(True)
        self.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        

        # MODEL_VISIBLE
        column = gtk.TreeViewColumn('visible')

        cell = gtk.CellRendererToggle()
        cell.set_property('activatable', True)
        cell.connect('toggled', self.on_toggled_bool, self.MODEL_VISIBLE)
        
        column.pack_start(cell)        
        column.set_attributes(cell, active=self.MODEL_VISIBLE)
        self.append_column(column)
        
        
        # MODEL_LABEL
        column = gtk.TreeViewColumn('label')

        cell = gtk.CellRendererText()
        cell.set_property('editable', True)        
        cell.connect('edited', self.on_edited_text, self.MODEL_LABEL, objects.Line.label)
        
        column.pack_start(cell)       
        column.set_attributes(cell, text=self.MODEL_LABEL)        
        self.append_column(column)


        # MODEL_WIDTH
        column = gtk.TreeViewColumn('width')
        
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited_text, self.MODEL_WIDTH, objects.Line.width)
        
        column.pack_start(cell)
        column.set_attributes(cell, text=self.MODEL_WIDTH)
        self.append_column(column)


        # MODEL_COLOR
        column = gtk.TreeViewColumn('color')

        # set up model with available colors and with an item _custom colors_
        system_colors = [None, 'black', 'green','red','blue']
        color_model = gtk.ListStore(str)
        for color in system_colors:
            color_model.append((color or "",))
        
        cell = gtk.CellRendererCombo()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited_combo, self.MODEL_COLOR)
        cell.set_property('text-column', 0)
        cell.set_property('model', color_model)
        
        column.pack_start(cell)
        column.set_attributes(cell, text=self.MODEL_COLOR)
        self.append_column(column)
        
                              
        # MODEL_STYLE
        column = gtk.TreeViewColumn('style')
        
        # set up model with all available line styles
        linestyle_model = gtk.ListStore(str)
        value_list = [None] + objects.Line.style.valid_values()
        for style in value_list:
            linestyle_model.append( (style or "",) )

        cell = gtk.CellRendererCombo()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited_combo, self.MODEL_STYLE)
        cell.set_property('text-column', 0)
        cell.set_property('model', linestyle_model)

        column.pack_start(cell)
        column.set_attributes(cell, text=self.MODEL_STYLE)
        self.append_column(column)


        # MODEL_MARKER
        column = gtk.TreeViewColumn('marker')

        # set up model with all available markers
        marker_model = gtk.ListStore(str)
        value_list = [None] + objects.Line.marker.valid_values()
        for marker in value_list:
            marker_model.append( (marker or "",) )

        cell = gtk.CellRendererCombo()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited_combo, self.MODEL_MARKER)
        cell.set_property('text-column', 0)
        cell.set_property('model', marker_model)

        column.pack_start(cell)
        column.set_attributes(cell, text=self.MODEL_MARKER)
        self.append_column(column)


        # MODEL_MARKER_COLOR
        column = gtk.TreeViewColumn('marker color')
        
        cell = gtk.CellRendererCombo()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited_combo, self.MODEL_MARKER_COLOR)
        cell.set_property('text-column', 0)
        cell.set_property('model', color_model)
        
        column.pack_start(cell)
        column.set_attributes(cell, text=self.MODEL_MARKER_COLOR)
        self.append_column(column)


        # MODEL_SOURCE_KEY
        column = gtk.TreeViewColumn('source')
        
        # set up model with all available datasets
        dataset_model = gtk.ListStore(str)        
        def refresh_dataset_model(sender, project, model):
            model.clear()
            model.append(("",))
            for ds in self.app.project.datasets:
                model.append( (ds.key,) )
        refresh_dataset_model(self, self.app.project, dataset_model)
       
        cell = gtk.CellRendererCombo()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited_combo, self.MODEL_SOURCE_KEY)
        cell.set_property('text-column', 0)
        cell.set_property('model', dataset_model)

        column.pack_start(cell)
        column.set_attributes(cell, text=self.MODEL_SOURCE_KEY)
        self.append_column(column)

        # MODEL_CX
        column = gtk.TreeViewColumn('cx')
        
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited_text, self.MODEL_CX, objects.Line.cx)

        column.pack_start(cell)
        column.set_attributes(cell, text=self.MODEL_CX)
        self.append_column(column)


        # MODEL_CY
        column = gtk.TreeViewColumn('cy')
        
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited_text, self.MODEL_CY, objects.Line.cy)

        column.pack_start(cell)
        column.set_attributes(cell, text=self.MODEL_CY)
        self.append_column(column)


        # MODEL_ROW_FIRST
        column = gtk.TreeViewColumn('row_first')
        
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited_text, self.MODEL_ROW_FIRST, objects.Line.row_first)

        column.pack_start(cell)
        column.set_attributes(cell, text=self.MODEL_ROW_FIRST)
        self.append_column(column)


        # MODEL_ROW_LAST
        column = gtk.TreeViewColumn('row_last')
        
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_edited_text, self.MODEL_ROW_LAST, objects.Line.row_last)

        column.pack_start(cell)
        column.set_attributes(cell, text=self.MODEL_ROW_LAST)
        self.append_column(column)



    def check_in(self):
        model = self.get_model()
        model.clear()

        for line in self.lines:
            model.append(None, self.model_row_from_line(line))

        ## group boxes
        #for gb in self.gblist:
        #    gb.check_in()

    def check_out(self, undolist=[]):        

        ul = UndoList().describe("Set Line Property")
        
        model = self.get_model()

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

        def check_out_line_from_iter(line, iter, undolist=[]):
            # existing line
            source_key = model.get_value(treeiter, self.MODEL_SOURCE_KEY)
            if not source_key:
                source = None
            else:
                source = self.app.project.get_dataset(source_key, default=None)

            uwrap.smart_set(line,
                            'visible', get_column(self.MODEL_VISIBLE),
                            'label', get_column(self.MODEL_LABEL),
                            'width', get_column(self.MODEL_WIDTH),
                            'color', get_column(self.MODEL_COLOR),                                
                            'style', get_column(self.MODEL_STYLE),
                            'marker', get_column(self.MODEL_MARKER),
                            'marker_color', get_column(self.MODEL_MARKER_COLOR),                                                                                               
                            'source', source,
                            'cx', get_column(self.MODEL_CX),
                            'cy', get_column(self.MODEL_CY),
                            'row_first', get_column(self.MODEL_ROW_FIRST),
                            'row_last', get_column(self.MODEL_ROW_LAST),
                            'cxerr', get_column(self.MODEL_CXERR),
                            'cyerr', get_column(self.MODEL_CYERR),
                            undolist=undolist)
            
            
        new_list = []                
        treeiter = model.get_iter_first()
        while treeiter:
            line = model.get_value(treeiter, self.MODEL_OBJECT)
            check_out_line_from_iter(line, treeiter, undolist=ul)        
            new_list.append(line)            
            treeiter = model.iter_next(treeiter)

        if self.layer.lines != new_list:
            uwrap.set(self.layer, lines=new_list, undolist=ul)
        
        ## group boxes
        #for gb in self.gblist:
        #    print "CHECKING OUT"
        #    #gb.check_out()
        
        undolist.append(ul)
        
        
    #----------------------------------------------------------------------
    # GUI Callbacks
    #

    def on_edited_text(self, cell, path, new_text, column, prop):
        # check if the new_text is appropriate for the property       
        try:
            if new_text == "":
                new_text = None
            new_text = prop.check(new_text)
        except (TypeError, ValueError):
            print "Invalid value"
        else:
            if new_text is None:
                new_text=""
            self.get_model()[path][column] = str(new_text)

    def on_toggled_bool(self, cell, path, column):
        model = self.get_model()
        model[path][column] = not model[path][column]
        
    def on_edited_combo(self, cell, path, new_text, column):
        model = self.get_model()
        model[path][column] = new_text




    #------------------------------------------------------------------------------

    def model_row_from_line(self, line):
        if line.source is not None:
            source_key = line.source.key
        else:
            source_key = ""
            
        return [line,
                line.visible,
                line.label or "",
                line.rget('width', None),
                line.rget('color', None),                                
                line.rget('style', None),
                line.rget('marker', None),
                line.rget('marker_color', None),                
                source_key,
                str(line.rget('cx',"")),
                str(line.rget('cy',"")),
                str(line.rget('row_first',"")),
                str(line.rget('row_last',"")),                
                str(line.rget('cxerr',"")),
                str(line.rget('cyerr',""))
                ]


    def remove_selection(self):
        selection = self.get_selection()
        model, pathlist = selection.get_selected_rows()        
        n = 0
        for path in pathlist:
            iter = model.get_iter((path[0] - n,))
            model.remove(iter)
            n += 1

    def insert_new(self):
        selection = self.get_selection()
        model, pathlist = selection.get_selected_rows()

        if model is None:
            model = self.get_model()
            
        if len(pathlist) > 0:
            source_key = model.get_value(model.get_iter(pathlist[0]), self.MODEL_SOURCE_KEY)
            source = self.app.project.get_dataset(source_key, default=None)
            sibling = model.get_iter(pathlist[-1])
        else:
            source = None
            sibling = None

        new_line = objects.Line(source=source)
        iter = model.insert_after(None, sibling, self.model_row_from_line(new_line))

        selection.unselect_all()
        selection.select_iter(iter)


    def move_selection(self, direction):
        (model, pathlist) = self.get_selection().get_selected_rows()
        if model is None:
            return

        new_row = max(0, pathlist[0][0] + direction)
        iter = model.get_iter(pathlist[0])        
        second_iter = model.iter_nth_child(None, new_row)

        if second_iter is not None:
            model.swap(iter, second_iter)
            self.grab_focus()
        
            
        








        
#         #
#         # Below the scrolled window, we add some boxes for group
#         # properties.
#         #
#         self.gblist = [GroupBox(self.layer, 'group_linestyle'),
#                        GroupBox(self.layer, 'group_linemarker'),
#                        GroupBox(self.layer, 'group_linewidth'),
#                         GroupBox(self.layer, 'group_linecolor')]

#         # TODO: we re-think the whole layerwin implementation before
#         # actually displaying the table with the group boxes.
#         for gb in self.gblist:
#             gb.show()
        
#         # Wrap group boxes into a table
#         table = gtk.Table(rows=len(self.gblist), columns=3)

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





        

        
