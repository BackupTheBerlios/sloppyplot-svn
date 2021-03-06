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


import gtk
import gobject

import uihelper
import mpl_selector

from matplotlib.backends.backend_gtk import FileChooserDialog


from Sloppy.Base import uwrap
from Sloppy.Base.backend import BackendRegistry
from Sloppy.Base.plugin import PluginRegistry

from Sloppy.Lib.Undo import UndoList, NullUndo, ulist




class MatplotlibWindow( gtk.Window ):

    actions_dict = {
        'MenuPlaceholders':
        [
        ('EditMenu', None, '_Edit'),
        ('PlotMenu', None, '_Plot'),
        ('DisplayMenu', None, '_Display'),
        ('AnalysisMenu', None, '_Analysis')
        ],        #
        'MatplotlibWindow':
        [
        ('Close', gtk.STOCK_CLOSE, '_Close', 'q', 'Close this Window', '_cb_close')
        ],
        'ViewMenu':
        [
        ('ViewMenu', None, '_View'),
        ('Fullscreen', None, 'Fullscreen Mode', 'F11', '', '_cb_fullscreen')
        ]
        }

    uistring = """
    <ui>
      <menubar name='MainMenu'>
        <menu action='PlotMenu'>
          <placeholder name='PlotMenuActions'/>
          <separator/>
          <menuitem action='Close'/>
        </menu>
        <menu action='EditMenu'>
          <menuitem action='Undo'/>
          <menuitem action='Redo'/>
        </menu>
        <menu action='DisplayMenu'/>
        <menu action='AnalysisMenu'/>       
        <menu action='ViewMenu'>
          <menuitem action='ToggleToolbox'/>
          <separator/>
          <menuitem action='Fullscreen'/>
        </menu>
      </menubar>
      <toolbar name='MainToolbar'>
        <placeholder name='MainToolbarEdit'/>
        <toolitem action='ToggleToolbox'/>
        <separator/>
        <toolitem action='Undo'/>
        <toolitem action='Redo'/>
        <separator/>              
      </toolbar>
    </ui>
    """


    
    def __init__(self, app, project, plot):

        gtk.Window.__init__(self)
        self.set_default_size(640,480)

        self.is_fullscreen = False
        self.app = app
        self.disabled_groups = list()
        
        self.mpl_widget = MatplotlibWidget(app, project, plot)
        
        # set up ui manager
        self.uimanager = gtk.UIManager()        
       
        # add undo/redo ui from application window
        ag = uihelper.get_action_group(self.app.window.uimanager, 'UndoRedo')
        self.uimanager.insert_action_group(ag,0)
        
        # add action group from window
        for ag in uihelper.construct_actiongroups(self.actions_dict, map=self):
            self.uimanager.insert_action_group(ag,0)

        # add action group for toolbox
        toolbox = self.app.window.toolbox
        def on_toggled(action, window):
            if action.get_active() is True:
                window.show()
            else:
                window.hide()
        t = gtk.ToggleAction('ToggleToolbox', 'Toolbox', 'ToggleToolbox visibility', gtk.STOCK_PROPERTIES)
        t.connect("toggled", on_toggled, toolbox)
        uihelper.get_action_group(self.uimanager, 'ViewMenu').add_action(t)
        t.set_active(toolbox.get_property('visible'))

        # ...and now that all action groups are created,
        # we can create the actual ui for the window 
        self.uimanager.add_ui_from_string(self.uistring)

        # add ui information from subwidget
        for ag in self.mpl_widget.get_actiongroups():
            self.uimanager.insert_action_group(ag,0)
        self.uimanager.add_ui_from_string(self.mpl_widget.get_uistring())

        # and set up accelerators for all of the above
        accel_group = self.uimanager.get_accel_group()
        self.add_accel_group(accel_group)

        # connect the ESC-key to the mpl widget's cancel button 
        key, modifier = gtk.accelerator_parse('Escape')
        self.mpl_widget.btn_cancel.add_accelerator("activate", accel_group, key, modifier, gtk.ACCEL_VISIBLE)
        
        # construct menubar 
        menubar = self.uimanager.get_widget('/MainMenu')
        menubar.show()

        # construct toolbar
        toolbar = self.uimanager.get_widget('/MainToolbar')
        toolbar.set_style(gtk.TOOLBAR_ICONS)
        toolbar.show()        

        # put everything in a vertical box
        vbox = gtk.VBox()
        vbox.pack_start(menubar, False, True)
        vbox.pack_start(toolbar, False, True)
        vbox.pack_start(self.mpl_widget, True, True)
        self.add(vbox)

        #self.set_title( "Plot: %s" % plot.key )
        
        self.mpl_widget.show()
        vbox.show()

        self.mpl_widget.connect("edit-mode-started", self.disable_interaction)
        self.mpl_widget.connect("edit-mode-ended", self.enable_interaction)
                                      
        self.connect("destroy", (lambda sender: self.destroy()))
        self.mpl_widget.connect("destroy", (lambda sender: self.destroy()))
        

    def destroy(self):
        self.mpl_widget.set_plot(None)
        gtk.Window.destroy(self)



    def disable_interaction(self, widget):
        " Disable most user interaction. "        
        actiongroups = self.uimanager.get_action_groups()
        for actiongroup in actiongroups:
            if actiongroup.get_name() in ['ViewMenu']:
                continue
            if actiongroup.get_sensitive() is True:
                actiongroup.set_sensitive(False)
                self.disabled_groups.append(actiongroup)               


    def enable_interaction(self, widget):
        " Re-enable all interaction disabled by disable_interaction. "
        for actiongroup in self.disabled_groups:
            actiongroup.set_sensitive(True)
        self.disabled_groups = list()

        

    def get_project(self):
        return self.mpl_widget.project

    def get_plot(self):
        return self.mpl_widget.plot

    def get_backend(self):
        return self.mpl_widget.backend


    #----------------------------------------------------------------------
    # CALLBACKS
    
    def _cb_fullscreen(self, action):
        " Toggle fullscreen mode. "
        if self.is_fullscreen is True:
            self.unfullscreen()
        else:
            self.fullscreen()
        self.is_fullscreen = not self.is_fullscreen

    def _cb_close(self, action):
        self.destroy()









class MatplotlibWidget(gtk.VBox):


    __gsignals__ = {
        'edit-mode-started' : (gobject.SIGNAL_RUN_FIRST , gobject.TYPE_NONE, ()),
        'edit-mode-ended' : (gobject.SIGNAL_RUN_FIRST , gobject.TYPE_NONE, ())        
        }

    
    actions_dict = {
        'Plot':
        [
        ('PlotMenu', None, '_Plot'),
        ('Replot', 'sloppy-replot', '_Replot', '<control>R', 'Replot', 'on_action_Replot'),
        ('EditLayer', gtk.STOCK_PROPERTIES, '_Edit Layer', '<control>E', 'Edit Layer', 'on_action_EditLayer'),
        ('ExportViaMPL', gtk.STOCK_SAVE_AS, 'Export via matplotlib...', None, 'Export via Matplotlib', 'on_action_ExportViaMPL'),
        ('ExportViaGnuplot', gtk.STOCK_SAVE_AS, 'Export via gnuplot...', None, 'Export via Gnuplot', 'on_action_ExportViaGnuplot'),
        ],
        'Analysis':
        [
        ('AnalysisMenu', None, '_Analysis')
        ],
        'Display':
        [
        ('DisplayMenu', None, '_Display'),
        ('ZoomIn', gtk.STOCK_ZOOM_IN, '_Zoom In', 'plus', 'Zoom', 'on_action_ZoomIn'),
        ('ZoomOut', gtk.STOCK_ZOOM_OUT, '_Zoom Out', 'minus', 'Zoom', 'on_action_ZoomOut'),
        ('ZoomFit', gtk.STOCK_ZOOM_FIT, '_Zoom Fit', '0', 'Zoom', 'on_action_ZoomFit'),
        ('ZoomRect', gtk.STOCK_ZOOM_FIT, '_Zoom Rectangle', 'r', 'Zoom', 'on_action_ZoomRect'),
        ('ToggleLogScaleY', None, 'Toggle Logarithmic Scale', 'l', 'Toggle Logscale', 'on_action_ToggleLogScaleY'),
        ('MoveAxes', None, 'Move Plot', 'm', '', 'on_action_MoveAxes'),
        ('DataCursor', None, 'Data Cursor (EXPERIMENTAL!)', 'c', '', 'on_action_DataCursor'),
        ('SelectLine', None, 'Select Line', 's', '', 'on_action_SelectLine'),
        ('ZoomAxes', None, 'Zoom Axes', 'z', '', 'on_action_ZoomAxes')
        ],
        'Experimental':
        [
        ('PeakFinder', None, 'Find Peaks (EXPERIMENTAL!)', None, '', 'on_action_PeakFinder')
        ]
        }

    uistring = """
    <ui>    
      <menubar name='MainMenu'>      
        <menu action='PlotMenu'>
          <placeholder name='PlotMenuActions'>
            <menuitem action='Replot'/>
            <menuitem action='EditLayer'/>
            <separator/>
            <menuitem action='ExportViaMPL'/>
            <menuitem action='ExportViaGnuplot'/>
          </placeholder>
        </menu>        
        <menu action='AnalysisMenu'>
          <menuitem action='DataCursor'/>
          <separator/>
          <menuitem action='PeakFinder'/>
        </menu>        
        <menu action='DisplayMenu'>
          <menuitem action='ToggleLogScaleY'/>
          <separator/>
          <menuitem action='ZoomRect'/>
          <menuitem action='ZoomIn'/>
          <menuitem action='ZoomOut'/>
          <menuitem action='ZoomFit'/>
          <menuitem action='ZoomAxes'/>          
          <separator/>
          <menuitem action='MoveAxes'/>
          <menuitem action='SelectLine'/>
        </menu>        
      </menubar>      
      <toolbar name='MainToolbar'>
        <placeholder name='MainToolbarEdit'>
        <toolitem action='EditLayer'/>
        </placeholder>
        <toolitem action='ZoomRect'/>
        <separator/>              
        <toolitem action='Replot'/>
      </toolbar>
    </ui>
    """



    def __init__(self, app, project, plot):
        gtk.VBox.__init__(self)

        self._current_selector = None
        
        self.app = app

        self._construct_actiongroups()        
        self.statusbar = self._construct_statusbar()
        self.coords = self._construct_coords()

        self.btn_cancel = self._construct_cancel_button()

        self.context_id = self.statusbar.get_context_id("coordinates")
        #self.statusbar.push(self.context_id, "X: 10, Y: 20")
        #self.statusbar.pop(self.context_id)
        
        vbox = self.vbox = gtk.VBox()
        hbox = gtk.HBox()
        hbox.pack_start(self.btn_cancel, False, padding=4)
        hbox.pack_start(self.coords, False, padding=4)
        hbox.pack_start(self.statusbar, padding=4)
        hbox.show()
        vbox.pack_end(hbox, False, True)
        vbox.show()

        self.add(vbox)

        # set up project/plot
        self.project = project        
        self.plot = None
        self.backend = None
        self.cursor = None

        self._signals = []
        self.cblist = []

        self.set_plot(plot)
        self.project.sig_connect("close", (lambda sender: self.destroy()))

        # set up file selector for export dialog
        # TODO: this could be put into a plugin, since it is desirable to have
        # TODO: such a method in the shell frontend as well.
        self.fileselect = FileChooserDialog(title='Save the figure', parent=None)



    def _construct_actiongroups(self):
        actiongroups = list()
        for key, actions in self.actions_dict.iteritems():
            ag = gtk.ActionGroup(key)
            ag.add_actions( uihelper.map_actions(actions, self) )
            actiongroups.append(ag)
        self.actiongroups = actiongroups

    def get_actiongroups(self):
        return self.actiongroups

    def get_uistring(self):
        return self.uistring




    def _construct_statusbar(self):
        statusbar = gtk.Statusbar()
        statusbar.show()
        return statusbar

    def _construct_coords(self):
        label = gtk.Label()
        label.show()
        return label 

    def _construct_cancel_button(self):
        button = gtk.Button(stock=gtk.STOCK_CANCEL)
        button.set_sensitive(False)
        button.show()
        return button
        
        

    #----------------------------------------------------------------------
    def set_coords(self, x, y):
        if x is not None and y is not None:
            self.coords.set_text("X: %1.2f, Y: %1.2f" % (x,y))
        else:
            self.coords.set_text("invalid coordinates")
        
    def set_plot(self, plot):
        # TODO: remove old plot
        # TODO: connect to plot's title    

        if plot is not None:
            backend = self.project.request_backend('matplotlib', plot=plot)

            #backend.canvas.set_size_request(800, 600)
            sw = uihelper.add_scrollbars(backend.canvas, viewport=True)
            sw.show()
            self.vbox.pack_start(sw)
        else:
            backend = None
           
        # disconnect old stuff
        if self.backend is not None and self.backend != backend:
            self.backend.disconnect()

        for cb in self.cblist:
            cb.disconnect()
        self.cblist = []
        
        if self.cursor is not None:
            self.cursor.finish()

        # connect new backend
        self.plot = plot
        self.backend = backend


        if backend is not None:
            self.cblist += [
                plot.sig_connect("changed", (lambda sender: backend.draw())),
                plot.sig_connect("closed", (lambda sender: self.destroy())),
                backend.sig_connect("closed", (lambda sender: self.destroy()))
                ]
            
            try:
                backend.draw()
            except:
                #gtkutils.info_msg("Nothing to plot.")
                raise            

            # Cursor
            self.cursor = mpl_selector.Cursor(self.backend.figure)
            self.cursor.sig_connect("move", (lambda sender,x,y: self.set_coords(x,y)))
            self.cursor.init()

        
    #----------------------------------------------------------------------
    def on_action_Replot(self, action):
        self.backend.draw()

    def on_action_EditLayer(self, action):
        self.app.edit_layer( self.plot, self.backend.layer )

    #----------------------------------------------------------------------

    def zoom_to_region(self, layer, region, undolist=[]):
       
        ul = UndoList().describe("Zoom Region")

        x0 = min( region[0], region[2] )
        x1 = max( region[0], region[2] )
            
        y0 = min( region[1], region[3] )
        y1 = max( region[1], region[3] )

        # Do not zoom if x0 == x1 or if y0 == y1, because
        # otherwise matplotlib will mess up.  Of course, if x0 and
        # x1 are None (or y0 and y1), i.e. if autoscale is turned on,
        # then it is ok to zoom.
        if ((x0 is not None) and (x0 == x1)) or \
           ((y0 is not None) and (y0 == y1)):            
            ul.append( NullUndo() )
            return          

        def set_axis(axis, start, end):
            if axis.start is not None and axis.end is not None:
                swap_axes = axis.start > axis.end
            else:
                swap_axes = False

            if swap_axes is True:
                _start, _end = end, start
            else:
                _start, _end = start, end
                
            uwrap.set(axis, start=_start, end=_end, undolist=ul)

        set_axis(layer.xaxis, x0, x1)
        set_axis(layer.yaxis, y0, y1)
        
        uwrap.emit_last( self.plot, "changed", undolist=ul )
        
        undolist.append(ul)

    def axes_from_xy(self, x, y):
        " x,y should be plot coordinates, not screen coordinates. "
        for layer in self.plot.layers:
            axes = self.backend.layer_to_axes[layer]
            if axes.bbox.contains(x,y) == 1:
                return axes
        else:
            return None

    # might be used in ZoomSelector as well
    # => either static method or put it somewhere else
    def calculate_zoom_region(self, axes, dx=0.1, dy=0.1):
        xmin, xmax = axes.get_xlim()
        width = (xmax-xmin)
        if axes.get_xscale() == 'log':
            alphax = pow(10.0, dx)
            xmin *= alphax
            xmax /= alphax
        else: # linear
            xmin += width*dx
            xmax -= width*dx

        ymin, ymax = axes.get_ylim()
        height = ymax-ymin
        if axes.get_yscale() == 'log':
            alphay = pow(10.0, dy)
            ymin *= alphay
            ymax /= alphay
        else: # linear
            ymin += height*dy
            ymax -= height*dy

        return (xmin, ymin, xmax, ymax)


    #------------------------------------------------------------------------------

    # current layer: OK
    def on_action_ZoomRect(self, action):

        def finish_zooming(sender):
            self.statusbar.pop(
                self.statusbar.get_context_id('action-zoom'))

            ul = UndoList().describe("Zoom Region")
            layer = self.backend.axes_to_layer[sender.axes]
            self.zoom_to_region(layer, sender.region, undolist=ul)
            self.project.journal.add_undo(ul)           

        layer = self.backend.layer
        axes = self.backend.layer_to_axes[layer]
        s = mpl_selector.SelectRegion(self.backend.figure, axes=axes)
        s.sig_connect('finished', finish_zooming)
        self.statusbar.push(
            self.statusbar.get_context_id('action-zoom'),
            "Use the left mouse button to zoom.")

        self.select(s)


    # current layer: OK
    def on_action_ZoomFit(self, action):
        self.abort_selection()

        layer = self.backend.layer
        if layer is not None:
            region = (None,None,None,None)
            self.zoom_to_region(layer, region, undolist=self.app.project.journal)


    # current layer: OK            
    def on_action_ZoomIn(self, action):
        self.abort_selection()

        layer = self.backend.layer
        if layer is not None:
            axes = self.backend.layer_to_axes[layer]
            region = self.calculate_zoom_region(axes)
            self.zoom_to_region(layer, region, undolist=self.app.project.journal)

        
    # current layer: OK    
    def on_action_ZoomOut(self, action):
        self.abort_selection()

        layer = self.backend.layer
        if layer is not None:
            axes = self.backend.layer_to_axes[layer]
            region = self.calculate_zoom_region(axes, dx=-0.1, dy=-0.1)
            self.zoom_to_region(layer, region, undolist=self.app.project.journal)

              
    # current layer: OK
    def on_action_ToggleLogScaleY(self, action):
        self.abort_selection()
        
        layer = self.backend.layer
        if layer is not None:        
            p = self.app.plugins['Default']
            p.toggle_logscale_y(self.plot, layer)

        
    # current layer: OK
    def on_action_MoveAxes(self, action):

        def finish_moving(sender):
            ul = UndoList().describe("Move Graph")
            layer = self.backend.axes_to_layer[sender.axes]
            self.zoom_to_region(layer, sender.region, undolist=ul)
            self.project.journal.add_undo(ul)           

        layer = self.backend.layer
        axes = self.backend.layer_to_axes[layer]
        s = mpl_selector.MoveAxes(self.backend.figure, axes)
        s.sig_connect("finished", finish_moving)

        self.select(s)
        

    # current layer: OK
    def on_action_DataCursor(self, action):

        layer = self.backend.layer
        axes = self.backend.layer_to_axes[layer]
        s = mpl_selector.DataCursor(self.backend.figure, axes)

        def abort_selector(sender, context_id):
            self.statusbar.pop(context_id)
            
        def finish_selector(sender, context_id):
            self.statusbar.pop(context_id)
            xvalue, yvalue = sender.point

        def update_position(sender, line, index, point, context_id):
            # Note that 'line' is a Line2d instance from matplotlib!
            x, y = point
            self.statusbar.pop(context_id)
            self.statusbar.push(context_id, "X: %f, Y: %f (value #%s)" %
                                (x, y, index))

        context_id = self.statusbar.get_context_id("data_cursor")
        s.sig_connect("update-position", update_position, context_id)
        s.sig_connect("finished", finish_selector, context_id)
        s.sig_connect("aborted", abort_selector, context_id)
        
        self.select(s)


    # current layer: OK
    def on_action_SelectLine(self, action):
            
        def finish_select_line(sender):
            print "FINISHED SELECT LINE", sender.line

        layer = self.backend.layer
        axes = self.backend.layer_to_axes[layer]
        s = mpl_selector.SelectLine(self.backend.figure, axes,
                                    mode=mpl_selector.SELECTLINE_VERTICAL)
        s.sig_connect("finished", finish_select_line)
        
        self.select(s)


    # current layer: OK
    def on_action_ZoomAxes(self, action):

        def finish_moving(sender):
            ul = UndoList().describe("Zoom Axes")
            layer = self.backend.axes_to_layer[sender.axes]
            self.zoom_to_region(layer, sender.region, undolist=ul)
            self.project.journal.add_undo(ul)           

        layer = self.backend.layer
        axes = self.backend.layer_to_axes[layer]
        s = mpl_selector.ZoomAxes(self.backend.figure, axes)
        s.sig_connect("finished", finish_moving)

        self.select(s)
        
        
    #----------------------------------------------------------------------
    def abort_selection(self):
        if self._current_selector is not None:
            self._current_selector.abort()
            self._current_selector = None

        for ag in self.get_actiongroups():
            ag.set_sensitive(True)

        self.btn_cancel.set_sensitive(False)


    def select(self, selector):

        self.emit("edit-mode-started")

        self._current_selector = None
        
        def on_finish(sender):            
            # Be careful not to call self.abort_selection() in this place.
            print "---"
            print "ABORTING"            
            self._current_selector = None
            self.btn_cancel.set_sensitive(False)
            self.emit("edit-mode-ended")

        self.btn_cancel.set_sensitive(True)
        self.btn_cancel.connect("clicked", (lambda sender: self.abort_selection()))

        selector.sig_connect("finished", on_finish)
        selector.sig_connect("aborted", on_finish)
        self._current_selector = selector
        selector.init()


   #----------------------------------------------------------------------
   # other callbacks

   
    def on_action_ExportViaMPL(self, action):
        self.abort_selection()

        # TODO: pick filename based on self.get_plot().key
        fname = self.fileselect.get_filename_from_user()
        if fname is not None:
            self.backend.canvas.print_figure(fname)


    def on_action_ExportViaGnuplot(self, action):
        self.abort_selection()

        self.app.plot_postscript(self.project, self.plot)
        

    #
    # TESTING
    #
    def on_action_PeakFinder(self, action):
        self.abort_selection()

        # we will simply take the first line available.
        layer = self.backend.layer
        line = layer.lines[0]

        print "USING LINE ", line

        p = self.app.get_plugin('PeakFinder')
        data = line.source.get_data()

        print
        print "Peak Search:"
        peaks = p.find_peaks(data[line.cx], data[line.cy], 600, 5)
        for x, y in peaks:
            print "  %f : %f" % (x,y)
        print

        p = self.app.get_plugin('PeakFinder::GTK::DialogBuilder')
        dialog = p.new_dialog()
        dialog.run()

        # a dialog should ask for the following:

        # Line (=> cx and cy will be automatically determined)
        # threshold
        # accuracy
        # max. nr. of points before aborting.

        # It should then have a list view with the list of points
        # and some options, e.g. 'add as label'.

        # In the next step, we will have a SIMS isotope library in
        # the SIMS plugin.  The SIMS plugin can then utilize the find_peak
        # method, look up the isotopes and determine the possible isotopes
        # from that!


#==============================================================================
gobject.type_register(MatplotlibWidget)        
        


