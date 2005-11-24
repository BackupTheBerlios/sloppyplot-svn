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


"""
"""

import logging
logger = logging.getLogger('gtk.application')

import pygtk # TBR
pygtk.require('2.0') # TBR

import gtk, gobject, pango
import gtkexcepthook

import uihelper
from gidlethread import *


import sys, glob, os.path, time
from os.path import basename

from tablewin import DatasetWindow
from gnuplot_window import GnuplotWindow
from appwindow import AppWindow
from mpl_window import MatplotlibWindow, MatplotlibWidget
from layerwin import LayerWindow

import Sloppy
from Sloppy.Base.application import Application
from Sloppy.Base import utils, error, config
from Sloppy.Base.objects import Plot, Axis, Line, Layer, new_lineplot2d
from Sloppy.Base.dataset import Dataset
from Sloppy.Base.project import Project
from Sloppy.Base.projectio import load_project, save_project, ParseError
from Sloppy.Base.backend import BackendRegistry
from Sloppy.Base.table import Table

from Sloppy.Base import pdict, uwrap
from Sloppy.Base.plugin import PluginRegistry

from Sloppy.Base import dataio

from Sloppy.Gnuplot.terminal import PostscriptTerminal
from options_dialog import OptionsDialog, NoOptionsError

from Sloppy.Lib.Undo import *

import import_dialog
import pwglade
   
#------------------------------------------------------------------------------
# Helper Methods
#

def register_all_png_icons(imgdir, prefix=""):
    """
    Register all svg icons in the Icons subdirectory as stock icons.
    
    @param prefix: Prefix for the created stock_id.
    """
    logger.debug("Trying to register png icons from dir '%s'" % imgdir)
    import glob, os
    filelist = map(lambda fn: ("%s%s" % (prefix, fn.split(os.path.sep)[-1][:-4]), fn), \
                   glob.glob(os.path.join(imgdir,'*.png')))
    
    iconfactory = gtk.IconFactory()
    stock_ids = gtk.stock_list_ids()
    for stock_id, file in filelist:
        # only load image files when our stock_id is not present
        if stock_id not in stock_ids:
            logger.debug( "loading image '%s' as stock icon '%s'" % (file, stock_id) )
            pixbuf = gtk.gdk.pixbuf_new_from_file(file)
            pixbuf = pixbuf.scale_simple(48,48,gtk.gdk.INTERP_BILINEAR)
            iconset = gtk.IconSet(pixbuf)
            iconfactory.add(stock_id, iconset)
    iconfactory.add_default()

        



#------------------------------------------------------------------------------
# GtkApplication, the main object
#

class GtkApplication(Application):
    """    
    Application is a wrapper window for the ProjectTreeView which
    holds the information on the current project.  It adds a menu bar
    and a toolbar as described in the two attributes window_actions
    and ui_string of this module.  Furthermore, it provides basic
    functions to work with the project.
    """
    
    def init(self):
        self.path.bset('icon_dir',  'system_prefix_dir', os.path.join('share', 'pixmaps', 'sloppyplot'))
        register_all_png_icons(self.path.get('icon_dir'), 'sloppy-')
        
        self.window = AppWindow(self)
        self._clipboard = gtk.Clipboard()  # not implemented yet
        self._current_plot = None
        

    def init_plugins(self):
        Application.init_plugins(self)

        for plugin in self.plugins.itervalues():

            if hasattr(plugin, 'gtk_popup_actions'):
                action_wrappers = plugin.gtk_popup_actions()                
                # create action group
                ag = gtk.ActionGroup("Plugin")
                for item in action_wrappers:
                    ag.add_action(item.action)
                self.window.uimanager.insert_action_group(ag, -1)

                # construct plugin ui
                plugin_ui = '<popup name="popup_dataset">'
                for item in action_wrappers:
                    plugin_ui += '<menuitem action="%s"/>' % item.name
                plugin_ui += '</popup>'
                        
                # merge plugin ui
                merge_id = self.window.uimanager.add_ui_from_string(plugin_ui)

    # ----------------------------------------------------------------------
    # Project
    
    def set_project(self, project, confirm=True):
        """
        Assign the given project to the Application.

        @param confirm: Ask user for permission to close the project
        (unless there were no changes).
        """

        if self._project is not None:
            if self._project.journal.can_undo() and confirm is True:        
                msg = \
                """
                You are about to close the Project.
                Do you want to save your changes ?
                """
                dialog = gtk.MessageDialog(type = gtk.MESSAGE_QUESTION, message_format = msg)
                dialog.add_button("_Don't Save", gtk.RESPONSE_NO)
                btn_default = dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
                dialog.add_button(gtk.STOCK_SAVE, gtk.RESPONSE_YES)

                btn_default.grab_focus()

                response = dialog.run()
                dialog.destroy()

                if response == gtk.RESPONSE_YES:
                    # yes = yes, save the file before closing
                    self.save_project()                    
                elif response == gtk.RESPONSE_NO:
                    # no = no, proceed with closing
                    pass
                else:
                    # everything else -> abort action
                    raise error.UserCancel

        # set new project
        Application.set_project(self, project)
        self.window.treeview.set_project(project)

        # assign project label to window title
        if project:
            title = project.filename or "<unnamed project>"
        else:
            title = "(no project)"
        self.window.set_title(basename(title))

        if project is not None:
            project.journal.on_change = self.window._refresh_undo_redo

        self.window._refresh_undo_redo()
        self.window._refresh_recentfiles()


    def load_project(self, filename=None):
        """
        Open a FileChooserDialog and let the user pick a new project
        to be loaded. The old project is replaced.
        """

        if filename is None:
            # TODO
            # maybe we could have application.load_project
            # just request the file name and we simply
            # create a method for this dialog.
            
            # create chooser object 
            chooser = gtk.FileChooserDialog(
                title="Open project",
                action=gtk.FILE_CHOOSER_ACTION_OPEN,
                buttons=(gtk.STOCK_CANCEL,
                         gtk.RESPONSE_CANCEL,
                         gtk.STOCK_OPEN,
                         gtk.RESPONSE_OK))
            chooser.set_default_response(gtk.RESPONSE_OK)
            chooser.set_current_folder( self.path.get('current_dir') )
            chooser.set_select_multiple(False)

            filter = gtk.FileFilter()
            filter.set_name("All files")
            filter.add_pattern("*")
            chooser.add_filter(filter)

            filter = gtk.FileFilter()
            filter.set_name("Sloppyplot Project files")
            filter.add_pattern("*.spj")
            filter.add_pattern("*.SPJ")
            chooser.add_filter(filter)
            chooser.set_filter(filter) # default filter

            shortcut_folder = self.path.get('example_dir')
            if os.path.exists(shortcut_folder):
                chooser.add_shortcut_folder( shortcut_folder )

            response = chooser.run()
            if response == gtk.RESPONSE_OK:
                filename = chooser.get_filename()
            else:
                filename = None
            chooser.destroy()


        if filename is not None:
            Application.load_project(self, filename)



    def save_project_as(self, filename = None):
        """ Save project under another filename. """
        pj = self._check_project()

        if not filename:
            # allow user to choose a filename
            chooser = gtk.FileChooserDialog(
                title="Save Project As",
                action=gtk.FILE_CHOOSER_ACTION_SAVE,
                buttons=(gtk.STOCK_CANCEL,
                         gtk.RESPONSE_CANCEL,
                         gtk.STOCK_SAVE,
                         gtk.RESPONSE_OK))
            chooser.set_default_response(gtk.RESPONSE_OK)
            chooser.set_current_folder( self.path.get('example_dir') )
            chooser.set_select_multiple(False)
            chooser.set_filename(pj.filename or "unnamed.spj")

            filter = gtk.FileFilter()
            filter.set_name("All files")
            filter.add_pattern("*")
            chooser.add_filter(filter)
            chooser.set_filter(filter) # default filter

            shortcut_folder = self.path.get('example_dir')
            if os.path.exists(shortcut_folder):
                chooser.add_shortcut_folder(shortcut_folder)

            response = chooser.run()
            try:
                if response == gtk.RESPONSE_OK:
                    filename = chooser.get_filename()                    
                else:
                    raise error.UserCancel
            finally:
                chooser.destroy()

            # add extension if not yet there
            if filename.lower().endswith('.spj') is False:
                filename = filename + ".spj"

        self._project.filename = filename
        self.window.set_title(basename(self._project.filename))
        save_project(self._project)
        self._project.journal.clear()

        self.recent_files.append(os.path.abspath(filename))
        self.sig_emit('update-recent-files')


    def quit(self):
        """ Quit Application and gtk main loop. """
        try:
            Application.quit(self)
            gtk.main_quit()
        except error.UserCancel:
            return

    # ----------------------------------------------------------------------
    # Callbacks
    #
    
    # delete-event/destroy/quit application
            
    def _cb_quit_application(self, action): self.quit()       

    def _cb_project_close(self,widget=None):  self.close_project()
    def _cb_project_open(self,widget): self.load_project()
    def _cb_project_save(self,widget):   self.save_project()            
    def _cb_project_save_as(self,widget): self.save_project_as()                        
    def _cb_project_new(self,widget): self.new_project()


    #----------------------------------------------------------------------
    
    def _cb_edit(self, action):
        plots, datasets = self.window.treeview.get_selected_plds()
        if len(plots) > 0:
            self.edit_layer(plots[0])
        else:
            for dataset in datasets:
                self.edit_dataset(dataset)        

                        
    # --- VIEW ---------------------------------------------------------------------
                
    def edit_dataset(self, ds, undolist=[]):
        assert( isinstance(ds, Dataset) )

        # reuse old DatasetWindow or create new one
        window = self.window.subwindow_match(
            (lambda win: isinstance(win, DatasetWindow) and (win.dataset == ds))) \
            or \
            self.window.subwindow_add( DatasetWindow(self, self._project, ds) )
	window.present()


    def edit_layer(self, plot, layer=None, current_page=None):
        """
        Edit the given layer of the given plot.
        If no layer is given, the method tries to edit the first Layer.
        If there is no Layer in the plot, an error will logged.

        TODO: current_page.
        """
        if layer is None:
            if len(plot.layers) > 0:
                layer = plot.layers[0]
            else:
                logger.error("The plot to be edited has not even a single layer!")
                return
            
        win = LayerWindow(self, plot, layer, current_page=current_page)
        win.set_modal(True)
        win.present()
        
    
    #----------------------------------------------------------------------

    def _cb_new_plot(self,widget):
        pj = self._check_project()
        
        plot = new_lineplot2d(key='empty plot')
        pj.add_plots([plot])
        


        
    # --- PLOT ---------------------------------------------------------------------
    
    def _cb_plot(self,widget): self.plot_current_objects()        
    def _cb_plot_gnuplot(self,widget): self.plot_current_objects('gnuplot/x11')
    def _cb_plot_matplotlib(self,widget): self.plot_current_objects('matplotlib')


    def plot(self,plot,backend_name='matplotlib'):
        
        logger.debug("Backend name is %s" % backend_name)
        
        if backend_name == 'gnuplot/x11':
            backend = self.project.request_backend('gnuplot/x11', plot=plot)
            backend.draw()
            return

        # TODO: open Gnuplot window

        # add_subwindow
        # match_subwindow
        # request_subwindow

        # evtl. schon als Toolbox ???
        
#             window = self.window.subwindow_match( \
#                 (lambda win: isinstance(win, GnuplotWindow) and \
#                  win.project == self.project and \
#                  win.plot == plot) )
#             if window is None:
#                 window = GnuplotWindow(self, project=self.project, plot=plot)
#                 self.window.subwindow_add( window )

        elif backend_name == 'matplotlib':

#             # as widget
#             widget = self.window.find_plotwidget(project=self.project,plot=plot)
#             if widget is None:
#                 widget = MatplotlibWidget(self, project=self.project, plot=plot)
#                 self.window.add_plotwidget(widget)
#             widget.show()

            # as window
            window = self.window.subwindow_match( \
                (lambda win: isinstance(win, MatplotlibWindow) \
                 and win.get_project() == self.project \
                 and win.get_plot() == plot) )

            if window is None:
                window = MatplotlibWindow(self, project=self.project, plot=plot)
                ##window.set_transient_for(self.window)
                self.window.subwindow_add(window)
                # TESTING
                # Of course, the toolbox might decide to not use the backend,
                # e.g. if there is an 'auto' button and it is not pressed. So I will
                # need to change that then.
                window.connect("focus-in-event", (lambda a,b: self.window.toolbox.set_backend(window.get_backend())))

            window.show()
            window.present()
            
        else:
            raise RuntimeError("Unknown backend %s" % backend_name)
        

    def plot_current_objects(self, backend_name='matplotlib', undolist=[]):
        (plots, datasets) = self.window.treeview.get_selected_plds()
        for plot in plots:
            self.plot(plot, backend_name)


    def on_action_export_via_gnuplot(self, action):
        plots = self.window.treeview.get_selected_plots()
        if len(plots) > 0:
            self.plot_postscript(self.project, plots[0])

        
    def plot_postscript(app, project, plot):

        #
        # request filename
        #
        filename = PostscriptTerminal.build_filename('ps', project, plot)
        
        chooser = gtk.FileChooserDialog(
            title="PostScript Export",
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL,
                         gtk.RESPONSE_CANCEL,
                         gtk.STOCK_SAVE,
                         gtk.RESPONSE_OK))
        chooser.set_default_response(gtk.RESPONSE_OK)        
        chooser.set_select_multiple(False)
        chooser.set_current_folder(os.path.dirname(filename))
        chooser.set_current_name(os.path.basename(filename))

        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        chooser.add_filter(filter)
        
        filter = gtk.FileFilter()
        filter.set_name("Postscript (.ps; .eps)")
        filter.add_pattern("*.ps")
        filter.add_pattern("*.eps")
        chooser.add_filter(filter)
        chooser.set_filter(filter) # default filter                

        response = chooser.run()
        try:
            if response == gtk.RESPONSE_OK:
                filename = chooser.get_filename()                    
            else:
                raise error.UserCancel
        finally:
            chooser.destroy()               

        #
        # request export options
        #
        ##props = ['mode', 'enhanced', 'color', 'blacktext', 'solid',
        ##         'dashlength', 'linewidth', 'duplexing', 'rounded', 'fontname',
        ##         'fontsize', 'timestamp']          
        
        dialog = OptionsDialog(PostscriptTerminal(),
                               title="Options Postscript Export",
                               parent=app.window)
        #dialog.set_size_request(320,520)

        # determine requested postscript mode (ps or eps) from extension
        path, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext == '.eps':
            dialog.owner.mode = 'eps'
        elif ext == '.ps':
            dialog.owner.mode = 'landscape'
            
        try:
            result = dialog.run()
            if result == gtk.RESPONSE_ACCEPT:            
                dialog.check_out()
            else:
                return
            terminal = dialog.owner
        finally:
            dialog.destroy()


        #
        # now check if mode and filename extension match
        #

        def fix_filename(filename, mode):
            msg = "The postscript mode you selected (%s) does not match the given filename extension (%s).  Do you want to adjust the filename to match the mode? " % (mode, os.path.splitext(filename)[1])
            dialog = gtk.MessageDialog(type = gtk.MESSAGE_QUESTION, message_format = msg)
            dialog.add_button("Keep Filename", gtk.RESPONSE_NO)
            btn_default = dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            dialog.add_button("Adjust Filename", gtk.RESPONSE_YES)

            btn_default.grab_focus()

            response = dialog.run()
            dialog.destroy()

            if response == gtk.RESPONSE_YES:
                # yes = yes, adjust filename
                if mode == '.eps':  new_ext = '.eps'
                else: new_ext = '.ps'
                path, ext = os.path.splitext(filename)
                return path + new_ext
            elif response == gtk.RESPONSE_NO:
                # no = no, keep filename
                return filename
            else:
                # everything else -> abort action
                raise error.UserCancel

        if (terminal.mode == 'eps' and ext != '.eps') or \
               (terminal.mode != 'eps' and ext != '.ps'):
            filename = fix_filename(filename, terminal.mode)
        
        #
        # construct backend for output
        #
        backend = BackendRegistry['gnuplot'](project=project,
                                             plot=plot,
                                             filename=filename,
                                             terminal=terminal)
        try:
            backend.draw()
        finally:
            backend.disconnect()

        

    # --- DATASET HANDLING -------------------------------------------------


    def _cb_import_dataset(self, action):
        pj = self._check_project()
        
        # allow user to choose files for import
        chooser = gtk.FileChooserDialog(
            title="Import Dataset from file",
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL,
                     gtk.RESPONSE_CANCEL,
                     gtk.STOCK_OPEN,
                     gtk.RESPONSE_OK))
        chooser.set_default_response(gtk.RESPONSE_OK)
        chooser.set_current_folder(self.path.get('current_dir'))
        chooser.set_select_multiple(True)

        filter_keys = {} # used for reference later on
        
        # add 'All Files' filter
        blurb_all_files = "All Files"
        filter = gtk.FileFilter()
        filter.set_name(blurb_all_files)
        filter.add_pattern("*")
        chooser.add_filter(filter)
        chooser.set_filter(filter)
        filter_keys[blurb_all_files] = 'auto' # default if nothing else specified

        #
        # create file filters
        #
        
        # Each item in ImporterRegistry is a class derived from
        # dataio.Importer.  By using IOTemplate objects we can
        # customize the default values for these templates.
        for (key, template) in dataio.import_templates.iteritems():
            ext_list = template.extensions.split(',')
            if len(ext_list) == 0:
                continue
            extensions = ';'.join(map(lambda ext: '*.'+ext, ext_list))
            blurb = "%s (%s)" % (template.blurb, extensions)

            filter = gtk.FileFilter()
            filter.set_name(blurb)
            for ext in ext_list:
                filter.add_pattern("*."+ext.lower())
                filter.add_pattern("*."+ext.upper())
            chooser.add_filter(filter)

            filter_keys[blurb] = key
            

        # add shortcut folder to example path, if such exists
        shortcut_folder = self.path.get('data_dir')
        if os.path.exists(shortcut_folder):
            chooser.add_shortcut_folder(shortcut_folder)

        
        #
        # prepare extra widget
        #
        
        # The custom widget `combobox` lets the user choose,
        # which ImporterTemplate is to be used.
        
        # model: key, blurb
        model = gtk.ListStore(str, str)
        # add 'Same as Filter' as first choice, then add all importers
        model.append( (None, "Auto") )
        for key, template in dataio.import_templates.iteritems():
                model.append( (key, template.blurb) )
        
        combobox = gtk.ComboBox(model)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 1)
        combobox.set_active(0)
        combobox.show()

        label = gtk.Label("Use Template: ")
        label.show()
            
        hbox = gtk.HBox()       
        hbox.pack_end(combobox,False)
        hbox.pack_end(label,False)
        hbox.show()        

        # The progress bar display which file is currently being imported.
        pbar = gtk.ProgressBar()
        
        vbox = gtk.VBox()
        vbox.pack_start(hbox,False)
        vbox.pack_start(pbar,False)
        vbox.show()
        
        chooser.set_extra_widget(vbox)

        #
        # run dialog
        #        
        try:
            response = chooser.run()
            if response == gtk.RESPONSE_OK:
                filenames = chooser.get_filenames()
                if len(filenames) == 0:
                    return
                
                template_key = model[combobox.get_active()][0]

                if template_key is None: # auto
                    f = chooser.get_filter()
                    template_key = filter_keys[f.get_name()]
                    # we skip the hard task of determining the template key here
                    if template_key is 'auto':
                        matches = dataio.importer_template_from_filename(filenames[0])
                        if len(matches) > 0:
                            template_key = matches[0]
                        else:
                            template_key = 'ASCII'                            
            else:
                return

            # TODO
            #chooser.set_active(False)
            pbar.show()

            #
            # Request import options
            #

            # Note that if 'skip_option' is set in the template, then
            # there will be no user options dialog.

            if dataio.import_templates[template_key].skip_options is False:
                dialog = import_dialog.ImportOptions(template_key) # filenames?
                try:
                    result = dialog.run()
                    if result == gtk.RESPONSE_ACCEPT:
                        importer = dialog.importer
                        # save template as 'recent'
                        template = dataio.IOTemplate()
                        template.defaults = dialog.importer.get_values(include=dialog.importer.public_props)
                        template.blurb = "Recently used Template"
                        template.importer_key = dialog.template.importer_key
                        template.write_config = True
                        dataio.import_templates['recent'] = template                    
                    else:
                        return
                finally:
                    dialog.destroy()


            def set_text(queue):
                while True:
                    try:
                        text, fraction = queue.get()
                        if text == -1:
                            pbar.hide()
                        elif text is not None:
                            pbar.set_text(text)                                        
                        if fraction is not None:
                            pbar.set_fraction(fraction)
                    except QueueEmpty:
                        pass
                    yield None

            queue = Queue()
            thread_progress = GIdleThread(set_text(queue))
            thread_progress.start()

            thread_import = GIdleThread(self.import_datasets(pj, filenames, importer), queue)
            thread_import.start()
            thread_import.wait()

        finally:
            chooser.destroy()



    def _cb_new_dataset(self,widget):
        """ Create a new dataset and switch to its editing window. """
        pj = self._check_project()        
        ds = pj.new_dataset()
        self.edit_dataset(ds)        


    def _cb_create_plot_from_datasets(self, widget):
        pj = self._check_project()
        datasets = self.window.treeview.get_selected_datasets()
        pj.create_plot_from_datasets(datasets)
        

    def _cb_add_datasets_to_plot(self, action):
        pj = self._check_project()
        (plots, datasets) = self.window.treeview.get_selected_plds()
        if len(plots) == 1 and len(datasets) > 0:
            pj.add_datasets_to_plot(datasets, plots[0])

    def _cb_delete(self, widget):
        pj = self._check_project()
        objects = self.window.treeview.get_selected_objects()
        pj.remove_objects(objects)        


    def _cb_experimental_plot(self, action):        
        pj = self._check_project()
        plugin = self.plugins['Default']
        plugin.add_experimental_plot(pj)



    # --- EDIT -------------------------------------------------------------

    ###
    ### TODO: implement cut/copy/paste
    ###
    def _cb_edit_cut(self, widget): pass
    def _cb_edit_copy(self, widget):  pass
    def _cb_edit_paste(self, widget):  pass
    
    # --- UNDO/REDO --------------------------------------------------------
        
    def _cb_undo(self, widget):
        pj = self._check_project()
        pj.undo()
        
    def _cb_redo(self, widget):
        pj = self._check_project()
        pj.redo()


    #----------------------------------------------------------------------
    # MISC CALLBACKS

    def _cb_recent_files_clear(self, action):
        self.clear_recent_files()


    def on_action_ConfigImportTemplates(self, action):
        # create simple add/remove/edit dialog
        dlg = gtk.Dialog("Edit ASCII Import Templates", None,
                         gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                         (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                          gtk.STOCK_CLOSE, gtk.RESPONSE_ACCEPT))

        # We create copies of all templates and put these into the
        # treeview.  This allows the user to reject the modifications
        # (RESPONSE_REJECT).  If however he wishes to use the
        # modifications (RESPONSE_ACCEPT), then we simply need to
        # replace the current templates with these temporary ones.

        # check in
        model = gtk.ListStore(str, object, str) # key, object, blurb
        for key,template in dataio.import_templates.iteritems():
            if template.importer_key == 'ASCII':
                model.append((key, template.copy(),"%s: %s" % (key, template.blurb)))

        # create gui
        tv = gtk.TreeView(model)
        column = gtk.TreeViewColumn("Available Templates")
        cell = gtk.CellRendererText()
        column.pack_start(cell,expand=True)
        column.set_attributes(cell, text=2)
        tv.set_headers_visible(False)
        tv.append_column(column)

        sw = uihelper.add_scrollbars(tv)

        def do_edit(template, allow_edit=True):
            # - what about editing the key?        
            importer = template.new_instance()

            dlg = gtk.Dialog("Edit Template Options",None,
                             gtk.DIALOG_MODAL,
                             (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                              gtk.STOCK_CLOSE, gtk.RESPONSE_ACCEPT))
            
            clist1 = pwglade.smart_construct_connectors(template, include=['blurb','extensions', 'skip_options'])            
            clist2 = pwglade.smart_construct_connectors(importer, include=importer.public_props)
            clist = clist1 + clist2
            table = pwglade.construct_table(clist)

            if allow_edit is False:
                notice = gtk.Label("This is an internal template\nwhich cannot be edited.")
                dlg.vbox.pack_start(notice,False,True)
                hseparator = gtk.HSeparator()
                dlg.vbox.pack_start(hseparator,False,True)
                #table.set_sensitive(False)
                for c in clist:
                    c.widget.set_sensitive(False)

            dlg.vbox.pack_start(table,True,True)            
            dlg.show_all()

            for c in clist:
                c.check_in()
                
            try:
                response = dlg.run()

                if response == gtk.RESPONSE_ACCEPT:
                    # TODO: check key
                    for c in clist:
                        c.check_out()

                    # move importer data to template
                    values = importer.get_values(importer.public_props, default=None)
                    template.set_values(defaults=values)                    
                    
            finally:
                dlg.destroy()

            return response

        # callbacks
        def edit_item(treeview):
            model,iter = treeview.get_selection().get_selected()
            if iter is None:
                return

            template = model.get_value(iter,1)
            if template.is_internal is True:
                do_edit(template, allow_edit=False)
            else:
                do_edit(template)   

        tv.connect("row-activated", (lambda treeview,b,c: edit_item(treeview)))
        
        def delete_item(btn):
            model,iter = tv.get_selection().get_selected()
            if iter is None:
                return            

            template = model.get_value(iter, 1)
            if template.is_internal is True:
                self.error_message("This is an internal template that cannot be edited or deleted.")
            else:
                model.remove(iter)
                

        def add_item(treeview):
            model,iter = treeview.get_selection().get_selected()
            if iter is None:
                print "INSERT AT BEGINNING"
                # TODO: insert at beginning
                pass
            else:
                key = model.get_value(iter,1)
                print "INSERT AT A POSITION, using the old one as template"
                template = dataio.IOTemplate(importer_key='ASCII')
                response = do_edit(template)
                if response == gtk.RESPONSE_ACCEPT:
                    model.insert_after(iter, ('key?', template, template.blurb))
            
        buttons=[(gtk.STOCK_EDIT, (lambda btn: edit_item(tv))),
                 (gtk.STOCK_ADD, (lambda btn: add_item(tv))),
                 (gtk.STOCK_DELETE, (lambda btn: delete_item(tv)))]
        btnbox = uihelper.construct_buttonbox(buttons,
                                              horizontal=False,
                                              layout=gtk.BUTTONBOX_START)

        hbox = gtk.HBox()
        hbox.pack_start(sw,True,True)
        hbox.pack_start(btnbox,False,True)
        
        dlg.vbox.pack_start(hbox,True,True)
        dlg.show_all()
        dlg.set_size_request(480,320)
        try:
            response = dlg.run()
            if response == gtk.RESPONSE_ACCEPT:
                # replace templates by the temporary ones
                templates = {}
                iter = model.get_iter_first()
                while iter is not None:
                    key = model.get_value(iter, 0)
                    template = model.get_value(iter, 1)
                    templates[key] = template
                    iter = model.iter_next(iter)

                # Note that this is an application specific operation,
                # and there is no undo available for this.
                dataio.import_templates = templates
        finally:
            dlg.destroy()
                         




    #----------------------------------------------------------------------
    # Simple user I/O
    #

    def ask_yes_no(self, msg):
        dialog = gtk.MessageDialog(parent=self.window,
                                   flags=0,
                                   type=gtk.MESSAGE_WARNING,
                                   buttons=gtk.BUTTONS_YES_NO,
                                   message_format=msg)
            
        result = dialog.run()
        dialog.destroy()

        return result == gtk.RESPONSE_YES


    def error_message(self, msg):
        dialog = gtk.MessageDialog(type=gtk.MESSAGE_ERROR,
                                   buttons=gtk.BUTTONS_OK,
                                   message_format=unicode(msg))
        dialog.run()
        dialog.destroy()




# ======================================================================    

def main(filename=None):

    app = GtkApplication()

    if filename is None:
        filename = os.path.join(app.path.get('example_dir'), 'example_01.spj')
    try:
        logger.debug("Trying to load file %s" % filename)
        app.load_project(filename)
    except IOError:
        app.set_project(Project())    
    gtk.main()

    
if __name__ == "__main__":
    main()
    
    
