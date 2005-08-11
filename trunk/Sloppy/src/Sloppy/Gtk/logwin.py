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

# $HeadURL: file:///home/nv/sloppysvn/trunk/Sloppy/src/Sloppy/Gtk/logwin.py $
# $Id: logwin.py 369 2005-06-23 09:15:13Z nv $


"""

This window catches logging messages and displays them in a TreeView.
Features include:

- Save log messages in a file.

- Limit number of logged records.

- Limit logging to a given root, e.g. only to messages from loggers
  beginning with 'gtk'

"""


import os.path
import gtk

import uihelper

import logging
logger = logging.getLogger('logwin')



class CustomHandler(logging.Handler):
    """
    Custom logging handler that passes the logger message on
    to a logwin instance.
    """
    def __init__(self, logwindow):
        logging.Handler.__init__(self)
        self.lw = logwindow

    def emit(self, record):
        self.lw.add_record(record)




class LogWindow(gtk.Window):

    def __init__(self, root='', maxrecords=100, ignore_delete_event=True):
        
        gtk.Window.__init__(self)
        self.set_size_request(width=600, height=400)

        # maximum number of records
        # Can be changed during runtime.
        self.maxrecords = maxrecords

        #
        # construct GUI
        #
        actions = [('SaveAs', gtk.STOCK_SAVE_AS, 'Save Log Messages as...',
                    None, 'Save Log Messages in a file.', 'cb_save_as'),]
                 
        ui = \
        """
        <ui>
          <toolbar name='Toolbar'>
            <toolitem action='SaveAs'/>
          </toolbar>
        </ui>
        """
        self.uimanager = self._construct_uimanager(actions, ui)

        self.toolbar = self._construct_toolbar()
        self.toolbar.show()
        
        self.tv, self.model = self._construct_treeview()
        self.tv.show()

        self.sw = uihelper.add_scrollbars(self.tv)
        self.sw.show()

        vbox = gtk.VBox()
        vbox.pack_start(self.toolbar, expand=False, fill=True)
        vbox.pack_start(self.sw, expand=True, fill=True)
        vbox.show()

        self.add(vbox)


        #
        # add logging handler
        #
        handler = CustomHandler(self)
        l = logging.getLogger(root)
        l.addHandler(handler)
#         def _cb_destroy_event(widget, event, log, hdlr):
#             print "HANDLER"
#             log.removeHandler(hdlr)
#             print "Handler removed"
#         self.connect('destroy_event', _cb_destroy_event, l, handler)
            
            


        # If ignore_delete_event is set, we will add a handler
        # to skip delete-events, i.e. if the user clicks on the
        # close button of his window, the window will only be hidden.
        if ignore_delete_event is True:
            def _cb_delete_event(widget, *args):
                self.hide()
                return True # don't continue deletion
            self.connect('delete_event', _cb_delete_event)



    #--- GUI CONSTRUCTION -------------------------------------------------
    
    def _construct_treeview(self):
        " Returns (treeview, model). "        
        # (level, name, text).
        model = gtk.ListStore(object)

        tv = gtk.TreeView()
        tv.set_model(model)
        tv.get_selection().set_mode(gtk.SELECTION_SINGLE)
        tv.columns_autosize()
        
        def record_column(fieldname):
            column = gtk.TreeViewColumn(fieldname)
            renderer = gtk.CellRendererText()
            column.pack_start(renderer, expand=False)
            column.set_cell_data_func(renderer, self.render_record, fieldname)
            column.set_resizable(True)
            return column

        for fieldname in ['name', 'levelno', 'msg', 'filename', 'module', 'lineno']:
            tv.append_column( record_column(fieldname) )

        return (tv, model)
        

    def _construct_uimanager(self, actions, ui):

        # create actiongroup
        ag = gtk.ActionGroup('main')                    
        ag.add_actions( uihelper.map_actions(actions, self) )

        # add action group to ui manager
        uimanager = gtk.UIManager()
        uimanager.insert_action_group(ag, 0)

        # build ui
        uimanager.add_ui_from_string(ui)
        self.add_accel_group(uimanager.get_accel_group())

        return uimanager


    def _construct_toolbar(self):        
        toolbar = self.uimanager.get_widget('/Toolbar')
        toolbar.set_style(gtk.TOOLBAR_ICONS)
        return toolbar



    #--- RECORD HANDLING --------------------------------------------------

    def add_record(self, record):
        if len(self.model) == self.maxrecords:
            self.model.remove(self.model.get_iter_first())            
        iter = self.model.append( [record] )
        self.tv.get_selection().select_path(self.tv.get_model().get_path(iter))

    def render_record(self, column, cell, model, iter, field):
        record = model.get_value(iter, 0)
        cell.set_property('text', getattr(record, field))

    def cb_save_as(self, action):

        chooser = gtk.FileChooserDialog(
            title = "Save log file",
            action = gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons = (gtk.STOCK_CANCEL,
                       gtk.RESPONSE_CANCEL,
                       gtk.STOCK_SAVE,
                       gtk.RESPONSE_OK) )
        chooser.set_default_response(gtk.RESPONSE_OK)
        chooser.set_current_folder(os.path.abspath(os.path.curdir))
        chooser.set_current_name('sloppyplot.log')
        
        try:
            response = chooser.run()
            if response == gtk.RESPONSE_OK:
                filename = chooser.get_filename()
            else:
                return
        finally:
            chooser.destroy()

        # ask before writing over an exisiting file
        if os.path.exists(filename):
            msg = u"A file with that name already exists.  Are you sure you want to replace that file?"
            dialog = gtk.MessageDialog(None,
                                       gtk.DIALOG_MODAL,
                                       gtk.MESSAGE_QUESTION,
                                       gtk.BUTTONS_OK_CANCEL,
                                       None)
            dialog.set_markup(msg)
            try:
                response = dialog.run()
                if response != gtk.RESPONSE_OK:
                    return
            finally:
                dialog.destroy()
                                       
                        
        # write records to file
        try:
            fd = None
            try:
                fd = open(filename, 'w+')

                model = self.model
                iter = model.get_iter_first()
                while iter is not None:
                    record, = model.get(iter, 0)
                    fd.write("[%2d] %s:%d:%s\n" %
                             (record.levelno,
                              record.module,
                              record.lineno,
                              record.msg) )
                    iter = model.iter_next(iter)

            except IOError, error:
                msg = "Saving log file failed: %s" % str(error)
                logger.error(msg)
        finally:
            fd is not None and fd.close()

        logger.info("Log messages saved.")        




if __name__ == "__main__":
    win = LogWindow(root='main', maxrecords=100, ignore_delete_event=False)
    win.show()

    win.connect("destroy", gtk.main_quit)

    logger = logging.getLogger('gtk')
    logger.warn("This is a warning!")

    logger2 = logging.getLogger('main')
    logger2.info("Information: Everything is o.k.!")
    logger2.warn("Warning: Something might be wrong!")
    

    for i in range(15):
        logger.warn("Automated msg #%d" % i)
    gtk.main()
