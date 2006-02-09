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
from Sloppy.Gtk import uihelper

from Sloppy.Lib.Props.main import PropertyError

import logging
logger = logging.getLogger('Gtk.treeview')
#------------------------------------------------------------------------------


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
        gtk.TreeView.__init__( self )
        self.set_headers_visible( True )
        self.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

        self.set_size_request(width=200, height=200)

        # init everything
        self.init_model()
        self.init_view_columns()
        self.init_dragndrop()
        
        # set_project will fill the treeview with contents
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
        if project is not None:
            self.set_property('sensitive',True)
        else:
            self.set_property('sensitive',False)
            
        self.project = project
        self.populate_treeview()

        # connect notify signals with update mechanism
        if self.project is not None:
            def on_notify(self, sender):
                self.populate_treeview()
            project.sig_connect("notify::datasets", self.on_notify)
            project.sig_connect("notify::plots", self.on_notify)


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
