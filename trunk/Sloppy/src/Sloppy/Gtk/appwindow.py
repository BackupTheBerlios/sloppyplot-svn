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


import os, gtk

from Sloppy.Gtk import uihelper, uidata, logwin, tools, mpl, dock
from Sloppy.Lib.ElementTree.ElementTree import Element, SubElement
from Sloppy.Base import utils, error, version, config, globals
from Sloppy.Base.objects import Plot
from Sloppy.Base.dataset import Dataset
from Sloppy.Lib.Signals import HasSignals


import logging
logger = logging.getLogger('Gtk.appwindow')

#------------------------------------------------------------------------------

class AppWindow( gtk.Window, HasSignals ):


    def __init__(self):
        HasSignals.__init__(self)
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_icon(self.render_icon('sloppy-Plot', gtk.ICON_SIZE_BUTTON))
        self.connect("delete-event", (lambda sender, event: globals.app.quit()))
        
        self.is_fullscreen = False
	self._windows = list() # keeps track of all subwindows
        self._windowlist_merge_id = None
        self._recentfiles_merge_id = None

        
        #
        # Create GUI
        #       
        self.toolbox = dock.Dock('Sidepane')
        self.toolbox.show()
        globals.app.sig_connect('write-config',
          lambda sender, eConfig: tools.dock_write_config(eConfig, self.toolbox))
        
        self.uimanager = uim = gtk.UIManager()        
        uihelper.add_actions(uim, "Application", self.actions_application, globals.app)
        uihelper.add_actions(uim, "AppWin", self.actions_appwin, self)
        uihelper.add_actions(uim, "Matplotlib", self.actions_matplotlib, globals.app)
        uihelper.add_actions(uim, "Gnuplot", self.actions_gnuplot, globals.app)
        uihelper.add_actions(uim, "Debug", self.actions_debug, globals.app)
        uihelper.add_actions(uim, "UndoRedo", self.actions_undoredo, globals.app)
        uihelper.add_actions(uim, "RecentFiles", self.actions_recentfiles, globals.app)     

        self._construct_logwindow()
       
        self.uimanager.add_ui_from_string(uidata.uistring_appwindow)
        self.add_accel_group(self.uimanager.get_accel_group())

        self.menubar = self.uimanager.get_widget('/MainMenu')
        self.menubar.show()

        self.toolbar = self.uimanager.get_widget('/MainToolbar')
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)
        self.toolbar.show()        

        self.init_actions()
        
        self.statusbar = gtk.Statusbar()
        self.statusbar.set_has_resize_grip(True)        
        self.statusbar.show()
        self.progressbar = gtk.ProgressBar()        
        self.progressbar.hide()

        notification_area = gtk.HBox()
        notification_area.pack_start(self.btn_cancel,False,True)
        notification_area.pack_start(self.statusbar,True,True)
        notification_area.pack_start(self.progressbar,False,True)
        notification_area.show()
    
        self.plotbook  = gtk.Notebook()
        self.plotbook.show()

        plot_area = gtk.VBox()
        plot_area.pack_start(self.plotbook, True, True)
        ##plot_area.pack_start(self.progressbar, False, False)
        ##plot_area.pack_end(self.statusbar,False, True)
        plot_area.show()
        
        self.hpaned = hpaned = gtk.HPaned()
        hpaned.pack1(plot_area, True, True)
        hpaned.pack2(self.toolbox, False, True)        
        hpaned.show()

        vbox = gtk.VBox()        
        vbox.pack_start(self.menubar, expand=False)
        vbox.pack_start(self.toolbar, expand=False)        
        vbox.pack_start(hpaned, True, True)
        vbox.pack_start(notification_area, False, False)
        ##vbox.pack_end(self.statusbar, False, True)
        vbox.show()
        self.add(vbox)

        #---
        globals.app.sig_connect("update-recent-files", lambda sender: self._refresh_recentfiles())

        #
        # Restore window size and position. The size is taken
        # either from config file or set to default.
        #
        self.set_gravity(gtk.gdk.GRAVITY_NORTH_WEST)
        self.move(0,0)        
        
        eWindow = globals.app.eConfig.find('AppWindow')
        if eWindow is not None:
            width = int(eWindow.attrib.get('width', 480))
            height = int(eWindow.attrib.get('height',320))
            position = eWindow.attrib.get('sidepane', width-120)
            self.hpaned.set_position(int(position))            
        else:
            width, height = 640,480
        self.set_size_request(480,320)
        self.resize(width, height)

    
        # register for config file
        globals.app.sig_connect("write-config", self.write_config)        

        self.show()        

    
    def _construct_logwindow(self):

        def cb_logwindow_hideshow(window, action):
            action.set_active(window.get_property('visible'))

        # logwindow is hidden by default. See _construct_uimanager if
        # you want to change this default
        logwindow = logwin.LogWindow()
        logwindow.set_transient_for(self)
        logwindow.set_destroy_with_parent(True)
        logwindow.hide()

        # logwindow specific
        def cb_toggle_logwindow(action, logwindow):
            if action.get_active() is True: logwindow.show()
            else: logwindow.hide()

        t = gtk.ToggleAction('ToggleLogwindow', 'Show Logwindow', None, None)
        t.connect("toggled", cb_toggle_logwindow, logwindow)
        uihelper.get_action_group(self.uimanager, 'Application').add_action(t)

        logwindow.connect('hide', cb_logwindow_hideshow, t)
        logwindow.connect('show', cb_logwindow_hideshow, t)
        
        return logwindow


    #------------------------------------------------------------------------------
    # Actions

    def init_actions(self):
        globals.app.sig_connect('begin-user-action', self.on_begin_action)
        globals.app.sig_connect('end-user-action', self.on_end_action)     

        # cancel button
        self.btn_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        self.btn_cancel.set_sensitive(False)
        self.btn_cancel.show()
        ##self.btn_cancel.hide()

        # connect the ESC-key to the cancel button 
        key, modifier = gtk.accelerator_parse('Escape')
        accel_group = self.uimanager.get_accel_group()        
        self.btn_cancel.add_accelerator("activate", accel_group, key, modifier, gtk.ACCEL_VISIBLE)


    def on_begin_action(self, sender, on_cancel_action=None):
        self.btn_cancel.set_sensitive(True)
        ##self.btn_cancel.show()
        self.btn_cancel.connect('clicked', \
          lambda sender: globals.app.sig_emit('cancel-user-action'))

        def stop(sender):            
            self.btn_cancel.set_sensitive(False)
            if on_cancel_action is not None:
                on_cancel_action(sender)
        globals.app.sig_connect('cancel-user-action', stop)
        
        return False # TODO: disconnect on False

    def on_end_action(self, sender):        
        self.btn_cancel.set_sensitive(False)
        ##self.btn_cancel.hide()


    #-----------------------------------------------------------------------
    # Dynamic UI

    def _refresh_undo_redo(self,*args):
        
        project = globals.app.project

        #
        # undo/redo only makes sense, if there is a project
        #
        if project is not None:
            undo_state = project.journal.can_undo()
            undo_text = "Undo: %s" % project.journal.undo_text()
            redo_state = project.journal.can_redo()
            redo_text = "Redo: %s" % project.journal.redo_text()
        else:
            undo_state = redo_state = False
            undo_text = "Undo" ; redo_text = "Redo"

        uim = self.uimanager
        
        action = uim.get_action('/MainToolbar/Undo')
        action.set_property('sensitive', undo_state )
        action = uim.get_action('/MainToolbar/Redo')
        action.set_property('sensitive', redo_state )

        undo_widget = uim.get_widget('/MainMenu/EditMenu/Undo')
        label = undo_widget.get_child()
        label.set_text_with_mnemonic( undo_text )
        
        redo_widget = uim.get_widget('/MainMenu/EditMenu/Redo')
        label = redo_widget.get_child()
        label.set_text_with_mnemonic( redo_text )


        #
        # don't allow the following actions if there is no project
        #
        state = project is not None
        actions = ['/MainMenu/FileMenu/FileSave',
                   '/MainMenu/FileMenu/FileSaveAs',
                   '/MainMenu/EditMenu',
                   '/MainMenu/FileMenu/FileClose']
        for action_name in actions:
            action = uim.get_action(action_name)
            if action is not None:
                action.set_sensitive(state)
            else:
                logger.error("Could not find action %s in ActionGroup 'Application'" % action_name)

        #
        # the following actions don't make sense if the project is unchanged
        #
        state = project is not None and project.journal.can_undo()
        actions = ['/MainMenu/FileMenu/FileSave']
        for action_name in actions:
            action = uim.get_action(action_name)
            if action is not None:
                action.set_property('sensitive', state)
            else:
                logger.error("Could not find action %s in ActionGroup 'Application'" % action_name)

        # if a redo is available, then we should display it, otherwise
        # we will check the undo.
        if redo_state is True:
            globals.app.status_msg("Finished: Reverted %s" % project.journal.redo_text())
        elif undo_state is True:
            globals.app.status_msg("Finished: %s" % project.journal.undo_text())


    def _refresh_recentfiles(self):
       
        # remove last recent files
        if self._recentfiles_merge_id is not None:
            ag = uihelper.get_action_group(self.uimanager, "DynamicRecentFiles")
            self.uimanager.remove_action_group(ag)
            self.uimanager.remove_ui(self._recentfiles_merge_id)

        # Create action group list from list of recent files.
        # The corresponding ui string is created as well.
        ui = ""
        n = 1
        ag = gtk.ActionGroup('DynamicRecentFiles')
        for file in globals.app.recent_files:
            key = 'recent_files_%d' % n
            label = os.path.basename(file)
            action = gtk.Action(key, label, None, None)
            action.connect('activate',
                           (lambda sender, filename: globals.app.load_project(filename)),
                           file)

            # the most recent file can be retrieved using <control><alt>r
            if n == 1:
                ag.add_action_with_accel(action, '<control><alt>r')
            else:
                ag.add_action(action)
            
            ui+="<menuitem action='%s'/>\n" % key
            n += 1
            
        self.uimanager.insert_action_group(ag, 0)

        # Wrap UI description.
        ui="""
        <ui>
          <menubar name='MainMenu'>
            <menu action='FileMenu'>
              <menu action='RecentFilesMenu'>
                <placeholder name='RecentFilesList'>
                  %s
                </placeholder>
               </menu>
             </menu>
          </menubar>
        </ui>
        """ % ui
            
        self._recentfiles_merge_id = self.uimanager.add_ui_from_string(ui)


                
            
    #--- SUBWINDOW HANDLING -------------------------------------------------------
    
    def _cb_subwindow_present(self, widget, window):
        self.subwindow_present(window)
       
    def subwindow_add(self, window):
        window.connect("destroy", self.subwindow_detach)
        self._windows.append(window)
        return window

    def subwindow_detach(self, window):
        self._windows.remove(window)
    def subwindow_present(self, window):
        window.present()

    def subwindow_match(self, condition):
        try:
            return [win for win in self._windows if condition(win)][0]                
        except IndexError:
            return None

    #----------------------------------------------------------------------
    # PLOTWINDOW HANDLING

    def find_plotwidget(self, project, plot):
        try:
            widgets = self.plotbook.get_children()
            return [widget for widget in widgets \
                    if isinstance(widget, mpl.MatplotlibWidget) \
                    and widget.project == project \
                    and widget.plot == plot][0]
        except IndexError:
            return None
        
    def add_plotwidget(self, widget):
        n = self.plotbook.append_page(widget)
        self.plotbook.set_tab_label_text(widget, "Plot")

        ### TODO: this signal should be a gobject signal
        ### TODO: Does this actually work?
        ##widget.connect("closed", self.detach_plotwidget)       

        for ag in widget.actiongroups:            
            self.uimanager.insert_action_group(ag,0)            
        self.add_accel_group(self.uimanager.get_accel_group())
        self.uimanager.add_ui_from_string(widget.uistring)


    def detach_plotwidget(self, widget):
        self.plotbook.remove(widget)
        #self.uimanager.remove_ui

    
    # ----------------------------------------------------------------------
    # MISC CALLBACKS


    def on_action_ToggleFullscreen(self, action):
        if self.is_fullscreen is True:
            self.unfullscreen()
        else:
            self.fullscreen()
        self.is_fullscreen = not self.is_fullscreen
    

    def _cb_help_about(self, action):
        " Display a help dialog with version and copyright information. "
        dialog = gtk.AboutDialog()
        dialog.set_name(version.NAME)
        dialog.set_version(version.VERSION)
        dialog.set_comments(version.DESCRIPTION)
        dialog.set_copyright(version.COPYRIGHT)
        dialog.set_license("\n\n\n".join(version.LICENSES))
        dialog.set_website(version.URL)
        #dialog.set_website_label("Heh?")
        dialog.set_authors(version.AUTHORS)
        #dialog.set_documenters(["Documenters"])
        #dialog.set_artists(["Artists"])
        #dialog.set_translator_credits("Whoever translated")
        #dialog.set_log_icon_name("SloppyPlot")
        path = os.path.join(globals.app.path.icon_dir, "Plot.png")
        logo = gtk.gdk.pixbuf_new_from_file(path)
        dialog.set_logo(logo)

        dialog.run()
        dialog.destroy()


    def write_config(self, app, eConfig):
        eWindow = eConfig.find('AppWindow')
        if eWindow is None:
            eWindow = SubElement(eConfig, "AppWindow")
        else:
            eWindow.clear()

        width, height = self.get_size()
        eWindow.attrib['width'] = str(width)
        eWindow.attrib['height'] = str(height)
        eWindow.attrib['sidepane'] = str(self.hpaned.get_position())

        
    #----------------------------------------------------------------------

    actions_application = [
        ('FileMenu', None, '_File'),
        ('FileNew', gtk.STOCK_NEW, '_New', '<control>N', 'Create a new file', '_cb_project_new'),
        ('FileOpen', gtk.STOCK_OPEN, '_Open', '<control>O', 'Open project', '_cb_project_open'),
        ('Quit', gtk.STOCK_QUIT, '_Quit', '<control>Q', 'Quit application', '_cb_quit_application'),
        ('HelpMenu', None, '_Help'),
        ('FileSave', gtk.STOCK_SAVE, '_Save', '<control>S', 'Save project', '_cb_project_save'),
        ('FileSaveAs', gtk.STOCK_SAVE_AS, 'Save _As', None, 'Save project under another filename', '_cb_project_save_as'),
        ('FileClose', gtk.STOCK_CLOSE, '_Close', '<control>W', 'Close the file', '_cb_project_close'),
        ('EditMenu', None, '_Edit'),
        ('EditCut', gtk.STOCK_CUT, 'Cut', '<control>X', 'Cut Selection', '_cb_edit_cut'),
        ('EditCopy', gtk.STOCK_COPY, 'Copy', '<control>C', 'Copy Selection', '_cb_edit_copy'),
        ('EditPaste', gtk.STOCK_PASTE, 'Paste', '<control>Y', 'Paste Selection', '_cb_edit_paste'),
        ('Delete', gtk.STOCK_DELETE, 'Delete', 'Delete', 'Delete Selection', '_cb_delete'),
        ('ViewMenu', None, '_View'),
        ('Plot', None, '_Plot', '<control>P', 'Plot the currently selected object with the default backend.', '_cb_plot'),
        ('PlotBackendMenu', None, 'Plot via backend'),
        ('NewPlot', None, 'New Plot', None, 'Create new Plot', '_cb_new_plot'),
        ('DatasetToPlot', None, 'Create Plot from Dataset', None, 'Create a new Plot object from the current Dataset', 'on_action_DatasetToPlot'),
        ('DatasetAddToPlot', None, 'Add Datasets to Plot', None, 'Add Datasets to Plot', '_cb_add_datasets_to_plot'),
        ('DatasetImport', None, 'Import Dataset', '<control>I', 'Import a dataset', '_cb_import_dataset'),
        ('NewDataset', gtk.STOCK_ADD, 'New Dataset', None, 'Create a new dataset', '_cb_new_dataset'),
        ('ViewMetadata', None, 'View Metadata', None, 'View Metadata', 'on_action_ViewMetadata'),
        #
        ('Preferences', gtk.STOCK_PREFERENCES, '_Preferences...', '<control>P', "Modify Preferences", 'on_action_Preferences'),
        ]

    actions_appwin = [                
        ('About', gtk.STOCK_ABOUT, '_About', None, 'About application', '_cb_help_about'),
        ('ToggleFullscreen', None, 'Fullscreen Mode', 'F11', '', 'on_action_ToggleFullscreen')        
        ]
    
    actions_matplotlib = [
        ('PlotBackendMatplotlib', None, 'Matplotlib', None, 'Plot current plot via matplotlib.', '_cb_plot_matplotlib'),
        ]

    actions_gnuplot = [
        ('PlotBackendGnuplot', None, 'gnuplot', None, 'Plot current plot via gnuplot. ', '_cb_plot_gnuplot'),
        ('ExportViaGnuplot', None, 'Export via gnuplot...', None, 'Export the current plot via Gnuplot as postscript file.', 'on_action_export_via_gnuplot')
        ]

    actions_debug = [
        ('ObjectMenu', None, '_Object'),
        ('Edit', gtk.STOCK_EDIT, '_Edit', '<control>E', 'Edit the currently selected object.', '_cb_edit'),
        ('DebugMenu', None, 'Debug'),
        ('WindowList', None, 'Windows...'),
        ]

    actions_undoredo = [
        ('Undo', gtk.STOCK_UNDO, 'Undo', '<control>Z', 'Undo last action', '_cb_undo'),
        ('Redo', gtk.STOCK_REDO, 'Redo', '<control><shift>z', 'Redo','_cb_redo')
        ]

    actions_recentfiles = [
        ('RecentFilesMenu', None, 'Recent Files'),
        ('RecentFilesClear', None, 'Clear Recent Files', None, None, '_cb_recent_files_clear')
        ]

