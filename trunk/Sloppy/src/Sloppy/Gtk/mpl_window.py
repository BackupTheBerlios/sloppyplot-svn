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
import Numeric

import uihelper
import mpl_selector

from matplotlib.backends.backend_gtk import FileChooserDialog


from Sloppy.Base import uwrap
from Sloppy.Base.backend import BackendRegistry
from Sloppy.Base.plugin import PluginRegistry

from Sloppy.Lib.Undo import UndoList, NullUndo, ulist
from Sloppy.Lib import Signals




class MatplotlibWindow( gtk.Window ):

    actions_dict = {
        'View':
        [
        ('EditMenu', None, '_Edit'),
        ('PlotMenu', None, '_Plot'),
        ('DisplayMenu', None, '_Display'),
        ('AnalysisMenu', None, '_Analysis'),
        ('ViewMenu', None, '_View'),
        ('Fullscreen', None, 'Fullscreen Mode', 'F11', '', '_cb_fullscreen')
        ]
        }

    action_list = ['/MainMenu/PlotMenu',
                   '/MainMenu/EditMenu',
                   '/MainMenu/DisplayMenu',
                   '/MainMenu/AnalysisMenu']

    uistring = """
    <ui>
      <menubar name='MainMenu'>
        <menu action='PlotMenu'/>
        <menu action='EditMenu'>
          <menuitem action='Undo'/>
          <menuitem action='Redo'/>
        </menu>
        <menu action='DisplayMenu'/>
        <menu action='AnalysisMenu'/>
        <menu action='ViewMenu'>
          <menuitem action='Fullscreen'/>
        </menu>
      </menubar>
      <toolbar name='MainToolbar'>
        <toolitem action='Undo'/>
        <toolitem action='Redo'/>
        <separator/>              
      </toolbar>
    </ui>
    """

    
    def __init__(self, app, project, plot):

        gtk.Window.__init__(self)
        self.set_default_size(640,480)
        #self.set_transient_for(app.window)
        self.is_fullscreen = False
        self.app = app
        self.ag_escape = None
        
        self.mpl_widget = MatplotlibWidget(app, project, plot)

        # set up ui manager
        self.uimanager = gtk.UIManager()        

        # add ui from application window
        ag = uihelper.get_action_group(self.app.window.uimanager, 'UndoRedo')
        self.uimanager.insert_action_group(ag,0)
        
        # add ui information from window
        for ag in uihelper.construct_actiongroups(self.actions_dict, map=self):
            self.uimanager.insert_action_group(ag,0)
        self.uimanager.add_ui_from_string(self.uistring)

        # add ui information from subwidget
        for ag in self.mpl_widget.get_actiongroups():
            self.uimanager.insert_action_group(ag,0)
        self.uimanager.add_ui_from_string(self.mpl_widget.get_uistring())

        # and set up accelerators for all of the above
        self.add_accel_group(self.uimanager.get_accel_group())

        
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
        Signals.connect(self.mpl_widget, "closed", (lambda sender: self.destroy()))

    def destroy(self):
        print "====================="
        self.mpl_widget.set_plot(None)
        gtk.Window.destroy(self)



    def disable_interaction(self, widget):
        uihelper.set_actions(self.uimanager, self.action_list, False)

        print "Adding accel group for ESCAPE"

        def my_callback(self, sender):
            print
            print "MY CALLBACK"
            print

        ag = gtk.AccelGroup()
        key, modifier = gtk.accelerator_parse('Escape')
        ag.connect_group(key, modifier, gtk.ACCEL_VISIBLE, my_callback)
        self.add_accel_group(ag)        
        
        self.ag_escape = ag


    def enable_interaction(self, widget):
        print "Removing accel group again"
        uihelper.set_actions(self.uimanager, self.action_list, True)                     
        self.remove_accel_group(self.ag_escape)

        

    def get_project(self):
        return self.mpl_widget.project

    def get_plot(self):
        return self.mpl_widget.plot


    def _cb_fullscreen(self, action):
        " Toggle fullscreen mode. "
        if self.is_fullscreen is True:
            self.unfullscreen()
        else:
            self.fullscreen()
        self.is_fullscreen = not self.is_fullscreen







class MatplotlibWidget(gtk.VBox):


    __gsignals__ = {
        'edit-mode-started' : (gobject.SIGNAL_RUN_FIRST , gobject.TYPE_NONE, ()),
        'edit-mode-ended' : (gobject.SIGNAL_RUN_FIRST , gobject.TYPE_NONE, ())        
        }

    
    actions_dict = {
        'Plot':
        [
        ('PlotMenu', None, '_Plot'),
        ('Replot', 'sloppy-replot', '_Replot', '<control>R', 'Replot', '_cb_replot'),
        ('Edit', gtk.STOCK_PROPERTIES, '_Edit', '<control>E', 'Edit', '_cb_edit'),
        ('Save As', gtk.STOCK_SAVE_AS, '_Save As', '<control><shift>S', 'Save As', '_cb_save_as'),
        ('Close', gtk.STOCK_CLOSE, '_Close', 'q', 'Close this Window', '_cb_close')
        ],
        'Analysis':
        [
        ('AnalysisMenu', None, '_Analysis')
        ],
        'Display':
        [
        ('DisplayMenu', None, '_Display'),
        ('ZoomIn', gtk.STOCK_ZOOM_IN, '_Zoom In', 'plus', 'Zoom', '_cb_zoom_in'),
        ('ZoomOut', gtk.STOCK_ZOOM_OUT, '_Zoom Out', 'minus', 'Zoom', '_cb_zoom_out'),
        ('ZoomFit', gtk.STOCK_ZOOM_FIT, '_Zoom Fit', '0', 'Zoom', '_cb_zoom_fit'),
        ('ZoomRect', gtk.STOCK_ZOOM_IN, '_Zoom Rectangle', 'r', 'Zoom', '_cb_zoom_rect'),
        ('ToggleLogScale', None, 'Toggle Logarithmic Scale', 'l', 'Toggle Logscale', '_cb_toggle_logscale'),
        ('MovePlot', None, 'Move Plot', 'm', '', '_cb_move_plot'),
        ('DataCursor', None, 'Data Cursor', 'c', '', '_cb_data_cursor'),
        ('SelectLine', None, 'Select Line', 's', '', '_cb_select_line'),
        ('ZoomAxes', None, 'Zoom Axes', 'z', '', '_cb_zoom_axes')
        ],
        }

    uistring = """
    <ui>
      <menubar name='MainMenu'>
        <menu action='PlotMenu'>
          <menuitem action='Replot'/>
          <menuitem action='Edit'/>
          <menuitem action='Save As'/>
          <separator/>
          <menuitem action='Close'/>
        </menu>
        <menu action='AnalysisMenu'>
          <menuitem action='DataCursor'/>
        </menu>
        <menu action='DisplayMenu'>
          <menuitem action='ToggleLogScale'/>
          <separator/>
          <menuitem action='ZoomRect'/>
          <menuitem action='ZoomIn'/>
          <menuitem action='ZoomOut'/>
          <menuitem action='ZoomFit'/>
          <menuitem action='ZoomAxes'/>          
          <separator/>
          <menuitem action='MovePlot'/>
        </menu>
      </menubar>
      <toolbar name='MainToolbar'>
        <toolitem action='ZoomIn'/>
        <toolitem action='ZoomFit'/>
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
        self.statusbar.push(self.context_id, "X: 10, Y: 20")
        self.statusbar.pop(self.context_id)
        
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

        self.set_plot(plot)
        Signals.connect(self.project, "close", (lambda sender: self.destroy()))

        ### prepare file selector
        ### TODO: this could be put into a plugin, since it is desirable to have
        ### TODO: such a method in the shell frontend as well.
        ##self.fileselect = FileChooserDialog(title='Save the figure', parent=self.parent_window)


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

        for signal in self._signals:
            Signals.disconnect(signal)
        self._signals = []
        
        if self.cursor is not None:
            self.cursor.finish()

        # connect new backend
        self.plot = plot
        self.backend = backend


        if backend is not None:
            self._signals.extend(
                [Signals.connect(plot, "plot-changed", (lambda sender: backend.draw())),
                 Signals.connect(plot, "closed", (lambda sender: Signals.emit(self, 'closed')))]
                )
            try:
                backend.draw()
            except:
                #gtkutils.info_msg("Nothing to plot.")
                raise            

            # Cursor
            self.cursor = mpl_selector.Cursor(self.backend.figure)
            Signals.connect(self.cursor, "move",
                            (lambda sender,x,y: self.set_coords(x,y)))
            self.cursor.init()

        
    #----------------------------------------------------------------------
    def _cb_close(self, action):
        self.destroy()

    def _cb_replot(self, action):
        self.backend.draw()

    def _cb_edit(self, action):
        self.app.edit_layer( self.plot, self.plot.layers[0] )        

    #----------------------------------------------------------------------

    def zoom_to_region(self, layer, region, undolist=[]):
       
        ul = UndoList()

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

        def set_axis(key, start, end):
            axis = layer.request_axis(key, undolist=ul)            
            if axis.start is not None and axis.end is not None:
                swap_axes = axis.start > axis.end
            else:
                swap_axes = False

            if swap_axes is True:
                _start, _end = end, start
            else:
                _start, _end = start, end
                
            uwrap.set(axis, start=_start, end=_end, undolist=ul)

        set_axis('x', x0, x1)
        set_axis('y', y0, y1)
        
        uwrap.emit_last( self.plot, "plot-changed", undolist=ul )
        
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
        
    def _cb_zoom_rect(self, action):

        def finish_zooming(sender):
            self.statusbar.pop(
                self.statusbar.get_context_id('action-zoom'))

            ul = UndoList().describe("Zoom Region")
            layer = self.backend.axes_to_layer[sender.axes]
            self.zoom_to_region(layer, sender.region, undolist=ul)
            self.project.journal.add_undo(ul)           
        
        s = mpl_selector.SelectRegion(self.backend.figure)
        Signals.connect(s, 'finished', finish_zooming)
        self.statusbar.push(
            self.statusbar.get_context_id('action-zoom'),
            "Use the left mouse button to zoom.")

        self.select(s)


    def _cb_zoom_fit(self, action):
        self.abort_selection()


        x,y,state = self.backend.canvas.window.get_pointer()
        y = self.backend.canvas.figure.bbox.height() - y
        axes = self.axes_from_xy(x,y)
        
        if axes is not None:
            layer = self.backend.axes_to_layer[axes]            
            region = (None,None,None,None)
            self.zoom_to_region(layer, region, undolist=self.app.project.journal)


    def _cb_zoom_in(self, action):
        self.abort_selection()

        x,y,state = self.backend.canvas.window.get_pointer()
        y = self.backend.canvas.figure.bbox.height() - y
        axes = self.axes_from_xy(x,y)
        
        if axes is not None:
            layer = self.backend.axes_to_layer[axes]            
            region = self.calculate_zoom_region(axes)
            self.zoom_to_region(layer, region, undolist=self.app.project.journal)
        
        
    def _cb_zoom_out(self, action):
        self.abort_selection()

        x,y,state = self.backend.canvas.window.get_pointer()
        y = self.backend.canvas.figure.bbox.height() - y
        axes = self.axes_from_xy(x,y)
        
        if axes is not None:
            layer = self.backend.axes_to_layer[axes]
            region = self.calculate_zoom_region(axes, dx=-0.1, dy=-0.1)
            self.zoom_to_region(layer, region, undolist=self.app.project.journal)

        

    def _cb_save_as(self, action):
        self.abort_selection()

        # TODO: call plugin method or something.
        return
    
        # pick filename  self.plot.key
        fname = self.fileselect.get_filename_from_user()
        if fname is not None:
            self.backend.canvas.print_figure(fname)
      

    def _cb_toggle_logscale(self, action):
        self.abort_selection()
        
        p = self.app.plugins['Default']
        p.toggle_logscale_y(self.plot, self.plot.layers[0])

        

    def _cb_move_plot(self, action):

        def finish_moving(sender):
            ul = UndoList().describe("Move Graph")
            layer = self.backend.axes_to_layer[sender.axes]
            self.zoom_to_region(layer, sender.region, undolist=ul)
            self.project.journal.add_undo(ul)           
           
        s = mpl_selector.MoveAxes(self.backend.figure)        
        Signals.connect(s, "finished", finish_moving)

        self.select(s)
        


    def _cb_data_cursor(self, action):

        s = mpl_selector.DataCursor(self.backend.figure)

        def abort_selector(sender, context_id):
            self.statusbar.pop(context_id)
            
        def finish_selector(sender, context_id):
            self.statusbar.pop(context_id)
            xvalue, yvalue = sender.point
            print "FINISHED", xvalue, yvalue

        def update_position(sender, context_id, line, index, point):
            # Note that 'line' is a Line2d instance from matplotlib!
            x, y = point
            self.statusbar.pop(context_id)
            self.statusbar.push(context_id, "[%4d] %f,%f" % (index, x, y))

        context_id = self.statusbar.get_context_id("data_cursor")
        Signals.connect(s, "update-position", update_position, context_id)
        Signals.connect(s, "finished", finish_selector, context_id)
        Signals.connect(s, "aborted", abort_selector, context_id)
        
        self.select(s)


    def _cb_select_line(self, action):
            
        def finish_select_line(sender):
            print "FINISHED SELECT LINE", sender.line

        s = mpl_selector.SelectLine(self.backend.figure,mode=mpl_selector.SELECTLINE_VERTICAL)
        Signals.connect(s, "finished", finish_select_line)
        
        self.select(s)


    def _cb_zoom_axes(self, action):

        def finish_moving(sender):
            ul = UndoList().describe("Zoom")
            layer = self.backend.axes_to_layer[sender.axes]
            self.zoom_to_region(layer, sender.region, undolist=ul)
            self.project.journal.add_undo(ul)           
           
        s = mpl_selector.ZoomAxes(self.backend.figure)
        Signals.connect(s, "finished", finish_moving)

        self.select(s)
        
        
    #----------------------------------------------------------------------
    def abort_selection(self):
        print "ABORTING"
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
            print "FINISHING"
            # Be careful not to call self.abort_selection() in this place.
            self._current_selector = None
            self.btn_cancel.set_sensitive(False)
            self.emit("edit-mode-ended")

        self.btn_cancel.set_sensitive(True)
        self.btn_cancel.connect("clicked", (lambda sender: self.abort_selection()))
        
        Signals.connect(selector, "finished", on_finish)
        Signals.connect(selector, "aborted", on_finish)
        self._current_selector = selector
        selector.init()

gobject.type_register(MatplotlibWidget)        
        
