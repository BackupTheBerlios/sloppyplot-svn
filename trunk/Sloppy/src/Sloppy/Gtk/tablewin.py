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


import logging
logger = logging.getLogger('Gtk.tablewin')

import pygtk # TBR
pygtk.require('2.0') # TBR

import gtk, gobject

from Sloppy.Base.table import Table
from Sloppy.Base.dataset import Dataset
from Sloppy.Base import uwrap

from Sloppy.Lib.Undo import UndoList, UndoInfo
from Sloppy.Lib import Signals

import Numeric

from tableview import TableView
import uihelper
import propwidgets



class DatasetWindow( gtk.Window ):    
    """
    A top level window holding a tableview widget and a treeview
    holding the Dataset's metadata.
    """

    actions = [
        ('DatasetMenu', None, '_Dataset'),
        ('Close', gtk.STOCK_CLOSE, 'Close this window', 'q', 'Close this window.', '_cb_close'),
        #
        ('RowInsert', gtk.STOCK_ADD, 'Insert new row', None, 'Insert a new row before the current position', 'cb_insert_row'),
        ('RowAppend', gtk.STOCK_ADD, 'Append new row', None, 'Insert a new row after the current position', 'cb_append_row'),
        ('RowRemove', gtk.STOCK_REMOVE, 'Remove row', 'Delete', 'Remove row at the current position', 'cb_remove_row'),
        #
        ('ColumnProperties', None, 'Edit column properties...', None, 'Edit column properties...', 'cb_column_properties'),
        ('ColumnCalculate', None, 'Calculate column data...', None, 'Calculate column data...', 'cb_column_calculate'),
        ('ColumnInsert', None, 'Insert Column before', None, 'Insert column just before this one', 'cb_column_insert'),
        ('ColumnInsertAfter', None, 'Insert Column after', None, 'Insert column after this one', 'cb_column_insert_after'),
        ('ColumnRemove', None, 'Remove Column', None, 'Remove this column', 'cb_column_remove'),
        #
        ('AnalysisMenu', None, '_Analysis'),
        ('Interpolate', None, 'Interpolate data (EXPERIMENTAL)', None, 'Interpolate data (EXPERIMENTAL)', 'cb_interpolate')
        ]
         
    ui = """
         <ui>
           <menubar name='MainMenu'>
             <menu action='DatasetMenu'>
               <menuitem action='Close'/>
             </menu>
             <menu action='AnalysisMenu'>
               <menuitem action='Interpolate'/>
             </menu>
           </menubar>              
           <toolbar name='Toolbar'>
             <separator/>
             <toolitem action='RowInsert'/>
             <toolitem action='RowAppend'/>
             <separator/>
             <toolitem action='RowRemove'/>
             <separator/>
           </toolbar>
           <popup name='popup_column'>
             <menuitem action='ColumnProperties'/>
             <menuitem action='ColumnCalculate'/>
             <separator/>
             <menuitem action='ColumnInsertAfter'/>                          
             <menuitem action='ColumnInsert'/>
             <menuitem action='ColumnRemove'/>
             <separator/>
             <menuitem action='RowInsert'/>
             <menuitem action='RowAppend'/>
             <menuitem action='RowRemove'/>             
           </popup>
         </ui>
         """
            
    
        
    def __init__(self, app, project, dataset=None):
        gtk.Window.__init__(self)
	self.set_size_request(280,320)
        self.set_transient_for(app.window)
        self.app = app
        
        self._signals = []

        self.uimanager = self._construct_uimanager()
        self.menubar = self._construct_menubar()
        self.toolbar = self._construct_toolbar()
        self.popup = self.uimanager.get_widget('/popup_column')
        self.popup_info = None # needed for popup
        
        self.tableview = self._construct_tableview()
        sw = uihelper.add_scrollbars(self.tableview)
        sw.show()
        
        hpaned = gtk.HPaned()
        hpaned.pack1( sw )
#        hpaned.pack2( self._construct_metadata_widget() )
        hpaned.show()
        self.hpaned = hpaned
        
        vbox = gtk.VBox()

        vbox.pack_start( self.menubar, expand=False, fill=True )
        vbox.pack_start( self.toolbar, expand=False, fill=True )
        vbox.pack_start( self.hpaned, expand=True, fill=True )

        vbox.show()
        self.add(vbox)

        self.project = project  # immutable
        self._dataset = None
        self.dataset = dataset        

        Signals.connect(self.project, "close", (lambda sender: self.destroy()))
        Signals.connect(self.dataset, "closed", (lambda sender: self.destroy()))
        
        
    def _cb_close(self, action):
        self.destroy()
        
    #--- GUI construction -------------------------------------------------
    
    def _construct_uimanager(self):
        uimanager = gtk.UIManager()
        uihelper.add_actions(uimanager, 'root', self.actions, map=self)
        uimanager.add_ui_from_string(self.ui)
        self.add_accel_group(uimanager.get_accel_group())
        return uimanager

    def _construct_menubar(self):
        menubar = self.uimanager.get_widget('/MainMenu')
        menubar.show()
        return menubar

    def _construct_toolbar(self):
        toolbar = self.uimanager.get_widget('/Toolbar')
        toolbar.set_style(gtk.TOOLBAR_ICONS)
        toolbar.show()
        return toolbar
        

    def _construct_tableview(self):        
        tableview = TableView(self.app)
        tableview.connect('button-press-event', self.cb_tableview_button_press_event)
        tableview.show()
        return tableview

    def _construct_metadata_widget(self):
        widget = gtk.Label('metadata')
        widget.show()
        return widget
        
    #--- Dataset ----------------------------------------------------------
    def set_dataset(self, dataset):
        
        if dataset is None:
            self.set_title("(no dataset)")
        else:
            self.set_title("DS: %s" % dataset.key)

        # FIXME
        # this is inconsistent: we expect 'table' to be fixed,
        # even though we argued before that the dataset.data field
        # is not necessarily fixed, only the Dataset.
        table = dataset.get_data()
        if not isinstance(table, Table):
            raise TypeError("TableWindow can only use Datasets with a Table as data.")
        self.tableview.set_table(table)

        for signal in self._signals:
            Signals.disconnect(signal)

        self._signals += [
            Signals.connect(table,
                            'update-columns',
                            (lambda sender: self.tableview.setup_columns())),
            Signals.connect(dataset,
                            'changed',
                            (lambda sender: self.tableview.queue_draw()))
            ]

        # TODO: set metadata widget       
            
        self._dataset = dataset
            
    def get_dataset(self):
        return self._dataset
    dataset = property(get_dataset,set_dataset)

    #--- Callbacks ---------------------------------------------------------

    def cb_insert_row(self, widget):
        model = self.tableview.get_model()
        if model is None:
            return

        # get_selected_rows returns a tuple (model, pathlist).
        # If there is no selection, None is returned as model,
        # which is not what we want. Therefore we will only use [1],
        # the pathlist.
        pathlist = self.tableview.get_selection().get_selected_rows()[1]
        if len(pathlist) == 0:
            path = (0,)
        elif len(pathlist) == 1:
            path = pathlist[0]
        else:
            logger.error("You may not have more than one row selected.")
            return

        # TODO: undo selection ?
        logger.debug( "INSERTING ROW %s ", str(model))

        ul = UndoList().describe("Insert row")
        model.insert_row(path, undolist=ul)
        self._dataset.notify_change(undolist=ul)
        self.project.journal.add_undo(ul)


    def cb_append_row(self, widget):
        model = self.tableview.get_model()
        if model is None:
            return

        # see the comment in cb_insert_row about get_selected_rows
        selection = self.tableview.get_selection()
        pathlist = selection.get_selected_rows()[1]
        if len(pathlist) == 0:
            path = (0,)
        elif len(pathlist) == 1:
            path = pathlist[0]
        else:
            logger.error("You may not have more than one row selected.")
            return

        # TODO: undo selection ?
        ul = UndoList().describe("Append row")
        path = (path[0]+1,)
        model.insert_row(path, undolist=ul)
        self._dataset.notify_change(undolist=ul)
        self.project.journal.add_undo(ul)

        selection.unselect_all()
        selection.select_path(path)
        

    def cb_remove_row(self, widget):
        model = self.tableview.get_model()
        if model is None:
            return

        # see the comment in cb_insert_row about get_selected_rows
        selection = self.tableview.get_selection()
        pathlist = selection.get_selected_rows()[1]
        if len(pathlist) > 0:
            ul = UndoList().describe("Remove rows")
            
            first_path = (max(pathlist[0][0],0),)

            model.delete_rows(pathlist, undolist=ul)
            self._dataset.notify_change(undolist=ul)
            
            selection.unselect_all()
            selection.select_path(first_path)        

            self.project.journal.append(ul)



    def cb_tableview_button_press_event(self, treeview, event):
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            time = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo != None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor( path, col, 0)

                # The following information is stored in self.popup_info
                #   (rownr, colnr, column object)
                # so that a callback called by the popup can determine
                # the current row and column.

                # Note that we don't open up a popup menu for the first
                # column which contains the row numbers.
                colnr = self.tableview.get_column_index(col)
                if colnr >= 0:
                    self.popup_info = (path[0], colnr, col)
                    self.popup.popup( None, None, None, event.button, time)
            return 1


    def cb_column_calculate(self, action):
        rownr, colnr, column_object = self.popup_info        
        table = self.dataset.get_data()

        cc = ColumnCalculator(self.app, self.dataset, colnr)        
        cc.show()

    def cb_column_insert(self, action):
        rownr, colnr, column_object = self.popup_info
        table = self.dataset.get_data()
        column = table.new_column('d')
        self.insert_column(table, colnr, column, undolist=self.project.journal)

    def cb_column_insert_after(self, action):
        rownr, colnr, column_object = self.popup_info
        table = self.dataset.get_data()
        column = table.new_column('d')
        self.insert_column(table, colnr+1, column, undolist=self.project.journal)

    def cb_column_remove(self, action):
        rownr, colnr, column_object = self.popup_info
        table = self.dataset.get_data()
        self.remove_column(table, colnr, undolist=self.project.journal)
    

    def insert_column(self, table, index, column, undolist=[]):
        table.insert(index, column)
        self.dataset.notify_change()
        
        ui = UndoInfo(self.remove_column, table, index).describe("Insert Column")
        undolist.append(ui)

    def remove_column(self, table, index, undolist=[]):
        old_column = table.column(index)
        table.remove_by_index(index)
        self.dataset.notify_change()

        ui = UndoInfo(self.insert_column, table, index, old_column).describe("Remove Column")        
        undolist.append(ui)                                      



    def cb_column_properties(self, action):
        rownr, colnr, column_object = self.popup_info
        table = self.dataset.get_data()

        dialog = ColumnPropertiesDialog(self.app, self, table, colnr)
        try:
            response = dialog.run()
        finally:
            dialog.destroy()
            


    def cb_interpolate(self, action):
        plugin = self.app.get_plugin('pygsl')
        pygsl = plugin.pygsl
        
        table = self.dataset.get_data()
        x, y = table[0], table[1]
        
        steps = table.rowcount * 3
        start, end = x[0], x[-1]
        stepwidth = (end - start) / steps
        new_x = Numeric.arange(start=start, stop=end+stepwidth, step=stepwidth)

        new_table = Table(rowcount=steps, colcount=2,
                          typecodes=[table.get_typecode(0),
                                     table.get_typecode(1)])

        sp = pygsl.spline.cspline(table.rowcount)
        sp.init(x, y)

        iter = new_table.row(0)
        for xi in new_x:
            iter.set( (xi, sp.eval(xi)) )
            try:
                iter = iter.next()
            except StopIteration:
                print "Iteration stopped"
            
        # set new Dataset
        self.project.datasets.append( Dataset(key="Niklas", data=new_table) )
        Signals.emit(self.project.datasets, "changed")        
        
        

class ColumnCalculator(gtk.Window):

    """
    An experimental tool window to calculate columns according to some expression.
    """

    def __init__(self, app, dataset, colnr):
        self.app = app
        self.dataset = dataset
        self.colnr = colnr
        
        gtk.Window.__init__(self)
        self.set_title("Cool Column Calculator")
        self.set_size_request(width=-1, height=200)

        vbox = gtk.VBox()

        self.label = gtk.Label("col(%d) = " % self.colnr)
        self.label.show()
        
        self.textview = gtk.TextView()
        self.textview.show()
        self.scrolled_window = uihelper.add_scrollbars(self.textview)
        self.scrolled_window.show()

        btn1 = gtk.Button(stock=gtk.STOCK_APPLY)
        btn1.connect('clicked', (lambda sender: self.evaluate()))
        btn1.show()

        btn2 = gtk.Button(stock=gtk.STOCK_CLOSE)
        btn2.connect('clicked', (lambda sender: self.destroy()))
        btn2.show()
        
        self.btnbox = gtk.HButtonBox()
        self.btnbox.pack_end(btn2)
        self.btnbox.pack_end(btn1)
        self.btnbox.show()

        vbox.pack_start(self.label, False)
        vbox.pack_start(self.scrolled_window, True, True)
        vbox.pack_end(self.btnbox, False)
        self.add(vbox)
        vbox.show()

    def evaluate(self):
        table = self.dataset.get_data() # TODO: type checking

        # sample expression
        #eval('col(0) = col(0) + 10')
        def col(nr):
            return table[nr].copy()

        buffer = self.textview.get_buffer()
        start, end = buffer.get_bounds()
        expression = buffer.get_text(start, end)        
    
        result = eval(expression,
                      {'__builtins__': {},
                       'sin': Numeric.sin},
                      {'col' : col,
                       'cc' : self.colnr
                       }
                      )

        # If the result is not an array, then it is probably a scalar.
        # We create an array from this by multiplying it with an array
        # that consists only of ones.
        if not isinstance(result, Numeric.ArrayType):
            o = Numeric.ones( (table.rowcount,), table[self.colnr].typecode() )
            result = o * result
            print "-- result is not an array --"
            print "==> converted to array"
            
        ul = UndoList().describe("Calculate column")
        try:
            def set_column_data(column, data, undolist=[]):
                old_data = column.data
                column.data = data
                undolist.append(UndoInfo(set_column_data, column, old_data))

            set_column_data(table.column(self.colnr), result, undolist=ul)

        except TypeError:
            print "-- incompatible result --", result
            return
        self.dataset.notify_change(undolist=ul)
        self.app.project.journal.add_undo(ul)



class ColumnPropertiesDialog(gtk.Dialog):

    def __init__(self, app, parent, table, colnr):

        gtk.Dialog.__init__(self, "Column Properties", parent,
                            gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        self.app = app
        self.table = table
        self.colnr = colnr
        self.pwdict = dict()
        
        pwlist = list()
        column = self.table.column(self.colnr)
        keys = ['key', 'designation', 'label']
        for key in keys:
            pw = propwidgets.construct_pw(column, key)
            self.pwdict[key] = pw
            pwlist.append(pw)

        self.tablewidget = propwidgets.construct_pw_table(pwlist)

        frame = gtk.Frame('Edit Column')
        frame.add(self.tablewidget)
        frame.show()

        self.vbox.pack_start(frame, False, True)
        self.tablewidget.show()
                    
        
    def check_in(self):
        for pw in self.pwdict.itervalues():
            pw.check_in()

    def check_out(self):
        ul = UndoList().describe("Set Column Properties")
        for pw in self.pwdict.itervalues():
            pw.check_out(undolist=ul)

        uwrap.emit_last(self.table, 'update-columns', undolist=ul)

        self.app.project.journal.add_undo(ul)
            

    def run(self):
        self.check_in()
        response = gtk.Dialog.run(self)
        if response == gtk.RESPONSE_ACCEPT:
            self.check_out()
        return response

        
        
        
