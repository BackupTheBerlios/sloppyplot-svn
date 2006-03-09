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

import gtk, gobject
import sys, glob, os.path

from Sloppy.Base.objects import *
from Sloppy.Base.dataset import *
from Sloppy.Base import pdict, uwrap, globals
from Sloppy.Gtk import uihelper, uidata
from Sloppy.Gtk.tools import Tool

from Sloppy.Lib.Props.main import PropertyError

import logging
logger = logging.getLogger('Gtk.project_view')
#------------------------------------------------------------------------------


class ProjectView(Tool):

    actions = [
        ('RenameItem', 'sloppy-rename', 'Rename', 'F2', 'Rename', 'action_RenameItem')
        ]

    name = "Project Overview"

    def __init__(self):
        Tool.__init__(self)
        
        # create gui (a treeview in a scrolled window with a
        # buttonbox underneath)
        treeview = ProjectTreeView()
        scrollwindow = uihelper.add_scrollbars(treeview)
        
        buttons = [(gtk.STOCK_ADD, lambda sender: None),
                   (gtk.STOCK_REMOVE, lambda sender: None)]
        buttonbox = uihelper.construct_hbuttonbox(buttons, labels=False)

        self.pack_start(scrollwindow, True, True)
        #self.pack_start(buttonbox, False, True)        
        self.show_all()
        
        self.buttonbox = buttonbox
        self.treeview = treeview
        self.scrollwindow = scrollwindow

        # connect to callbacks
        treeview.connect( "row-activated", self.on_row_activated )
        treeview.connect( "button-press-event", self.on_button_press_event )
        treeview.connect( "popup-menu", self.on_popup_menu, 3, 0 )

        # create actions for ui manager
        uimanager = globals.app.window.uimanager
        uihelper.add_actions(uimanager, "ProjectView", self.actions, self)
        uimanager.add_ui_from_string(uidata.uistring_project_view)
        
##        globals.app.window.add_accel_group(self.uimanager.get_accel_group())


    def action_RenameItem(self, action):
        self.treeview.start_editing_key()

        
    def on_row_activated(self,widget,*udata):
        """
        plot -> plot item
        dataset -> edit dataset
        """
        (plots, datasets) = widget.get_selected_plds()
        for plot in plots:
            globals.app.plot(plot)
        for ds in datasets:
            globals.app.edit_dataset(ds)

        
    def on_button_press_event(self, widget, event):
        " RMB: Pop up a menu if plot is active object. "
        if event.button != 3:
            return False

        # RMB has been clicked -> popup menu

        # Different cases are possible
        # - The user has not yet selected anything.
        #   In this case, we select the row on which the cursor
        #   resides.
        # - The user has made a selection.
        #   In this case, we will leave it as it is.

        # get mouse coords and corresponding path
        x = int(event.x)
        y = int(event.y)
        time = event.time
        try:
            path, col, cellx, celly = widget.get_path_at_pos(x, y)
        except TypeError:
            # => user clicked on empty space -> offer creation of objects
            pass                
        else:
            # If user clicked on a row, then select it.
            selection = widget.get_selection()
            if selection.count_selected_rows() == 0:              
                widget.grab_focus()
                widget.set_cursor( path, col, 0)

        return self.on_popup_menu(widget,event.button,event.time)            
            

    def on_popup_menu(self, widget, button, time):
        " Returns True if a popup has been popped up. "

        uim = globals.app.window.uimanager
        
        # create popup menu according to object type
        objects = widget.get_selected_objects()
        if len(objects) == 0:
            popup = uim.get_widget('/popup_empty')
        else:
            object = objects[0]
            if isinstance(object,Plot):
                popup = uim.get_widget('/popup_plot')
            elif isinstance(object,Dataset):
                popup = uim.get_widget('/popup_dataset')
            else:
                return False

        if popup is not None:
            popup.popup(None,None,None,button,time)
            return True
        else:
            return False






class ProjectTreeView( gtk.TreeView ):

    (MODEL_KEY, MODEL_OBJECT, MODEL_CLASSNAME) = range(3)
    (COLUMN_ALL,) = range(1) 
    (DND_TEXT_URI_LIST,) = range(1)
    
    dnd_targets = [
        #(target name, flags, unique identifier)
        ('text/uri-list',0, DND_TEXT_URI_LIST)
        ]

    # ----------------------------------------------------------------------
    #  Initialization
    # ----------------------------------------------------------------------
    
    def __init__(self, project=None):
       
        # init TreeView
        gtk.TreeView.__init__(self)
        self.set_headers_visible(False)
        self.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

        self.set_size_request(width=200, height=200)

        # init everything
        self.init_model()
        self.init_view_columns()
        self.init_dragndrop()
        
        # keep project current
        self.project = None
        globals.app.sig_connect('update::project',\
          lambda sender, value: self.set_project(value))
        self.set_project(project)
        
        
        
    def init_model(self):
        """        
        Init the TreeView model.        
        """
        model = gtk.TreeStore(str, object, str)
        self.main_model = model
        self.set_model(model)
        
        #filter_toplevel = model.filter_new()
        #filter_toplevel.set_visible_func(self.cb_filter_toplevel)
        #self.set_model( filter_toplevel )

    def init_view_columns(self):
        """
        Create the visible columns and connect them to the render
        functions render_xxx which dynamically create contents from
        the object.           
        """
        # COLUMN_ALL (includes image for classname and key)
        column = gtk.TreeViewColumn('plots and datasets')
        column.set_property('resizable', True)
        
        cell = gtk.CellRendererPixbuf()                        
        column.pack_start(cell,expand=False)
        column.set_attributes(cell, stock_id=self.MODEL_CLASSNAME)

        cell = gtk.CellRendererText()
        column.pack_start(cell,expand=True)
        column.set_attributes(cell, text=self.MODEL_KEY)
        cell.set_property('editable', False)
        cell.connect('edited', self.on_key_edited)        
        self.text_renderer = cell # for reference
        
        self.append_column(column)
                
        
    # ----------------------------------------------------------------------
    
    def populate_treeview(self, sender=None):
        """
        Fill the TreeView with the objects from the given Plot.           
        """
        model = self.main_model
        model.clear()

        if not self.project:
            return

        # add Plots
        def add_plot_object(plots, model, parent=None):            
            for (key, plot) in pdict.iteritems( self.project.plots ):
                iter = model.append(parent, [unicode(key), plot, 'sloppy-%s' % plot.__class__.__name__])
        add_plot_object(self.project.plots, model)
            
        # add Datasets
        for (key, ds) in pdict.iteritems( self.project.datasets ):
            model.append(None, [unicode(key), ds, 'sloppy-%s' % ds.__class__.__name__])

        self.collapse_all()


    def set_project(self, project):
        """
        Assign a project to the TreeView and repopulate the tree.  If
        no project is given, the TreeView will be empty.
        """
        if project == self.project:
            return
        
        # connect update signals with update mechanism
        if project is not None:
            self.set_property('sensitive',True)            
            def on_update(sender, updateinfo):
                self.populate_treeview()
            project.sig_connect("update::datasets", on_update)
            project.sig_connect("update::plots", on_update)
        else:
            self.set_property('sensitive',False)

        self.project = project                    
        self.populate_treeview()



    # ----------------------------------------------------------------------
    # Render Functions
    # ----------------------------------------------------------------------
    
    def render_label(self,column,cell,model,iter):
        """
        Return the description that corresponds to the object
        of the specified row.
        """
        #
        # NOT USED RIGHT NOW. Maybe later again...
        #
        object = model.get_value(iter, self.MODEL_OBJECT)

        label = object.get_option('label')
        if label is None:
            label = "<unnamed %s>" % object.getName()

        # add extra information to label
        if isinstance(object, Plot):
            label += "  (%d)" % len(object.curves)
            
        cell.set_property('text', label)

    def render_type(self,column,cell,model,iter):
        object = model.get_value(iter, self.MODEL_OBJECT)
        classname = object.__class__.__name__
        if classname is None:
            classname = ""
        cell.set_property('text', classname)

    # ----------------------------------------------------------------------
    # Filter
    # ----------------------------------------------------------------------

    # Stub for further development
    def cb_filter_toplevel(self,model,iter):
        """
        Don't allow project item
        """
        #print model.get_value(iter,self.MODEL_CLASSNAME) != 'Project'
        #return model.get_value(iter,self.MODEL_CLASSNAME) != 'Project'
        return True


    # ----------------------------------------------------------------------
    #  object retrieval
    # ----------------------------------------------------------------------

    def get_selected_objects(self):
        " Return the list of currently selected objects. "
        (model, pathlist) = self.get_selection().get_selected_rows()
        return [model.get(model.get_iter(path),self.MODEL_OBJECT)[0] for path in pathlist]

    def get_selected_plds(self):        
        " Returns 2-tuple ([plots], [datasets]). "
        (model, pathlist) = self.get_selection().get_selected_rows()
        objects = [self.get_object_by_path(path) for path in pathlist]
        if len(objects) > 0:
            logger.debug("object[0] = %s" % objects[0])
            plots = [obj for obj in objects if isinstance(obj,Plot)]
            datasets = [obj for obj in objects if isinstance(obj,Dataset)]
            return (plots, datasets)
        else:
            return ([],[])

    def get_selected_datasets(self):        
        (model, pathlist) = self.get_selection().get_selected_rows()
        objects = [self.get_object_by_path(path) for path in pathlist]
        plots = [obj for obj in objects if isinstance(obj,Plot)]
        datasets = [obj for obj in objects if isinstance(obj,Dataset)]
        return datasets

    def get_selected_plots(self):        
        (model, pathlist) = self.get_selection().get_selected_rows()
        objects = [self.get_object_by_path(path) for path in pathlist]
        plots = [obj for obj in objects if isinstance(obj,Plot)]
        return plots
    
    def get_object_by_path(self, path):
        " Return object that corresponds to the given path. "
        model = self.get_model()
        return model.get(model.get_iter(path),self.MODEL_OBJECT)[0]
    
        

    #----------------------------------------------------------------------
    #
    # Key Editing
    #
    
    def start_editing_key(self):        
        selection = self.get_selection()
        if selection is None:
            return
        
        model, pathlist = selection.get_selected_rows()
        if len(pathlist) > 0:
            path = pathlist[0]

            self.text_renderer.set_property('editable', True)
            try:
                self.set_cursor(path, self.get_column(self.COLUMN_ALL), start_editing=True)
            finally:
                self.text_renderer.set_property('editable', False)

        
    def on_key_edited(self, cell, path, new_text):
        """
        When an object key is edited, we need to check whether
        the key is valid. If so, the key is changed.
        """
        model = self.get_model()
        object = model[path][self.MODEL_OBJECT]

        ul = UndoList()

        try:
            if isinstance(object , Dataset):
                self.project.rename_dataset(object, new_text, undolist=ul)
            elif isinstance(object, Plot):
                self.project.rename_plot(object, new_text, undolist=ul)
        except PropertyError, msg:
            globals.app.error_msg(msg)

        if len(ul) > 0:
            self.project.journal.append(ul)        




    #------------------------------------------------------------------------------
    #
    # Drag 'N Drop
    #
    
    def init_dragndrop(self):
        """
        Set up drag 'n drop mechanism.
        """
        self.enable_model_drag_dest(self.dnd_targets, gtk.gdk.ACTION_DEFAULT)
        self.connect("drag_data_received", self.on_drag_data_received)


    def on_drag_data_received(self, sender, context,
                              x, y, selection, info, timestamp):
        """
        React on the drag of data onto the TreeView.

        Currently, only 'text/uri-list' is supported: If is is a
        single file with the extension '.spj', then the project is
        loaded as new project.  In all other cases, we try to import
        the given files.        
        """
        if info == self.DND_TEXT_URI_LIST:
            uri = selection.data.strip()
            uri_splitted = uri.split()

            filenames = []
            for uri in uri_splitted:
                path = uihelper.get_file_path_from_dnd_dropped_uri(uri)
                filenames.append(path)

            logger.debug("Filenames from drag 'n drop:\n%s\n" % filenames)

            try:
                # Check if we have a single file and if this is a sloppy project
                # then load it. Otherwise import the files!
                if len(filenames) == 1 and filenames[0].endswith('.spj'):
                    globals.app.load_project(filenames[0])
                else:
                    globals.app.do_import(self.project, filenames)
            finally:
                context.finish(True,False,timestamp)
        else:
            context.drag_abort(timestamp)
