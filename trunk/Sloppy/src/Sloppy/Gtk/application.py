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

import glob, os, sys
import gtk, gobject, pango

from Sloppy.Gtk import uihelper, gtkexcepthook, import_dialog, preferences, \
     mpl,datawin
from Sloppy.Gtk.gnuplot_window import GnuplotWindow
from Sloppy.Gtk.appwindow import AppWindow
from Sloppy.Gtk.layerwin import LayerWindow
from Sloppy.Gtk.options_dialog import OptionsDialog, NoOptionsError
from Sloppy.Gtk import toolbox, dock
from Sloppy.Gtk.Tools import *

from Sloppy.Base import \
     utils, error, application, globals, pdict, uwrap, dataio, backend
from Sloppy.Base.objects import Plot, Axis, Line, Layer
from Sloppy.Base.dataset import Dataset
from Sloppy.Base.project import Project
from Sloppy.Base.projectio import load_project, save_project, ParseError

from Sloppy.Gnuplot.terminal import PostscriptTerminal

from Sloppy.Lib.ElementTree.ElementTree import Element, SubElement
from Sloppy.Lib.Check import Instance, List, values_as_dict, AnyValue
from Sloppy.Lib.Undo import *


#------------------------------------------------------------------------------
# GtkApplication, the main object
#

class GtkApplication(application.Application):
    """    
    Application is a wrapper window for the ProjectTreeView which
    holds the information on the current project.  It adds a menu bar
    and a toolbar as described in the two attributes window_actions
    and ui_string of this module.  Furthermore, it provides basic
    functions to work with the project.
    """

    active_backend = Instance(backend.Backend, required=False, init=None)
    selected_plots = List(Instance(Plot))
    selected_datasets = List(Instance(Dataset))
    
    def init(self):
        self.sig_register('begin-user-action')
        self.sig_register('cancel-user-action')
        self.sig_register('end-user-action')
        
        self.window = AppWindow()
        self._clipboard = gtk.Clipboard()  # not implemented yet
        self._current_plot = None
        self.path.icon_dir = os.path.join(self.path.base_dir, 'Gtk','Icons')
        self.register_stock()
        self.popup_info = None
        
        # === Plugins ===
        self.init_plugins()

        # === Tools ===

        # TODO: The add_tool function is called if you add a Tool
        # from any Tool's popup menu. The popup
        # menu triggers the action, which emits the action's 'connect'
        # signal, which calls 'add_tool'. But there seems to be
        # no way of knowing which Tool triggered the action. So
        # currently I am using the application's popup_info field
        # to get that information ;-)
        #
        def add_tool(sender, toolklass):
            new_tool = toolklass()
            tool = globals.app.popup_info
            book = tool.dockbook
            book.add(new_tool)
            index = book.get_children().index(new_tool)
            book.set_current_page(index)

        def close_tool(sender):
            tool = globals.app.popup_info
            book = tool.dockbook
            book.remove(tool)

        # Create Actiongroup 
        ag = gtk.ActionGroup("ToolConfig")
        for key, toolklass in toolbox.ToolRegistry.iteritems():
            aw = uihelper.ActionWrapper(key, toolklass.label, stock_id=toolklass.icon_id)
            aw.connect(add_tool, toolklass)
            ag.add_action(aw.action)

        aw = uihelper.ActionWrapper('CloseTool', 'Close Tool', gtk.STOCK_CLOSE)
        aw.connect(close_tool)
        ag.add_action(aw.action)
        
        self.window.uimanager.insert_action_group(ag, -1)

        ui = '<popup name="popup_toolconfig">'
        ui += '  <menu action="AddTool">'
        for key, tool in toolbox.ToolRegistry.iteritems():
            ui += '<menuitem action="%s"/>' % key
        ui += '  </menu>'
        ui += '  <menuitem action="CloseTool"/>'
        ui += '</popup>'
                        
        # merge plugin ui
        merge_id = self.window.uimanager.add_ui_from_string(ui)

        self.window.sidepane.read_config(globals.app.eConfig,                                         
          default=['ProjectExplorer', 'PropertyEditor'])

    def register_stock(self):
        """
        Register png images from the GTK icon directory as stock icons.
        """
        uihelper.register_stock_icons(self.path.icon_dir, prefix='sloppy-')

        # register stock items
        items = [('sloppy-rename', '_Rename', 0, 0, None)]
        aliases = [('sloppy-rename', 'gtk-edit')]

        gtk.stock_add(items)

        factory = gtk.IconFactory()
        factory.add_default()
        style = self.window.get_style()
        for new_stock, alias in aliases:
            icon_set = style.lookup_icon_set(alias)
            factory.add(new_stock, icon_set)
            

    # Plugin Handling ------------------------------------------------------       
        
    def init_plugins(self):
        for plugin in self.plugins.itervalues():
            if hasattr(plugin, 'gtk_init'):
                plugin.gtk_init(self)

    def register_actions(self, action_wrappers):
        " Helper function for plugins. "
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
        Returns the new current project.

        @param confirm: Ask user for permission to close the project
        (unless there were no changes).
        """


# class ProjectCheck(Check):

#     def check(self, value):
# TODO: how can we access the old value in the check? DARN!
# But maybe we can simply put this question into an action?
#
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

        # THIS WOULD BE CONNECTED TO THE update::project EVENT.
        # self.sig_connect('update::project', self.on_update_project)
        # def on_update_project(self, sender, project):
        
        # set new project
        application.Application.set_project(self, project)

        # assign project label to window title
        if project:
            title = project.filename or "<unnamed project>"
        else:
            title = "(no project)"
        self.window.set_title(os.path.basename(title))

        if project is not None:
            project.journal.on_change = self.window._refresh_undo_redo

        self.window._refresh_undo_redo()
        self.window._refresh_recentfiles()

        return self._project


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
            chooser.set_current_folder(os.path.abspath(self.path.current_dir))
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

            shortcut_folder = self.path.example_dir
            if os.path.exists(shortcut_folder):
                chooser.add_shortcut_folder( shortcut_folder )

            response = chooser.run()
            if response == gtk.RESPONSE_OK:
                filename = chooser.get_filename()
            else:
                filename = None
            chooser.destroy()


        if filename is not None:
            application.Application.load_project(self, filename)
                



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
            chooser.set_current_folder(os.path.abspath(self.path.example_dir))
            chooser.set_select_multiple(False)
            chooser.set_filename(os.path.abspath(pj.filename or "unnamed.spj"))

            major,minor,micro = gtk.pygtk_version
            if major > 1 and minor >= 8:
                chooser.set_do_overwrite_confirmation(True)
            
            filter = gtk.FileFilter()
            filter.set_name("All files")
            filter.add_pattern("*")
            chooser.add_filter(filter)
            chooser.set_filter(filter) # default filter

            shortcut_folder = self.path.example_dir
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
        self.window.set_title(os.path.basename(self._project.filename))
        save_project(self._project)
        self._project.journal.clear()

        self.recent_files.insert(0, os.path.abspath(filename))
        self.sig_emit('update-recent-files')


    def quit(self):
        """ Quit Application and gtk main loop. """
        try:
            application.Application.quit(self)
            gtk.main_quit()
        except error.UserCancel:
            return




    # ----------------------------------------------------------------------
    # Callbacks
    #
    
    # delete-event/destroy/quit application
            
    def _cb_quit_application(self, action): self.quit()       
    def _cb_project_close(self,widget=None):  self.set_project(None)
    def _cb_project_open(self,widget): self.load_project()
    def _cb_project_save(self,widget):   self.save_project()            
    def _cb_project_save_as(self,widget): self.save_project_as()                        
    def _cb_project_new(self,widget): self.new_project()


    #----------------------------------------------------------------------
    
    def _cb_edit(self, action):
        plots, datasets = self.selected_plots, self.selected_datasets
        if len(plots) > 0:
            self.edit_layer(plots[0])
        else:
            for dataset in datasets:
                self.edit_dataset(dataset)        

                        
    # --- VIEW ---------------------------------------------------------------------
                
    def edit_dataset(self, ds, undolist=[]):
        widget = self.window.find_dataset_widget(self.project, ds)       
        if widget is None:
            widget = datawin.DatasetWidget(self.project, ds)
            self.window.add_basewidget(widget)
            widget.show()



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
            
        win = LayerWindow(plot, layer, current_page=current_page)
        win.set_modal(True)
        win.present()

    def edit_line(self, line):
        dialog = OptionsDialog(line)
        try:           
            response = dialog.run()
            if response == gtk.RESPONSE_ACCEPT:
                ul = UndoList("Edit Line")                                
                dialog.check_out(undolist=ul)
                #uwrap.emit_last(self.backend, 'redraw', undolist=ul)
                self.project.journal.append(ul)
                
                return dialog.owner
            else:
                raise error.UserCancel

        finally:
            dialog.destroy()

        #         win = gtk.Window()
        #         self.factory = checkwidgets.DisplayFactory(line)
        #         self.factory.add_keys(line._checks.keys())
        #         table = self.factory.create_table()
        #         frame = uihelper.new_section("Line", table)
        #         self.factory.check_in(line)
        
    
    #----------------------------------------------------------------------

    def _cb_new_plot(self,widget):
        pj = self._check_project()
        plot = self.core.new_lineplot2d(key='empty plot')
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


        elif backend_name == 'matplotlib':

            # as widget
            widget = self.window.find_plot_widget(project=self.project, plot=plot)
            if widget is None:
                widget = mpl.MatplotlibWidget(project=self.project, plot=plot)
                self.window.add_basewidget(widget)
            widget.show()

            backend = widget.backend

        else:
            raise RuntimeError("Unknown backend %s" % backend_name)

        self.active_backend = backend

    def plot_current_objects(self, backend_name='matplotlib', undolist=[]):
        plots, datasets = self.selected_plots, self.selected_datasets
        for plot in plots:
            self.plot(plot, backend_name)


    def on_action_export_via_gnuplot(self, action):
        plots = self.selected_plots
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
        chooser.set_current_folder(os.path.abspath(os.path.dirname(filename)))
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
        backend = globals.BackendRegistry['gnuplot'](
            project=project,
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
        chooser.set_current_folder(os.path.abspath(self.path.current_dir))
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
        
        # Each item in importer_registry is a class derived from
        # dataio.Importer.  By using IOTemplate objects we can
        # customize the default values for these templates.
        for (key, template) in globals.import_templates.iteritems():
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
        shortcut_folder = self.path.data_dir
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
        for key, template in globals.import_templates.iteritems():
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
        
        vbox = gtk.VBox()
        vbox.pack_start(hbox,False)
        #vbox.pack_start(pbar,False)
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
            else:
                return
        finally:
            chooser.destroy()

        self.do_import(pj, filenames, template_key)



    def do_import(self, project, filenames, template_key=None):

        # try to determine template key if it is not given
        if template_key is None or template_key=='auto':
            matches = dataio.importer_template_from_filename(filenames[0])
            if len(matches) > 0:
                template_key = matches[0]
            else:
                template_key = 'ASCII'                            
                  
        #
        # Request import options
        #

        # Note that if 'skip_option' is set in the template, then
        # there will be no user options dialog.

        if globals.import_templates[template_key].skip_options is False:
            dialog = import_dialog.ImportOptions(template_key, previewfile=filenames[0])
            try:
                result = dialog.run()
                if result == gtk.RESPONSE_ACCEPT:
                    # save template as 'recently used'
                    template = dataio.IOTemplate()
                    template.defaults = values_as_dict(dialog.importer, dialog.importer.public_props)
                    template.blurb = "Recently used Template"
                    template.importer_key = dialog.template.importer_key
                    template.write_config = True
                    template.immutable = True
                    globals.import_templates['recently used'] = template
                else:
                    return
            finally:
                dialog.destroy()
        else:
            template = template_key

        self.core.import_datasets(project, filenames, template)             


    def _cb_new_dataset(self,widget):
        """ Create a new dataset and switch to its editing window. """
        pj = self._check_project()        
        ds = pj.new_dataset()
        self.edit_dataset(ds)        


    def on_action_DatasetToPlot(self, action):
        pj = self._check_project()
        self.core.create_plot_from_datasets(pj, self.selected_datasets)
                     

    def _cb_add_datasets_to_plot(self, action):
        pj = self._check_project()
        plots, datasets = self.selected_plots, self.selected_datasets
        if len(plots) == 1 and len(datasets) > 0:
            pj.add_datasets_to_plot(datasets, plots[0])

    def _cb_delete(self, widget):
        pj = self._check_project()
        objects = self.selected_datasets + self.selected_plots
        pj.remove_objects(objects)        


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


    def on_action_Preferences(self, action):
        dlg = preferences.ConfigurationDialog()
        try:
            dlg.run()
        finally:
            dlg.destroy()
           

    #----------------------------------------------------------------------
    # Simple user I/O, inherited from Base.Application
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


    def error_msg(self, msg):
        dialog = gtk.MessageDialog(type=gtk.MESSAGE_ERROR,
                                   buttons=gtk.BUTTONS_OK,
                                   message_format=unicode(msg))
        dialog.run()
        dialog.destroy()


    def status_msg(self, msg):
        sb = self.window.statusbar
        context = sb.get_context_id("main")
        id = sb.push(context, msg)

        def remove_msg(statusbar, a_context, a_id):
            statusbar.remove(a_context, a_id)
            return False            
        gobject.timeout_add(3000, remove_msg, sb, context, id)


    def progress(self, fraction):
        pb = self.window.progressbar

        if fraction == 0:
            pb.show()
            pb.set_fraction(0)
        elif fraction == -1:
            pb.hide()
        else:
            pb.set_fraction(fraction)

        # Calling main_iteration is definitely not the only way to
        # update the progressbar; see FAQ 23.20 for details.  But
        # I refrain from using generators for the import function.
        while gtk.events_pending():
            gtk.main_iteration()


    def get_uistring(self, resource):
        """ Return ui string for the given resource.

        E.g. resource='appwindow' returns the contents of the file
        'UI/appwindow.ui' (if available).
        """
        path = os.path.join(self.path.internal_path, 'Gtk', 'UI', "%s.ui"%resource)
        fd = open(path, 'r')
        try:
            ui = fd.read()
        finally:
            fd.close()

        return ui

# ======================================================================    

def main(filename=None):
    
    app = GtkApplication()

    if filename is None:
        spj = app.set_project(Project())

        ## FOR TESTING
        # TODO: maybe as command line option?
        app.core.add_experimental_plot(spj)
        spj.journal.clear()
        app.window.sidepane.show()
    else:
        try:
            logger.debug("Trying to load file %s" % filename)
            app.load_project(filename)
        except IOError:
            app.set_project(Project())
                
    gtk.main()

    
if __name__ == "__main__":
    main()
    
    
