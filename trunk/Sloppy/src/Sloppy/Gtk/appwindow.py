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


import os
import gtk

from logwin import LogWindow
from treeview import ProjectTreeView
import uihelper

import tools

import Sloppy

from Sloppy.Base import utils, error, version, config
from Sloppy.Base.objects import Plot
from Sloppy.Base.dataset import Dataset
from Sloppy.Base.backend import BackendRegistry

from Sloppy.Gtk.mpl_window import MatplotlibWidget

from Sloppy.Lib.ElementTree.ElementTree import Element, SubElement


#------------------------------------------------------------------------------
import logging
logger = logging.getLogger('Gtk.appwindow')




class AppWindow( gtk.Window ):

    def __init__(self, app):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

        self.app = app
	self._windows = list() # keeps track of all subwindows

        self._windowlist_merge_id = None
        self._recentfiles_merge_id = None

        self.app.sig_connect("write-config", self.write_appwindow_config)

        # restore position
        self.set_gravity(gtk.gdk.GRAVITY_NORTH_WEST)
        self.move(0,0)        

        # TODO: read config data
        eWindow = app.eConfig.find('AppWindow')
        if eWindow is not None:
            try:
                x = int(eWindow.attrib['width'])
                y = int(eWindow.attrib['height'])
                self.set_size_request(width, height)
            except KeyError:
                pass

        icon = self.render_icon('sloppy-Plot', gtk.ICON_SIZE_BUTTON)
        self.set_icon(icon)

        self.connect("delete-event", (lambda sender, event: app.quit()))
        #self.connect("destroy", (lambda sender: app.quit()))

        self.uimanager = self._construct_uimanager()
        self._construct_logwindow()
        self.toolbox = self._construct_toolbox()

        # and build ui
        self.uimanager.add_ui_from_string(self.ui_string)
        self.add_accel_group(self.uimanager.get_accel_group())
        
        self._construct_menubar()
        self._construct_toolbar()
        self._construct_treeview()
        self._construct_statusbar()

        self.plotbook  = gtk.Notebook()
        self.plotbook.show()

        hpaned = gtk.HPaned()
        hpaned.pack1(self.treeview_window, True, True)
#        hpaned.pack2(self.plotbook, True, True)
        hpaned.show()


        
        ##vpaned = gtk.VPaned()
        ##vpaned.pack1(self.treeview_window,True,True)
        ###vpaned.pack2(self.logwidget,False,True)
        ##vpaned.show()
        
        # Set up vbox to hold everything...
        vbox = gtk.VBox()
        vbox.pack_start(self.menubar, expand=False)
        vbox.pack_start(self.toolbar, expand=False)        
        ###vbox.pack_start(self.treeview_window, expand=True, fill=True)
        vbox.pack_start(hpaned, True, True)
        vbox.pack_end(self.statusbar, expand=False)
        vbox.show()

        # ...and add vbox to the window.
        self.add( vbox )        
        self.show()        


        self._refresh_windowlist()
        self.app.sig_connect("update-recent-files", (lambda sender: self._refresh_recentfiles()))

    def _construct_uimanager(self):

        uim = gtk.UIManager()
        
        uihelper.add_actions(uim, "Application", self.actions_application, self.app)
        uihelper.add_actions(uim, "AppWin", self.actions_appwin, self)
        uihelper.add_actions(uim, "Matplotlib", self.actions_matplotlib, self.app)
        uihelper.add_actions(uim, "Gnuplot", self.actions_gnuplot, self.app)
        uihelper.add_actions(uim, "Debug", self.actions_debug, self.app)
        uihelper.add_actions(uim, "UndoRedo", self.actions_undoredo, self.app)
        uihelper.add_actions(uim, "RecentFiles", self.actions_recentfiles, self.app)

        return uim
        

    def _construct_menubar(self):
        menubar = self.uimanager.get_widget('/MainMenu')
        menubar.show()

        self.menubar = menubar
        return menubar


    def _construct_toolbar(self):        
        toolbar = self.uimanager.get_widget('/MainToolbar')
        toolbar.set_style(gtk.TOOLBAR_ICONS)
        toolbar.show()
        
        self.toolbar = toolbar
        return toolbar

    def _construct_treeview(self):       
        treeview = ProjectTreeView(self.app)
        treeview.connect( "row-activated", self._cb_row_activated )
        treeview.connect( "button-press-event", self._cb_button_pressed )
        treeview.connect( "popup-menu", self.popup_menu, 3, 0 )
        treeview.show()

        # the treeview is put into a scrolled window
        treeview_window = gtk.ScrolledWindow()
        treeview_window.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        treeview_window.add(treeview)
        treeview_window.show()

        self.treeview = treeview
        self.treeview_window = treeview_window
        return (treeview, treeview_window)

        
    def _construct_statusbar(self):
        statusbar = gtk.Statusbar()
        statusbar.set_has_resize_grip(True)        
        statusbar.show()

        self.statusbar = statusbar
        return statusbar


    def _construct_toolbox(self):

        window = tools.Toolbox(self.app, None)
        window.set_transient_for(self)
        window.set_destroy_with_parent(True)
        window.hide()

        def cb_toggle_window(action, window):
            if action.get_active() is True: window.show()
            else: window.hide()        
        t = gtk.ToggleAction('ToggleToolbox', 'Show tools window', None, None)
        t.connect("toggled", cb_toggle_window, window)
        uihelper.get_action_group(self.uimanager, 'Application').add_action(t)

        def on_window_visibility_toggled(window, action):
            action.set_active(window.get_property('visible'))
        window.connect('hide', on_window_visibility_toggled, t)
        window.connect('show', on_window_visibility_toggled, t)

        def on_notify_project(sender, project, toolwin):
            toolwin.set_project(project)
        self.app.sig_connect('notify::project', on_notify_project, window)
        
        return window

    
    def _construct_logwindow(self):

        def cb_logwindow_hideshow(window, action):
            action.set_active(window.get_property('visible'))

        # logwindow is hidden by default. See _construct_uimanager if
        # you want to change this default
        logwindow = LogWindow()
        logwindow.set_transient_for(self)
        logwindow.set_destroy_with_parent(True)
        logwindow.hide()

        # logwindow specific
        def cb_toggle_logwindow(action, logwindow):
            if action.get_active() is True: logwindow.show()
            else: logwindow.hide()

        t = gtk.ToggleAction('ToggleLogwindow', 'Show debug window', None, None)
        t.connect("toggled", cb_toggle_logwindow, logwindow)
        uihelper.get_action_group(self.uimanager, 'Application').add_action(t)

        logwindow.connect('hide', cb_logwindow_hideshow, t)
        logwindow.connect('show', cb_logwindow_hideshow, t)
        
        return logwindow


    #-----------------------------------------------------------------------
    # Dynamic UI

    def _refresh_undo_redo(self,*args):
        
        project = self.app.project

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
                   '/MainMenu/DatasetMenu',
                   '/MainMenu/PlotMenu',
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
            
        

    def _refresh_windowlist(self):      

        # We are going to recreate the actiongroup 'WindowList'.
        # To avoid adding this actiongroup multiple times, we need
        # to remove it first.
        if self._windowlist_merge_id is not None:
            ag = uihelper.get_action_group(self.uimanager, "DynamicWindowList")
            self.uimanager.remove_action_group(ag)
            self.uimanager.remove_ui(self._windowlist_merge_id)
            
        # Create action groups list from windowlist.
        # The corresponding ui string is created as well.
        ui = ""
        ag =  gtk.ActionGroup('DynamicWindowList')
        for window in self._windows:            
            title = window.get_title() or "noname"
            logger.debug("Window title is %s" % title)
            action = gtk.Action(id(window), title, None, None)
            action.connect('activate', self._cb_subwindow_present, window)
            ag.add_action(action)
            ui+="<menuitem action='%s'/>\n" % id(window)
        self.uimanager.insert_action_group(ag,0)

        # Wrap UI description.
        ui="""
        <ui>
          <menubar name='MainMenu'>
            <menu action='ViewMenu'>
            %s
            </menu>
          </menubar>
        </ui>
        """ % ui
                       
        self._windowlist_merge_id = self.uimanager.add_ui_from_string(ui)                      


    def _refresh_recentfiles(self):
       
        # remove last recent files
        if self._recentfiles_merge_id is not None:
            ag = uihelper.get_action_group(self.uimanager, "DynamicRecentFiles")
            self.uimanager.remove_action_group(ag)
            self.uimanager.remove_ui(self._recentfiles_merge_id)

        # Create action group list from list of recent files.
        # The corresponding ui string is created as well.
        ui = ""
        n = 0
        ag = gtk.ActionGroup('DynamicRecentFiles')
        for file in self.app.recent_files:
            key = 'recent_files_%d' % n
            action = gtk.Action(key, '%d: %s' % (n, os.path.basename(file)), None, None)
            action.connect('activate',
                           (lambda sender, filename: self.app.load_project(filename)),
                           file)
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
        window.connect("notify::title", self._refresh_windowlist)
        self._refresh_windowlist()
        return window

    def subwindow_detach(self, window):
        self._windows.remove(window)
        self._refresh_windowlist()
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
                    if isinstance(widget, MatplotlibWidget) \
                    and widget.project == project \
                    and widget.plot == plot][0]
        except IndexError:
            return None
        
    def add_plotwidget(self, widget):
        n = self.plotbook.append_page(widget)
        self.plotbook.set_tab_label_text(widget, "Plot")

        # TODO: this signal should be a gobject signal
        # TODO: Does this actually work?
        widget.connect("closed", self.detach_plotwidget)       

        for ag in widget.get_actiongroups():            
            self.uimanager.insert_action_group(ag,0)            
        self.add_accel_group(self.uimanager.get_accel_group())
        self.uimanager.add_ui_from_string(widget.get_uistring())


    def detach_plotwidget(self, widget):
        self.plotbook.remove(widget)
        #self.uimanager.remove_ui

    
    # ----------------------------------------------------------------------
    # MISC CALLBACKS

        
    def _cb_rename_item(self, action):
        self.treeview.start_editing_key()

        
    def _cb_row_activated(self,widget,*udata):
        """
        plot -> plot item
        dataset -> edit dataset
        """
        (plots, datasets) = widget.get_selected_plds()
        for plot in plots:
            self.app.plot(plot)
        for ds in datasets:
            self.app.edit_dataset(ds)

        
    def _cb_button_pressed(self, widget, event):
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

        return self.popup_menu(widget,event.button,event.time)
                
            

    def popup_menu(self, widget, button, time):
        " Returns True if a popup has been popped up. "
        # create popup menu according to object type
        objects = widget.get_selected_objects()
        if len(objects) == 0:
            popup = self.uimanager.get_widget('/popup_empty')
        else:
            object = objects[0]
            if isinstance(object,Plot):
                popup = self.uimanager.get_widget('/popup_plot')
            elif isinstance(object,Dataset):
                popup = self.uimanager.get_widget('/popup_dataset')
            else:
                return False

        if popup is not None:
            popup.popup(None,None,None,button,time)
            return True
        else:
            return False


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
        path = os.path.join(self.app.path.get('icon_dir'), "Plot.png")
        logo = gtk.gdk.pixbuf_new_from_file(path)
        dialog.set_logo(logo)

        dialog.run()
        dialog.destroy()

    # for config file
    def write_appwindow_config(self, app):
        eAppWindow = app.eConfig.find('AppWindow')
        if eAppWindow is None:
            eAppWindow = SubElement(app.eConfig, "AppWindow")
        else:
            eAppWindow.clear()

        # according to the pygtk documentation, we should never
        # use self.get_size(), though I don't see any other way
        # to obtain the window size.  I guess I need to ask about this.
        
        #width, height = self.get_position()
        #eAppWindow.attrib['width'] = str(width)
        #eAppWindow.attrib['height'] = str(height)

        
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
        ('PlotMenu', None, '_Plot'),
        ('Plot', None, '_Plot', '<control>P', 'Plot the currently selected object with the default backend.', '_cb_plot'),
        ('PlotBackendMenu', None, 'Plot via backend'),
        ('NewPlot', None, 'New Plot', None, 'Create new Plot', '_cb_new_plot'),
        ('DatasetMenu', None, 'Dataset'),
        ('DatasetToPlot', None, 'Create Plot from Dataset', None, 'Create a new Plot object from the current Dataset', '_cb_create_plot_from_datasets'),
        ('DatasetAddToPlot', None, 'Add Datasets to Plot', None, 'Add Datasets to Plot', '_cb_add_datasets_to_plot'),
        ('DatasetImport', None, 'Import Dataset', '<control>I', 'Import a dataset', '_cb_import_dataset'),
        ('NewDataset', gtk.STOCK_ADD, 'New Dataset', None, 'Create a new dataset', '_cb_new_dataset'),
        ('ExperimentalPlot', None, 'Create Multiplot (EXPERIMENTAL!)', None, None, '_cb_experimental_plot'),
        #
        ('Preferences', gtk.STOCK_PREFERENCES, '_Preferences...', None, "Modify Preferences", 'on_action_Preferences'),
        ]

    actions_appwin = [        
        ('RenameItem', None, 'Rename', 'F2', 'Rename', '_cb_rename_item'),
        ('About', gtk.STOCK_ABOUT, '_About', None, 'About application', '_cb_help_about')
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
    #----------------------------------------------------------------------
    ui_string = \
    """
    <ui>
      <menubar name='MainMenu'>
        <menu action='FileMenu'>
          <menuitem action='FileNew'/>
          <menuitem action='FileOpen'/>
          <menu action='RecentFilesMenu'>
            <placeholder name='RecentFilesList'/>
            <separator/>
            <menuitem action='RecentFilesClear'/>            
          </menu>
          <separator/>
          <menuitem action='FileSave'/>
          <menuitem action='FileSaveAs'/>
          <separator/>
          <menuitem action='FileClose'/>
          <menuitem action='Quit'/>
        </menu>
        <menu action='EditMenu'>        
          <menuitem action='Undo'/>
          <menuitem action='Redo'/>
          <separator/>
          <menuitem action='Edit'/>
          <menuitem action='RenameItem'/>          
          <menuitem action='Delete'/>
          <separator/>
          <menuitem action='Preferences'/>
        </menu>
        <menu action='DatasetMenu'>
          <menuitem action='NewDataset'/>   
          <menuitem action='DatasetImport'/>
          <separator/>
          <menuitem action='DatasetToPlot'/>
          <menuitem action='DatasetAddToPlot'/>
        </menu>
        <menu action='PlotMenu'>
          <menuitem action='Plot'/>
          <menu action='PlotBackendMenu'>
             <menuitem action='PlotBackendGnuplot'/>
             <menuitem action='PlotBackendMatplotlib'/>
          </menu>
          <menuitem action='ExportViaGnuplot'/>
          <separator/>
          <menuitem action='NewPlot'/>
          <menuitem action='DatasetToPlot'/>
          <separator/>
          <menuitem action='ExperimentalPlot'/>
        </menu>
        <menu action='ViewMenu'>
          <menuitem action='ToggleToolbox'/>
          <menuitem action='ToggleLogwindow'/>          
          <separator/>
        </menu>        
        <menu action='HelpMenu'>
          <menuitem action='About'/>
        </menu>
      </menubar>
      <toolbar name='MainToolbar'>
        <toolitem action='FileNew'/>
        <toolitem action='FileOpen'/>
        <toolitem action='FileSave'/>
        <separator/>
        <toolitem action='Undo'/>
        <toolitem action='Redo'/>
        <separator/>
        <toolitem action='Quit'/>
      </toolbar>
      <popup name="popup_plot">
        <menuitem action='Plot'/>
        <menu action='PlotBackendMenu'>
           <menuitem action='PlotBackendGnuplot'/>
           <menuitem action='PlotBackendMatplotlib'/>
        </menu>
        <menuitem action='ExportViaGnuplot'/>
        <separator/>
        <menuitem action='Edit'/>
        <menuitem action='RenameItem'/>
        <separator/>        
        <menuitem action='Delete'/>
      </popup>
      <popup name="popup_dataset">
        <menuitem action='Edit'/>
        <menuitem action='RenameItem'/>
        <separator/>      
        <menuitem action='DatasetToPlot'/>
        <menuitem action='DatasetAddToPlot'/>
        <separator/>
        <menuitem action='Delete'/>
        <separator/>
      </popup>
      <popup name="popup_empty">
        <menuitem action='NewDataset'/>
        <menuitem action='NewPlot'/>
      </popup>
    </ui>
    """
