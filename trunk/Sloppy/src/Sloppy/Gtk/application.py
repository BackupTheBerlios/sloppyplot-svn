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
logger = logging.getLogger('gtk.application')

import pygtk # TBR
pygtk.require('2.0') # TBR

import gtk, gobject, pango
import gtkexcepthook

import gtkutils, uihelper


import sys, glob, os.path, time
from os.path import basename

from tablewin import DatasetWindow
from gnuplot_window import GnuplotWindow
from appwindow import AppWindow
from mpl_window import MatplotlibWindow, MatplotlibWidget
from layerwin import LayerWindow

import Sloppy
from Sloppy.Base.application import Application
from Sloppy.Base import const, utils, error
from Sloppy.Base.objects import Plot, Axis, Line, Layer, new_lineplot2d
from Sloppy.Base.dataset import Dataset
from Sloppy.Base.project import Project
from Sloppy.Base.projectio import load_project, save_project, ParseError
from Sloppy.Base.backend import BackendRegistry
from Sloppy.Base.table import Table
from Sloppy.Base.dataio import ImporterRegistry, ExporterRegistry, importer_from_filename
from Sloppy.Base import pdict, uwrap
from Sloppy.Base.plugin import PluginRegistry

from Sloppy.Gnuplot.terminal import PostscriptTerminal
from options_dialog import OptionsDialog, NoOptionsError

from Sloppy.Lib.Undo import *
from Sloppy.Lib import Signals

   
#------------------------------------------------------------------------------
# Helper Methods
#

def register_all_png_icons(imgdir, prefix=""):
    """
    Register all svg icons in the Icons subdirectory as stock icons.
    The prefix is the prefix for the stock_id.
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



class ProgressIndicator:
    def __init__(self, pb):
        self.pb = pb
        self.pb.set_pulse_step(0.1)
    def set_text(self, text):
        self.pb.set_text(text) # TODO: encode properly
        while gtk.events_pending():
            gtk.main_iteration()                                        
    def set_fraction(self, fraction):
        self.pb.set_fraction(fraction)
        while gtk.events_pending():
            gtk.main_iteration()
    def pulse(self):
        self.pb.pulse()
        while gtk.events_pending():
            gtk.main_iteration()
        



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
        register_all_png_icons(const.internal_path(const.PATH_ICONS), 'sloppy-')
        
        self.window = AppWindow(self)
        self._clipboard = gtk.Clipboard()  # not implemented yet


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
        " Assign the given project to the Application. "

        # ask for permission to close the project
        # (unless there were no changes)
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

    # ----------------------------------------------------------------------
    # delete-event/destroy/quit application
            
    def _cb_quit_application(self, action):
        self.quit()

    def quit(self):
        try:
            Application.quit(self)
            gtk.main_quit()
        except error.UserCancel:
            return
        

    #
    # callbacks
    #
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

                        
    # ----------------------------------------------------------------------

    def _cb_load_test_project(self,widget):
        try:
            filename = const.internal_path(const.PATH_EXAMPLE+'/example.spj')
            spj = self.load_project(filename)
        except IOError:
            # TODO: Message Box
            return None
        self.set_project(spj)

        
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
            chooser.set_current_folder( const.internal_path(const.PATH_EXAMPLE) )
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

            shortcut_folder = const.internal_path(const.PATH_EXAMPLE)
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



    def save_project_as(self, filename = None, undolist=[]):
        " Save project under another filename -- no undo possible. "
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
            chooser.set_current_folder( const.internal_path(const.PATH_EXAMPLE) )
            chooser.set_select_multiple(False)
            chooser.set_filename(pj.filename or "unnamed.spj")

            filter = gtk.FileFilter()
            filter.set_name("All files")
            filter.add_pattern("*")
            chooser.add_filter(filter)
            chooser.set_filter(filter) # default filter

            shortcut_folder = const.internal_path(const.PATH_EXAMPLE)
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
        Signals.emit(self, 'update-recent-files')


        
    # --- PLOT ---------------------------------------------------------------------
    
    def _cb_plot(self,widget): self.plot_current_objects()        
    def _cb_plot_gnuplot(self,widget): self.plot_current_objects('gnuplot/x11')
    def _cb_plot_matplotlib(self,widget): self.plot_current_objects('matplotlib')


    def plot(self,plot,backend_name=const.DEFAULT_BACKEND):
        
        logger.debug("Backend name is %s" % backend_name)
        
        if backend_name == 'gnuplot/x11':
            backend = self.project.request_backend('gnuplot/x11', plot=plot)
            backend.draw()
            return

        # TODO: open Gnuplot window

        # add_subwindow
        # match_subwindow
        # request_subwindow

        # evtl. schon als ToolWindow ???
        
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
                self.window.subwindow_add(window)

            window.show()
            window.present()
            
        else:
            raise RuntimeError("Unknown backend %s" % backend_name)
        

    def plot_current_objects(self, backend_name=const.DEFAULT_BACKEND, undolist=[]):
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
        
        dialog = OptionsDialog(PostscriptTerminal(), app.window)
        dialog.set_size_request(320,520)

        # determine requested postscript mode (ps or eps) from extension
        path, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext == '.eps':
            dialog.container.mode = 'eps'
        elif ext == '.ps':
            dialog.container.mode = 'landscape'
            
        try:
            result = dialog.run()
            terminal = dialog.container
        finally:
            dialog.destroy()

        if result != gtk.RESPONSE_ACCEPT:
            return
        

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
        backend = BackendRegistry.new_instance(
            'gnuplot', project=project, plot=plot,
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
        chooser.set_current_folder(const.internal_path(const.PATH_DATA))
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
        
        # create file filters
        for (key, val) in ImporterRegistry.iteritems():            
            klass = val.klass
            extensions = ';'.join(map(lambda ext: '*.'+ext, klass.extensions))
            blurb = "%s (%s)" % (klass.blurb, extensions)

            filter = gtk.FileFilter()
            filter.set_name(blurb)
            for ext in klass.extensions:
                filter.add_pattern("*."+ext.lower())
                filter.add_pattern("*."+ext.upper())
            chooser.add_filter(filter)

            filter_keys[blurb] = key

        # add shortcut folder to example path, if such exists
        shortcut_folder = const.internal_path(const.PATH_EXAMPLE)
        if os.path.exists(shortcut_folder):
            chooser.add_shortcut_folder(shortcut_folder)

        #
        # prepare extra widget
        #
        
        # The custom widget `combobox` lets the user choose,
        # which Importer is to be used.
        
        # model: key, blurb
        model = gtk.ListStore(str, str)
        # add 'Same as Filter' as first choice, then add all importers
        model.append( (None, "Auto") )
        for key, val in ImporterRegistry.iteritems():
            model.append( (key, val.klass.blurb) )

        combobox = gtk.ComboBox(model)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 1)
        combobox.set_active(0)
        combobox.show()

        label = gtk.Label("Importer")
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
                
                importer_key = model[combobox.get_active()][0]
                if importer_key is None: # auto
                    f = chooser.get_filter()
                    importer_key = filter_keys[f.get_name()]
                    if importer_key is 'auto':
                        matches = importer_from_filename(filenames[0])
                        if len(matches) > 0:
                            importer_key = matches[0]
                        else:
                            importer_key = 'ASCII'
            else:
                return

            # TODO
            #chooser.set_active(False)
            pbar.show()
            
            # request import options
            importer = ImporterRegistry.new_instance(importer_key)

            try:
                dialog = OptionsDialog(importer, self.window)
            except NoOptionsError:
                pass
            else:
                # If there are any options, construct a
                # preview widget to help the user.
                view = gtk.TextView()
                buffer = view.get_buffer()
                view.set_editable(False)
                view.show()

                tag_main = buffer.create_tag(family="Courier")
                tag_linenr = buffer.create_tag(family="Courier", weight=pango.WEIGHT_HEAVY)

                # fill preview buffer with at most 100 lines
                preview_file = filenames[0]
                try:
                    fd = open(preview_file, 'r')
                except IOError:
                    raise RuntimeError("Could not open file %s for preview!" % preview_file)

                iter = buffer.get_start_iter()        
                try:
                    for j in range(100):
                        line = fd.readline()
                        if len(line) == 0:
                            break
                        buffer.insert_with_tags(iter, u"%3d\t" % j, tag_linenr)
                        try:
                            buffer.insert_with_tags(iter, unicode(line), tag_main)
                        except UnicodeDecodeError:
                            buffer.insert_with_tags(iter, u"<unreadable line>\n", tag_main)
                finally:
                    fd.close()

                preview_widget = uihelper.add_scrollbars(view)
                preview_widget.show()

                dialog.vbox.add(preview_widget)
                dialog.set_size_request(480,320)

                try:
                    result = dialog.run()
                finally:
                    dialog.destroy()

                if result != gtk.RESPONSE_ACCEPT:
                    return

            pj.import_datasets(filenames, importer,
                               progress_indicator=ProgressIndicator(pbar))

        finally:
            chooser.destroy()




    ###
    ### TODO: rewrite this!
    ###
    def _cb_export_dataset(self, widget):
        """
        Export the selected Dataset to a file.
        Currently, only the csv format is supported.
        TODO: Support for arbitrary export filters.
        """
        pj = self._check_project()
        objects = self.window.treeview.get_selected_objects()
        if len(objects) == 0:
            return
        object = objects[0]

        if not isinstance(object,Dataset):
            return

        # allow user to choose a filename
        chooser = gtk.FileChooserDialog(
            title="Export Dataset %s" % object.get_option('label'),
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL,
                     gtk.RESPONSE_CANCEL,
                     gtk.STOCK_SAVE,
                     gtk.RESPONSE_OK))
        chooser.set_default_response(gtk.RESPONSE_OK)
        chooser.set_current_folder(const.internal_path(const.PATH_EXAMPLE))
        chooser.set_select_multiple(False)

        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        chooser.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("Data Files")
        filter.add_pattern("*.dat")
        chooser.add_filter(filter)
        chooser.set_filter(filter) # default filter

        shortcut_folder = const.internal_path(const.PATH_EXAMPLE)
        if os.path.exists(shortcut_folder):
            chooser.add_shortcut_folder(shortcut_folder)

        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
        else:
            filename = None
        chooser.destroy()

        # export file, using the filter 'f'
        filename = os.path.abspath(filename)
        logger.debug("Exporting file %s as csv..." % filename )
        f = FilterRegistry.new_instance('comma separated values')
        f.export_to_file(filename, object)


    def _cb_new_dataset(self,widget):
        " Create a new dataset and switch to its editing window. "
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

        response = gtkutils.dialog_confirm_list(\
            title = "Remove Objects ?",
            msg =
            """
            Do you really wish to remove
            the following objects ?
            """,
            objects = objects)

        if response == gtk.RESPONSE_OK:
            print "OBJECTS", objects
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

def main(filename):
    filename = filename or const.internal_path(const.PATH_EXAMPLE, 'example.spj')
    app = GtkApplication(filename)
    gtk.main()

    
if __name__ == "__main__":
    const.set_path(Sloppy.__path__[0])
    main()
    
    
