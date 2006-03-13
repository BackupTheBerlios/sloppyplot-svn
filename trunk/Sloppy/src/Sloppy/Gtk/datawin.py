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


import gtk, numpy

from Sloppy.Base.dataset import Dataset, Table
from Sloppy.Base import uwrap, globals, utils, error
from Sloppy.Lib.Undo import UndoList, UndoInfo

from Sloppy.Gtk.options_dialog import OptionsDialog
from Sloppy.Gtk import uihelper, checkwidgets, dataview

import logging
logger = logging.getLogger('Gtk.datawin')
#------------------------------------------------------------------------------

class ColumnInfoDialog(gtk.Dialog):

    """ Edit the info object and the name of a column.

    You must specify the info object 'col_info', the column name
    'col_name' and a list of names that are already in use 'used_names'.
    The dialog rejects any name that is already in this list, unless
    it is the initially proposed name 'col_name'.

    The run() method returns gtk.RESPONSE_ACCEPT or gtk.RESPONSE_REJECT
    as one expects from a gtk Dialog.

    The info can be checked out using the 'check_out' method. The
    entered name can be retrieved using the attribute 'new_name'.    
    """

    def __init__(self, col_info, col_name, used_names):
        gtk.Dialog.__init__(self, "Edit Column",None,
                            gtk.DIALOG_MODAL,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        # TODO: It would be nicer to have all entries arranged in
        # TODO: one table. A nice implementation would be similar
        # TODO: to the one in CRendererFactory, defining dummy
        # TODO: pseudo keys in the factory and then filling this
        # TODO: entry on our own.
        
        self.col_info = col_info
        self.col_name = col_name
        self.used_names = used_names

        self.new_name = None # result

        name_label = gtk.Label("Name:")
        name_entry = gtk.Entry()
        name_entry.set_text(unicode(col_name))
        name_entry.set_activates_default(True)
        name_box = gtk.HBox()
        name_box.pack_start(name_label,False,True)
        name_box.pack_start(name_entry,True,True)

        hint = gtk.Label()

        factory = checkwidgets.DisplayFactory(col_info)
        factory.add_keys('label', 'designation')
        table = factory.create_table()
        factory.check_in(col_info)

        vbox = gtk.VBox()
        vbox.pack_start(name_box, True, True)
        vbox.pack_start(hint, False, True)
#        self.vbox.pack_start(gtk.HSeparator(), False, True)
        vbox.pack_start(table, True, True)
        frame = uihelper.new_section('Edit Column Information', vbox)
        
        self.vbox.add(frame)
        self.vbox.show_all()

        self.name_entry = name_entry
        self.factory = factory
        self.hint = hint
        

    def run(self):
        while True:
            response = gtk.Dialog.run(self)
            if response == gtk.RESPONSE_ACCEPT:
                # check column name
                new_name = self.name_entry.get_text()
                if len(new_name) == 0:
                    continue                    

                if new_name != self.col_name and new_name in self.used_names:
                    self.hint.set_markup("<b>Sorry, this name is already in use!\nPlease choose another one.</b>")
                    continue

                self.new_name = new_name
                return response             
            else:
                return response


    def check_out(self, undolist=[]):
        self.factory.check_out(undolist=undolist)
        

#------------------------------------------------------------------------------
class ColumnView(gtk.TreeView):

    """ TreeView that displays infos and names of a given Table.

    Actually, copies of the info objects are displayed. This is
    a helper class for the EditStructureDialog.
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
        # model := (field key, Table.Info, old_key)
        model = gtk.ListStore(str, object, str)
        self.set_model(model)

    def get_columns(self):
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
        dtype = self.dataset._array.dtype
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
                transferdict[key] = self.dataset.get_column(old_key)
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



#------------------------------------------------------------------------------
class EditStructureDialog(gtk.Dialog):

    """ Modify the structure of a Table, i.e. all its infos and field names.

    The dialog displays a treeview with all column infos and names
    along with a buttonbox that enables the user to add/remove/edit entries,
    as well as move items up or down.

    The infos are not modified directly, but rather copies of them; the
    caller must invoke 'check_out' if the new infos and names should
    be used.
    """
    
    def __init__(self, dataset, parent=None):

        self.dataset = dataset

        gtk.Dialog.__init__(self, "Edit Structure", parent,
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
                
                
        # cview = column view
        cview = ColumnView(dataset)
        cview.connect( "row-activated", self.on_row_activated )        
        self.cview = cview

        # put cview and btnbox next to each other into a hbox
        hbox = gtk.HBox()
        hbox.set_spacing(5)
        hbox.pack_start(cview, True, True)
        hbox.pack_start(btnbox, False, True)

        self.vbox.add(hbox)
        self.show_all()



    def check_out(self, undolist=[]):
        self.cview.check_out(undolist=undolist)

        
    def run(self):
        self.cview.check_in()
        return gtk.Dialog.run(self)


    #----------------------------------------------------------------------
    # BUTTON CALLBACKS
        
    def on_row_activated(self, treeview, *udata):
        model, pathlist = self.cview.get_selection().get_selected_rows()
        if model is None:
            return
        iter = model.get_iter(pathlist[0])
        name = model.get_value(iter, 0)
        info = model.get_value(iter, 1)

        fields = self.cview.get_columns()
        del fields[name]

        dialog = ColumnInfoDialog(info, name, fields)            
        try:
            response = dialog.run()
            if response == gtk.RESPONSE_ACCEPT:
                dialog.check_out()
                model[iter][0] = dialog.new_name                
        finally:
            dialog.destroy()
            
        self.cview.grab_focus()


    def on_btn_move_clicked(self, button, direction):
        (model, pathlist) = self.cview.get_selection().get_selected_rows()
        if model is None:
            return

        new_row = max(0, pathlist[0][0] + direction)
        iter = model.get_iter(pathlist[0])        
        second_iter = model.iter_nth_child(None, new_row)

        if second_iter is not None:
            model.swap(iter, second_iter)
            self.cview.grab_focus()
        

    def on_btn_add_clicked(self, button):        
        selection = self.cview.get_selection()
        (model, iter) = selection.get_selected()
        
        new_info = Table.Info()
        fields = self.cview.get_columns()        
        new_key = utils.unique_names(['new_column'], fields)[0]
        iter = model.insert_after(iter, (new_key, new_info, None))
        selection.select_iter(iter)
        
        self.cview.grab_focus()


    def on_btn_remove_clicked(self, button):        
        selection = self.cview.get_selection()
        (model, iter) = selection.get_selected()
        if iter is None:
            return

        new_iter = model.iter_next(iter)
        model.remove(iter)

        if new_iter is not None:
            selection.select_iter(new_iter)
        
        self.cview.grab_focus()        



#------------------------------------------------------------------------------
class DatasetWindow( gtk.Window ):

    """ High-level window for the manipulation of a Dataset. """

    actions = [
        ('DatasetMenu', None, '_Dataset'),
        ('EditInfos', gtk.STOCK_EDIT, 'Edit Structure...', '<control>E', '', 'on_action_EditInfos'),        
        ('Close', gtk.STOCK_CLOSE, 'Close This Window', 'q', 'Close this window.', '_cb_close'),       
        #
        ('ColumnMenu', None, '_Columns'),
        ('RowMenu', None, '_Rows'),
        #
        ('RowInsert', gtk.STOCK_ADD, 'Insert New Row', None, 'Insert a new row before the current position', 'on_action_RowInsert'),
        ('RowAppend', gtk.STOCK_ADD, 'Append New Row', 'Insert', 'Insert a new row after the current position', 'on_action_RowAppend'),
        ('RowRemove', gtk.STOCK_REMOVE, 'Remove Selected Row(s)', 'Delete', 'Remove row at the current position', 'on_action_RowRemove'),
        #
        ('ColumnInfo', None, 'Edit Column...', None, 'Edit column properties...', 'on_action_ColumnInfo'),
        ('ColumnCalculator', None, 'Calculate Column Values...', None, 'Calculate column data...', 'on_action_ColumnCalculator'),
        ('ColumnInsert', None, 'Insert New Column', None, 'Insert column just before this one', 'on_action_ColumnInsert'),
        ('ColumnAppend', None, 'Append New Column', '<shift>Insert', 'Insert column after this one', 'on_action_ColumnAppend'),
        ('ColumnRemove', None, 'Remove Selected Column', '<shift>Delete', 'Remove this column', 'on_action_ColumnRemove'),
        #
        ('DesignationMenu', None, 'Set Designation'),
        ('DesignationX', None, 'X', None, None, 'on_action_DesignationX'),
        ('DesignationY', None, 'Y', None, None, 'on_action_DesignationY'),
        ('DesignationXErr', None, 'XErr', None, None, 'on_action_DesignationXErr'),
        ('DesignationYErr', None, 'XErr', None, None, 'on_action_DesignationYErr'),
        ('DesignationLabel', None, 'Label', None, None, 'on_action_DesignationLabel'),
        ('DesignationDisregard', None, 'Disregard', None, None, 'on_action_DesignationDisregard'),        
        #
        ('AnalysisMenu', None, '_Analysis')
        ]
        
    def __init__(self, project, dataset=None):
        gtk.Window.__init__(self)
	self.set_size_request(280,320)
        self.set_transient_for(globals.app.window)
        
        self.cblist = []

        # GUI elements
        self.ui = globals.app.get_uistring('datawin')
        self.uimanager = self._construct_uimanager()

        self.menubar = self.uimanager.get_widget('/MainMenu')

        self.toolbar = self.uimanager.get_widget('/Toolbar')
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)

        self.popup = self.uimanager.get_widget('/popup_column')

        self.statusbar = gtk.Statusbar()
        self.statusbar.set_has_resize_grip(True)        

        self.dataview = self._construct_dataview()
        sw = uihelper.add_scrollbars(self.dataview)
                
        hpaned = gtk.HPaned()
        hpaned.pack1( sw )
#        hpaned.pack2( self._construct_metadata_widget() )
        self.hpaned = hpaned
        
        vbox = gtk.VBox()

        vbox.pack_start( self.menubar, expand=False, fill=True )
        # toolbar disabled right now -- it clutters and is not so useful
#        vbox.pack_start( self.toolbar, expand=False, fill=True )
        vbox.pack_start( self.hpaned, expand=True, fill=True )
        vbox.pack_start( self.statusbar, expand=False, fill=True )

        self.add(vbox)

        self.project = project  # immutable
        self._dataset = None

        self.set_dataset(dataset)        
        self.project.sig_connect("close", (lambda sender: self.destroy()))

        self.dataview.emit('cursor_changed')

        self.show_all()

        
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
       

    def _construct_dataview(self):        
        view = dataview.DatasetView()
        view.connect('button-press-event', self.cb_view_button_press_event)
        contextid = self.statusbar.get_context_id("coordinates")
        view.connect('cursor-changed', self.on_cursor_changed, contextid)
        view.connect('column-clicked', self.on_column_clicked)
        view.connect('popup-menu', self.popup_menu, 3, 0)
        return view

    def _construct_metadata_widget(self):
        widget = gtk.Label('metadata')
        return widget


    
    #----------------------------------------------------------------------
    # Dataset Handling
    #
    
    def set_dataset(self, dataset):

        if dataset is None:
            self.set_title("(no dataset)")
        else:
            self.set_title("DS: %s" % dataset.key)
            # TODO: this is not the correct place for this
            dataset.get_array()

        self.dataview.set_dataset(dataset)

        for cb in self.cblist:
            cb.disconnect()
        self.cblist = []

        self.cblist += [
            # disable this for now
            #dataset.sig_connect('notify',
            #                (lambda sender,*changeset: self.dataview.queue_draw())),
            dataset.sig_connect('closed', (lambda sender: self.destroy()))
            ]

        self._dataset = dataset
            
    def get_dataset(self):
        return self._dataset
    dataset = property(get_dataset,set_dataset)


    #----------------------------------------------------------------------
    # Callbacks
    #

    def on_action_RowInsert(self, widget, offset=0):
        model, pathlist = self.dataview.get_selection().get_selected_rows()
        if len(pathlist) == 0:
            if offset == 0: pathlist = [(0,)]
            else: pathlist = [(max(self.dataset.nrows-1,0),)]
            model = self.dataview.get_model()
            
        model.insert_rows_by_path(pathlist, offset=offset, undolist=self.project.journal)

        new_path = (pathlist[0][0]+offset,)
        selection = self.dataview.get_selection()
        selection.unselect_all()
        selection.select_path(new_path)
        self.dataview.set_cursor(new_path)
               
    def on_action_RowAppend(self, widget):
        self.on_action_RowInsert(widget, offset=1)
        
    def on_action_RowRemove(self, widget):
        model, pathlist = self.dataview.get_selection().get_selected_rows()
        if len(pathlist) > 0:
            model.remove_rows_by_path(pathlist, undolist=self.project.journal)
            selection = self.dataview.get_selection()
            selection.unselect_all()
            selection.select_path(pathlist[0])

    def on_action_ColumnInsert(self, action, offset=0):
        path, column = self.dataview.get_cursor()        
        if column is None:
            if offset==0: colnr=0
            else: colnr=max(self.dataset.ncols-1,0)
        else:            
            colnr = self.dataview.get_columns().index(column)
        
        ul = UndoList().describe("Insert column")
        self.dataset.insert_columns(colnr+offset, 1, undolist=ul)
        self.project.journal.append(ul)

        if path is not None:
            new_column = self.dataview.get_columns()[colnr+offset]
            self.dataview.set_cursor_on_cell(path, new_column) # start_editing=True
        
    def on_action_ColumnAppend(self, action):
        self.on_action_ColumnInsert(action, offset=1)

    def on_action_ColumnRemove(self, action):
        path, column = self.dataview.get_cursor()
        if column is None:
            return
        else:            
            colnr = self.dataview.get_columns().index(column)

        ul = UndoList().describe("Remove column")
        self.dataset.remove_n_columns(colnr, 1, undolist=ul)
        self.project.journal.append(ul)

    def on_action_ColumnInfo(self, action):
        path, column = self.dataview.get_cursor()
        if column is None:
            return
        else:            
            colnr = self.dataview.get_columns().index(column)

        self.edit_column_info(colnr)


    def on_action_ColumnCalculator(self, action):
        # get column
        path, column = self.dataview.get_cursor()
        if column is None:
            return
        else:            
            colnr = self.dataview.get_columns().index(column)

        cc = ColumnCalculator(self.project, self.dataset, colnr)



    def on_action_EditInfos(self, action):
        dialog = EditStructureDialog(self.dataset)
        try:
            response = dialog.run()
            if response == gtk.RESPONSE_ACCEPT:
                ul = UndoList().describe("Update Fields")
                dialog.check_out(undolist=ul)
                self.project.journal.append(ul)
        finally:
            dialog.destroy()
    
    def on_action_DesignationX(self, action): self.set_designation('X')
    def on_action_DesignationY(self, action): self.set_designation('Y')
    def on_action_DesignationXErr(self, action): self.set_designation('XERR')
    def on_action_DesignationYErr(self, action): self.set_designation('YERR')
    def on_action_DesignationLabel(self, action): self.set_designation('LABEL')
    def on_action_DesignationDisregard(self, action): self.set_designation(None)


    #-- END ACTIONS -------------------------------------------------------

    def on_column_clicked(self, dataview, tvcolumn):
        columns = dataview.get_columns()
        colnr = columns.index(tvcolumn)
        self.edit_column_info(colnr)

    def on_cursor_changed(self, dataview, contextid):
        total_rows = self.dataview.get_model().dataset.nrows
        path, column = dataview.get_cursor()
        if path is not None:
            row = str(path[0]+1)            
            msg = 'row %s of %s' % (row, total_rows)            
        else:
            msg = '%s rows' % total_rows


        self.statusbar.pop(contextid)        
        self.statusbar.push (contextid, msg)

    def edit_column_info(self, colnr):
        self._edit_column_info(colnr)
            
    def _edit_column_info(self, colnr):
        info = self.dataset.get_info(colnr)                        
        name = self.dataset.get_name(colnr)            
        names = self.dataset.names

        dlg = ColumnInfoDialog(info, name, names)
        try:
            response = dlg.run()
            if response == gtk.RESPONSE_ACCEPT:
                # check out
                ul = UndoList("edit column info")
                dlg.check_out(undolist=ul)
                self.dataset.rename_column(colnr, dlg.new_name, undolist=ul)
                uwrap.emit_last(self.dataset, 'update-fields', undolist=ul)
                self.project.journal.append(ul)                
        finally:
            dlg.destroy()
            
    

    def cb_view_button_press_event(self, widget, event):
        # constant editing turned off right now
        if False is True and event.button == 1:
            try:
                path, col, cellx, celly = widget.get_path_at_pos(int(event.x), int(event.y))
            except TypeError:
                return False

            widget.set_cursor(path, col, start_editing=True)
            widget.grab_focus()
            
        if event.button != 3:
            return False

        # RMB has been clicked -> popup menu

        # Different cases are possible        
        # - The user has not yet selected anything.  In this case, we
        # select the row on which the cursor resides.        
        # - The user has made a selection.  In this case, we will
        # leave it as it is.
        
        time = event.time
        try:
            path, col, cellx, celly = widget.get_path_at_pos(int(event.x), int(event.y))
        except TypeError:
            # => user clicked on empty space -> offer some other popup
            print "EMPTY?"
            pass
        else:
            # If user clicked on a row, then select it.
            selection = widget.get_selection()
            if selection.count_selected_rows() == 0:              
                widget.grab_focus()
                widget.set_cursor(path, col, 0)
            
        return self.popup_menu(widget, event.button, event.time)


    def popup_menu(self, widget, button, time):
        " Returns True if a popup has been popped up. "

        model, pathlist = widget.get_selection().get_selected_rows()
        rowcount = len(pathlist)
        if rowcount == 0:
            popup = None # TODO: popup if nothing was selected
        else:
            popup = self.popup           
            
        if popup is not None:
            popup.popup(None,None,None,button,time)
            return True
        else:
            return False

    def set_designation(self, d):
        path, column = self.dataview.get_cursor()
        if column is None:
            return
        else:            
            colnr = self.dataview.get_columns().index(column)
        
        info = self.dataset.get_info(colnr)
        ul = UndoList().describe("Change designation")        
        uwrap.set(info, designation=d, undolist=ul)
        uwrap.emit_last(self.dataset, 'update-fields', undolist=ul)
        self.project.journal.append(ul)

        

class ColumnCalculator(gtk.Window):

    """ An experimental tool window to calculate columns according to
    some expression.  """

    def __init__(self, project, dataset, colnr):
        gtk.Window.__init__(self)
        self.set_title("Cool Column Calculator")
        self.set_size_request(width=-1, height=200)
        
        self.project = project
        self.dataset = dataset
        self.colnr = colnr    

        vbox = gtk.VBox()

        self.label = gtk.Label("col(%d) = " % self.colnr)       

        self.textview = gtk.TextView()
        self.scrolled_window = uihelper.add_scrollbars(self.textview)

        btn1 = gtk.Button(stock=gtk.STOCK_APPLY)
        btn1.connect('clicked', self.on_apply)
        btn2 = gtk.Button(stock=gtk.STOCK_CLOSE)
        btn2.connect('clicked', (lambda sender: self.destroy()))
        
        self.btnbox = gtk.HButtonBox()
        self.btnbox.pack_end(btn2)
        self.btnbox.pack_end(btn1)

        vbox.pack_start(self.label, False)
        vbox.pack_start(self.scrolled_window, True, True)
        vbox.pack_end(self.btnbox, False)
        self.add(vbox)
        self.show_all()
        

    def on_apply(self, sender):
        ds = self.dataset
        
        # fetch expression from textview
        buffer = self.textview.get_buffer()
        start, end = buffer.get_bounds()
        expression = buffer.get_text(start, end)

        local_vars = {'cc': self.colnr}
        result = self.evaluate(ds, expression, local_vars)

        # copy new value to the column
        ds.set_column(self.colnr, result, undolist=self.project.journal)


        
    def evaluate(self, ds, expression, local_vars={}):

        """ Evaluate the entered expression and return the result.

        Examples:

        >>> evaluate('col(0) + 10')
        >>> evaluate('col(0) + col('f2')')
        >>> evaluate('sinus(col(0))', {'sinus': numpy.sin})
        """        

        # if we really wanted to avoid any value setting on the
        # right side of the equation, then we need to copy the
        # column: ds.get_column(nr).copy.
        # But this of course means some overhead, so I avoid it
        # right now and wait for complaints.
        def col(nr):
            return ds.get_column(nr)

        # evaluate expression
        _globals = {'__builtins__': {},
                    'sin': numpy.sin, 'cos': numpy.cos, 'tan': numpy.tan,
                    'pi': numpy.pi}
        _locals = {'col': col}
        _locals.update(local_vars)
        result = eval(expression, _globals, _locals)

        # If the result is not an array, then it is probably a scalar.
        # We create an array from this by multiplying it with an array
        # that consists only of ones.
        if not isinstance(result, numpy.ndarray):
            if numpy.isscalar(result):           
                o = numpy.ones((ds.nrows,), ds.get_column_dtype(self.colnr))
                return  o * result
            else:
                logger.error("result has unknown type %s" % type(result))
                return

        return result
