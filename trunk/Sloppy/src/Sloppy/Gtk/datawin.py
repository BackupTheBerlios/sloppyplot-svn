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

# $HeadURL: svn+ssh://niklasv@svn.berlios.de/svnroot/repos/sloppyplot/trunk/Sloppy/src/Sloppy/Gtk/tablewin.py $
# $Id: tablewin.py 457 2006-01-19 20:45:02Z niklasv $


import pygtk # TBR
pygtk.require('2.0') # TBR

from Sloppy.Base.dataset import Dataset, FieldInfo
from Sloppy.Base import uwrap
from Sloppy.Lib.Undo import UndoList, UndoInfo

import numpy

from dataview import DatasetView

from options_dialog import OptionsDialog
import gtk, uihelper, widget_factory


def unique_key(adict, key):

    """    
    Return a valid key that is not yet in use in the dict based on the
    proposal. 
    """
    
    suggestion = key
    counter = 1
    while adict.has_key(suggestion):
        suggestion = "%s_%02d" % (key, counter)
        counter += 1        
    return suggestion


#------------------------------------------------------------------------------
import logging
logger = logging.getLogger('Gtk.datawin')


class DatasetWindow( gtk.Window ):    

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
        ('EditFields', gtk.STOCK_EDIT, 'Edit Fields', '<control>E', '', 'cb_edit_fields'),
        #
        ('AnalysisMenu', None, '_Analysis'),
        ('Interpolate', None, 'Interpolate data (EXPERIMENTAL)', None, 'Interpolate data (EXPERIMENTAL)', 'cb_interpolate')
        ]
         
    ui = """
         <ui>
           <menubar name='MainMenu'>
             <menu action='DatasetMenu'>
               <menuitem action='EditFields'/>
               <separator/>
               <menuitem action='Close'/>
             </menu>
             <menu action='AnalysisMenu'>
               <menuitem action='Interpolate'/>
             </menu>
           </menubar>              
           <toolbar name='Toolbar'>
             <toolitem action='EditColumns'/>           
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
        
        self.cblist = []

        self.uimanager = self._construct_uimanager()
        self.menubar = self._construct_menubar()
        self.toolbar = self._construct_toolbar()
        self.popup = self.uimanager.get_widget('/popup_column')
        self.popup_info = None # needed for popup
        self.statusbar = self._construct_statusbar()

        self.dataview = self._construct_dataview()
        sw = uihelper.add_scrollbars(self.dataview)
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
        vbox.pack_start( self.statusbar, expand=False, fill=True )

        vbox.show()
        self.add(vbox)

        self.project = project  # immutable
        self._dataset = None

        self.set_dataset(dataset)        
        self.project.sig_connect("close", (lambda sender: self.destroy()))

        self.dataview.emit('cursor_changed')                

        
    def _cb_close(self, action):
        self.destroy()

    #----------------------------------------------------------------------
    # GUI Construction
    #
    
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
        

    def _construct_dataview(self):        
        dataview = DatasetView(self.app)
        dataview.connect('button-press-event', self.cb_dataview_button_press_event)
        contextid = self.statusbar.get_context_id("coordinates")
        dataview.connect('cursor-changed', self.on_cursor_changed, contextid)
        dataview.connect('column-clicked', self.on_column_clicked)
        dataview.show()
        return dataview

    def _construct_metadata_widget(self):
        widget = gtk.Label('metadata')
        widget.show()
        return widget


    def _construct_statusbar(self):
        statusbar = gtk.Statusbar()
        statusbar.set_has_resize_grip(True)        
        statusbar.show()
        return statusbar

    
    #----------------------------------------------------------------------
    # Dataset Handling
    #
    
    def set_dataset(self, dataset):

        if dataset is None:
            self.set_title("(no dataset)")
        else:
            self.set_title("DS: %s" % dataset.key)

        self.dataview.set_dataset(dataset)

        for cb in self.cblist:
            cb.disconnect()
        self.cblist = []

        self.cblist += [
            dataset.sig_connect('update-fields',
                            (lambda sender: self.dataview.setup_columns())),
            dataset.sig_connect('notify',
                            (lambda sender,*changeset: self.dataview.queue_draw())),
            dataset.sig_connect('closed',
                                (lambda sender: self.destroy()))
            
            ]

        # TODO: set metadata widget       
        print
        print "========== METADATA =========="
        print dataset.node_info.metadata
        print
        
        self._dataset = dataset
            
    def get_dataset(self):
        return self._dataset
    dataset = property(get_dataset,set_dataset)


    #----------------------------------------------------------------------
    # Callbacks
    #

    def on_column_clicked(self, dataview, tvcolumn):
        print "CLICK!"
        
    def cb_insert_row(self, widget):
        model = self.dataview.get_model()
        if model is None:
            return

        # get_selected_rows returns a tuple (model, pathlist).
        # If there is no selection, None is returned as model,
        # which is not what we want. Therefore we will only use [1],
        # the pathlist.
        pathlist = self.dataview.get_selection().get_selected_rows()[1]
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
        model = self.dataview.get_model()
        if model is None:
            return

        # see the comment in cb_insert_row about get_selected_rows
        selection = self.dataview.get_selection()
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
        model = self.dataview.get_model()
        if model is None:
            return

        # see the comment in cb_insert_row about get_selected_rows
        selection = self.dataview.get_selection()
        pathlist = selection.get_selected_rows()[1]
        if len(pathlist) > 0:
            ul = UndoList().describe("Remove rows")
            
            first_path = (max(pathlist[0][0],0),)

            model.delete_rows(pathlist, undolist=ul)
            self._dataset.notify_change(undolist=ul)
            
            selection.unselect_all()
            selection.select_path(first_path)        

            self.project.journal.append(ul)



    def cb_dataview_button_press_event(self, treeview, event):
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
                colnr = self.dataview.get_column_index(col)
                if colnr >= 0:
                    self.popup_info = (path[0], colnr, col)
                    self.popup.popup( None, None, None, event.button, time)
            return 1


    def cb_column_calculate(self, action):
        # TODO
        pass
        #rownr, colnr, column_object = self.popup_info        
        #table = self.dataset.get_data()
        #cc = ColumnCalculator(self.project, self.dataset, colnr)        
        #cc.show()

    def cb_column_insert(self, action):
        # TODO
        pass
        #rownr, colnr, column_object = self.popup_info
        #table = self.dataset.get_data()
        #column = table.new_column('f')
        #self.insert_column(table, colnr, column, undolist=self.project.journal)

    def cb_column_insert_after(self, action):
        # TODO
        pass
        #rownr, colnr, column_object = self.popup_info
        #table = self.dataset.get_data()
        #column = table.new_column('f')
        #self.insert_column(table, colnr+1, column, undolist=self.project.journal)

    def cb_column_remove(self, action):
        # TODO
        pass
        #rownr, colnr, column_object = self.popup_info
        #table = self.dataset.get_data()
        #self.remove_column(table, colnr, undolist=self.project.journal)
    

    def insert_column(self, table, index, column, undolist=[]):
        # TODO
        pass
        #table.insert(index, column)
        #self.dataset.notify_change()        
        #ui = UndoInfo(self.remove_column, table, index).describe("Insert Column")
        #undolist.append(ui)

    def remove_column(self, table, index, undolist=[]):
        # TODO
        pass
        #old_column = table.column(index)
        #table.remove_by_index(index)
        #self.dataset.notify_change()

        #ui = UndoInfo(self.insert_column, table, index, old_column).describe("Remove Column")        
        #undolist.append(ui)                                      

    def cb_column_properties(self, action):
        # TODO
        return
    
        # column_object = treeview_column
        rownr, colnr, column_object = self.popup_info
        table = self.dataset.get_data()

        column = table.get_column(colnr)
        dialog = OptionsDialog(column.copy())

        try:
            response = dialog.run()
            if response == gtk.RESPONSE_ACCEPT:
                # check out data 
                new_column = dialog.check_out()
                changeset = column.create_changeset(new_column)

                ul = UndoList().describe("Update Fields")
                uwrap.set(column, **changeset)
                uwrap.emit_last(table, 'update-fields', undolist=ul)
                self.project.journal.append(ul)
        finally:
            dialog.destroy()



    def cb_edit_fields(self, action):
        dialog = ModifyDatasetDialog(self.dataset)
        try:
            response = dialog.run()
            if response == gtk.RESPONSE_ACCEPT:
                ul = UndoList().describe("Update Fields")
                dialog.check_out(undolist=ul)
                uwrap.emit_last(self.dataset, 'update-fields', undolist=ul)
                self.project.journal.append(ul)
        finally:
            dialog.destroy()



    def on_cursor_changed(self, dataview, contextid):
        # TODO
        return
    
        total_rows = self.dataview.get_model().table.nrows        
        path, column = dataview.get_cursor()
        if path is not None:
            row = str(path[0]+1)            
            msg = 'row %s of %s' % (row, total_rows)            
        else:
            msg = '%s rows' % total_rows


        self.statusbar.pop(contextid)        
        self.statusbar.push (contextid, msg)


    # JUST FOR TESTING
    def cb_interpolate(self, action):
        # TODO
        return
    
        plugin = self.app.get_plugin('pygsl')
        pygsl = plugin.pygsl
        
        table = self.dataset.get_data()
        x, y = table[0], table[1]
        
        steps = table.nrows * 3
        start, end = x[0], x[-1]
        stepwidth = (end - start) / steps
        new_x = numpy.arange(start=start, stop=end+stepwidth, step=stepwidth)

        new_table = Table(nrows=steps, ncols=2,
                          typecodes=[table.get_typecode(0),
                                     table.get_typecode(1)])

        sp = pygsl.spline.cspline(table.nrows)
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
    
        self.project.sig_emit('notify::datasets')
        
        

class ColumnCalculator(gtk.Window):

    """ An experimental tool window to calculate columns according to
    some expression.  """

    def __init__(self, project, dataset, colnr):
        self.project = project
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
                       'sin': numpy.sin},
                      {'col' : col,
                       'cc' : self.colnr
                       }
                      )

        # If the result is not an array, then it is probably a scalar.
        # We create an array from this by multiplying it with an array
        # that consists only of ones.
        if not isinstance(result, ArrayType):
            o = numpy.ones( (table.nrows,), table[self.colnr].typecode() )
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
        self.project.journal.append(ul)

     



class FieldView(gtk.TreeView):

    """
    fields = dictionary of FieldInfo instances.
    """
    
    def __init__(self, dataset):        
        gtk.TreeView.__init__(self)
        self.set_dataset(dataset)

        # set up first column
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn('key', cell)
        column.set_attributes(cell, text=0)
        self.append_column(column)
        
        # set up other columns
        def add_column(key):
            cell = gtk.CellRendererText()            
            column = gtk.TreeViewColumn(key, cell)
            column.set_cell_data_func(cell, self.render_column_prop, key)
            self.append_column(column)

        for key in ['label', 'designation']:
            add_column(key)


    def set_dataset(self, dataset):
        self.dataset = dataset
        # model := (field key, FieldInfo, old_key)
        model = gtk.ListStore(str, object, str)
        self.set_model(model)

    def get_fields(self):
        " Return list of fields in the treeview. "
        model = self.get_model()
        
        fields = {}
        iter =model.get_iter_first()
        while iter is not None:
            key = model.get_value(iter,0)
            value = model.get_value(iter, 1)
            fields[key] = value
            iter = model.iter_next(iter)
        return fields        

    def check_in(self):
        # create copies of fields (except for the data)
        model = self.get_model()
        model.clear()
        for name in self.dataset.names:
            info = self.dataset.get_info(name)
            model.append( (name, info.copy(), name) )


    def check_out(self, undolist=[]):
        old_infos = self.dataset.infos
        dtype = self.dataset.array.dtype
        old_names = dtype.fields[-1]
        
        model = self.get_model()
        iter = model.get_iter_first()
        n = 0
        
        infos = {}
        names = []
        formats = []
        transferdict = {}
        
        while iter:
            key = model.get_value(iter, 0)
            info = model.get_value(iter, 1)
            old_key = model.get_value(iter, 2)

            if old_key in old_names:
                # field existed before => mark for content transfer
                transferdict[key] = self.dataset.get_field(old_key)
                format = dtype.fields[old_key][0].str
            else:
                format = 'f4' # TODO: let user specify format

            names.append(key)
            formats.append(format)
            infos[key] = info
            
            iter = model.iter_next(iter)

        # instantiate new array from names and formats
        array = numpy.zeros( (self.dataset.nrows,),
                             dtype={'names':names, 'formats':formats})       
        def transfer(dest, adict):
            for key, data in adict.iteritems():
                dest[key] = data            
        transfer(array, transferdict)

        self.dataset.set_array(array, infos, undolist=undolist)
        
        
    def render_column_prop(self, column, cell, model, iter, propkey):
        info = model.get_value(iter, 1)
        cell.set_property('text', info.get_value(propkey) or "")








class ModifyDatasetDialog(gtk.Dialog):

    # This is actually something like a PW.
    # We check in a dataset, keep the copy of the new values in memory
    # and if we like the changes, we check out the new values.
    
    def __init__(self, dataset, parent=None):

        self.dataset = dataset

        gtk.Dialog.__init__(self, "Modify Dataset", parent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.set_size_request(480,300)

        #
        # button box
        #

        buttons = [(gtk.STOCK_EDIT, self.on_row_activated),
                   (gtk.STOCK_NEW, self.on_btn_add_clicked),
                   (gtk.STOCK_REMOVE, self.on_btn_remove_clicked),
                   (gtk.STOCK_GO_UP, self.on_btn_move_clicked, -1),
                   (gtk.STOCK_GO_DOWN, self.on_btn_move_clicked, +1)
                   ]

        btnbox = uihelper.construct_vbuttonbox(buttons)
        btnbox.set_spacing(uihelper.SECTION_SPACING)
        btnbox.set_border_width(uihelper.SECTION_SPACING)
                
                
        # fview = column view
        fview = FieldView(dataset)
        fview.connect( "row-activated", self.on_row_activated )        
        self.fview = fview

        # put fview and btnbox next to each other into a hbox
        hbox = gtk.HBox()
        hbox.set_spacing(5)
        hbox.pack_start(fview, True, True)
        hbox.pack_start(btnbox, False, True)

        self.vbox.add(hbox)
        self.show_all()



    def check_out(self, undolist=[]):
        self.fview.check_out(undolist=undolist)

        
    def run(self):
        self.fview.check_in()
        return gtk.Dialog.run(self)


    #----------------------------------------------------------------------
    # BUTTON CALLBACKS
        
    def on_row_activated(self, treeview, *udata):
        model, pathlist = self.fview.get_selection().get_selected_rows()
        if model is None:
            return
        iter = model.get_iter(pathlist[0])
        name = model.get_value(iter, 0)
        info = model.get_value(iter, 1)

        fields = self.fview.get_fields()
        del fields[name]
        # TODO: insert field for key into OptionsDialog
        
        dialog = OptionsDialog(info)
        try:
            response = dialog.run()
            if response == gtk.RESPONSE_ACCEPT:
                dialog.check_out()                
        finally:
            dialog.destroy()
        self.fview.grab_focus()


    def on_btn_move_clicked(self, button, direction):
        (model, pathlist) = self.fview.get_selection().get_selected_rows()
        if model is None:
            return

        new_row = max(0, pathlist[0][0] + direction)
        iter = model.get_iter(pathlist[0])        
        second_iter = model.iter_nth_child(None, new_row)

        if second_iter is not None:
            model.swap(iter, second_iter)
            self.fview.grab_focus()
        

    def on_btn_add_clicked(self, button):        
        selection = self.fview.get_selection()
        (model, iter) = selection.get_selected()
        
        new_info = FieldInfo()
        fields = self.fview.get_fields()        
        new_key = unique_key(fields, 'new_field')
        iter = model.insert_after(iter, (new_key, new_info, None))
        selection.select_iter(iter)
        
        self.fview.grab_focus()


    def on_btn_remove_clicked(self, button):        
        selection = self.fview.get_selection()
        (model, iter) = selection.get_selected()
        if iter is None:
            return

        new_iter = model.iter_next(iter)
        model.remove(iter)

        if new_iter is not None:
            selection.select_iter(new_iter)
        
        self.fview.grab_focus()        
        


###############################################################################

if __name__ == "__main__":

    win = DatasetWindow
