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


import pygtk # TBR
pygtk.require('2.0') # TBR

import gtk, gobject
import sys, glob, os.path
import gtkutils

from Sloppy.Base.objects import *
from Sloppy.Base.dataset import *
from Sloppy.Base import pdict, uwrap

from Sloppy.Lib import Signals

#------------------------------------------------------------------------------
import logging
logger = logging.getLogger('Gtk.treeview')



class ProjectTreeView( gtk.TreeView ):

    COL_KEY = 0
    COL_OBJECT = 1
    COL_CLASSNAME = 2
    
    dnd_targets = [
        ('MY_TREE_MODEL_ROW', gtk.TARGET_SAME_WIDGET, 0),
        ('file/uri', 0, 3)
        ]

    # ----------------------------------------------------------------------
    #  Initialization
    # ----------------------------------------------------------------------
    
    def __init__(self, app, project=None):
       
        # init TreeView
        gtk.TreeView.__init__( self )
        self.set_headers_visible( True )
        self.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

        self.set_size_request(width=200, height=200)

        self.app = app
        
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
        column = gtk.TreeViewColumn('plots and datasets')
        pixbuf_renderer = gtk.CellRendererPixbuf()        
        column.pack_start(pixbuf_renderer,expand=False)
        column.set_attributes(pixbuf_renderer, stock_id=self.COL_CLASSNAME)
        text_renderer = gtk.CellRendererText()
        column.pack_start(text_renderer,expand=True)
        column.set_attributes(text_renderer, text=self.COL_KEY)
        column.set_property('resizable', True)
        text_renderer.set_property('editable', False)
        text_renderer.connect('edited', self.cb_edited_key)
        
        self.append_column(column)

        self.text_renderer = text_renderer # for reference
        
    def init_dragndrop(self):
        """
        Set up drag 'n drop mechanism.
        NOT YET IMPLEMENTED. WILL BE USEFUL FOR IMPORTING DATA
        FROM A FILE MANAGER OR EXPORTING IT TO AN EDITOR.
        """
        return # currently disabled

        self.enable_model_drag_dest( self.dnd_targets, gtk.gdk.ACTION_DEFAULT )
        self.connect( "drag_data_received", self.cb_received_drag_data )


    # ----------------------------------------------------------------------
    
    def populate_treeview(self, sender=None):
        """
        Fill the TreeView with the objects from the given Plot.           
        """
        model = self.main_model
        model.clear()

        if not self._project:
            return

	logger.debug("self._project: %s" % self._project)
	
        # add Plots
        def add_plot_object(plots, model, parent=None):            
            for (key, plot) in pdict.iteritems( self._project.plots ):
                iter = model.append(parent, [unicode(key), plot, 'sloppy-%s' % plot.__class__.__name__])
            # TODO ?
            # We might add Layers here
        add_plot_object(self._project.plots, model)
            
        # add Datasets
        for (key, ds) in pdict.iteritems( self._project.datasets ):
            model.append(None, [unicode(key), ds, 'sloppy-%s' % ds.__class__.__name__])

        self.collapse_all()

    def get_project(self):
        return self._project

    def set_project(self,project):
        """
        Assign a project to the TreeView and repopulate the tree.  If
        no project is given, the TreeView will be empty.
        """
        if project is not None:
            self.set_property('sensitive',True)
        else:
            self.set_property('sensitive',False)
            
        self._project = project

        self.populate_treeview()

        # TODO: remove old signals
        if self.project is not None:
            Signals.connect(self.project, "notify::datasets", self.populate_treeview)
            Signals.connect(self.project, "notify::plots", self.populate_treeview)
            
        
    project = property(get_project,set_project)

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
        object = model.get_value(iter, self.COL_OBJECT)

        label = object.get_option('label')
        if label is None:
            label = "<unnamed %s>" % object.getName()

        # add extra information to label
        if isinstance(object, Plot):
            label += "  (%d)" % len(object.curves)
            
        cell.set_property('text', label)

    def render_type(self,column,cell,model,iter):
        object = model.get_value(iter, self.COL_OBJECT)
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
        #print model.get_value(iter,self.COL_CLASSNAME) != 'Project'
        #return model.get_value(iter,self.COL_CLASSNAME) != 'Project'
        return True


    # ----------------------------------------------------------------------
    #  object retrieval
    # ----------------------------------------------------------------------

    def get_selected_objects(self):
        " Return the list of currently selected objects. "
        (model, pathlist) = self.get_selection().get_selected_rows()
        return [model.get(model.get_iter(path),self.COL_OBJECT)[0] for path in pathlist]

    def get_selected_plds(self):        
        " Returns 2-tuple ([plots], [datasets]). "
        (model, pathlist) = self.get_selection().get_selected_rows()
        objects = [self.get_object_by_path(path) for path in pathlist]
        logger.debug("object[0] = %s" % objects[0])
        plots = [obj for obj in objects if isinstance(obj,Plot)]
        datasets = [obj for obj in objects if isinstance(obj,Dataset)]
        return (plots, datasets)

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
        return model.get(model.get_iter(path),self.COL_OBJECT)[0]
    
        

    #----------------------------------------------------------------------

    def start_editing_key(self):        
        selection = self.get_selection()
        if selection is None:
            return
        
        model, pathlist = selection.get_selected_rows()
        if len(pathlist) > 0:
            path = pathlist[0]

            self.text_renderer.set_property('editable', True)
            try:
                self.set_cursor(path, self.get_column(self.COL_KEY), start_editing=True)
            finally:
                self.text_renderer.set_property('editable', False)

        
    def cb_edited_key(self, cell, path, new_text):
        """
        When an object key is edited, we need to check whether
        the key is valid. If so, the key is changed.
        """        
        model = self.get_model()
        object = model[path][self.COL_OBJECT]

        ul = UndoList()
        if isinstance(object , Dataset):
            if new_text not in [dataset.key for dataset in self.project.datasets]:
                ul.describe("Edit Dataset key")
                uwrap.set(object, key=new_text, undolist=ul)
                uwrap.emit_last(self.project.datasets, "notify", undolist=ul)
        elif isinstance(object, Plot):
            if new_text not in [plot.key for plot in self.project.plots]:
                ul.describe("Edit Plot key")
                uwrap.set(object, key=new_text, undolist=ul)
                uwrap.emit_last(self.project.plots, "notify", undolist=ul)

        if len(ul) > 0:
            self.project.journal.append(ul)        



