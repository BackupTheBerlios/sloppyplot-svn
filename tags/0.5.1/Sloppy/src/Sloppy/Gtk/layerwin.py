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


import config, pwglade



def construct_imageview():
    """
    Returns (scrolled window, treeview).
    Scrolled window is not shown by default while treeview is.
    """
    # stock-id, label
    model = gtk.ListStore(str, str)

    column = gtk.TreeViewColumn('Axis')

    renderer = gtk.CellRendererPixbuf()        
    column.pack_start(renderer, expand=False)
    column.set_attributes(renderer, stock_id=0)

    renderer = gtk.CellRendererText()
    column.pack_start(renderer, expand=True)
    column.set_attributes(renderer, text=1)

    tv = gtk.TreeView()
    tv.set_model(model)
    tv.append_column(column)
    tv.get_selection().set_mode(gtk.SELECTION_SINGLE)
    tv.set_headers_visible(False)
    tv.show()

    # put treeview in a scrolled window
    sw = gtk.ScrolledWindow()
    sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    sw.add(tv)

    return (sw, tv)




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
        
        self.plot = plot
        self.app = app
        self.layer = layer

        self.set_title("[Edit Plot Layer]")
        
        #
        # init UI
        #
        
        # list of tabs with a check_in/check_out method
        self.tabs = []
        self.tablabels = []
        
        nb_main = gtk.Notebook() ; nb_main.show()        
        nb_main.set_property('tab-pos', gtk.POS_LEFT)

        # tabs: general
        tab = LayerTab(app, layer) ; tab.show()
        nb_main.append_page(tab)
        nb_main.set_tab_label_text(tab, "Layer")

        self.tabs.append(tab)
        self.tablabels.append("Layer")

        # tab: axes
        tab = AxesTab(app, layer)
        tab.show()
        nb_main.append_page(tab)
        nb_main.set_tab_label_text(tab, "Axes")

        self.tabs.append(tab)
        self.tablabels.append("Axes")

        
        # tab: legend
        tab = LegendTab(app, layer)
        tab.show()
        nb_main.append_page(tab)
        nb_main.set_tab_label_text(tab, "Legend")

        self.tabs.append(tab)
        self.tablabels.append("Lines")

        # tab: lines
        tab = LinesTab(app, layer)
        tab.show()
        nb_main.append_page(tab)
        nb_main.set_tab_label_text(tab, "Lines")

        self.tabs.append(tab)
        self.tablabels.append("Lines")

        #
        # New Tab Mechanism
        #

        #
        # This is going to replace all other tabs.
        #
        if False: # CURRENTLY DISABLED!
            for tab in [NewLinesTab(app, layer), NewLegendTab(app, layer)]:
                nb_main.append_page(tab)
                nb_main.set_tab_label_text(tab, tab.title)
                tab.check_in()


        # if requested, set the page with the name `tab` as current page
        if current_page is not None:
            try:
                index = self.tablabels.index(current_page)                
            except ValueError:
                raise KeyError("There is no Tab with the label %s" % current_page)
            nb_main.set_current_page(index)
            


        btnbox = self._construct_btnbox()
        separator = gtk.HSeparator()
             
        vbox = gtk.VBox()
        vbox.pack_start(nb_main, True, True)
        vbox.pack_start(separator, False, False, padding=4)
        vbox.pack_end(btnbox, False, False)
        self.add(vbox)
        self.show_all()

        self.notebook = nb_main
        
    def _construct_btnbox(self):
        box = gtk.HBox()

        btn_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        btn_cancel.connect("clicked", self.cb_cancel)
        btn_cancel.show()
        
        btn_revert = gtk.Button(stock=gtk.STOCK_REVERT_TO_SAVED)
        btn_revert.connect("clicked", self.cb_revert)
        btn_revert.show()

        btn_apply = gtk.Button(stock=gtk.STOCK_APPLY)
        btn_apply.connect("clicked", self.cb_apply)
        btn_apply.show()        

        btn_ok = gtk.Button(stock=gtk.STOCK_OK)
        btn_ok.connect("clicked", self.cb_ok)
        btn_ok.show()

        box.pack_start(btn_revert, False, True)
        
        box.pack_end(btn_ok, False, True, padding=2)
        box.pack_end(btn_apply, False, True, padding=2)
        box.pack_end(btn_cancel, False, True, padding=2)
        
        return box


    def cb_cancel(self, sender):
        self.destroy()

    def cb_revert(self, sender):
        for tab in self.tabs:
            tab.check_in()

    def cb_apply(self, sender):
        sender.grab_focus()
        self.apply_changes()
            
    def cb_ok(self, sender):
        sender.grab_focus()
        self.apply_changes()
        self.destroy()            

    def apply_changes(self):
        ul = UndoList().describe("Edit Plot Properties")
        for tab in self.tabs:
            ui = UndoList()
            tab.check_out(undolist=ui)
            ul.append(ui.simplify())


        ul = ul.simplify(preserve_list=True)
        
        if len(ul) > 0:
            uwrap.emit_last(self.plot, "changed", undolist=ul)            
        else:
            ul = NullUndo()
            
        self.app.project.journal.add_undo(ul)



class AbstractTab(gtk.HBox, PWContainer):

    def __init__(self, app, layer):
        self.app = app
        self.layer = layer

        gtk.HBox.__init__(self)
        PWContainer.__init__(self)

        
    def get_tab_label(self):
        label = gtk.Label("Unnamed Tab") ; label.show()
        return label



class LayerTab(AbstractTab):

    def construct_pwdict(self):        
        frame = gtk.Frame("Layer") ; frame.show()
        
        pwlist = list()
        for key in ['title','visible', 'grid']:
            pw = construct_pw(self.layer, key)
            self.pwdict[key] = pw
            pwlist.append(pw)

        tablewidget = construct_pw_table(pwlist)
        tablewidget.show()
        frame.add(tablewidget)
        self.pack_end(frame)

     
        

        
class LegendTab(AbstractTab):

    def construct_pwdict(self):
        self.legend = self.layer.legend
                                                
        frame = gtk.Frame("Legend") ; frame.show()

        pwlist = list()
        for key in ['label', 'position', 'visible', 'border', 'x', 'y']:
            pw = construct_pw(self.legend, key)
            self.pwdict[key] = pw
            pwlist.append(pw)
        tablewidget = construct_pw_table(pwlist)
        tablewidget.show()
        frame.add(tablewidget)
        self.pack_end(frame)       
        
        
class AxisTab(AbstractTab):

    def __init__(self, app, layer, axis_key):
        self.layer = layer
        self.axis = layer.axes[axis_key]
        self.axis_key = axis_key

        AbstractTab.__init__(self, app, layer)

        
    def construct_pwdict(self):
        vbox = gtk.VBox()
        tt = gtk.Tooltips()

        pwlist = list()
        for key in ['label', 'start', 'end', 'scale', 'format']:
            pw = construct_pw(self.axis, key)
            self.pwdict[key] = pw
            pwlist.append(pw)

        tablewidget = construct_pw_table(pwlist)

        self.pack_end(tablewidget)        
        tablewidget.show()
        
        
    def get_tab_label(self):
        vbox = gtk.VBox()
        label = gtk.Label("Axis") ; label.show()
        label2 = gtk.Label(self.axis_key); label2.show()
        vbox.pack_start(label)
        vbox.pack_start(label2)
        vbox.show()
        return vbox



class AxesTab(AbstractTab):

    def construct_pwdict(self):
        layer = self.layer
        
        xaxis = AxisTab(self.app, layer, 'x')
        xaxis.show()
        xframe = gtk.Frame("X-Axis")
        xframe.add(xaxis)
        xframe.show()
        
        yaxis = AxisTab(self.app, layer, 'y')
        yaxis.show()
        yframe = gtk.Frame("Y-Axis")
        yframe.add(yaxis)
        yframe.show()

        # We abuse the pwdict attribute here.  Actually we should
        # add only PW objects, but since pwdict is only needed
        # to call 'check_in' and 'check_out', we can use AxisTab objects
        # as well.
        self.pwdict['xaxis'] = xaxis
        self.pwdict['yaxis'] = yaxis

        self.pack_start(xframe, True, True)
        self.pack_start(yframe, True, True)


class LinesTab(AbstractTab):

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
    
    def construct_pwdict(self):
        layer = self.layer
        lines = layer.lines

        # construct an hbox with the line treeview on the left
        # and a buttonbox to add/remove lines on the right.
        hbox = gtk.HBox()
        hbox.show()
        
        sw = self.construct_treeview()
        sw.show()        
        hbox.pack_start(sw, True, True)

        # TODO: set up button box
        bb = self.construct_btnbox()
        bb.show()
        hbox.pack_start(bb, False, True, padding=5)
        
        # put hbox in a nice frame
        frame = gtk.Frame("Lines")
        frame.show()
        frame.add(hbox)

        self.add(frame)
        
        self.check_in()

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


    def construct_btnbox(self):

        box = gtk.VBox()

        btn = gtk.Button("") ; btn.show()
        image = gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON)
        btn.set_image(image)
        box.pack_start(btn, False, True, 3)
        btn.connect("clicked", self._cb_btn_add_clicked)

        btn = gtk.Button("") ; btn.show()
        image = gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON)
        btn.set_image(image)
        btn.connect("clicked", self._cb_btn_remove_clicked)
        
        box.pack_start(btn, False, True, 3)
        
        return box
    

    #--- CHECK IN/CHECK OUT -----------------------------------------------    

    def check_out(self, undolist=[]):

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

    def _cb_btn_add_clicked(self, sender):        
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

    def _cb_btn_remove_clicked(self, sender):
        selection = self.treeview.get_selection()
        model, pathlist = selection.get_selected_rows()

        n = 0
        for path in pathlist:
            iter = model.get_iter((path[0] - n,))
            model.remove(iter)
            n += 1

        



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


class NewLegendTab(config.ConfigurationPage):

    title = "Legend (New)"

    def __init__(self, app, layer):
        config.ConfigurationPage.__init__(self)
        self.app = app
        self.layer = layer

        keys = ['label', 'position', 'visible', 'border', 'x', 'y']
        clist = pwglade.smart_construct_connectors(layer.legend, include=keys)
        table = pwglade.construct_table(clist)

        frame = uihelper.new_section("Legend", table)
        self.add(frame)

        self.clist = clist

        self.show_all()
        
    def check_in(self):
        for c in self.clist:
            c.check_in()

    def check_out(self):
        for c in self.clist:
            c.check_out()

        # PROBLEM: No Undo here!




class NewLinesTab(config.ConfigurationPage):

    title = "Lines (New)"
    
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
        config.ConfigurationPage.__init__(self)        
        self.app = app
        self.layer = layer
                
        lines = layer.lines

        # Set up treeview
        sw = self.construct_treeview()

        # Set up button box
        buttons=[#(gtk.STOCK_EDIT, (lambda btn: self._cb_btn_),
                 (gtk.STOCK_ADD, (lambda btn: self.on_btn_add_clicked)),
                 (gtk.STOCK_DELETE, (lambda btn: self.on_btn_delete_clicked))]

        btnbox = uihelper.construct_buttonbox(buttons,
                                              horizontal=False,
                                              layout=gtk.BUTTONBOX_START)
        btnbox.set_spacing(uihelper.SECTION_SPACING)
        btnbox.set_border_width(uihelper.SECTION_SPACING)

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

        
        

        
